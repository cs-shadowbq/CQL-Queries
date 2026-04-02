# NGSIEM Reference Material

Here are some of the out of the box queries that are available to customers in NGSIEM. These can be used as is, or as a starting point for your own custom queries. Below Im showcasing extended versions of some of the queries that include additional context from other datasets, and some tips on how to use the various functions and operators in CQL to get the most out of your data.

## Users with most detections

```f#
#repo=detections ExternalApiType=Event_EppDetectionSummaryEvent 
CustomerIdString=?cid UserName!=""
| in(Objective, values=[?objective], ignoreCase=true)
| in(Tactic, values=[?tactic], ignoreCase=true)
| in(SeverityName, values=[?severity])
| groupBy([CompositeId, FileName, Description], function=[selectLast([UserName])], limit=max)
| groupBy([UserName], function=[count(as=Count)], limit=max)
| table([UserName, Count], sortby=Count, order=desc, limit=20000)
```

### Enhanced User Detections with Identity Context for Privileged & Human User Filtering

Identify some quick examples of how to use rich topics like "user.is_privileged" and "user.is_human" in CQL queries with Detection Event data to find privileged human users in the detections data.


```f#
#repo=detections ExternalApiType=Event_EppDetectionSummaryEvent
| match(
    file="falconUserIdentityContext.csv",
    field=UserName,
    column="user.active_directory.samaccountname",
    include=["user.is_privileged", "user.is_human"],
    strict=false
  )
| in(user.is_human, values=[?Human], ignoreCase=true)
| in("user.is_privileged", values=[?Priviledged_User], ignoreCase=true)
| select([
    "user.is_privileged",
    "user.is_human",
    "_count",
    AgentId,
    Description,
    EventType,
    Hostname,
    LocalIP,
    Objective,
    PlatformName,
    Severity,
    Tactic,
    Technique,
    "process.command_line"
  ]) 
| format("%,.150s", field="process.command_line", as=shortCmdLine)
| drop("process.command_line")
```

## Host Detections

Hosts with the Most Detections

```f#
#repo=detections ExternalApiType=Event_EppDetectionSummaryEvent CustomerIdString=?cid Hostname!=""
| in(Objective, values=[?objective], ignoreCase=true)
| in(Tactic, values=[?tactic], ignoreCase=true)
| in(SeverityName, values=[?severity])
| groupBy([CompositeId, FileName, Description], function=[selectLast([Hostname])], limit=max)
| groupBy([Hostname], function=[count(as=Count)], limit=max)
| table([Hostname, Count], sortby=Count, order=desc, limit=20000)
```

### Hosts with the Most Detections Enhanced with Host Context

| Addition | Reason |
| --- | --- |
| `min/max(@timestamp)` in first `groupBy` | Capture detection time range per deduped event |
| `AgentId` in `selectLast` | Needed for AID master lookup |
| `aid_master_main.csv` match | Adds OS version, platform, manufacturer per host |
| `$falcon/helper:enrich(ProductType)` | Converts ProductType decimal → readable string |
| `collect()` in second `groupBy` | Surfaces Tactics, Techniques, Users, Filenames per host |
| Formatted timestamps | Human-readable `EarliestDetection` / `LatestDetection` |

```f#
#repo=detections ExternalApiType=Event_EppDetectionSummaryEvent CustomerIdString=?cid Hostname!=""
| in(Objective, values=[?objective], ignoreCase=true)
| in(Tactic, values=[?tactic], ignoreCase=true)
| in(SeverityName, values=[?severity])

// Step 1: Deduplicate per detection; carry context fields + time range
| groupBy([CompositeId, FileName, Description], function=[
    selectLast([Hostname, UserName, Tactic, Technique, SeverityName, AgentId]),
    min(@timestamp, as=FirstDetection),
    max(@timestamp, as=LastDetection)
  ], limit=max)

// Step 2: Enrich with host platform data from AID master
| AgentId=~match(
    file="aid_master_main.csv",
    column=[aid],
    include=[ProductType, Version, SystemManufacturer, SystemProductName],
    strict=false
  )
| $falcon/helper:enrich(field=ProductType)

// Step 3: Roll up to Hostname with full context
| groupBy([Hostname, ProductType, Version, SystemManufacturer], function=[
    count(as=DetectionCount),
    collect([Tactic, Technique, FileName, Description, UserName, SeverityName]),
    min(FirstDetection, as=EarliestDetection),
    max(LastDetection, as=LatestDetection)
  ], limit=max)

// Step 4: Human-readable timestamps
| EarliestDetection := formatTime("%Y-%m-%d %H:%M:%S", field=EarliestDetection, locale=en_US, timezone=Z)
| LatestDetection   := formatTime("%Y-%m-%d %H:%M:%S", field=LatestDetection,   locale=en_US, timezone=Z)

// Step 5: Final output
| table(
    [Hostname, DetectionCount, ProductType, Version, SystemManufacturer,
     Tactic, Technique, FileName, UserName, SeverityName,
     EarliestDetection, LatestDetection],
    sortby=DetectionCount, order=desc, limit=20000
  )
```

