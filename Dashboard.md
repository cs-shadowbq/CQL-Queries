# LogScale Dashboards

Dashboards are composed of widgets that you create based on frequently used searches, to view server activities in the form of various graphs and tables of relevant data.

Dashboards are a great way to summarize key information from the logs and to engage users. Dashboards can contain many different widgets (charts, graphs, or tables).

Think about whether it is better to have a single dashboard with many widgets or whether there is a logical grouping of content which could mean that multiple different dashboards, each with widgets relevant to a particular use, are more appropriate.

Be clear about the expected use of the dashboards and think how the user's next steps could be anticipated and catered for in the dashboards.

## Parameters

To make dashboards more useful you can use parameters to take input from the user to re-draw the dashboard based on their inputs.

These can be very useful when dealing with large sets of data as they allow the user to narrow the scope of the dashboard widget to a subset of data or a particular single value.

Parameters allow users to dynamically filter and modify dashboard results without editing the underlying queries. By using parameter syntax (such as `?username`, `?host` or `?{env=staging}`) within queries, you create replaceable values that users can adjust directly at widget level.

When a dashboard loads, these parameter values are read from the URL and applied to the queries, filtering the results accordingly.

## Links in Dashboards

Often a dashboard will identify something at a high level that needs more investigation and sometimes the next step for the user can be pre-empted.

Consider whether links to either external URLs or additional LogScale searches could be added to dashboard tables to provide convenience for the user.

In LogScale dashboards it is possible to use dashboard parameters, time windows and/or fields from the relevant events in constructing links for deep LogScale links or external URL links.

Note that the URL for the customer's LogScale service is unknown (could be self-cloud or different LogScale clouds and repositories), so this limits the practical possibilities.

## Sections

Creating sections allows you to group relevant content together to maintain a clean and organized layout, making it easier to find and analyze related information. Sections can contain data visualizations as well as parameter panels. Additionally, they offer more flexibility when using the Time Selector, enabling users to apply a time setting across multiple widgets.

Sections allow you to:

- Visually separate related widgets by grouping them together.
- Add a Section Time Selector for comparative analysis between sections.
- Keep parameters together with linked widgets using Parameter Panels.
- Keep sections collapsed in the dashboard when not needed to reduce visual clutter.

## Filters vs Parameters

Filters allow you to reduce data displayed on a dashboard and to look at a subset of your data across all widgets simultaneously. Unlike parameters, filters operate as global dashboard-level constraints. You can save filter configurations as presets to quickly switch between different views of the same dashboard for various environments, systems, or customers.

Parameters allow users to dynamically filter and modify dashboard results without editing the underlying queries. By using parameter syntax within queries, you create replaceable values that users can adjust directly at widget level.

## Dashboard Interactions

LogScale allows you to interact with your data in a dynamic way. Not only can you monitor data in dashboards, but you can also create your own custom Dashboard Interactions, to get workflows that optimize your daily analysis. One of the most common cases with using dashboards is when you notice behaviors and want to explore that information in the widget in more detail.

Interactions automate the process of checking data, entities or any behavior you may want to explore in another detailed dashboard, as they create workflows for easy navigation between related dashboards.

Interactions are configured on widgets, where you set the values you want to explore leveraging a Template Language to enter field values and keep the same context to pass to the destination dashboard, or to the external URL — for example, the value of a column in a table are passed to the destination URL.

Types of interactions are:

- **Link to Dashboard** — allows navigation between related LogScale dashboards.
- **Link to Custom URL** — allows navigation outside LogScale.
- **Link to Search page** — allows navigation from a dashboard to the Search page by running a query detected from the dashboard.

Interactions are configurable on all widgets (except World Map).

---

## Dashboard Files

Dashboards examples live in `./dashboards/` as YAML files conforming to the schema: `https://schemas.humio.com/dashboard/v0.23.0`.

The schema is available online, but also in this repo for reference: [schema-dashboard-v0.23.0.json](./dashboards/schema-dashboard-v0.23.0.json).

### Dashboard YAML Structure

```yaml
name: My Dashboard v1.0
updateFrequency: never
timeSelector:
  defaultTimeJumpInMs: 30000
sharedTimeInterval:
  enabled: true
  isLive: false
  start: 7d
labels:
  - IT Automation
  - Security & Compliance
$schema: https://schemas.humio.com/dashboard/v0.23.0

# Optional: named sections to group widgets in the UI
sections:
  section-0:
    collapsed: false
    order: 0
    title: Summary
    widgetIds:
      - my-kpi-widget

# Optional: user-visible filter parameters
parameters:
  hostname_filter:
    label: Hostname
    order: 10
    type: text
    defaultValue: '*'
    width: 2

widgets:
  my-kpi-widget:
    x: 0
    y: 0
    width: 2
    height: 3
    title: My KPI
    description: Short description shown on hover.
    type: query
    isLive: false
    start: 7d
    end: now
    visualization: single-value
    queryString: |
      #repo = "falcon_for_it" event_type=ITQueryResult "host_execution_status"="*Completed*"
      | query_id = "YOUR_QUERY_ID_HERE"
      | groupBy([aid], function=tail(1))
      | count(as="My Metric")
    options:
      valueFormat: raw
    interactions:
      - name: View results
        type: customlink
        urlTemplate: /it-automation/tasks/saved/YOUR_QUERY_ID_HERE?tab=execution-log
        urlEncodeArgs: true
        openInNewTab: true
```

### Visualization Types

| `visualization` value | Use case |
|---|---|
| `single-value` | KPI counts, summary numbers |
| `table-view` | Detailed inventory / drilldown tables |
| `pie-chart` | Distribution / breakdown by category |
| `bar-chart` | Ranked lists, timelines, comparisons |
| `gauge` | Compliance percentages, readiness scores |
| `note` | Static markdown text panels (no `queryString`) |

#### KPI Single-Value with Alert Color

```yaml
options:
  background-color: '#DB2D24'   # red  — critical
  # background-color: '#F49125' # orange — warning
  # background-color: '#34B248' # green  — healthy
  valueFormat: raw
visualization: single-value
```

#### Gauge with Thresholds

```yaml
visualization: gauge
options:
  gaugeType: radialNeedle
  thresholdConfig:
    defaultColor: '#F04242FF'
    reversePalette: true   # low = bad, high = good
    thresholds:
      - { value: 20, color: '#f15249ff' }
      - { value: 40, color: '#f7bd75ff' }
      - { value: 60, color: '#91c569ff' }
      - { value: 80, color: '#34B248'   }
```

#### Table with Column Renames

```yaml
visualization: table-view
options:
  row-numbers-enabled: false
  cell-overflow: wrap-text
  column-overflow: truncate
  configured-columns:
    hostname:
      rename: Hostname
    result.cert_subject_cn:
      rename: Certificate
```

#### Bar Chart (Horizontal / Stacked)

```yaml
visualization: bar-chart
options:
  barChartOrientation: horizontal   # or vertical
  barChartType: stacked             # omit for grouped
  labelLimit: 75
  valuesOnBars: true
```

---

### Common F4IT Query Patterns for Dashboards

#### Base Filter (all F4IT widgets start here)

```f#
#repo = "falcon_for_it" event_type=ITQueryResult "host_execution_status"="*Completed*"
| query_id = "YOUR_QUERY_ID_HERE"
```

