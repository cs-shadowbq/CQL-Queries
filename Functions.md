# CQL Advanced Functions

These four functions — `correlate()`, `coalesce()`, `series()`, and `neighbor()` — unlock powerful analytical patterns in CQL (CrowdStrike Query Language / LogScale). They are frequently underutilized but are essential for event correlation, data normalization, session reconstruction, and row-level delta analysis.

All examples below use `createEvents()` so they can be run immediately in any LogScale repository **without needing external data**.

## Best Practices

### Pipeline Ordering

Follow the standard CQL optimization order — filter early, aggregate late. Place `coalesce()` immediately after tag/field filters so all downstream steps operate on clean, normalized fields. Apply `sort()` before any `neighbor()` call.

| Step | Functions Used |
|---|---|
| Time | *(no functions here — narrow the search window first)* |
| Tags | *(no functions here — filter on indexed tag fields like `#repo`, `#event_simpleName`)* |
| Filter | `coalesce()` — normalize field names before any downstream filtering |
| Neg Filter | *(no functions here — exclude unwanted values after positive filters)* |
| Regex | *(no functions here — apply regex extraction last among filters)* |
| Functions | `neighbor()` — compute row-to-row deltas after `sort()`; requires sorted pipeline |
| Aggregate | `series()` — reconstruct sessions per group inside `groupBy()` |
| Aggregate | `correlate()` — join independent sub-query streams on a shared key |
| Rename | *(no functions here — rename fields before view)* |
| Join Data | `correlate()` also applies here when joining across log sources |
| View | *(no functions here — `table()`, `sort()` for final presentation)* |

### `coalesce()`

- List fields in **priority order** — most authoritative source first, literal default last.
- Use `ignoreEmpty=false` only when an empty string is a valid, meaningful value.
- For field names with hyphens or spaces, wrap them in `getField()`: `coalesce([getField("host-name"), hostname, "unknown"])`.
- Assign the result to a new named field (`:=`) rather than relying on the default `_coalesce` output field.

### `neighbor()`

- Always `sort()` before calling `neighbor()`. Without a sort, the adjacent row is undefined.
- Use `sort(field=[identity, ts])` followed by `groupBy([identity], function=neighbor(...))` when your data spans multiple entities. Pass only `neighbor()` as the single `function=` argument — combining it with other functions in `function=[]` produces a cartesian product error.
- Handle null on the first row with `default(value="...", field=[prev.field])` immediately after `neighbor()`. The output field name is `prefix.field` (e.g., `neighbor(bytes_total, prefix=prev)` → `prev.bytes_total`). Without `default()`, the first row's result field will be empty and arithmetic on it will produce null.
- Use `direction=succeeding` to look forward instead of back. The `distance` parameter is always a positive integer (default `1`); it controls how many events to skip, not direction.

### `series()`

- Always run inside `groupBy()` when correlating per identity (user, session ID, host). Top-level `series()` aggregates the entire result set into one event.
- Set `memlimit` explicitly for large or long-running sessions — the default `1KiB` cap will silently truncate high-cardinality series.
- Use `maxpause=` to split a continuous stream into discrete sessions (e.g., `maxpause=5min` for web visits). This avoids one enormous series spanning hours of inactivity.
- Use `startmatch={}` / `endmatch={}` when your data has explicit session delimiters (login/logout, job start/stop). Filters must be field-specific (e.g., `startmatch={ msg=/Login attempt:/ }`) — free-text regex is not supported inside aggregate contexts. `startmatch` drops events before the first start; `endmatch` does not drop partial sessions.
- Choose a separator that cannot appear in your data values. Semicolon (`;`), pipe (`|`), or arrow (` → `) are common safe choices.

### `correlate()`

- Pre-filter aggressively inside each sub-query. Every sub-query is a full pipeline execution — unfiltered sub-queries multiply cost.
- Always place tag filters (`#repo`, `#event_simpleName`) as the first statement inside each sub-query block.
- Use the `<=>` link operator to declare relationships explicitly. All fields used in `on=[]` must exist in the events produced by their respective sub-query.
- Start with two sub-queries and validate the match count before adding a third. Adding streams multiplies the join space.
- `correlate()` cannot be used in parsers (no aggregate functions in parsers). It is a query-only function.

---

## `coalesce()` — First Non-Null Field Selection

### Why Use It

Real-world data sources are inconsistent. A hostname might appear as `host`, `hostname`, `server`, or `agent_name` depending on the parser, product, or schema version. `coalesce()` picks the **first non-null, non-empty value** from a prioritized list of expressions — eliminating verbose `case` or `if()` chains.

It also accepts **string literals** as fallback defaults, making it safe to use even when no field is present.

