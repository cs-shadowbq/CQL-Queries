# Falcon 4 IT 

Focusing on a Query with an ID of `abcdefgh123441aa811316b39e1234ab`

Note: `query_id` is the defined Query, The `execution_id` is the instance of the result of one of the queries. 

## Example `result.script_output`

```f#
| "result.script_output" = "{\"metadata\":{\"version\":\"1.0.0\",\"errors\":[],\"timestamp\":\"2026-02-27T09:16:19Z\"},\"myset\":{\"aaa\":{\"value\":\"11111111\"},\"bbb\":{\"value\":\"222222222\"},\"ccc\":{\"value\":\"333333333\"}}}\n"
```
TODO: Update this example to make the CQL example a create

```
createEvents([""]) | kvParse()
```

## Stacking a Falcon 4 IT Query to include the last entry from all hosts seen in any run of a Query within a Date range

```f#
#repo="falcon_for_it" event_type=ITQueryResult
| query_id="abcdefgh123441aa811316b39e1234ab"
| groupBy([aid], function=tail(1))
| parseJson("result.script_output", prefix="result.script_output.")
| last_updated := formatTime("%Y-%m-%d %H:%M:%S", field=@timestamp, locale=en_US, timezone=Z)
| result.script_output =*
```

## Dropping the verbose fields `(result.script_output, script, @rawstring)`

```f#
#repo="falcon_for_it" event_type=ITQueryResult
| query_id="abcdefgh123441aa811316b39e1234ab"
| groupBy([aid], function=tail(1))
| parseJson("result.script_output", prefix="result.script_output.")
| last_updated := formatTime("%Y-%m-%d %H:%M:%S", field=@timestamp, locale=en_US, timezone=Z)
| result.script_output =*
| drop(result.script_output, script, @rawstring)
```

## Applying Filters 

Filtering an extracted value with `in()` searching for `Needle*`

```f#
#repo="falcon_for_it" event_type=ITQueryResult  
| query_id="abcdefgh123441aa811316b39e1234ab"
| groupBy([aid], function=tail(1))
| parseJson("result.script_output", prefix="result.script_output.")
| last_updated := formatTime("%Y-%m-%d %H:%M:%S", field=@timestamp, locale=en_US, timezone=Z)
| result.script_output.myset.aaaa.value =*
| in("result.script_output.myset.aaaa.value", values=["Needle*"])
```

## Formatting and Selecting Sepecific fields for a Table after Aggregation

Filtering an extracted value with `in()` searching for `Needle*`

```f#
#repo="falcon_for_it" event_type=ITQueryResult  
| query_id="abcdefgh123441aa811316b39e1234ab"
| groupBy([aid], function=tail(1))
| parseJson("result.script_output", prefix="result.script_output.")
| last_updated := formatTime("%Y-%m-%d %H:%M:%S", field=@timestamp, locale=en_US, timezone=Z)
| result.script_output.myset.aaaa.value =*
| device_id := aid
| last_seen := last_updated
| aaaaa := "result.script_output.myset.aaaa.value"
| bbbb := "result.script_output.myset.bbbb.value"
| cccc := "result.script_output.myset.cccc.value"
| table([hostname, device_id, last_seen, aaaa, bbbb, cccc])
```