> `#repo = falcon_for_it*` (wildcard) matches both `falcon_for_it` and `falcon_for_it_cloud` repos.

#### Deduplicate: Latest Result per Host

```f#
| groupBy([aid], function=tail(1))
```

#### Deduplicate: Latest Result per Host + Unique Key (e.g., certificate thumbprint)

```f#
| groupBy([aid, result.cert_thumbprint], function=tail(1))
```

#### Human-Readable "Last Seen" Age

```f#
| groupBy([result.name], function=[count(aid, distinct=true, as=Endpoints), max(@timestamp, as=_last)], limit=max)
| _age_min := (now() - _last) / 1000 / 60
| _age_hr  := _age_min / 60
| _age_d   := _age_hr  / 24
| "Last Seen" := if(_age_min < 60,
    then=format("%.0f min ago",   field=_age_min),
    else=if(_age_hr < 24,
      then=format("%.0f hours ago", field=_age_hr),
      else=format("%.0f days ago",  field=_age_d)))
```

#### KPI Count Formatted with Commas

```f#
| count(as="Total Certificates")
| "Total Certificates" := format("%,.0f", field="Total Certificates")
```

#### Percentage Gauge Value (e.g., compliance %)

```f#
| stats([count(as=total), sum(is_vulnerable, as=vulnerable)])
| "Readiness %" := 100 - (vulnerable / total * 100)
| drop([total, vulnerable])
```

#### Wildcard User Parameter Filter

Wires up a dashboard `parameter` to a widget query:

```f#
| wildcard(field=hostname,    pattern=?hostname_filter,  ignoreCase=true)
| wildcard(field=result.name, pattern=?artifact_filter,  ignoreCase=true)
```

#### Multi-Query Fan-Out with `in()`

Filter for results from several queries at once:

```f#
| in(query_id, values=["id1", "id2", "id3"])
```

#### Categorical Classification with `case {}`

```f#
| case {
    query_id = "id1" AND result.category != "no_data_found" | Category := "AI Tools & IDEs";
    query_id = "id2" AND result.name     != "no_data_found" | Category := "LLM Models";
    * | Category := "no_data";
  }
| Category != "no_data"
```

#### Splitting Comma-Separated Fields

```f#
| splitString(field=result.accepted_ciphers, by=", ", as=cipher_list)
| split(cipher_list)           // expands array into individual rows
| cipher_list != "N/A"
| groupBy([cipher_list], function=count(as="Count"))
```

#### Cross-Query Join with `defineTable` + `match`

Use when a single widget needs data from multiple F4IT query IDs:

```f#
defineTable(name="models", query={
  #repo = falcon_for_it* event_type=ITQueryResult "host_execution_status"="*Completed*"
  | query_id = "MODEL_QUERY_ID"
  | NOT result.name = "no_data_found"
  | groupBy([aid, result.name], function=[selectLast(execution_id)], limit=max)
  | groupBy(aid, function=count(as=_models_f), limit=max)
}, include=[aid, _models_f])
| #repo = falcon_for_it* event_type=ITQueryResult "host_execution_status"="*Completed*"
| query_id = "PRIMARY_QUERY_ID"
| groupBy([aid], function=count(as=_tools_f), limit=max)
| match(table="models", field=aid, column=aid, strict=false)
| default(field=_models_f, value=0)
```

#### Service-Certificate Join with `join()`

Correlate two query results by shared key fields:

```f#
| join(
    query={
      #repo = "falcon_for_it" event_type=ITQueryResult "host_execution_status"="*Completed*"
      | query_id = "OTHER_QUERY_ID"
      | groupBy([aid, result.cert_thumbprint], function=tail(1))
    },
    field=[aid, result.cert_thumbprint],
    include=[result.process_name, result.local_port]
  )
```

---

### Example Dashboards in This Repo

| File | Purpose |
| --- | --- |
| [Synthetic_Dashboardv1.2.yaml](./dashboards/Synthetic_Dashboardv1.2.yaml) | Synthetic threat detection dashboard |


## Dashboard Design Patterns

Reference for building new dashboards against unfamiliar datasets. Patterns extracted from all eight dashboards in `dashboards/`.

### YAML Skeleton

```yaml
$schema: https://schemas.humio.com/dashboard/v0.23.0
name: My Dashboard
timeSelector: {}                 # show the time picker UI
sharedTimeInterval:
  enabled: true
  isLive: false                  # set true for auto-refresh
  defaultTime: 7d
parameters:                      # define all params here (see §Parameters)
  my_filter:
    label: Filter Label
    order: 1
    type: text
    defaultValue: '*'
    width: 1
widgets:                         # keyed by widget ID (UUID or descriptive string)
  some-uuid:
    type: query
    title: My Widget
    x: 0
    y: 0
    width: 6
    height: 4
    queryString: |
      #repo="base_sensor" #event_simpleName="MyEvent"
      | myField =~ wildcard(?my_filter)
    visualization: table-view
    options: {}
sections:                        # logical grouping of widget IDs
  section-id-1:
    title: Section Title
    order: 0
    collapsed: false
    widgetIds:
    - some-uuid
```

---

### Parameters

#### `type: text` — Free-text filter

```yaml
parameters:
  hostname_filter:
    label: Hostname
    order: 1
    type: text
    defaultValue: '*'       # '*' = match everything (pass-through)
    width: 1
```

Referenced in queries as `?hostname_filter`. Default `'*'` means "show all" — no events are filtered out until the user types something.

For regex-style parameters (partial match, case-insensitive), use `defaultValue: .*`:

```yaml
  user_name:
    label: User Name
    order: 2
    type: text
    defaultValue: .*        # '.*' = match everything via regex
    width: 1
    invalidInputPatterns:
    - ^[\s\*]*$             # prevent blank/all-wildcard input
```

#### `type: list` — Dropdown with fixed choices

```yaml
  os_platform:
    label: OS Platform
    order: 1
    type: list
    defaultValue: '*'     # must match a value key, not a label
    width: 1
    values:
      '*': 'All'          # value=*, label=All — wildcard pass-through
      Win: Windows        # value=Win, label=Windows
      Mac: macOS          # value=Mac, label=macOS
      Lin: Linux          # value=Lin, label=Linux
```

`values:` is a map of **`value: label`** — the **key** is the internal value substituted into queries; the **value** is the display label shown in the dropdown UI. This is the reverse of what the key name order might suggest.

- `defaultValue` must match a **key** (internal value), not a label. `defaultValue: '*'` is valid only if `'*'` is a key in `values:`.
- For a wildcard "All" option, use `'*': 'All'`. The query must use `wildcard(..., includeEverythingOnAsterisk=true)` to make pattern `*` match all events instead of looking for a literal `*` character:

```cql
| wildcard(field=plat, pattern=?os_platform, ignoreCase=true, includeEverythingOnAsterisk=true)
```

- Make sure value keys match the actual field values in your data (e.g., if data has `plat=Win`, the key must be `Win`, not `Windows`).

Referenced with `=~ in(values=[?os_platform])` in queries when using exact-match list semantics.

#### `type: query` — Dropdown populated dynamically

```yaml
  policy_name:
    label: Policy Name
    order: 1
    type: query
    defaultValue: '*'
    width: 1
    valueField: PolicyName        # which output field becomes the option value
    useDashboardTimeIfSet: true   # use dashboard time window for this query
    timeInterval: 7d              # fallback time window
    query: |
      #repo="base_sensor" #event_simpleName="DataEgress"
      | groupBy(PolicyName, function=[])
```