```
coalesce([field1, field2, field3, "default_value"])
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `expressions` | list of expressions | required | Ordered candidate list; first non-null result is returned |
| `as` | string | `_coalesce` | Output field name |
| `ignoreEmpty` | boolean | `true` | Treat empty strings as null |

### Use Case 1 — Normalize Inconsistent Hostname Fields

Different log sources use different field names for the same concept. Normalize them into a single `host_normalized` field before grouping.

```f#
createEvents([
  "{\"host\":\"web-01\",     \"src_port\":\"443\"}",
  "{\"hostname\":\"db-02\",  \"src_port\":\"5432\"}",
  "{\"server\":\"cache-03\", \"src_port\":\"6379\"}",
  "{\"src_port\":\"22\"}"
])
| parseJson()
// Pick the first non-null value from the candidate fields
| host_normalized := coalesce([host, hostname, server, "unknown"])
| table([host_normalized, src_port])
```

**Expected output:**

| host_normalized | src_port |
|---|---|
| web-01 | 443 |
| db-02 | 5432 |
| cache-03 | 6379 |
| unknown | 22 |

### Use Case 2 — Safe Fallback in Expressions with `getField()`

When a field name contains characters unsupported in bare expressions (e.g., hyphens, spaces), use `getField()` inside `coalesce()`:

```f#
// Handles field names like "host-name" or "source ip" that cannot be quoted directly
| host_normalized := coalesce([getField("host-name"), getField("source ip"), hostname, "unknown"])
```

### Use Case 3 — Default Value for Missing Severity

```f#
createEvents([
  "{\"event\":\"alert\", \"severity\":\"high\"}",
  "{\"event\":\"alert\"}",
  "{\"event\":\"info\",  \"severity\":\"\"}"
])
| parseJson()
// severity may be missing or empty; default to "informational"
| severity_norm := coalesce([severity, "informational"])
| table([event, severity, severity_norm])
```

**Expected output:**

| event | severity | severity_norm |
|---|---|---|
| alert | high | high |
| alert | (no value) | informational |
| info | (empty string) | informational |

> **Best practice:** Place `coalesce()` early in the pipeline, before any `groupBy()` or `table()` that depends on the normalized field. This avoids null-group noise in aggregation results.

---

## `neighbor()` — Row-to-Row Delta and Context

### Why Use It

`neighbor()` reads field values from **adjacent events** in the current result stream (the event immediately before or after). It is essential for:

- Calculating byte/count **deltas** between consecutive metric events
- Detecting **state transitions** (e.g., process started then terminated)
- Carrying **context forward** from one event to the next (e.g., marking the event that preceded an alert)

`neighbor()` is a **non-aggregate** transformation — it operates row-by-row on the sorted pipeline. Always `sort()` before using it.

```
neighbor(field, prefix=prev)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `include` | string | required | Field name(s) to read from the neighboring event (argument name may be omitted) |
| `prefix` | string | *(none)* | Prefix added to the included field names in output (e.g., `prefix=prev` → output field `prev.field`) |
| `distance` | integer | `1` | Number of events to look ahead or behind (always positive; use `direction` to control which way) |
| `direction` | enum | `preceding` | `preceding` (look back) or `succeeding` (look forward) |

### Use Case 1 — Bytes Transferred Delta Between Metric Events

Cumulative counters need differencing to produce per-interval rates.

```f#
createEvents([
  "{\"host\":\"fw-01\", \"ts\":\"1\", \"bytes_total\":\"1000\"}",
  "{\"host\":\"fw-01\", \"ts\":\"2\", \"bytes_total\":\"2500\"}",
  "{\"host\":\"fw-01\", \"ts\":\"3\", \"bytes_total\":\"4200\"}",
  "{\"host\":\"fw-01\", \"ts\":\"4\", \"bytes_total\":\"4200\"}"
])
| parseJson()
| sort(field=ts, order=asc)
// Read bytes_total from the previous row; output field is prev.bytes_total
| neighbor(bytes_total, prefix=prev)
// Fill null on the first row (no prior neighbor) with 0
| default(value="0", field=[prev.bytes_total])
| bytes_delta := bytes_total - prev.bytes_total
// Drop the first row where prev.bytes_total is "0" (no prior context)
| test(bytes_delta >= 0)
| table([host, ts, bytes_total, prev.bytes_total, bytes_delta])
```

**Expected output:**

| host | ts | bytes_total | prev.bytes_total | bytes_delta |
|---|---|---|---|---|
| fw-01 | 1 | 1000 | 0 | 1000 |
| fw-01 | 2 | 2500 | 1000 | 1500 |
| fw-01 | 3 | 4200 | 2500 | 1700 |
| fw-01 | 4 | 4200 | 4200 | 0 |

### Use Case 2 — Detect State Transitions (Process Start → Stop)

Flag events where a process state changed compared to the previous event for the same host.

