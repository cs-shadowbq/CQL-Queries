# Testing CQL Queries with `createEvents()`

> **Testing `correlate()` requires real ingested data.** `correlate()` is incompatible with `createEvents()` — its sub-queries must be pure filter subqueries and cannot use source or aggregate functions. To test `correlate()` against known, deterministic data, use the [`./ingest-testing/`](ingest-testing/README.md) tooling: run `push_events.py` to push 13 synthetic events into NGSIEM with timestamps rebased to now, then query over the last 4 hours.

`createEvents()` is a **preamble function** that injects synthetic events directly into the query pipeline. It completely replaces any repository data — nothing is read from storage. This makes it the standard tool for developing, testing, and documenting CQL queries without needing access to a live data source.

## Reference

- <https://library.humio.com/data-analysis/functions-create-events.html>

---

## Why Use `createEvents()`

| Benefit | Explanation |
|---|---|
| No repository dependency | Queries run in any LogScale environment with zero data |
| Repeatable | The same input always produces the same output — no time-range sensitivity |
| Self-documenting | The test data is embedded in the query itself, showing exactly what input is expected |
| Safe for sharing | No production data is exposed in examples or documentation |
| Fast iteration | No need to wait for real events to ingest; test logic changes immediately |

A query that cannot be run standalone with `createEvents()` is harder to debug, harder to share, and harder to verify after changes. Treat `createEvents()` test coverage as a requirement, not optional.

---

## Event Formats and Parsers

`createEvents()` accepts an array of strings. Those strings can be in any format — the format determines which parser you pipe them through next.

### Format 1 — Key=Value (`kvParse()`)

The simplest and most compact format. Good for tabular data with uniform fields.

```f#
createEvents(["name=alice,role=admin,status=active",
              "name=bob,role=user,status=inactive",
              "name=carol,role=user,status=active"])
| kvParse()
| table([name, role, status])
```

**Expected output:**

| name | role | status |
|---|---|---|
| alice | admin | active |
| bob | user | inactive |
| carol | user | active |

Use `kvParse()` when:

- Fields are simple scalars with no nested structure
- You want concise, readable test data
- The separator is `,` (default) and values contain no commas

### Format 2 — JSON (`parseJson()`)

Use JSON when fields have nested structure, numeric values, boolean flags, or when field names contain spaces. JSON is the best format for queries that use `coalesce()`, `correlate()`, or `series()`.

```f#
createEvents([
  "{\"host\":\"web-01\", \"bytes\":1024, \"status\":200, \"tls\":true}",
  "{\"host\":\"db-02\",  \"bytes\":512,  \"status\":500, \"tls\":false}",
  "{\"host\":\"cache-03\"}"
])
| parseJson()
| table([host, bytes, status, tls])
```

> **Note:** Fields missing from some events (like `bytes` on `cache-03` above) will be null in CQL — use `default()` or `coalesce()` to handle them explicitly.

**Expected output:**

| host | bytes | status | tls |
|---|---|---|---|
| web-01 | 1024 | 200 | true |
| db-02  | 512  | 500 | false |
| cache-03 | *(no value)* | *(no value)* | *(no value)* |

### Format 3 — Raw String (`@rawstring`)

When you need to test a regex-based filter or parser that operates on `@rawstring`, pass the raw log line directly. Use `regex()` explicitly to extract named fields — the shorthand `/pattern/` form only filters, it does not extract named capture groups into fields.

```f#
createEvents([
  "host=web-01 level=ERROR msg=disk_full",
  "host=web-01 level=INFO  msg=request_ok",
  "host=db-02  level=WARN  msg=slow_query"
])
// regex() both filters and extracts named fields from @rawstring
| regex("host=(?<host>\\S+)\\s+level=(?<level>\\S+)\\s+msg=(?<msg>\\S+)")
// Now level is a real field — filter on it normally
| in(field=level, values=["ERROR", "WARN"])
| table([host, level, msg])
```

**Expected output:**

| host | level | msg |
|---|---|---|
| web-01 | ERROR | disk_full |
| db-02 | WARN | slow_query |

> **Note:** All events from `createEvents()` share the same `@timestamp` (query execution time). Do not include embedded timestamp strings in raw-format events expecting them to be parsed — use `findTimestamp()` (Format 4) for time-aware testing.

