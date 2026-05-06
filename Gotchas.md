# CQL Gotchas

Common mistakes and known-correct patterns for CrowdStrike LogScale CQL.
Organized by the markdown file where each topic best belongs.

---

## General / Pipeline (`README.md`)

### `table()` and `select()` — Row Cap

`table()` caps at 200 rows by default. Always add `limit=max` to remove the cap. `select()` is the canonical cap-free alternative — it does not aggregate and has no row limit.

```f#
// CORRECT
| table([fields], limit=max)
| sort(field, order=desc, limit=max)
```

### Pipeline Order Exceptions

The standard pipeline order (Time → Tags → Filter → Negative Filter → Regex → Functions → Aggregate → Rename → Join → View) has two critical exceptions:

- `$falcon/helper:enrich()` and `match()` **MUST** run before any filter or `groupBy` that depends on the enriched/joined field — even if that means running before step 7. Enrichment order is dependency-driven, not position-driven.
- `correlate()` must appear before any `groupBy()`, `table()`, or `timechart()`.
- Aggregate functions cannot be used inside `correlate()` query blocks.

### `eval()` — No Function Calls Inside

`eval()` cannot contain function calls directly. Assign any function output to a field first, then use that field in `eval()`.

```f#
// WRONG
| eval(ageDays = (now() - lastTS) / 86400000)

// CORRECT
| nowMS := now()
| eval(ageDays = (nowMS - lastTS) / 86400000)
```

### `test()` — Usage Rules

- `test()` is **required** in pipeline filter steps for field-to-field comparisons. Direct `!=` compares against a literal string, not the field value.
- `test()` is **required** inside `case{}` for numeric comparisons (`<=`, `>=`, `>`, `<`).
- `test()` is **NOT supported** inside `case{}` for string field comparisons — use direct equality.
- Function calls are **NOT supported** in `case{}` filter expressions.

```f#
// WRONG — direct field-to-field comparison
| fieldA != fieldB

// CORRECT — field-to-field comparison
| test(fieldA != fieldB)

// WRONG — test() wrapping string comparison inside case{}
| case { test(fieldA = "value") AND test(fieldB = "value") | result := "x"; }

// CORRECT — direct equality inside case{}
| case { fieldA = "value" AND fieldB = "value" | result := "x"; }

// CORRECT — numeric comparison inside case{} requires test()
| case {
    test(ageDays <= 7)   | bucket := "Active";
    test(ageDays <= 30)  | bucket := "Recent";
    * | bucket := "Stale";
  }
```

### `in()` Syntax

SQL-style `in()` is not supported. Use the explicit function form.

```f#
// WRONG
| fieldName in (value1, value2, value3)

// CORRECT
| in(field="fieldName", values=[value1, value2, value3])
```

### `round()` Cannot Take Expressions Directly

`round()` operates on a field, not an expression. Evaluate first, then round the resulting field.

```f#
// WRONG
| round((a / b) * 100)

// CORRECT
| eval(pct = (a / b) * 100)
| round(pct)
```

### `readFile()` Cannot Be OR'd With Event Stream Queries

`readFile()` operates independently of the event stream. It cannot be combined with tag-filtered event queries in a single OR expression. Use `union()` for separate pipelines instead.

```f#
// WRONG
readFile("lookup.csv") OR #repo = "base_sensor" ...

// CORRECT — use union() to combine separate pipelines
```

---

## Functions (`Functions.md`)

### `max()` on String Fields

`max()` is a numeric aggregation — unreliable on string fields. Assign a numeric score pre-`groupBy`, aggregate on the integer, then map back to a readable label post-`groupBy`.

```f#
// WRONG
| groupBy([field], function=[max(stringField, as=worstValue)])

// CORRECT
| case {
    profile = "Critical" | score := 4;
    profile = "High"     | score := 3;
    * | score := 0;
  }
| groupBy([field], function=[max(score, as=worstScore)], limit=max)
| case {
    worstScore = 4 | worstProfile := "Critical";
    worstScore = 3 | worstProfile := "High";
    * | worstProfile := "Unknown";
  }
```