```f#
createEvents([
  "{\"host\":\"ws-01\", \"ts\":\"1\", \"process\":\"svchost\", \"state\":\"running\"}",
  "{\"host\":\"ws-01\", \"ts\":\"2\", \"process\":\"svchost\", \"state\":\"running\"}",
  "{\"host\":\"ws-01\", \"ts\":\"3\", \"process\":\"svchost\", \"state\":\"stopped\"}",
  "{\"host\":\"ws-01\", \"ts\":\"4\", \"process\":\"svchost\", \"state\":\"running\"}"
])
| parseJson()
| sort(field=ts, order=asc)
| neighbor(state, prefix=prev)
| default(value="unknown", field=[prev.state])
// Only surface rows where state changed
| state_changed := if(state != prev.state, then="YES", else="no")
| state_changed = "YES"
| table([host, ts, process, prev.state, state])
```

**Expected output:**

| host | ts | process | prev.state | state |
|---|---|---|---|---|
| ws-01 | 1 | svchost | unknown | running |
| ws-01 | 3 | svchost | running | stopped |
| ws-01 | 4 | svchost | stopped | running |

### Use Case 3 — Respect Group Boundaries Across Multiple Hosts

When the event stream contains multiple entities (hosts, users, sessions), a top-level `neighbor()` will bleed across group boundaries — the last event for `host-A` will become the neighbor of the first event for `host-B`. Wrap `sort()` and `neighbor()` inside `groupBy()` to keep each entity's sequence isolated.

```f#
createEvents([
  "{\"host\":\"fw-01\", \"ts\":\"1\", \"bytes_total\":\"1000\"}",
  "{\"host\":\"fw-01\", \"ts\":\"2\", \"bytes_total\":\"3500\"}",
  "{\"host\":\"fw-01\", \"ts\":\"3\", \"bytes_total\":\"6000\"}",
  "{\"host\":\"fw-02\", \"ts\":\"1\", \"bytes_total\":\"500\"}",
  "{\"host\":\"fw-02\", \"ts\":\"2\", \"bytes_total\":\"2000\"}",
  "{\"host\":\"fw-02\", \"ts\":\"3\", \"bytes_total\":\"2000\"}"
])
| parseJson()
// Pre-sort by host then ts so neighbor() sees events in the right order within each group
| sort(field=[host, ts], order=asc)
// groupBy isolates neighbor() to each host — only neighbor() as the function (no array)
| groupBy([host], function=neighbor(bytes_total, prefix=prev))
| default(value="0", field=[prev.bytes_total])
| bytes_delta := bytes_total - prev.bytes_total
| test(bytes_delta >= 0)
| table([host, ts, bytes_total, prev.bytes_total, bytes_delta])
```

**Expected output:**

| host | ts | bytes_total | prev.bytes_total | bytes_delta |
|---|---|---|---|---|
| fw-01 | 1 | 1000 | 0 | 1000 |
| fw-01 | 2 | 3500 | 1000 | 2500 |
| fw-01 | 3 | 6000 | 3500 | 2500 |
| fw-02 | 1 | 500 | 0 | 500 |
| fw-02 | 2 | 2000 | 500 | 1500 |
| fw-02 | 3 | 2000 | 2000 | 0 |

---

## `series()` — Session/Transaction Reconstruction

### Why Use It

`series()` collapses a **sequence of related events** into a single event whose fields contain the ordered, concatenated values. Combined with `groupBy()`, it answers questions like:

- "What URLs did this user visit in a single session?"
- "What was the command sequence in this process lineage?"
- "Which authentication events belong to one login session?"

`series()` is an **aggregate function** — it must be used inside `groupBy()` or at the top level. The output is one event per series (or per group), with field values joined by a configurable separator.