## Deep Linking Detections

```f#
#repo=detections ExternalApiType=Event_EppDetectionSummaryEvent
| ComputerName := rename(Hostname)
| wildcard(field=ComputerName, pattern=?ComputerName, ignoreCase=true)
| wildcard(field=AgentIdString, pattern=?aid, ignoreCase=true)
| wildcard(field=LogonDomain, pattern=?LogonDomain, ignoreCase=true)
| CompositeId=/\S+\:(?<aid>\S+)\:(?<DetectId>\S+)$/i
| format("[Detection Link](%s)", field=FalconHostLink, as=FalconHostLink)
| groupBy([aid, CompositeId], function=([sum(Severity, as=SeveritySum), collect([ComputerName, DetectId, FalconHostLink, SeverityName])]), limit=max)
| table([aid, ComputerName, DetectId, SeverityName, SeveritySum, FalconHostLink], limit=100, sortby=SeveritySum)
```

### Enhanced Deep Links with Host Context & User Identity

| Addition | Purpose |
| --- | --- |
| `aid_master_main.csv` match | Adds `ProductType`, `Version`, `SystemManufacturer`, `SystemProductName`, `FirstSeen` --- host context at a glance |
| `$falcon/helper:enrich(field=ProductType)` | Decodes numeric `ProductType` → `Workstation / Server / Domain Controller` |
| `falconUserIdentityContext.csv` match | Flags detections involving privileged or human accounts |
| `default()` | Prevents blank cells for unmatched rows --- keeps the table readable |
| `selectLast()` over `collect()` | `CompositeId` is per-detection unique; `collect()` here would just create noisy arrays |
| `select()` over `table()` | Removes the hard 200-row cap that `table()` enforces |

```f#
// ── TAGS & EVENT TYPE FILTER ─────────────────────────────────────────────────
#repo=detections ExternalApiType=Event_EppDetectionSummaryEvent

// ── FIELD FILTERS & WILDCARDS ────────────────────────────────────────────────
| ComputerName := rename(Hostname)
| wildcard(field=ComputerName,   pattern=?ComputerName, ignoreCase=true)
| wildcard(field=AgentIdString,  pattern=?aid,          ignoreCase=true)
| wildcard(field=LogonDomain,    pattern=?LogonDomain,  ignoreCase=true)

// ── EXTRACT aid + DetectId FROM CompositeId ──────────────────────────────────
| CompositeId =~ /\S+:(?<aid>\S+):(?<DetectId>\S+)$/

// ── FORMAT MARKDOWN LINK BEFORE AGGREGATION ──────────────────────────────────
| format("[Detection Link](%s)", field=FalconHostLink, as=FalconHostLink)

// ── DEDUPLICATE & AGGREGATE PER DETECTION ────────────────────────────────────
| groupBy([aid, CompositeId], function=[
    sum(Severity,   as=SeveritySum),
    selectLast([
      SeverityName, ComputerName, UserName,
      DetectId,     Description,  Tactic,
      Technique,    Objective,    LocalIP,
      FalconHostLink
    ])
  ], limit=max)

// ── ENRICH: AID MASTER (host metadata) ───────────────────────────────────────
| aid =~ match(
    file="aid_master_main.csv",
    column=[aid],
    include=[ProductType, Version, SystemManufacturer, SystemProductName, FirstSeen],
    strict=false
  )
| $falcon/helper:enrich(field=ProductType)

// ── ENRICH: USER IDENTITY CONTEXT ────────────────────────────────────────────
| match(
    file="falconUserIdentityContext.csv",
    field=UserName,
    column="user.active_directory.samaccountname",
    include=["user.is_privileged", "user.is_human"],
    strict=false
  )
| default(value="N/A", field=["user.is_privileged", "user.is_human", ProductType])

// ── FORMAT TIMESTAMPS ─────────────────────────────────────────────────────────
| First_Seen := formatTime(format="%Y-%m-%d %H:%M:%S", field=FirstSeen, locale=en_US, timezone=Z)
| drop([FirstSeen])

// ── SORT + VIEW (select avoids 200-row table() cap) ──────────────────────────
| sort(SeveritySum, order=desc, limit=10000)
| select([
    aid,              ComputerName,        UserName,
    "user.is_privileged", "user.is_human",
    DetectId,         SeverityName,        SeveritySum,
    Tactic,           Technique,           Objective,
    Description,      ProductType,         Version,
    SystemManufacturer, SystemProductName, LocalIP,
    First_Seen,       FalconHostLink
  ])
```