### `groupBy` Key Granularity Affects `count(distinct)`

Over-specified `groupBy` keys produce one row per unique combination. `count(distinct)` will always return 1 if the counted field is in the key. Only include fields that define the grouping dimension in the key — fields that should be aggregated across must **NOT** be in the `groupBy` key.

### Regex as Filter + Extractor

Regex on a field simultaneously filters **and** extracts. Any event where the field does not match is silently dropped. Use `case{}` with a wildcard fallback to handle all formats without data loss.

```f#
// WRONG — silently drops non-matching events
| field = /^pattern\/(?P<capture>[^\/]+)/

// CORRECT — handles all formats
| case {
    field = /^pattern\/(?P<capture>[^\/]+)/ | format := "TypeA";
    * | capture := field | format := "TypeB";
  }
```

### `case{}` Supports Regex — `if()` Does Not

`if()` does not support regex conditions. Use `case{}` for any regex-based conditional assignment.

```f#
// WRONG
| if(field = /regex/, then="x", else="y")

// CORRECT
| case {
    field = /regex/ | newfield := "x";
    * | newfield := "y";
  }
```

### `wildcard()` for Parameter-Driven Filtering

`wildcard()` is the correct mechanism for user-input dashboard parameters. Supports glob patterns (`*value*`), case-insensitive when `ignoreCase=true`. Default value of `*` returns all results without filtering.

```f#
// WRONG
| field = ?Parameter

// CORRECT
| wildcard(field=fieldName, pattern=?Parameter, ignoreCase=true)
```

### `formatTime()` Required for Epoch Output / `findTimestamp()` Reverse

`min()` and `max()` on `@timestamp` return epoch milliseconds — always convert to human-readable format before display. `findTimestamp()` is the reverse: it parses date strings into epoch ms.

```f#
// Epoch ms → human readable
| formatTime(format="%Y-%m-%d %H:%M:%S", as=lastSeen,
    field=lastAuthTS, locale=en_US, timezone=Z)

// Date string → epoch ms
| lastActive := findTimestamp(field=some.date.field)

// Recency calculation — nowMS assigned first, eval() uses field not function
| nowMS := now()
| eval(ageDays = (nowMS - lastAuthTS) / 86400000)
| case {
    test(ageDays <= 7)   | recencyBucket := "1 · Active   (≤ 7d)";
    test(ageDays <= 30)  | recencyBucket := "2 · Recent   (≤ 30d)";
    test(ageDays <= 90)  | recencyBucket := "3 · Moderate (≤ 90d)";
    test(ageDays <= 180) | recencyBucket := "4 · Aging    (≤ 180d)";
    *                    | recencyBucket := "5 · Stale    (> 180d)";
  }
```

### `collect()` Requires Explicit Separator and Limit

The default `collect()` separator is a newline — unreadable in table cells. Always specify `separator=` and `limit=` explicitly.

```f#
// WRONG
| collect([field])

// CORRECT
| collect([field], separator=", ", limit=200)
```

### `format()` Field Parameter Separator Syntax

Parentheses and special characters in `format()` output break `?Parameter` substitution on dashboards. Use underscore `_` as separator when the value will be used as a dashboard parameter.

```f#
// WRONG — breaks parameter substitution
| format("%s(%s)", field=[fieldA, fieldB])

// CORRECT
| format("%s_%s", field=[fieldA, fieldB])
```

### `coalesce()` for Multi-Source Field Unification

`coalesce()` assigns the first non-null value from a prioritized list to a new field. Use when the same logical value lives in different field names across sources. Essential for building unified parameter dropdown values across repos.

```f#
| coalesce([fieldA, fieldB, fieldC], as=UnifiedField)
```

### `correlate()` Rules