### Format 4 — Epoch Timestamp (`findTimestamp()`)

When testing time-based queries (e.g., `bucket()`, `timechart()`, `slidingTimeWindow()`), embed a Unix epoch timestamp in the event data and promote it to `@timestamp` with `findTimestamp()`.

```f#
createEvents([
  "name=alice,event=login,ts=1744201562",
  "name=alice,event=access,ts=1744201800",
  "name=alice,event=logout,ts=1744205162",
  "name=bob,  event=login,ts=1744201900"
])
| kvParse()
// Promote the ts field to @timestamp so time functions work correctly
| findTimestamp(field=ts)
| table([name, event, @timestamp])
```

> Without `findTimestamp()`, all `createEvents()` events share the same synthetic `@timestamp` (query execution time). Time-windowed aggregations will collapse all events into a single bucket.

**Expected output:**

| name | event | @timestamp |
|---|---|---|
| alice | logout | Apr. 9, 2025 13:26:02.000 |
| bob   | login  | Apr. 9, 2025 12:31:40.000 |
| alice | access | Apr. 9, 2025 12:30:00.000 |
| alice | login  | Apr. 9, 2025 12:26:02.000 |

---

## Testing Patterns

### Pattern: Testing a Filter (Positive + Negative Cases)

Always include events that should match **and** events that should not. If only matching events are present, a broken filter that passes everything will appear to work.

```f#
createEvents([
  "host=web-01,status=200,method=GET",   // should pass: status 200
  "host=web-01,status=404,method=GET",   // should be filtered OUT: 404
  "host=db-02,status=500,method=POST",   // should be filtered OUT: 500
  "host=cache-01,status=200,method=POST" // should pass: status 200
])
| kvParse()
// Only keep successful responses
| status = "200"
| table([host, status, method])
```

**Expected output:** only the two `status=200` rows.

### Pattern: Testing Field Normalization

Include events with different field names representing the same concept. Verify the normalized output is always populated.

```f#
createEvents([
  "host=web-01,src_port=443",
  "hostname=db-02,src_port=5432",
  "server=cache-03,src_port=6379",
  "src_port=22"
])
| kvParse()
| host_norm := coalesce([host, hostname, server, "unknown"])
| table([host_norm, src_port])
```

**Expected output:** `host_norm` is populated for every row, including `"unknown"` for the last event.

### Pattern: Testing Aggregations

For `groupBy()`, `sum()`, `count()`, etc., include enough events to verify the grouping and arithmetic — not just that the query runs.

```f#
createEvents(["src=alice,dst=web,bytes=1000",
              "src=alice,dst=web,bytes=2000",
              "src=alice,dst=db,bytes=500",
              "src=bob,dst=web,bytes=300"])
| kvParse()
| groupBy([src, dst], function=sum(bytes, as=total_bytes))
| sort(total_bytes, order=desc)
| table([src, dst, total_bytes])
```

**Expected output:**

| src | dst | total_bytes |
|---|---|---|
| alice | web | 3000 |
| alice | db | 500 |
| bob | web | 300 |

### Pattern: Testing Joins with `defineTable()`

`createEvents()` can be embedded directly inside `defineTable()` to build both the lookup table and the main event stream without any external files.

```f#
// Define the lookup table inline — no CSV file needed
defineTable(
  name="users_table",
  query={ createEvents(["name=alice,dept=security", "name=bob,dept=engineering", "name=carol,dept=ops"]) | kvParse() },
  include=[name, dept]
)
// Main event stream — also synthetic
| createEvents(["user=alice,action=login", "user=bob,action=sudo", "user=dave,action=login"])
| kvParse()
// Left join: strict=false returns dave even though he has no dept entry
| match(table=users_table, field=user, column=name, strict=false)
| table([user, dept, action])
```

**Expected output (left join):**

| user | dept | action |
|---|---|---|
| alice | security | login |
| bob | engineering | sudo |
| dave | *(no value)* | login |

> See [README.md](README.md) for `defineTable()` left/right/inner join patterns.

### Pattern: Testing Edge Cases

Always include at least one edge-case event — a missing field, an empty value, or a value at a boundary condition. Edge cases reveal assumption errors that normal inputs hide.