Use this when the set of valid filter values changes over time (e.g., policy names, classification labels). Chain earlier parameters into this query so the dropdown stays consistent with other active filters.

##### `valueField` vs `labelField` — show one thing, store another

When the raw data value is a numeric code but you want a human-readable label in the dropdown, use both `valueField` and `labelField`:

```yaml
  web_egress_policy_action:
    label: Policy Rule Action
    type: query
    defaultValue: '*'
    valueField: DataProtectionPolicyRuleAction  # stored value sent to queries
    labelField: Action                          # display label shown in dropdown
    query: |
      #repo="base_sensor" #event_simpleName="DataEgress"
      | groupBy(DataProtectionPolicyRuleAction, limit=max, function=[])
      | case {
          DataProtectionPolicyRuleAction=0 | Action := "Monitored";
          DataProtectionPolicyRuleAction=1 | Action := "Blocked";
          DataProtectionPolicyRuleAction=2 | Action := "Allowed";
          DataProtectionPolicyRuleAction=3 | Action := "Simulated Block";
          DataProtectionPolicyRuleAction=4 | Action := "Simulated Allow";
          * | Action := "Other";
        }
```

The dropdown shows `"Monitored"`, `"Blocked"` etc., but the parameter value stored is `0`, `1`, etc. Queries then filter with `DataProtectionPolicyRuleAction =~ in(values=[?web_egress_policy_action])`.

Same technique for channel labels:

```yaml
  fdp_det_channel:
    label: Egress Channel
    type: query
    defaultValue: '*'
    valueField: Destination.Channel    # raw value: "usb", "web", "printer"
    labelField: _label                 # display: "USB Egress", "Web Egress", etc.
    query: |
      #repo="detections" #event_simpleName="Event_DataProtectionDetectionSummaryEvent"
      | groupBy(Destination.Channel, function=[])
      | case {
          Destination.Channel="usb"     | _label := "USB Egress";
          Destination.Channel="web"     | _label := "Web Egress";
          Destination.Channel="printer" | _label := "Printer Egress";
          * | _label := format("%s Egress", field=Destination.Channel);
        }
```

##### Cascading dynamic dropdowns

Dropdown queries that themselves filter by the currently active global (and section) parameters. This means the options shown in a dropdown stay in sync with other selected filters — you only see values that actually exist given the current context.

**Pattern:** Include the global params (`user_name`, `user_sid`) and all higher-priority section params inside the dropdown's own query:

```yaml
  web_egress_cp:
    label: Content Pattern
    type: query
    defaultValue: '*'
    valueField: _cp
    useDashboardTimeIfSet: true
    query: |
      #repo="base_sensor" #event_simpleName="DataEgress"
      // Dashboard parameters — global filters applied first
      | UserName =~ regex(?user_name, flags="i")
      | UserSid =~ regex(?user_sid, flags="i")
      // Section parameters — earlier section filters applied second
      | DataProtectionPolicyRuleAction =~ in(values=[?web_egress_policy_action])
      | PolicyName =~ in(values=[?web_egress_policy_name])
      // Extract and list content patterns
      | objectArray:eval("cp.data_labels[]", asArray="_cp[]", var=x, function={ _cp := x.content_pattern_name[0] })
      | split(_cp)
      | groupBy(_cp, function=[])
```

**Why:** If an analyst has filtered to a specific user and a specific policy, the Content Pattern dropdown should only show patterns that appear in that user's data under that policy. Without cascading, the dropdown would show all possible content patterns in the entire dataset, creating noise and confusion.

**Rule of thumb for ordering:** A dropdown for filter N should include filters 0 through N-1 in its query. Use the `order:` field on each parameter to make the hierarchy explicit:

```yaml
  user_name:          order: 0   # global: no dependencies
  user_sid:           order: 1   # global: no dependencies
  policy_action:      order: 0   # section: depends on globals only
  policy_name:        order: 1   # section: depends on globals + policy_action
  applied_classif:    order: 3   # section: depends on globals + policy_action + policy_name
  sensitivity_label:  order: 2   # section: depends on globals + policy_action + policy_name
  content_pattern:    order: 4   # section: depends on all of the above
```

#### `parameterPanel` widget — Inline filter bar

Renders selected parameters as an inline filter strip at a specific grid position. Does not run a query.

```yaml
widgets:
  parameter-panel-1756131755767-0:
    type: parameterPanel
    title: ''
    x: 0
    y: 0
    width: 12
    height: 2
    parameterIds:
    - fdp_det_action
    - fdp_det_channel
    - fdp_det_severity
```