- Must appear before any `groupBy()`, `table()`, or `timechart()`.
- Aggregate functions cannot be used inside `correlate()` query blocks.
- `!=` is not a supported link operator inside `correlate()`.
- Use `<=>` for field-level pairing when field names differ between queries.
- Use `globalConstraints=[]` when ALL queries share the same field name.

```f#
| correlate(
    QueryA: {
        #event_simpleName = EventTypeA
        | field = value
    } include: [field1, field2],
    QueryB: {
        #event_simpleName = EventTypeB
        | field = value
    } include: [field1, field2],
    globalConstraints=[sharedField],
    sequence=true,
    within=5m,
    includeMatchesOnceOnly=true
  )
```

---

## NGSIEM-Specific (`NGSIEM.md`)

### `match()` — Case Sensitivity

`match()` is case-sensitive. A case mismatch produces zero matches with **no error**. Normalize case on both sides before joining, or use `ignoreCase=true`. This applies to all join fields — GUIDs, hostnames, usernames, domain names.

```f#
// CORRECT — Option A: normalize before match
| lower(field=fieldA, as=fieldA)
| match(file="lookup.csv", field=fieldA, column="csv_col", strict=false)

// CORRECT — Option B: ignoreCase on match
| match(file="lookup.csv", field=fieldA, column="csv_col",
    ignoreCase=true, strict=false)
```

### `match()` — Explicit `field=` and `column=` When Names Differ

The `=~match()` shorthand is **only** valid when the telemetry field name exactly matches the CSV column name. Use explicit `field=` and `column=` when names differ.

```f#
// SHORTHAND — only when names match exactly
| aid=~match(file="aid_master_main.csv", column=[aid])

// EXPLICIT — when names differ
| match(file="lookup.csv", field=telemetryField, column="csv_column",
    include=[...], strict=false)
```

---

## Extended / Enrichment (`Extended.md`)

### `$falcon/helper:enrich()` — Pipeline Order

Enrich **MUST** run before any filter or `groupBy` on the enriched field. Filtering on an unenriched field produces zero results with no error.

```f#
// WRONG
| field = "EnrichedValue"
| $falcon/helper:enrich(field=field)

// CORRECT
| $falcon/helper:enrich(field=field)
| field = "EnrichedValue"
```

### Enrichment Before Aggregation

When an enriched or joined field is needed as a `groupBy` key or filter, enrichment must run **before** aggregation — not after.

```f#
// WRONG
| groupBy([enrichedField, ...], ...)
| $falcon/helper:enrich(field=X)

// CORRECT
| $falcon/helper:enrich(field=X)
| groupBy([enrichedField, ...], ...)
```

### Additional References

- Parser schema: https://schemas.humio.com/parser/v0.3.0
- Parsing standard (PASTA): https://library.humio.com/logscale-parsing-standard/pasta.html
- ECS field reference: https://www.elastic.co/docs/reference/ecs/ecs-category-field-values-reference

---

## Buckets (`Buckets.md`)

### `bucket()` Must Precede `groupBy`

`bucket()` must run as a separate pipeline step **before** `groupBy`. It creates the `_bucket` field which is then referenced in `groupBy`. It cannot be nested inside the `groupBy` field list.

```f#
// WRONG
| groupBy([field, bucket(span=5m)], ...)

// CORRECT
| bucket(span=5m)
| groupBy([field, _bucket], ...)
```

---

## Parsing (`Parsing.md`)

### `fieldset()` for Pipeline Field Validation

Insert `fieldset()` at any point in the pipeline to see what fields are available at that step. Fields present in raw events may not survive upstream filters — always validate with `fieldset()` before referencing a field downstream.

```f#
| fieldset()
```

### `case{}` Supports Regex — `if()` Does Not

Parsers make heavy use of both conditional forms. `if()` does not support regex conditions — use `case{}` for any regex-based conditional assignment.

```f#
// WRONG
| if(field = /regex/, then="x", else="y")

// CORRECT
| case {
    field = /regex/ | newfield := "x";
    * | newfield := "y";
  }
```