```
groupBy(identity_field, function=series(collect=[fields], separator=";", maxpause=5min))
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `collect` | array of strings | required | Fields whose values are concatenated in time order |
| `separator` | string | `\n` | String placed between collected values |
| `maxpause` | relative-time | none | Start a new series if this gap between events is exceeded |
| `maxduration` | relative-time | none | Hard cap on total series duration |
| `startmatch` | filter | none | Filter expression that marks the start of a new series |
| `endmatch` | filter | none | Filter expression that marks the end of a series |
| `memlimit` | string | `1KiB` | Per-invocation memory cap for collected values |

The output event includes:

- `_duration` — milliseconds between first and last event in the series
- `@timestamp` — timestamp of the first event in the series

### Use Case 1 — Reconstruct HTTP Session URL Path

```f#
createEvents([
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T10:00:00Z\", \"url\":\"/login\",    \"method\":\"POST\"}",
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T10:02:30Z\", \"url\":\"/home\",     \"method\":\"GET\"}",
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T10:05:00Z\", \"url\":\"/settings\", \"method\":\"GET\"}",
  "{\"session\":\"s2\", \"ts\":\"2024-01-01T10:00:00Z\", \"url\":\"/login\",    \"method\":\"POST\"}",
  "{\"session\":\"s2\", \"ts\":\"2024-01-01T10:01:00Z\", \"url\":\"/admin\",    \"method\":\"GET\"}"
])
| parseJson()
// Promote the ts field to @timestamp so series() computes a real _duration
| findTimestamp(field=ts)
| groupBy([session], function=series(collect=[url, method], separator=" → "))
| table([session, url, method, _duration])
```

**Expected output:**

| session | url | method | _duration |
|---|---|---|---|
| s1 | /login → /home → /settings | POST → GET → GET | 300000 |
| s2 | /login → /admin | POST → GET | 60000 |

> `_duration` is in milliseconds — s1 spans 5 minutes (300,000 ms), s2 spans 1 minute (60,000 ms). Without `findTimestamp()`, all events share the query execution timestamp and `_duration` is always `0`.

### Use Case 2 — Detect Brute-Force Login Sequences with `startmatch`/`endmatch`

Partition authentication logs into per-user windows that start on `Login attempt:` and end on `Failed Login`. Each window becomes one output event with a concatenated message trail.

```f#
createEvents([
  "{\"user\":\"alice\", \"ts\":\"2024-01-01T10:00:00Z\", \"msg\":\"Login attempt: alice\"}",
  "{\"user\":\"alice\", \"ts\":\"2024-01-01T10:00:15Z\", \"msg\":\"Bad password\"}",
  "{\"user\":\"alice\", \"ts\":\"2024-01-01T10:00:30Z\", \"msg\":\"Failed Login\"}",
  "{\"user\":\"alice\", \"ts\":\"2024-01-01T10:01:00Z\", \"msg\":\"Login attempt: alice\"}",
  "{\"user\":\"alice\", \"ts\":\"2024-01-01T10:01:45Z\", \"msg\":\"Success\"}"
])
| parseJson()
// Promote ts to @timestamp so series() measures real elapsed time per window
| findTimestamp(field=ts)
| groupBy([user], function=series(
    collect=[msg],
    separator=" | ",
    startmatch={ msg=/Login attempt:/ },
    endmatch={ msg=/Failed Login/ }
  ))
| table([user, msg, _duration])
```

**Expected output:**

| user | msg | _duration |
|---|---|---|
| alice | Login attempt: alice \| Success | 45000 |
| alice | Login attempt: alice \| Bad password \| Failed Login | 30000 |

> **Notes:**
>
> - `_duration` is the millisecond difference between `@timestamp` of the **first and last event** in the series. The first window (attempt → failed login) spans 30 seconds (30,000 ms); the second (attempt → success) spans 45 seconds. Without `findTimestamp()`, all events share the query execution time and `_duration` is `0`.
> - `endmatch` closes the window when the pattern matches but does **not** discard open/partial series. The second window has no `Failed Login` so it remains open and is still returned — useful for detecting incomplete or in-progress attack sequences.
> - Use `collect=[msg]` rather than `collect=[@rawstring]` when you only need the message content. Collecting `@rawstring` concatenates full raw event strings, which is verbose and will break markdown table rendering if the separator is ` | `.

### Use Case 3 — Aggregate Visit Bursts with `maxpause`

Split activity into distinct "visits" by restarting the series after a 30-second gap. Two IPs are included to show per-group series splitting independently.

```f#
createEvents([
  "{\"client_ip\":\"10.0.0.1\", \"ts\":\"2024-01-01T10:00:00Z\", \"url\":\"/login\"}",
  "{\"client_ip\":\"10.0.0.1\", \"ts\":\"2024-01-01T10:00:10Z\", \"url\":\"/home\"}",
  "{\"client_ip\":\"10.0.0.1\", \"ts\":\"2024-01-01T10:00:25Z\", \"url\":\"/search\"}",
  "{\"client_ip\":\"10.0.0.1\", \"ts\":\"2024-01-01T10:01:10Z\", \"url\":\"/results\"}",
  "{\"client_ip\":\"10.0.0.1\", \"ts\":\"2024-01-01T10:01:20Z\", \"url\":\"/detail\"}",
  "{\"client_ip\":\"10.0.0.2\", \"ts\":\"2024-01-01T10:00:00Z\", \"url\":\"/login\"}",
  "{\"client_ip\":\"10.0.0.2\", \"ts\":\"2024-01-01T10:00:45Z\", \"url\":\"/admin\"}",
  "{\"client_ip\":\"10.0.0.2\", \"ts\":\"2024-01-01T10:01:00Z\", \"url\":\"/settings\"}"
])
| parseJson()
// Promote ts to @timestamp so maxpause gap detection and _duration work correctly
| findTimestamp(field=ts)
| groupBy(client_ip, function=series(collect=[url], maxpause=30s, separator=" → "))
| table([client_ip, url, _duration])
```

Gap analysis for `10.0.0.1` (maxpause=30s):

- `/login` → `/home`: 10s gap → same series
- `/home` → `/search`: 15s gap → same series
- `/search` → `/results`: 45s gap → **new series** (gap exceeds 30s)
- `/results` → `/detail`: 10s gap → same series

Gap analysis for `10.0.0.2` (maxpause=30s):

- `/login` → `/admin`: 45s gap → **new series**
- `/admin` → `/settings`: 15s gap → same series

**Expected output:**

| client_ip | url | _duration |
|---|---|---|
| 10.0.0.1 | /results → /detail | 10000 |
| 10.0.0.2 | /admin → /settings | 15000 |
| 10.0.0.1 | /login → /home → /search | 25000 |
| 10.0.0.2 | /login | 0 |

> Without `findTimestamp()` all events share the same `@timestamp`, every gap is 0, and `maxpause` never triggers — all URLs would collapse into one series per IP.

### Use Case 4 — Understanding `memlimit` for Long Sessions

`memlimit` caps the bytes used to buffer collected field values per series invocation. The **system-enforced maximum** is controlled by the LogScale server setting `MAX_SERIES_MEMLIMIT` (default: `1024` bytes). You cannot set `memlimit` above that ceiling without a system operator changing the server configuration. Any attempt will produce:

```
Given value for memlimit (N) is outside the configured range. Choose a value between 1 and max=1024,
or alternatively contact your system operator and ask to have the parameter MAX_SERIES_MEMLIMIT changed.
```

A rough estimate of required buffer: `(avg field value length in bytes) × (max events per series) × (number of collect fields)`.

The example below uses `memlimit=1024` (the system maximum on a default install) and short field values so the 8-event session fits within budget:

```f#
createEvents([
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T09:00:00Z\", \"url\":\"/login\",     \"status\":\"200\"}",
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T09:05:00Z\", \"url\":\"/dashboard\", \"status\":\"200\"}",
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T09:12:00Z\", \"url\":\"/reports\",   \"status\":\"200\"}",
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T09:18:00Z\", \"url\":\"/export\",    \"status\":\"200\"}",
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T09:25:00Z\", \"url\":\"/settings\",  \"status\":\"200\"}",
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T09:30:00Z\", \"url\":\"/profile\",   \"status\":\"200\"}",
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T09:40:00Z\", \"url\":\"/help\",      \"status\":\"200\"}",
  "{\"session\":\"s1\", \"ts\":\"2024-01-01T09:55:00Z\", \"url\":\"/logout\",    \"status\":\"200\"}"
])
| parseJson()
| findTimestamp(field=ts)
// Set memlimit explicitly up to the system maximum (default MAX_SERIES_MEMLIMIT=1024)
| groupBy([session], function=series(
    collect=[url, status],
    separator=" → ",
    memlimit=1024
  ))
