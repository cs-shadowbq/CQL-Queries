# Text Widgets in LogScale Dashboards

Two distinct widget types are used to display static or curated text content in LogScale dashboards: **`createEvents()` query widgets** (tabular data embedded in a query) and **`note` widgets** (markdown panels with no query).

---

## `createEvents()` Query Widgets

`createEvents()` widgets embed static JSON records directly inside a query string. The query generates rows from hardcoded data, then pipes them through standard CQL transformations (`parseJson`, `case {}`, `table()`, etc.) to produce a filtered, styled table. This is the right choice when the content is structured, filterable, or needs column-level styling.

### Minimal pattern

```f#
createEvents([
  "{\"Field1\": \"value\", \"Field2\": \"value\"}",
  "{\"Field1\": \"value2\", \"Field2\": \"value2\"}"
])
| parseJson()
| table([Field1, Field2], sortby=Field1, order=asc)
```

### With nested keys and `removePrefixes`

When JSON keys share a common prefix (e.g., `"Dashboard.Dashboard Name"`), use `removePrefixes` to strip it:

```f#
createEvents(["{
  \"Dashboard\": {
    \"Dashboard Name\": \"My Dashboard\",
    \"Data Source / Data Connector\": \"AWS CloudTrail\"
  }
}"])
| parseJson(removePrefixes=["Dashboard."])
| table(["Dashboard Name", "Data Source / Data Connector"])
```

### With parameter-driven filtering via `case {}`

A `case {}` block can classify rows before a parameter filter is applied. This is the standard pattern for the "Dashboards available for external data sources" widget:

```f#
// Last updated: 2026-01-25

createEvents(["{
    \"Dashboard\": {
      \"Dashboard Name\": \"[AWS - CloudTrail - Overview](/investigate/search/custom-dashboards/AWS%20-%20CloudTrail%20-%20Overview?repoOrViewName=search-all&packageScope=falcon/ngsiem-content)\",
      \"Data Source / Data Connector\": \"AWS CloudTrail\",
      \"Descriptions and Additional Notes\": \"Provides visibility into AWS CloudTrail data.\",
      \"#Vendor.dash\": \"aws\",
      \"#event.module.dash\": \"cloudtrail\"
    }
  }",
  "{
    \"Dashboard\": {
      \"Dashboard Name\": \"[Fortinet - NGFW - Overview](/investigate/search/custom-dashboards/Fortinet%20-%20NGFW%20-%20Overview?repoOrViewName=search-all&packageScope=falcon/ngsiem-content)\",
      \"Data Source / Data Connector\": \"Fortinet Fortigate\",
      \"Descriptions and Additional Notes\": \"Comprehensive monitoring of FortiGate NGFW environments.\",
      \"#Vendor.dash\": \"fortinet\",
      \"#event.module.dash\": \"fortigate\"
    }
  }"])
| parseJson(removePrefixes=["Dashboard."])

| case {
  in("Data Source / Data Connector", ignoreCase=true, values=["*aws*", "*amazon*"]) | Data_Source := "AWS";
  in("Data Source / Data Connector", ignoreCase=true, values=["*fortinet*"]) | Data_Source := "Fortinet";
  *;
}

| Data_Source = ?Data_Source

| table(["Dashboard Name", "Descriptions and Additional Notes", "Data Source / Data Connector"], sortby="Dashboard Name", order=asc)
```

The `?Data_Source` parameter defaults to `*` and is defined on the dashboard so analysts can filter by vendor without editing the query.

### YAML widget wrapper

```yaml
widgets:
  000ebefe-4bce-4e92-9d98-30fbe8bf93e4:
    x: 0
    y: 34
    description: This is not an exhaustive list — new dashboards are added regularly.
    height: 8
    queryString: |-
      // Last updated: 2026-01-25

      createEvents([...])
      | parseJson(removePrefixes=["Dashboard."])
      | case { ... }
      | Data_Source = ?Data_Source
      | table(["Dashboard Name", "Descriptions and Additional Notes", "Data Source / Data Connector"], sortby="Dashboard Name", order=asc)
    end: now
    start: 10m
    width: 12
    options:
      cell-overflow: wrap-text
      column-overflow: truncate
      configured-columns:
        Dashboard Name:
          color: '#29a34bff'
          open-links-in-new-tab: true
          render-as: link
        Data Source / Data Connector:
          color: '#8661D1'
        Descriptions and Additional Notes:
          color: '#126CC6FF'
      row-numbers-enabled: false
    visualization: table-view
    title: Dashboards available for external data sources
    isLive: false
    type: query
```

