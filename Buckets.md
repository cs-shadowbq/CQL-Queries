# Buckets 

CrowdStrike Humio provides excellent bucketing for slicing data. 

## Bucket N over a day

In an example below, you can create 24 buckets (+1) that each hold 3 response that map to the `groupby()`.

```f#
#repo=base_sensor 
| #event_simpleName=ProcessRollup2 OR #event_simpleName=SensorHeartbeat OR #event_simpleName=ResourceUtilization 
| event_platform="Win" ComputerName="*"
| bucket(buckets=24, function=groupby("#event_simpleName"))
| parseTimestamp(field=_bucket,format=millis)
| table([_bucket, @timestamp, #event_simpleName, _count])
```

|_bucket|@timestamp|#event_simpleName|_count|
|---|---|---|---|
|1744675200000|Apr. 15, 2025 23:51:55.344|ProcessRollup2|3672|
|1744675200000|Apr. 15, 2025 23:51:55.344|ResourceUtilization|233|
|1744675200000|Apr. 15, 2025 23:51:55.344|SensorHeartbeat|1723|
|1744676100000|Apr. 15, 2025 22:51:55.345|ProcessRollup2|3070|
|1744676100000|Apr. 15, 2025 22:51:55.345|ResourceUtilization|233|
|1744676100000|Apr. 15, 2025 22:51:55.345|SensorHeartbeat|1771|
|...|
|...|
|...|


## TimeChart N over a day

```f#
#repo=base_sensor
| #event_simpleName=ProcessRollup2 OR #event_simpleName=SensorHeartbeat OR #event_simpleName=ResourceUtilization 
| event_platform="Win" ComputerName="*"
// Comment out the explicit bucket because timeChart() does this
//| bucket(buckets=24, function=groupby("#event_simpleName"))
| parseTimestamp(field=_bucket,format=millis)
| timeChart(series=#event_simpleName)
```

On the backend, timeChart() creates buckets for you.. 

|_bucket|#event_simpleName|_count|
|---|---|---|
|1744675200000|ProcessRollup2|3672|
|1744675200000|ResourceUtilization|233|
|1744675200000|SensorHeartbeat|1723|
|1744676100000|ProcessRollup2|3070|
|1744676100000|ResourceUtilization|233|
|1744676100000|SensorHeartbeat|1771|
|...|
|...|
|...|