| table([session, url, status, _duration])
```

**Expected output:**

| session | url | status | _duration |
|---|---|---|---|
| s1 | /login → /dashboard → /reports → /export → /settings → /profile → /help → /logout | 200 → 200 → 200 → 200 → 200 → 200 → 200 → 200 | 3300000 |

> `_duration` = 55 minutes (3,300,000 ms). This 8-URL session uses ~120 bytes of buffer — well under 1024. In production, sessions with long URL paths or many events will exceed 1024 bytes. To support those, ask your system operator to increase `MAX_SERIES_MEMLIMIT` in the LogScale server configuration. If a series is truncated due to the limit, LogScale emits a warning in the query status panel.

---

## `correlate()` — Multi-Stream Event Correlation

### Why Use It

`correlate()` is the most powerful of the four functions. It executes **two or more independent sub-queries** and joins their results where specified fields match — producing a merged event for each successful correlation. This is how you detect attack chains that span different log sources:

- Credential theft (auth log) followed by lateral movement (network log)
- AWS token generation event correlated with a console login
- A scheduled task created and then executed within the same host

`correlate()` uses the **link operator `<=>`** to declare which field in one sub-query corresponds to which field in another.

```f#
correlate(
  A: { filter-A
    | link_field <=> B.link_field
  } include: [field1, field2],
  B: { filter-B
  } include: [field1, field2],
  globalConstraints=[shared_field],
  sequence=true,
  within=15m
)
```

Key syntax rules:

- Query names use **colon** (`Name:`) not `=`
- Link constraints (`<=>`) go **inside** the sub-query block as piped statements
- `include: [fields]` selects which fields from each sub-query appear in output (use `include: *` while authoring, then narrow)
- `globalConstraints=[]` is shorthand for linking all sub-queries on a common field
- `correlate()` **is incompatible with `createEvents()` in all positions**: it cannot follow `createEvents()` at the top level, and sub-query blocks must be pure filter subqueries (no source or aggregate functions). All `correlate()` examples must run against actual repository data.

The result set contains all fields from all matched sub-queries, prefixed with their query name (e.g., `A.field1`, `B.field2`).

> **Important:** `correlate()` runs its sub-queries over the **same time range** as the outer query. Events in sub-query A and B must overlap in time to correlate.

> **Note on testing:** `correlate()` sub-queries must be filter subqueries — they cannot contain source functions (`createEvents()`, `readFile()`) or aggregate functions. `correlate()` also cannot follow a source function at the pipeline level. These examples must be run against actual repository data that matches the described event shapes.

> **Ingesting known test data for `correlate()` testing:** Use the [`./ingest-testing/`](ingest-testing/README.md) tooling to push 13 synthetic events (auth, network, process, recon, exploit, exfil) into your NGSIEM repository. Run `push_events.py` — it rebases all timestamps to the current time so events are always queryable within the last 4 hours. This gives you a deterministic, repeatable data set to validate `correlate()` queries against real ingested events.

### Use Case 1 — Correlate Failed Auth Followed by Lateral Movement

Detect accounts that had a failed authentication followed by an SMB (port 445) connection — a common lateral movement indicator.

**Ingest these events into your repository before running:**

| event_type | user | result | src_ip | dst_ip | dst_port |
|---|---|---|---|---|---|
| auth | alice | failed | 10.0.0.5 | | |
| auth | bob | success | 10.0.0.9 | | |
| network | alice | | | 192.168.1.100 | 445 |
| network | carol | | | 10.0.0.2 | 22 |

> **Parser field mapping:** The `JSON-CQLTest` parser maps all raw event fields under the `Vendor.` namespace (e.g., `event_type` → `Vendor.event_type`, `user` → `Vendor.user`). Queries must reference `Vendor.*` fields, not the bare source names. The parser also produces ECS aliases (`user.name`, `source.ip`, `destination.port`, etc.) but those are enrichment side-effects — link on `Vendor.user` for a direct, stable match. The exported events in [`ingest-testing/export.ndjson`](ingest-testing/export.ndjson) confirm this mapping.

Fields from [`ingest-testing/export.ndjson`](ingest-testing/export.ndjson) relevant to this use case:

| Raw field | After parser | Example value |
|---|---|---|
| `event_type` | `Vendor.event_type` | `"auth"` / `"network"` |
| `result` | `Vendor.result` | `"failed"` |
| `user` | `Vendor.user` | `"alice"` |
| `src_ip` | `Vendor.src_ip` | `"10.0.0.5"` |
| `dst_port` | `Vendor.dst_port` | `"445"` |
| `dst_ip` | `Vendor.dst_ip` | `"192.168.1.100"` |


```f#
correlate(
  failed_auth: {
    #repo = "3pi_auto_raptor_1777927834886"
    #Vendor = "TestLab"
    Vendor.event_type = "auth"
    Vendor.result = "failed"
  } include: [Vendor.user, Vendor.src_ip],
  lateral_move: {
    #repo = "3pi_auto_raptor_1777927834886"
    #Vendor = "TestLab"
    Vendor.event_type = "network"
    Vendor.dst_port = "445"
    | Vendor.user <=> failed_auth.Vendor.user
  } include: [Vendor.user, Vendor.dst_ip, Vendor.dst_port],
  within=1h
)
| table([failed_auth.Vendor.user, failed_auth.Vendor.src_ip, lateral_move.Vendor.dst_ip, lateral_move.Vendor.dst_port])
```

**Expected output (only alice matches both sub-queries on `Vendor.user`):**

It actually groups on failed_auth and lateral_move with just two columns (one for each sub-query), and the output is a single row with all fields from both failed_auth and lateral_move, not two rows. The output is:


`{"failed_auth.Vendor.src_ip":"10.0.0.5","lateral_move.Vendor.dst_ip":"192.168.1.100","lateral_move.Vendor.dst_port":"445","failed_auth.Vendor.user":"alice"}`

| failed_auth |  lateral_move |
|---|---|
| Vendor.user alice  |Vendor.dst_ip 192.168.1.100 |
|Vendor.src_ip 10.0.0.5 | Vendor.dst_port 445 |

> `bob` (success, not failed) and `carol` (port 22, not 445) do not satisfy both sub-queries simultaneously.

### Use Case 2 — Correlate Process Creation and Network Connection

Detect processes that spawned and then opened outbound connections — a common C2 beaconing indicator. `sequence=true` enforces that the process creation event must precede the network connection. Links on `Vendor.host` and `Vendor.pid` are placed inside the `netconn` sub-query.

**Ingest these events into your repository before running:**

| event_type | host | pid | image | cmdline | dst_ip | dst_port |
|---|---|---|---|---|---|---|
| process | ws-01 | 1234 | cmd.exe | cmd.exe /c whoami | | |
| process | ws-01 | 5678 | notepad.exe | notepad.exe | | |
| network | ws-01 | 1234 | | | 185.220.101.5 | 443 |
| network | ws-02 | 9999 | | | 8.8.8.8 | 53 |

> **Parser field mapping:** The `JSON-CQLTest` / `JSON-CQLTest` parser maps all raw event fields under the `Vendor.` namespace. Process-specific fields map as: `host` → `Vendor.host`, `pid` → `Vendor.pid`, `image` → `Vendor.image`, `cmdline` → `Vendor.cmdline`. Network fields: `dst_ip` → `Vendor.dst_ip`, `dst_port` → `Vendor.dst_port`. The parser also produces ECS aliases (`process.pid`, `process.executable`, `process.command_line`, `destination.ip`, `destination.port`) but `Vendor.*` fields are used here for a consistent, direct match. The exported events in [`ingest-testing/export.ndjson`](ingest-testing/export.ndjson) confirm this mapping.

```f#
correlate(
  proc: {
    #repo = "3pi_auto_raptor_1777927834886"
    #Vendor = "TestLab"
    Vendor.event_type = "process"
  } include: [Vendor.host, Vendor.pid, Vendor.image, Vendor.cmdline],
  netconn: {
    #repo = "3pi_auto_raptor_1777927834886"
    #Vendor = "TestLab"
    Vendor.event_type = "network"
    | Vendor.host <=> proc.Vendor.host
    | Vendor.pid  <=> proc.Vendor.pid
  } include: [Vendor.host, Vendor.pid, Vendor.dst_ip, Vendor.dst_port],
  sequence=true,
  within=5m
)
| table([proc.Vendor.host, proc.Vendor.pid, proc.Vendor.image, proc.Vendor.cmdline, netconn.Vendor.dst_ip, netconn.Vendor.dst_port])
```

**Expected output (only ws-01 pid 1234 matches both sub-queries on `Vendor.host` and `Vendor.pid`):**

> `notepad.exe` (pid 5678) has no matching network event. `ws-02` pid 9999 has no matching process event.

Again it actually groups on proc and netconn with just two columns (one for each sub-query), and the output is a single row with all fields from both proc and netconn, not two rows. The output is:

`{"proc.Vendor.host":"ws-01","proc.Vendor.pid":"1234","proc.Vendor.image":"cmd.exe","proc.Vendor.cmdline":"cmd.exe /c whoami","netconn.Vendor.dst_ip":"185.220.101.5","netconn.Vendor.dst_port":"443"}`

### Use Case 3 — Three-Way Correlation: Recon → Exploit → Exfil

A three-stream correlation across reconnaissance, exploitation, and data exfiltration events for the same host. `globalConstraints=[Vendor.host]` links all three sub-queries on `Vendor.host` — equivalent to adding `| Vendor.host <=> recon.Vendor.host` inside every sub-query but more concise.

**Ingest these events into your repository before running:**

| phase | host | tool | cve | bytes_sent |
|---|---|---|---|---|
| recon | victim-01 | nmap | | |
| recon | victim-02 | nmap | | |
| exploit | victim-01 | | CVE-2024-1234 | |
| exfil | victim-01 | | | 52000 |
| exfil | victim-03 | | | 1000 |

> **Parser field mapping:** The `JSON-CQLTest` / `JSON-CQLTest` parser maps all raw event fields under the `Vendor.` namespace. Phase-event fields map as: `phase` → `Vendor.phase`, `host` → `Vendor.host`, `tool` → `Vendor.tool`, `cve` → `Vendor.cve`, `bytes_sent` → `Vendor.bytes_sent`. The parser also produces ECS aliases (`host.name`, `vulnerability.id`, `network.bytes`) but `Vendor.*` fields are used here for a consistent, direct match. The exported events in [`ingest-testing/export.ndjson`](ingest-testing/export.ndjson) confirm this mapping.

Fields from [`ingest-testing/export.ndjson`](ingest-testing/export.ndjson) relevant to this use case:

| Raw field | After parser | Example value |
|---|---|---|
| `phase` | `Vendor.phase` | `"recon"` / `"exploit"` / `"exfil"` |
| `host` | `Vendor.host` | `"victim-01"` |
| `tool` | `Vendor.tool` | `"nmap"` |
| `cve` | `Vendor.cve` | `"CVE-2024-1234"` |
| `bytes_sent` | `Vendor.bytes_sent` | `"52000"` |

```f#
correlate(
  recon: {
    #repo = "3pi_auto_raptor_1777927834886"
    #Vendor = "TestLab"
    Vendor.phase = "recon"
  } include: [Vendor.host, Vendor.tool],
  exploit: {
    #repo = "3pi_auto_raptor_1777927834886"
    #Vendor = "TestLab"
    Vendor.phase = "exploit"
  } include: [Vendor.host, Vendor.cve],
  exfil: {
    #repo = "3pi_auto_raptor_1777927834886"
    #Vendor = "TestLab"
    Vendor.phase = "exfil"
  } include: [Vendor.host, Vendor.bytes_sent],
  globalConstraints=[Vendor.host],
  sequence=true,
  within=24h
)
| table([recon.Vendor.host, recon.Vendor.tool, exploit.Vendor.cve, exfil.Vendor.bytes_sent])
```

**Expected output (only victim-01 has all three phases):**

Again it groups on recon, exploit, and exfil with just three columns (one for each sub-query), and the output is a single row with all fields from all three sub-queries, not three rows. The output is:

`{"recon.Vendor.host":"victim-01","recon.Vendor.tool":"nmap","exploit.Vendor.cve":"CVE-2024-1234","exfil.Vendor.bytes_sent":"52000"}`

| recon | exploit | exfil |
|---|---|---|
| Vendor.host victim-01 | Vendor.cve CVE-2024-1234 | Vendor.bytes_sent 52000 |
| Vendor.tool nmap|||

> `victim-02` has recon but no exploit or exfil. `victim-03` has exfil but no recon or exploit. Neither forms a complete constellation.

> **Best practice:** Keep sub-queries in `correlate()` narrow and pre-filtered. Each sub-query is a full pipeline run, so expensive regex or broad scans inside `correlate()` multiply query cost. Apply tag filters (`#event_simpleName`, `#repo`) as early as possible inside each sub-query.