**Key `options` for `createEvents()` table widgets:**

| Option | Purpose |
|--------|---------|
| `render-as: link` | Renders markdown link syntax `[text](url)` as a clickable hyperlink |
| `open-links-in-new-tab: true` | Opens the rendered link in a new browser tab |
| `cell-overflow: wrap-text` | Wraps long text instead of truncating mid-word |
| `column-overflow: truncate` | Truncates at the column boundary (used alongside `wrap-text`) |
| `color: '#RRGGBBAA'` | Column header and cell text tint |

---

## `note` Widgets

Note widgets display static markdown content with no query. They are always visible (unlike the `description:` field on query widgets, which only appears on hover). Use them for dashboard introductions, section headers, callout banners, version stamps, and inline images.

### Basic note

```yaml
widgets:
  note-1756956466056-1:
    x: 2
    y: 1
    height: 3
    text: "### This dashboard introduces you to CrowdStrike's Next-Gen SIEM solution.\n\n\
      ### Training and resources are in the \"📚 Additional Information\" section.\n\n\
      ---\n\nⓘ **FUN FACT!** *Some widgets here are borrowed from other dashboards.*"
    width: 8
    title: ''
    type: note
```

### Colored banner / callout note

Add `backgroundColor` and `textColor` to create high-visibility banners (e.g., alerting notices, warnings):

```yaml
widgets:
  73791ebe-0aaa-440a-8ae4-e33f8b44c84f:
    x: 1
    backgroundColor: '#b52026'
    y: 9
    text: '### **ALERTING:** See the section "⚙️ Fusion SOAR" for information on
      sending alerts from CrowdStrike''s Next-Gen SIEM'
    width: 11
    height: 1
    textColor: '#f5f5f5'
    title: ' '
    type: note
```

`title: ' '` (single space) suppresses the title bar without triggering a YAML null/empty warning.

### Note with inline image

Images are embedded using standard markdown syntax. The URL can be a plain HTTPS link, a link with query parameters, or a `{{ parameter }}` interpolated URL.

> **CSP warning — US-1 cloud:** LogScale's `img-src` Content Security Policy restricts which external domains can serve images. In US-1, `assets.crowdstrike.com` is **not** on the allowlist — the browser blocks the request with a CSP violation error.
>
> The allowlist permits `data:` URIs, so **base64-embedded images always work** regardless of cloud. For external URLs, only these domains are permitted in US-1:
>
> - `https://assets.falcon.crowdstrike.com`
> - `https://assets-public.falcon.crowdstrike.com`
> - `https://storage.googleapis.com`
> - `https://*.qualtrics.com` / `https://*.chargebee.com`
> - `'self'`, `blob:`, `data:`
>
> If an image must come from an external URL, host it under an allowed domain or convert it to base64.

**Plain URL (subject to CSP — see above):**

```yaml
widgets:
  ngsiem-screenshot:
    x: 0
    y: 0
    width: 6
    height: 3
    title: ''
    type: note
    text: "![NG-SIEM overview](https://assets.crowdstrike.com/is/image/crowdstrikeinc/NG-Siem-Cap-1-1?wid=400&hei=200&fmt=png-alpha&qlt=95,0&resMode=sharp2&op_usm=3.0,0.3,2,0)"
```

**With `{{ parameter }}` interpolation** — useful when the asset hostname differs between cloud environments (US-1, US-2, EU-1, etc.):