```f#
createEvents([
  "{\"user\":\"alice\", \"score\":\"95\"}",  // normal: score present
  "{\"user\":\"bob\",  \"score\":\"\"}",      // edge: score is empty string
  "{\"user\":\"carol\"}"                      // edge: score field missing entirely
])
| parseJson()
| score_safe := coalesce([score, "0"])
// CQL coerces strings to numbers automatically in expression contexts
| pass_fail := if(score_safe >= 60, then="pass", else="fail")
| table([user, score, score_safe, pass_fail])
```

**Expected output:**

| user | score | score_safe | pass_fail |
|---|---|---|---|
| alice | 95 | 95 | pass |
| bob | (empty) | 0 | fail |
| carol | *(no value)* | 0 | fail |

---

## Functions That Cannot Be Tested with `createEvents()`

Some functions impose hard architectural constraints that prevent `createEvents()` from being used, regardless of where it is placed.

### `correlate()`

`correlate()` **is incompatible with `createEvents()` in all positions**:

| Position | Result |
|---|---|
| Before `correlate()` at top level | `correlate()` requires events from a real repository — a `createEvents()` source is rejected |
| Inside a sub-query block | Sub-queries inside `correlate()` must be **pure filter expressions** — no source functions (`createEvents()`), no aggregate functions. Attempting this produces a `NonAggregateFunctionExpected` error |

**`defineTable()` does not help either.** `defineTable()` is a join/enrichment tool consumed by `match()`. Its sub-query note says *"Do not nest them inside functions or subqueries"*, so it cannot be placed inside a `correlate()` sub-query block. Even in the preamble, it only creates a lookup side-table — it does not inject events into the main stream that `correlate()` filters.

**The only way to test `correlate()` is to ingest real events into a repository.** Document queries with an explicit "Ingest these events before running" data table and run the query over a time range that covers those events:

```cql
// UC — Detect Lateral Movement After Failed Auth
// Ingest these test events into your repo before running, then run over last 1h:
//   event_type=auth result=failed user=jdoe src_ip=10.1.1.1
//   event_type=network dst_port=445 user=jdoe dst_ip=10.2.2.2

correlate(
  failed_auth: {
    event_type = "auth"
    result = "failed"
  } include: [user, src_ip],
  lateral_move: {
    event_type = "network"
    dst_port = "445"
    | user <=> failed_auth.user
  } include: [user, dst_ip, dst_port],
  within=1h
)
| table([failed_auth.user, failed_auth.src_ip, lateral_move.dst_ip, lateral_move.dst_port])
```

This is not a limitation of the documentation style — it is a hard constraint of the LogScale execution engine.

---

## Testing Checklist

Before promoting a query from development to a saved search or use-case library, verify the following using `createEvents()`:

| Check | What to verify |
|---|---|
| Positive match | At least one event that satisfies all filter conditions |
| Negative match | At least one event that is explicitly excluded by filters |
| Missing field | At least one event with a key field absent — does the query handle null gracefully? |
| Empty value | At least one event with a key field set to `""` — does `ignoreEmpty` behave as expected? |
| Aggregation correctness | Numeric totals, group counts, or collected values match hand-calculated expected output |
| Sort order | Sorted results appear in the declared order |
| Time sensitivity | If using time functions, at least two events with distinct `findTimestamp()` values |

---

## Promoting a Query to Production

When a query is ready to run against real data, replace the `createEvents()` preamble with live filters. The rest of the pipeline should require no changes if the test data was representative.

```f#
// Development version — self-contained, repo-independent
createEvents(["host=web-01,status=500,bytes=0",
              "host=web-01,status=200,bytes=1024"])
| kvParse()
| status = "500"
| table([host, status, bytes])
```

```f#
// Production version — replace createEvents with real tag/field filters
#repo="web_logs" #event_simpleName=HttpResponse
| status = "500"
| table([host, status, bytes])
```

**Rules for promotion:**

- Remove `createEvents()` and its paired parser (`kvParse()` / `parseJson()`)
- Replace with the appropriate `#repo` and tag filters
- Preserve all downstream pipeline steps unchanged
- Keep the `createEvents()` version in a comment block or companion `.md` file for future regression testing