---

## Combining the Four Functions

These functions compose well. A common advanced pattern is:

1. Use `coalesce()` to normalize identifiers across log sources
2. Use `series()` to reconstruct session sequences per identity
3. Use `neighbor()` to compute deltas within the event stream

### Example — Session Reconstruction with Normalized User and Delta Timing

```f#
createEvents([
  "{\"event\":\"web_access\", \"src\":\"alice\",  \"username\":\"alice\",  \"ts\":\"100\", \"url\":\"/login\",   \"bytes\":\"512\"}",
  "{\"event\":\"web_access\", \"src\":\"alice\",  \"username\":\"alice\",  \"ts\":\"110\", \"url\":\"/home\",    \"bytes\":\"8192\"}",
  "{\"event\":\"web_access\", \"src\":\"alice\",  \"username\":\"alice\",  \"ts\":\"115\", \"url\":\"/logout\",  \"bytes\":\"256\"}",
  "{\"event\":\"web_access\", \"src\":\"bob_srv\",\"login_name\":\"bob\",   \"ts\":\"200\", \"url\":\"/admin\",   \"bytes\":\"4096\"}",
  "{\"event\":\"web_access\", \"src\":\"bob_srv\",\"login_name\":\"bob\",   \"ts\":\"205\", \"url\":\"/export\",  \"bytes\":\"204800\"}"
])
| parseJson()
// Step 1: Normalize identity field — prefer username, fall back to login_name, then src
| identity := coalesce([username, login_name, src, "anonymous"])
| sort(field=ts, order=asc)
// Step 2: Compute time delta from prior event using neighbor
| neighbor(ts, prefix=prev)
| default(value="0", field=[prev.ts])
| time_delta_ms := if(prev.ts != "0", then=ts - prev.ts, else=0)
// Step 3: Reconstruct per-user URL sequences with series
| groupBy([identity], function=[
    series(collect=[url, bytes], separator=" → "),
    sum(time_delta_ms, as=total_time_ms),
    sum(bytes, as=total_bytes)
  ])
| table([identity, url, bytes, total_time_ms, total_bytes])
```

