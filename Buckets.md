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

![Screenshot 2025-04-16 at 2 24 39 PM](https://github.com/user-attachments/assets/ac388db4-3143-4d7c-92de-c7540668366b)

![Screenshot 2025-04-16 at 2 25 31 PM](https://github.com/user-attachments/assets/57d078e4-71b8-4e35-9228-7f83352b7acb)

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

![Screenshot 2025-04-16 at 2 42 58 PM](https://github.com/user-attachments/assets/f5634c03-616a-4c25-94a5-270f6aaa2108)


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

## Stacked Bar Chart over Time

Group detection events by `DetectName` into daily buckets and display as a stacked bar chart over 30 days.

### Using timeChart()

```f#
#event_simpleName!=* OR #streamingApiEvent=Event_DetectionSummaryEvent
| EventType=Event_ExternalApiEvent
| ExternalApiType=Event_DetectionSummaryEvent
| timeChart(series=DetectName, span=1d, limit=20)
```

In the visualization settings, change **Interpolation > Type** to `Step after` to render as a stacked bar chart.

### Using groupBy()

```f#
#event_simpleName!=* OR #streamingApiEvent=Event_DetectionSummaryEvent
| EventType=Event_ExternalApiEvent
| ExternalApiType=Event_DetectionSummaryEvent
| dateBucket:=formatTime("%Y-%m-%d", field=@timestamp)
| groupBy([dateBucket, DetectName], limit=max)
```

Select **Bar Chart** for the visualization and **Stacked** for the Type. The `formatTime()` approach gives you a human-readable `dateBucket` field (e.g. `2025-04-15`) in the results table, whereas `timeChart()` handles bucketing internally.