```yaml
widgets:
  logo-note:
    x: 0
    y: 0
    width: 2
    height: 2
    title: ''
    type: note
    text: "![CrowdStrike logo](https://assets.{{ parameter \"CrowdStrike_cloud\" }}crowdstrike.com/store/partners/crowdstrike/CrowdStrike%20Logo%20512x512%20-%20white%20background%20%281%29.png)"
```

The `{{ parameter "CrowdStrike_cloud" }}` value is substituted at render time — e.g., `us-1.` or `eu-1.` — so the same dashboard YAML works across regions without editing the URL. Note that `assets.crowdstrike.com` is still CSP-blocked in US-1 regardless of parameter substitution; this pattern is only useful if your image is hosted on an allowed domain that differs per cloud.

### Note with base64 embedded image

When a dashboard must be self-contained (no external URL dependency, air-gapped environments, or package exports), images can be embedded directly as a base64 data URI using standard markdown syntax:

```markdown
![alt text](data:image/png;base64,<BASE64_DATA>)
```

The full YAML form in a note widget:

```yaml
widgets:
  logo-note-b64:
    x: 0
    y: 0
    width: 2
    height: 3
    title: ''
    type: note
    text: "![Example base64 image](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAIAAADTED8xAAADMElEQVR4nOzVwQnAIBQFQYXff81RUkQCOyDj1YOPnbXWPmeTRef+/3O/OyBjzh3CD95BfqICMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMO0TAAD//2Anhf4QtqobAAAAAElFTkSuQmCC)"
```

**Practical notes:**

- Base64 data URIs are fully self-contained — the image travels with the YAML file and requires no network access at render time.
- PNG is the most common format. Use `data:image/png;base64,` for PNGs, `data:image/jpeg;base64,` for JPEGs, `data:image/svg+xml;base64,` for SVGs.
- The base64 string must have **no line breaks** — it must be a single uninterrupted string inside the YAML value.
- In YAML double-quoted strings (`"..."`), the base64 payload requires no escaping as it contains only alphanumeric characters, `+`, `/`, and `=`.
- Large images significantly increase YAML file size. Prefer small logos or icons (< 50 KB source) over full-resolution photographs.

**Generating base64 from a file (shell):**

```bash
# macOS / Linux
base64 -i logo.png | tr -d '\n'

# Output is a single line — paste directly after "data:image/png;base64,"
```

### Note field reference

| Field | Type | Notes |
|-------|------|-------|
| `type` | `note` | Required |
| `text` | string | Markdown content. Use `\n` for newlines in single-quoted YAML strings. |
| `title` | string | Widget title bar. Use `''` or `' '` to suppress. |
| `x`, `y`, `width`, `height` | int | Grid position (12-column grid, section-relative `y`). |
| `backgroundColor` | hex string | Background fill color (e.g., `'#b52026'`). |
| `textColor` | hex string | Text color (e.g., `'#f5f5f5'`). |

### Common placement patterns

| Use case | Typical size | Position |
|----------|-------------|----------|
| Dashboard overview / intro | `width: 5–7, height: 6–8` | Top-right: `x: 5` or `x: 7, y: 0` |
| Section description | `width: 12, height: 2` | First widget in section: `x: 0, y: 0` |
| Alert / callout banner | `width: 11–12, height: 1` | Inline at relevant `y` |
| Version stamp | `width: 4–5, height: 2` | Top-left: `x: 0, y: 0` |
| Inline logo | `width: 1–2, height: 1–2` | Top-left alongside params |

### Version stamp pattern

```yaml
    text: |
      ```
      My Dashboard
      Version: 1.0.0
      Last updated: 2026-01-25
      ```
```

The fenced code block prevents markdown from formatting the version string.

---

## Choosing between `createEvents()` and `note`

| Scenario | Use |
|----------|-----|
| Curated list of links, descriptions, or metadata | `createEvents()` query widget |
| Content that needs filtering via a parameter | `createEvents()` query widget |
| Columns need per-value coloring or link rendering | `createEvents()` query widget |
| Static narrative text, section intros, callouts | `note` widget |
| Colored banner or alert notice | `note` widget with `backgroundColor` |
| Inline image or logo | `note` widget |
| Version / build stamp | `note` widget |