**Expected output:**

| identity | url | bytes | total_time_ms | total_bytes |
|---|---|---|---|---|
| alice | /login → /home → /logout | 512 → 8192 → 256 | 15 | 8960 |
| bob_srv | /admin → /export | 4096 → 204800 | 90 | 208896 |

---

## Quick Reference: When to Use Which

| Function | Use When | Not Suitable For |
|---|---|---|
| `coalesce()` | Field names vary by source; need a safe default value | Selecting between different filters (use `case` instead) |
| `neighbor()` | You need the value from the row before/after; computing deltas | Cross-session or cross-group comparisons (rows must be sorted and adjacent) |
| `series()` | Collapsing a sequence of events into one row per session/transaction | Real-time streaming (it must buffer all events in the series) |
| `correlate()` | Joining two or more independent event streams on a shared key | Simple same-stream lookups (use `match()`, `join()`, or `selfJoin()`) |

## Operator Quick Reference

Operators relevant to these functions:

| Operator | Context | Example |
|---|---|---|
| `:=` | Field assignment | `host_norm := coalesce([host, hostname])` |
| `=~` | Shorthand — pass field into function | `field =~ regex("pattern")` |
| `<=>` | Link operator in `correlate()` | `user <=> auth.user` |
| `==` | Expression equality (inside `test()`, `eval()`, `if()`) | `test(bytes > 0)` |
| `!=` | Expression inequality | `test(state != prev_state)` |