**Why use it:** Place one `parameterPanel` at the top of each section (`y: 0` within the section's row range) to give analysts in-context filter controls without scrolling to the top of the dashboard. Use `height: 1` for single-row parameter panels (e.g., a single "selected user" parameter), `height: 2` for multi-parameter rows.

---

### Wiring Parameters to Queries

#### Pattern 1 — Wildcard text (hostname, device names)

```cql
| hostname =~ wildcard(?hostname_filter, ignoreCase=true)
```

Default `'*'` passes all events through. User types `web-*` to filter to matching hostnames.

#### Pattern 2 — Regex text (user names, partial string match)

```cql
| UserName =~ regex(?user_name, flags="i")
```

Default `.*` passes all events. Case-insensitive. Works well for partial names (e.g., `john` matches `john.doe@corp.com`).

#### Pattern 3 — List / multi-select (enum values)

```cql
| SeverityName =~ in(values=[?fdp_det_severity])
```

Default `'*'` matches the literal string `"*"` via `in()`, which acts as a pass-through when no real values contain `"*"`. When an option is selected, `in()` restricts to that exact value.

#### Pattern 4 — Optional array filter (pass-through trick)

Use when the field being filtered lives inside a nested array and the parameter should be skippable:

```cql
| _default := "*"
| case {
    _default =~ in(values=[?sensitivity_label]);          // branch 1: passes all when param="*"
    objectArray:exists("properties.labels[]", condition={
      properties.labels.label_name[0] =~ in(values=[?sensitivity_label])
    });                                                   // branch 2: when a real value is selected
  }
```

**Why:** `in(values=["*"])` evaluates true for any row that has `_default="*"`, so branch 1 matches everything. Once the user selects a real label, `"*"` no longer matches `_default`, so branch 2 runs instead.

For regex-style optional filters (text params with `.*` default):

```cql
| _default_rg := ".*"
| case {
    _default_rg=?web_egress_origin;                    // passes all when param=".*"
    field =~ regex(?web_egress_origin, flags="i");     // filtered when param changed
  }
```

#### Pattern 5 — Null-field handling before `in()` filters

If the field you're filtering on can be null/missing in some events, `in()` will silently drop those rows even when the parameter is at its default `"*"`. Use `default()` to assign a sentinel value first:

```cql
| default(value="none", field=ResponseAction)   // null ResponseAction → "none"
| ResponseAction =~ in(values=[?fdp_det_action])
```

Then ensure `"none"` is a valid option in the dropdown query:

```yaml
  fdp_det_action:
    type: query
    query: |
      | default(value="none", field=ResponseAction)
      | groupBy(ResponseAction, function=[])
```

This keeps events with no `ResponseAction` visible (as `"none"`) rather than silently discarded.

#### Pattern 6 — SYSTEM account normalization

The local SYSTEM account (`S-1-5-18`) shares its SID across all machines. To make it unique per host before grouping or filtering by user:

```cql
// Apply once at the top of every query, before any user-related filters
| case {
    UserSid="S-1-5-18"
    | _computer_name := replace("\\$", with="", field=UserName)
    | UserSid := format("%s_%s", field=[UserSid, _computer_name]);
    *;
  }
// Now UserSid is unique per host for SYSTEM: "S-1-5-18_HOSTNAME"
| UserName =~ regex(?user_name, flags="i")
| UserSid =~ regex(?user_sid, flags="i")
```

**Why:** `UserName` for machine accounts ends with `$` (e.g., `HOSTNAME$`). Stripping the `$` and appending to the SID creates a stable, unique identity like `S-1-5-18_HOSTNAME` that survives `groupBy(UserSid)` correctly. This same normalization block must be applied consistently in **every** widget query and every dynamic dropdown query on the dashboard.

---

### Selected-User Drill-Down Pattern

The most powerful UX pattern in the FDP dashboard: a two-level investigation flow where analysts first see a **summary table** (one row per user), then click to load **per-event detail** for a selected user in a table below.

#### How it works

```
[Global params: user_name, user_sid]  ← regex text, filter all widgets
        │
        ▼
[Summary Table — aggregated per user]
  • interactions: "Filter" (sets user_name+user_sid globally)
                  "Select User" (sets section_selected_user only)
        │
        ▼
[parameterPanel — shows only selected_user param, height=1]
        │
        ▼
[Detail Event Table — exact match: UserSid=?section_selected_user]
```

#### Step 1 — Define the `selected_user` parameter

```yaml
parameters:
  fdp_det_selected_user:
    label: Select User
    type: query                      # dynamic dropdown
    defaultValue: '*'                # no user selected = show nothing (detail table returns 0 rows)
    width: 1
    order: 0
    valueField: UserSid              # stored value
    labelField: UserName             # shown in dropdown
    useDashboardTimeIfSet: true
    query: |
      #repo="detections" #event_simpleName="Event_DataProtectionDetectionSummaryEvent"
      | case { UserSid="S-1-5-18" | ... }   // SYSTEM normalization
      // Respect ALL active filters — dropdown only shows users matching current context
      | UserName =~ regex(?user_name, flags="i")
      | UserSid =~ regex(?user_sid, flags="i")
      | Destination.Channel =~ in(values=[?fdp_det_channel])
      | SeverityName =~ in(values=[?fdp_det_severity])
      | groupBy(UserSid, limit=max, function=collect([UserName], separator=", "))
```

**Key:** `defaultValue: '*'` and the detail table using an **exact match** `UserSid=?fdp_det_selected_user` means the detail table shows **zero rows** until a user is selected. This is intentional — the table only loads on demand.

#### Step 2 — Summary table interactions

```yaml
    interactions:
    # Global filter: scopes entire dashboard to this user across all sections
    - name: Filter by User Name
      titleTemplate: '▼ Filter by "{{ fields["User Name"] }}" user'
      type: updateparameters
      arguments:
        user_name: '["{{ fields.UserName }}"]'   # sets global text param
        user_sid:  '["{{ fields.UserSid }}"]'    # sets global text param
        # Also sync the selected_user params across all sections at once:
        fdp_det_selected_user:       '["{{ fields.UserSid }}"]'
        evt_web_egress_selected_user: '["{{ fields.UserSid }}"]'
        usb_egress_selected_user:    '["{{ fields.UserSid }}"]'

    # Section-only select: just loads that user's events without changing global scope
    - name: Select User
      titleTemplate: '⤵ Select "{{ fields["User Name"] }}" user - Load Detections'
      type: updateparameters
      arguments:
        fdp_det_selected_user: '["{{ fields.UserSid }}"]'   # section-scoped only
```

**Convention distinction:**
- `▼ Filter by` — sets `user_name` + `user_sid` globally: all sections and all charts narrow to this user
- `⤵ Select` — sets only the `selected_user` for this section: only the event detail table below loads; charts above are unchanged

This lets analysts explore multiple users' summaries while only loading one user's full event list at a time.

#### Step 3 — parameterPanel for the selected-user slot

```yaml
  parameter-panel-1755351171545-0:
    type: parameterPanel
    x: 0
    y: 19          # just above the detail table
    width: 12
    height: 1      # single-row — only one parameter
    title: ''
    parameterIds:
    - fdp_det_selected_user
```

This renders as a narrow bar showing the currently selected user's name. The analyst can also manually choose a user from the dropdown here.

#### Step 4 — Detail event table

```cql
// All the same base query + global + section filters as the summary table, THEN:
| UserSid=?fdp_det_selected_user    // exact match — only one user's events
| "Time (UTC)" := formatTime("%Y-%m-%d %H:%M:%S", field=@timestamp)
| table(["Time (UTC)", _invLink, ...], limit=1000, sortby=@timestamp, order=desc)
```

Note: `UserSid=?fdp_det_selected_user` is an **equality filter** (not `=~`). When `defaultValue: '*'` and no user is selected, `UserSid="*"` matches zero real events — effectively hiding the table until a user is clicked.

#### Complete parameter map for this dashboard

```
Global (all sections):
  user_name          text  .*    — partial match on UserName
  user_sid           text  .*    — partial match on UserSid

FDP Detection section:
  fdp_det_channel         query  *   — Egress Channel (Web/USB/Printer)
  fdp_det_severity        query  *   — Severity level
  fdp_det_action          query  *   — Response Action
  fdp_det_type            query  *   — Detection Type
  fdp_det_label           query  *   — Sensitivity Labels
  fdp_det_contentPatterns query  *   — Content Patterns
  fdp_det_selected_user   query  *   — Selected User → loads event list

Web Egress section:
  web_egress_policy_action  query  *    — Policy Rule Action (code→label)
  web_egress_policy_name    query  *    — Policy Name
  web_egress_applied_classif query *    — Applied Classification
  web_egress_label          query  *    — Sensitivity Labels
  web_egress_cp             query  *    — Content Pattern
  web_egress_origin         text   .*   — Data Origin (regex)
  web_egress_destination    text   .*   — Data Destination (regex)
  evt_web_egress_selected_user query *  — Selected User → loads event list

USB Egress section:  (mirrors Web Egress with usb_ prefix)
  usb_egress_policy_action, usb_egress_policy_name,
  usb_egress_applied_classif, usb_egress_label, usb_egress_cp,
  usb_egress_origin, usb_egress_selected_user
```

---

### Documentation (Note) Widgets

```yaml
widgets:
  note-1754400613423-4:
    type: note
    title: ''
    x: 5
    y: 0
    width: 7
    height: 8
    text: |
      ## Dashboard Overview

      One-paragraph description of what this dashboard shows and who it's for.

      ## Dashboard Sections

      ### ⏵ Section One
      What it covers.

      ### ⏵ Section Two
      What it covers.

      ## Quick Workflow
      1. Use global filters at top to scope by user/device.
      2. Click a chart bar to drill into that category.
      3. Select a row in the summary table to load event details.

      ## Interactions
      `▼ Filter by` — global filter  `▽ Filter by` — section filter
      `↻ Reset` — clear filter  `⧁ Investigate` — open in search
```

**Placement conventions:**
- Dashboard overview note: top-right corner (e.g., `x: 5, y: 0, width: 7, height: 8`)
- Section description note: first widget in a section, full width (`width: 12, height: 2`)
- Version stamp note: small top-left (`x: 0, y: 0, width: 5, height: 2`) using a code block:

```yaml
    text: |
      ```
      My Dashboard
      Version: 1.0.0
      ```
```

**When to use notes:**
- Explain what data sources / subscriptions are required
- List the interactions and their symbols so new analysts understand clickable elements
- Quick workflow guide (numbered steps) for common analyst tasks
- Section-level descriptions that won't fit in a `description:` field

The `description:` field on a query widget shows as a tooltip; the `note` widget is always visible.

---

### Counter / KPI Widgets

#### `single-value` — a single large number

```yaml
widgets:
  my-kpi:
    type: query
    title: Critical Certs
    x: 0
    y: 0
    width: 3
    height: 3
    queryString: |
      #repo="base_sensor" #event_simpleName="CertInfo"
      | expiresInDays < 30
      | count()
    visualization: single-value
    options:
      default: {}
      background-color: '#DB2D24'   # red alert background
```

**Standard alert colors:**

| Meaning | Hex |
|---------|-----|
| Critical / red | `#DB2D24` |
| Warning / orange | `#F49125` |
| Caution / yellow | `#FFC107` |
| OK / green | `#34B248` |
| Info / teal | `#0b6c84` |

To use conditional coloring, compute a `Status` field in the query using `case {}` and use a `gauge` instead (see below).

Format large numbers as comma-separated integers before displaying:

```cql
| format("%,.0f", field=myCount, as=Display)
```

#### `gauge` — progress/score indicator with color bands

```yaml
    visualization: gauge
    options:
      gaugeType: radialNeedle     # or: radialFull, barHorizontal, barVertical
      thresholdConfig:
        thresholds:
        - { value: 0,  color: '#DB2D24' }   # red zone: 0–20
        - { value: 20, color: '#F49125' }   # orange zone: 20–40
        - { value: 40, color: '#FFC107' }   # yellow zone: 40–60
        - { value: 60, color: '#34B248' }   # green zone: 60–100
      maxVal: 100
      minVal: 0
```

Alternatively use a `palette` object when the field value maps to named status strings:

```yaml
      palette:
        Compliant: '#34B248'
        Non-Compliant: '#DB2D24'
        Unknown: '#888888'
```

Query pattern for a percentage score:

```cql
| stats([
    count(as=total),
    { myCondition=true | count(as=compliant) }
  ])
| score := (compliant / total) * 100
| default(value=0, field=[compliant, score])
```

---

### Interactions

All interactions are defined under the `interactions:` key on a query widget. Each interaction appears in the right-click (⋮) menu on chart elements or table rows.

#### `type: customlink` — open a URL

```yaml
    interactions:
    - name: View Execution Log
      titleTemplate: '⧉ View execution log for {{ fields.JobName }}'
      type: customlink
      url: '/it-automation/tasks/saved/{{ fields.job_id }}?tab=execution-log'
      openInNewTab: true
```

Use `{{ fields.FieldName }}` in `url` or `titleTemplate` to interpolate values from the clicked row. URL-encode field values using `urlEncode()` in the query before passing them to an interaction.

#### `type: updateparameters` — update dashboard filters on click

```yaml
    interactions:
    # Filter action: set param to clicked value
    - name: Filter by Severity
      titleTemplate: '▽ Filter by "{{ fields.SeverityName }}" severity'
      useWidgetTimeWindow: false
      type: updateparameters
      arguments:
        fdp_det_severity: '["{{ fields.SeverityName }}"]'

    # Reset action: restore param to default
    - name: Reset Severity filter
      titleTemplate: '↻ Reset Severity filter'
      useWidgetTimeWindow: false
      type: updateparameters
      arguments:
        fdp_det_severity: '["*"]'

    # Bulk reset: clear all section filters at once
    - name: Reset section filters
      titleTemplate: '↻ Reset section filters'
      useWidgetTimeWindow: false
      type: updateparameters
      arguments:
        fdp_det_severity: '["*"]'
        fdp_det_action: '["*"]'
        fdp_det_type: '["*"]'
```

**Convention:** Always provide a reset interaction alongside every filter interaction. Add a bulk "Reset section filters" that clears all parameters for that section in one click. For regex-style parameters (default `.*`), reset value is `'[".*"]'`, not `'["*"]'`.

**Multi-parameter global filter** (e.g., "select this user" updates user params across all sections):

```yaml
    - name: Filter by User
      titleTemplate: '▼ Filter by "{{ fields["User Name"] }}" user'
      type: updateparameters
      arguments:
        user_sid: '["{{ fields.UserSid }}"]'
        user_name: '["{{ fields.UserName }}"]'
        section_a_selected_user: '["{{ fields.UserSid }}"]'
        section_b_selected_user: '["{{ fields.UserSid }}"]'
```

Use `▼` (filled triangle) for global (dashboard-wide) filters and `▽` (outline triangle) for section-scoped filters — this visual distinction tells analysts which scope is affected.

#### `type: searchlink` — open Advanced Event Search

```yaml
    interactions:
    - name: Investigate in Advanced Event Search
      titleTemplate: '⧁ Investigate in Advanced Event Search'
      type: searchlink
      queryString: |
        #repo="base_sensor" #event_simpleName="DataEgress"
        | UserSid=?_user_sid
      arguments:
        _user_sid: '["{{ fields.UserSid }}"]'
      useWidgetTimeWindow: true
      openInNewTab: true
      isLive: false
```

The `queryString` is a template with `?param` placeholders; `arguments` maps those placeholders to field values from the clicked row. Use `useWidgetTimeWindow: true` to carry the widget's time range into the search.

For complex investigation queries (multiple `defineTable` sub-queries), the full multi-step query can be embedded directly in `queryString` using YAML block scalar (`|`).

---

### Section Structure

```yaml
sections:
  overview-section:
    title: Overview
    order: 0
    collapsed: false
    widgetIds:
    - kpi-uuid-1
    - kpi-uuid-2
    - note-uuid-1
  detail-section:
    title: Detail Analysis
    order: 1
    collapsed: true          # sections can start collapsed
    timeSelector: {}         # per-section time picker (overrides shared)
    widgetIds:
    - chart-uuid-1
    - table-uuid-1
```

Widget `x`/`y` coordinates are **section-relative** — each section's grid starts at `y: 0`. Sections are purely for display grouping (collapsible) and optional per-section time override. All widgets in a section must have `y` values that begin at `0` and increase within that section only; do **not** carry over the `y` totals from a preceding section.

Add `description:` to widgets (not sections) for tooltip text that guides analysts on what to expect and how to interact with a widget.

### Widget Grid Layout

The dashboard uses a **12-column grid**. Each widget declares its own absolute position:

| Field | Meaning |
|-------|---------|
| `x` | Left-edge column (0–11) |
| `y` | Top-edge row (0-based, in grid units) |
| `width` | Number of columns |
| `height` | Number of rows tall |

**Key rules:**

- Widgets do **not** auto-flow — the renderer places each widget exactly at `x`/`y`.
- Widgets sharing a visual row **must share the same `y` value** and their widths must sum to 12 (or to the available working width when a sidebar occupies some columns).
- A **hole** appears whenever: widths don't sum to the row's full width (gap on the right), `y` values leave a strip between rows, or a widget is listed in `widgetIds` but not defined.

**Sidebar pattern — tall note widget:**  
Place a documentation `note` at a fixed `x` with a large `height`. It blocks those columns for every row within its span, and all other widgets in that range must fit within the remaining columns to the left.

**Working example — `Synthetic_Dashboard v1.2.yaml` (12-col grid):**

```text
Col → 0    1    2    3    4    5    6  │  7    8    9   10   11
      ┌─────────────────────────────────┐  ┌───────────────────────┐
y=0   │  widget-params  (w=7, h=2)      │  │  widget-note          │
y=1   │                                 │  │  (w=5, h=15)          │
      ├──────┬──────┬──────┬────────────┤  │  sidebar: y=0–14      │
y=2   │kpi-t │kpi-c │kpi-h │kpi-u       │  │                       │
y=3   │(w=2) │(w=2) │(w=2) │(w=1)       │  │                       │
y=4   │      │      │      │            │  │                       │
      ├──────────────┬─────────────────-┤  │                       │
y=5   │chart-sev     │chart-platform    │  │                       │
y=6   │(w=4, h=5)    │(w=3, h=5)        │  │                       │
      │              │                  │  │                       │
y=9   │              │                  │  │                       │
      ├──────────────┬──────────────────┤  │                       │
y=10  │chart-tactic  │chart-gauge       │  │                       │
y=11  │(w=4, h=5)    │(w=3, h=5)        │  │                       │
      │              │                  │  │                       │
y=14  │              │                  │  └───────────────────────┘
      ├──────────────────────────────────────────────────────────────┤
y=15  │  chart-timeline  (w=12, h=5)                                 │
y=19  │                                                              │
      ├──────────────────────────────────────────────────────────────┤
y=20  │  table-detail  (w=12, h=8)                                   │
y=27  │                                                              │
      └──────────────────────────────────────────────────────────────┘
```

Working area (y=0–14): columns 0–6 (7 cols) — columns 7–11 blocked by `widget-note`  
Full width (y=15+): columns 0–11 — note ends at y=15

**Row band summary:**

| Band | y start | height | Widgets (widths) | Width check |
|------|---------|--------|------------------|-------------|
| Params + note | 0 | 2 | params(7) + note(5) | = 12 ✓ |
| KPIs | 2 | 3 | total(2) + critical(2) + hosts(2) + users(1) | = 7 (working) ✓ |
| Charts row 1 | 5 | 5 | severity(4) + platform(3) | = 7 (working) ✓ |
| Charts row 2 | 10 | 5 | tactic(4) + gauge(3) | = 7 (working) ✓ |
| Timeline | 15 | 5 | timeline(12) | = 12 ✓ |
| Detail table | 20 | 8 | detail(12) | = 12 ✓ |

**Common causes of layout holes:**

- Widths on the same row don't sum to 12 (or available working width) → empty column gap on the right
- `y` value gap between rows (e.g., row A ends at y=4, row B starts at y=6) → blank horizontal strip
- Widget listed in `widgetIds` but not defined in `widgets:` → invisible placeholder that disrupts layout
- Tall sidebar widget defined in `widgets:` but omitted from `widgetIds` → sidebar absent, adjacent widgets fill wrong columns

> **Gotcha — section y-offsets:** `y` values are **section-relative**, not global. If a dashboard has two sections and the first section spans rows 0–26, the second section's first widget must still start at `y: 0`, **not** `y: 27`. Using the cumulative global row count as the `y` value in a subsequent section creates a blank space as tall as all preceding sections before the first widget appears. Always reset `y` to `0` at the start of each new section.

---

### Time Control

| Setting | Effect |
|---------|--------|
| `sharedTimeInterval.enabled: true` | All widgets share one time picker |
| `sharedTimeInterval.isLive: true` | Auto-refresh enabled |
| `sharedTimeInterval.defaultTime: 7d` | Default lookback window |
| `timeSelector: {}` at dashboard root | Renders the time picker UI |
| `timeSelector: {}` inside a section | Per-section time override |
| `start: 7d` / `end: now` on widget | Override shared time for this widget only |

Use `isLive: true` for operational dashboards watching running jobs or scanning activity. Keep it `false` for investigation/reporting dashboards where time stability matters more.

---

### Visualization Types Reference

| `visualization:` value | Use case | Key `options:` fields |
|------------------------|----------|-----------------------|
| `single-value` | KPI counter | `background-color:`, `default: {}` |
| `gauge` | Score / percentage | `gaugeType:`, `thresholdConfig.thresholds:`, `palette:` |
| `bar-chart` | Categorical counts | `barChartOrientation:`, `barChartType:`, `valuesOnBars:`, `labelLimit:`, `orderBy:` |
| `pie-chart` | Part-of-whole | `innerRadius:` (0=pie, >0=donut), `legendPosition:`, `legendTitle:` |
| `time-chart` | Trend over time | `plotType:` (line/area), `stacking:`, `interpolation:`, `lastBucketBehavior:` |
| `table-view` | Row-level detail | `configured-columns:`, `cell-overflow:`, `row-numbers-enabled:` |
| `world-map` | Geo distribution | Requires `worldMap(lat=, lon=)` as final query step |
| `sankey` | Flow mapping (A→B) | `labelLimit:`, `showAxes:` |
| `heat-map` | 2D correlation matrix | `xAxisTitle:`, `yAxisTitle:`, `labelAlign:` |
| `note` | Documentation widget | `text:` (markdown) |
| `parameterPanel` | Inline filter bar | `parameterIds:` |

#### `time-chart` options

```yaml
    options:
      plotType: area              # line | area | bar
      stacking: normal            # none | normal (100% stacked)
      interpolation: monotone     # linear | monotone | step-after
      lastBucketBehavior: exclude # exclude incomplete last bucket
      connect-points: false
      showDataPoints: true
      yAxisScale: linear          # linear | log
      yAxisTitle: Count
      imputation: none
```

Multi-series stacked area (e.g., coverage breakdown):

```cql
| timeChart(_action, function=sum(Size))
| unit:convert(_sum, from="B", to="GB")
```

```yaml
      stacking: normal
      plotType: area
```

Named series colors:

```yaml
      series:
        Blocked:
          color: '#DB2D24'
        Allowed:
          color: '#34B248'
        Monitored:
          color: '#F49125'
```

#### `world-map` query requirement

```cql
| ipLocation(field=aip)           // enrich IP → lat/lon/country
| worldMap(lat=latitude, lon=longitude)
```

#### `sankey` — flow mapping between two categorical fields

Maps how events flow from a source category to a target category, with link width proportional to volume.

**When to use:** Use a sankey when you want to show the relationship and relative volume between two categorical dimensions — for example, which severity levels lead to which response actions, or which data origin locations send traffic to which destinations. It answers "how much of X ends up as Y?" at a glance. A table can show the same data, but a sankey makes dominant flows and unexpected correlations (e.g., high-severity events being allowed rather than blocked) immediately visible without scanning rows.

```yaml
widgets:
  my-sankey:
    type: query
    title: Detection Severity to Response Action Mapping
    x: 0
    y: 2
    width: 5
    height: 5
    queryString: |
      #repo="detections" #event_simpleName="MyDetection"
      | sankey(source="SeverityName", target="ResponseAction", weight=count())
    visualization: sankey
    options:
      labelLimit: 306
      showAxes: true
    interactions:
    - name: Filter by Source
      titleTemplate: '▽ Filter by "{{ fields.source }}" severity'
      useWidgetTimeWindow: false
      type: updateparameters
      arguments:
        my_severity: '["{{ fields.source }}"]'
    - name: Filter by Target
      titleTemplate: '▽ Filter by "{{ fields.target }}" action'
      useWidgetTimeWindow: false
      type: updateparameters
      arguments:
        my_action: '["{{ fields.target }}"]'
    - name: Reset filters
      titleTemplate: '↻ Reset filters'
      useWidgetTimeWindow: false
      type: updateparameters
      arguments:
        my_severity: '["*"]'
        my_action: '["*"]'
```

The `sankey()` function takes:
- `source=` — field name for the left-side nodes
- `target=` — field name for the right-side nodes
- `weight=` — aggregation for link thickness (defaults to event count if omitted)

Interactions on sankey widgets use `{{ fields.source }}` and `{{ fields.target }}` to reference the clicked node.

For flows with nested or array fields, access the value directly in the `sankey()` call:

```cql
| sankey(source="properties.origin_web_locations[0].web_location_name[0]", target="destination.web_destination[0].web_location_name[0]")
```

---

#### `bar-chart` options

```yaml
    options:
      barChartOrientation: horizontal   # or: vertical
      barChartType: stacked             # omit for grouped
      valuesOnBars: true
      labelLimit: 600
      orderBy: _count
      xAxisTitle: Category
      yAxisTitle: Count
```

---

### Table Column Configuration

Table widget column behavior is controlled via `options.configured-columns`:

```yaml
    options:
      cell-overflow: wrap-text         # wrap long values
      row-numbers-enabled: true
      configured-columns:
        UserSid:
          hidden: true                 # hide internal/raw ID columns
        UserName:
          hidden: true
          color: '#22C3C322'          # teal highlight (ARGB alpha suffix)
        "User Name":
          color: '#22C3C322'          # highlight display column with same tint
        Destination:
          color: '#126CC633'          # blue tint for destination column
          width: 200                  # fixed pixel width
        "Last Ingest":
          data-type: time_duration    # render as human-readable duration
```

#### Conditional column coloring (severity levels)

```yaml
        Severity:
          color:
            conditions:
            - color: '#E54FA922'      # pink/magenta — Critical
              condition:
                type: Equal
                arg: Critical
            - color: '#F0424299'      # red — High
              condition:
                type: Equal
                arg: High
            - color: '#f7bd75ff'      # orange — Medium
              condition:
                type: Equal
                arg: Medium
            - color: '#e4df80ff'      # yellow — Low
              condition:
                type: Equal
                arg: Low
            - color: '#29a34bff'      # green — Informational
              condition:
                type: Equal
                arg: Informational
```

Color hex format: `#RRGGBBAA` (with alpha) or `#RRGGBB`. Low alpha values (e.g., `22` = ~13% opacity) produce subtle background tints; full alpha (`ff`) produces solid color.

**Hiding columns while keeping their values:** Compute a display alias in the query, hide the raw column, color both together:

```cql
| "User Name" := replace(field=UserName, regex="\\|", with=", ")
| table([UserSid, UserName, "User Name", Count])
```

```yaml
        UserSid:   { hidden: true }
        UserName:  { hidden: true, color: '#22C3C322' }
        "User Name": { color: '#22C3C322' }
```

This keeps raw values accessible to interactions while showing only the formatted display version.

---

### Layout Conventions (12-column grid)

```
x: 0          x: 3          x: 6          x: 9
|--- 3 cols ---|--- 3 cols ---|--- 3 cols ---|--- 3 cols ---|

Row y=0, h=2:  [parameterPanel — full width 12            ]
Row y=2, h=3:  [single-value x=0,w=2] [single-value x=2,w=2] [single-value x=4,w=2] [note x=6,w=6]
Row y=5, h=4:  [pie-chart x=0,w=4]    [bar-chart x=4,w=4]    [gauge x=8,w=4]
Row y=9, h=5:  [time-chart x=0,w=8]   [pie-chart x=8,w=4]
Row y=14, h=6: [table-view — full width 12 — summary      ]
Row y=20, h=5: [parameterPanel row — selected item filter  ]
Row y=21, h=5: [table-view — full width 12 — event detail ]
```

**Conventions observed across all dashboards:**
- `width: 12` — full-width rows: parameterPanels, summary tables, event detail tables, note widgets at top
- `width: 2–3, height: 2–3` — KPI single-value counters, placed in a row at the top of a section
- `width: 4–6, height: 4–5` — charts (pie, bar, gauge) in the middle
- `width: 6–8, height: 4` — time-charts (trend lines)
- Note widget at top-right: `x=5` or `x=8`, `width=4–7`, `height=6–8`
- parameterPanel at top of each section: `x=0, width=12, height=1–2`
- Full-width detail table at bottom of each section: `x=0, width=12`

---

### Advanced Query Patterns

#### Array field processing

```cql
// Iterate array and extract a sub-field from each element
| objectArray:eval("ContentPatterns[]", asArray="_cp[]", var=x, function={
    _cp := x.Name
  })

// Filter rows where any array element matches a condition
| objectArray:exists(array="Labels[]", condition={
    Labels.Name =~ in(values=[?fdp_det_label])
  })

// Expand array into separate rows, then group
| split(_cp)
| groupBy(_cp)

// Deduplicate and stringify an array
| array:dedup("_cpArray[]")
| "Content Pattern" := concatArray(_cpArray, separator=", ")

// Get array length
| _len := array:length("ContentPatternsNames[]")
```

#### Multi-source data merge with `defineTable`

```cql
| readFile(["ai_tools", "ai_browsers"])   // merge two defineTable results
```

```cql
// Load external CSV for lookup/enrichment
| readFile("cc_lookup.csv")
| match(file="cc_lookup.csv", field=country_code, column=cc, include=[country_name])
```

#### Geolocation

**Why it's useful:** Fleet location visibility across a mixed platform environment. Windows endpoints use the Windows Location Service (WLS) — real GPS, WiFi, or cellular — collected via an RTR query. Non-Windows endpoints fall back to IP geolocation. Combining both gives complete fleet coverage on a world map with per-country and accuracy breakdowns.

##### `ipLocation()` — IP-based enrichment

```cql
| ipLocation(field=aip)
// Adds prefixed fields: aip.lat, aip.lon, aip.city, aip.state, aip.country
| rename(field="aip.lat", as=latitude)
| rename(field="aip.lon", as=longitude)
| rename(field="aip.country", as=iso2)
```

The added fields are **prefixed** with the source field name (e.g., `aip.lat`, not just `lat`). Always rename after enrichment. Filter out failed enrichments with `| aip.lat = *` before renaming.

##### Dual-source merge for mixed-platform fleet

When Windows endpoints have precise GPS/WiFi coordinates (from an RTR query) and non-Windows have only IP geolocation, merge both into one stream via two `defineTable` blocks:

```cql
defineTable(
  name="sensor_geo",
  query={
    readFile("aid_master_main.csv")
    | version != Windows*                // non-Windows only
    | aip = *
    | ipLocation(field=aip)
    | aip.lat = *                        // drop if IP enrichment failed
    | rename(field=ComputerName, as=hostname)
    | rename(field="aip.lat", as=latitude)
    | rename(field="aip.lon", as=longitude)
    | source := "ipaddress"
  },
  include=[aid, hostname, latitude, longitude, source]
)
| defineTable(
  name="f4it_geo",
  query={
    event_type = ITQueryResult           // F4IT RTR query results (Windows GPS/WiFi/cellular)
    | host_execution_status = *Completed*
    | query_id = "0000000000000000000000000000000c"
    | result.status = ok*
    | groupBy([aid], function=selectLast([hostname, result.latitude, result.longitude, result.source]), limit=max)
    | rename(field=result.latitude, as=latitude)
    | rename(field=result.longitude, as=longitude)
    | rename(field=result.source, as=source)
  },
  include=[aid, hostname, latitude, longitude, source]
)
| readFile(["f4it_geo", "sensor_geo"])   // union both — f4it_geo listed first
```

`readFile([...])` unions both tables. Listing `f4it_geo` first means when a later `groupBy([hostname], function=selectLast(...))` resolves duplicate entries for the same host, the Windows GPS record wins over the fallback IP record.

##### Reverse geocoding pipeline (coordinates → city/country)

`ipLocation()` provides city/country only for IP-based lookups. For platform-consistent reverse geocoding, match rounded coordinates against a pre-built cities CSV:

```cql
| round(field=latitude, how=floor, as=lat_round)
| round(field=longitude, how=floor, as=lon_round)
| match(
    file="geolocation_dashboard_v1.0.9_cities_full.csv",
    field=[lat_round, lon_round],
    column=[lat_round, lon_round],
    include=[city, admin_name, country, iso2, city_lat, city_lon],
    strict=false,
    nrows=max
  )
| city_lat := city_lat * 1              // coerce CSV string → numeric
| city_lon := city_lon * 1
| geography:distance(lat1=latitude, lon1=longitude, lat2=city_lat, lon2=city_lon, as=distance_m)
| groupBy([aid], function=selectFromMin(distance_m, include=[hostname, country, city]), limit=max)
| groupBy([hostname], function=selectLast([country, city]), limit=max)
```

**How it works:** Round to a 1° grid cell → `match()` returns candidate cities in that cell (multiple rows per aid) → `geography:distance()` calculates exact distance to each candidate → `selectFromMin(distance_m)` picks the nearest city.

**`* 1` coercion:** CSV values load as strings. Multiply by `1` to coerce to numeric before passing to `geography:distance()`.

##### Accuracy bucketing with nested `if()`

Use nested `if()` to bin a continuous numeric field into labeled ranges for a distribution bar chart:

```cql
| accuracy_m := accuracy_m * 1          // coerce to numeric
| bucket := if(accuracy_m < 25, then="< 25m",
    else=if(accuracy_m < 100, then="25-100m",
      else=if(accuracy_m < 1000, then="100-1000m",
        else="> 1000m")))
| groupBy([bucket], limit=max)
```

Set a sentinel for endpoints with no accuracy data (IP-based geolocation has no GPS accuracy field):

```cql
| accuracy_m := "99999"     // inside the sensor_geo defineTable
```

This puts IP-based endpoints consistently in the `> 1000m` bucket, making them easy to distinguish from precise GPS readings in the chart.

##### `pie-chart` — per-series named colors

Use named `series:` entries under `options:` to assign specific colors to each categorical value:

```yaml
    visualization: pie-chart
    options:
      legendTitle: Source
      series:
        wifi:       { color: '#0073E6' }   # blue  — reliable indoor positioning
        satellite:  { color: '#34B248' }   # green — precise outdoor
        cellular:   { color: '#9B59B6' }   # purple
        ip:         { color: '#F49125' }   # orange — city-level only
        ipaddress:  { color: '#F49125' }   # same as ip (both are IP geolocation)
        unknown:    { color: '#B0B0B0' }   # grey  — no position data
        _count:
          title: Endpoint Count            # rename the count metric in the legend
```

Both `ip` (from F4IT RTR) and `ipaddress` (from `ipLocation()`) represent IP geolocation so they share a color. Assigning consistent meaning to colors across dashboards lets analysts recognize source types at a glance. The `_count.title` rename controls the label that appears in the legend and tooltip for the count metric.

#### Aggregation helpers

```cql
// Collect multiple values into one cell
| collect(UserName, separator=", ")

// Pick the record with the minimum value for a field (within groupBy)
| groupBy([aid], function=[
    selectFromMin(@timestamp, include=[hostname]),
    selectLast(Status)
  ])

// Human-readable duration from milliseconds
| formatDuration(field=duration_ms, precision=3)

// Unit conversion
| unit:convert(field=DataVolume, from="B", to="GB")

// Bit flag extraction
| bitfield:extractFlags(field="Attributes", onlyTrue=true, output=[[0, IsClipboard]])
```

#### URL construction for table link columns

```cql
| _url_param := "?"
| _encoded := urlEncode(SomeField)
| _link := format("[⧁](/investigate/search%srepo=all&query=%%23repo%%3D%%22base_sensor%%22%%20%%7C%%20aid%%3D%%22%s%%22&start=30d)", field=[_url_param, _encoded])
| rename(_link, as="")     // empty column header = icon-only column
```

**Why the empty rename:** Renaming the link column to `""` or `" "` (space) creates a narrow icon-only column that doesn't clutter the table header.

#### Emoji in queries for visual status indicators

```cql
| case {
    _eventCount > 0 | Status := "✅";
    *               | Status := "❌";
  }

// Or in a table with numeric encoding
| case {
    Severity=5 | _icon := "🔴";
    Severity=4 | _icon := "🟠";
    Severity=3 | _icon := "🟡";
    *          | _icon := "🟢";
  }
```

#### Inline query comments for readability

```cql
// Base Query - DataEgress Web
#repo="base_sensor" #event_simpleName="DataEgress"
| parseJson(DataEgressDestination, prefix=destination.)
| destination.channel[0]=0   //Web destination only
// Dashboard parameters (filters)
| UserName =~ regex(?user_name, flags="i")
// Section parameters (filters)
| PolicyName =~ in(values=[?web_egress_policy_name])
// Widget-specific filtering & aggregation
| groupBy(PolicyName)
```

**Convention:** Use three comment sections in every query on a multi-parameter dashboard:
1. `// Base Query` — event source and structural filters
2. `// Dashboard parameters` — global parameters shared across all sections
3. `// Section parameters` — parameters scoped to this section only

This makes it immediately obvious which filters are interactive vs. structural.

---

### Data Source Detector Pattern

A common "health check" widget that shows whether a data source is actively ingesting:

```cql
#repo="base_sensor" #event_simpleName="DataEgress"
| stats([
    count(as=_eventCount),
    max(@timestamp, as=_latest_event)
  ])
| "Data Source" := "⛁ My Data Source"
| case {
    _eventCount > 0 | Status := "✅" | _latest_event_duration := now() - _latest_event;
    *               | Status := "❌";
  }
| table(["Data Source", Status, _eventCount, _latest_event_duration])
| default(value="-", field=[_latest_event_duration])
| rename(_latest_event_duration, as="Last Ingest")
```

```yaml
    visualization: table-view
    options:
      configured-columns:
        Last Ingest:
          data-type: time_duration
```

Place this as a small `width: 5–6, height: 2` widget at the top of a section. It confirms data is flowing before analysts spend time interpreting empty charts.
