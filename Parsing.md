# Parsing

The main difference between writing a parser and writing a CQL search query is that you cannot use aggregate functions:
* `groupBy()`
* `table()`
* `worldMap()`
* ...

## Use the Schemas

CrowdStrike Parsing Standard (CPS) - An derived Standard from the Elastic Common Schema (ECS 8.x)

* Parser Schemas - https://schemas.humio.com/parser/v0.3.0

At a high level, ECS provides fields to classify events in two different ways: "Where it’s from" (e.g., event.module, event.dataset, agent.type, observer.type, etc.), and "What it is." The categorization fields hold the "What it is" information, independent of the source of the events.

ECS defines four categorization fields for this purpose, each of which falls under the event.* field set.

* event.kind 
  * `alert|asset|enrichment|event|metric|state|pipeline_error|signal`
* event.category 
  * `api|authentication|configuration|database|driver|email|file|host|iam|intrusion_detection|library|malware|network|package|process|registry|session|threat|vulnerability|web`
* event.type 
  * `access|admin|allowed|change|connection|creation|deletion|denied|end|error|group|indicator|info|installation|protocol|start|use`
* event.outcome 
  * `failure|success|unknown`

Reference: 
* https://schemas.humio.com/
* https://library.humio.com/logscale-parsing-standard/pasta.html
* https://www.elastic.co/docs/reference/ecs/ecs-category-field-values-reference

Additional ECS Fields

* https://github.com/elastic/ecs/blob/v8.17.0/generated/csv/fields.csv

## Dropping Common items

If events are received via syslog, there may be a priority number at the beginning you want to drop. Drop this early in the parser, or parse it later. 

```f#
|...
| replace("^\<[\d]+\>", with="") |
|...
```

Drop empty lines

```f#
| case {
    @rawstring="" | dropEvent();
    *
  }
```

Remove carriage returns and new lines as this may cause issues parsing JSON

```f#
| ...
| replace(regex="\n", replacement="")
| replace(regex="\r", replacement="")
| ...
```

## Time Issues

### Set Time the most common way

```f#
| ...
| findTimestamp(field=Vendor.timestamp,timezone=UTC)
| ...
```

### Fix inconsistent timestamp Epoch lengths

```f#
| ...
|  case {
      regex("^(?<epoch>.{13})", field=eventtime) | parseTimestamp(field=epoch, format=unixtimeMillis);
      regex("^(?<epoch>.{10})", field=eventtime) | parseTimestamp(field=epoch, format=unixtime);
  * } 
|  drop(epoch)
| ...
```

### Fix Uncombined DateTimeStamp

Note: We have Date (MM/dd/yy) and Time (HH:mm:ss) and will drop it directly onto @timestamp

```f#
| ...
| concat([Date, Time], as=@timestamp)
| parseTimestamp("MM/dd/yyHH:mm:ss", field=@timestamp, timezone="UTC")
| ...
```

## Syslog Items

### Parsing Standard Syslog

Use regular expression named grouping for assigning common values

```f#
 @rawstring = /^(\<(?<log.syslog.priority>\d+?)\>)?(?<@timestamp>(?:[A-Za-z]{3} \d{1,2} \d{4} \d{2}:\d{2}:\d{2})|(?:[\d\-]+T[\d\:]+\S+))[\s\:]+(?<log.syslog.hostname>\-|[!-~]+)?[\s\:]+((?<log.syslog.appname>[^\s\:\[\]]+)\[(?<log.syslog.procid>\d+)\]:\s)?\%(?<Vendor.facility>[A-Za-z0-9_]+)-(?<log.syslog.severity.code>[0-7]+)-(?<Vendor.mnemonic>(?<_cls>[A-Z0-9_]{3})[A-Z0-9_]*): (?<Vendor.message>.*)[\r\n]*$/
```

These extra CPS/ECS fields are defined in ECS 8.17


|Field_Set|Field|Type|Level|Example|Description
|---|---|---|---|---|---|
|log|log.syslog|object|extended||Syslog metadata|
|log|log.syslog.appname|keyword|extended|sshd|The device or application that originated the Syslog message.|
|log|log.syslog.facility.code|long|extended|23|Syslog numeric facility of the event.|
|log|log.syslog.facility.name|keyword|extended|local7|Syslog text-based facility of the event.|
|log|log.syslog.hostname|keyword|extended|example-host|The host that originated the Syslog message.|
|log|log.syslog.msgid|keyword|extended|ID47|An identifier for the type of Syslog message.|
|log|log.syslog.priority|long|extended|135|Syslog priority of the event.|
|log|log.syslog.procid|keyword|extended|12345|The process name or ID that originated the Syslog message.|
|log|log.syslog.severity.code|long|extended|3|Syslog numeric severity of the event.|
|log|log.syslog.severity.name|keyword|extended|Error|Syslog text-based severity of the event.|
|log|log.syslog.structured_data|flattened|extended||Structured data expressed in RFC 5424 messages.|
|log|log.syslog.version|keyword|extended|1||


### Keeping Syslog priority

log syslog severity numbers may need to be decoded.

```f#
| log.syslog.severity.code match {
      "1" => log.syslog.severity.name := "Alert";
      "2" => log.syslog.severity.name := "Critical";
      "3" => log.syslog.severity.name := "Error";
      "4" => log.syslog.severity.name := "Warning";
      "5" => log.syslog.severity.name := "Notification";
      "6" => log.syslog.severity.name := "Informational";
      "7" => log.syslog.severity.name := "Debugging";
      * => *
  }
```

## Keeping fields Compliant to CPS

If the event contains fields which don't exist in ECS, their name is prefixed with the string literal `Vendor.`

This gives the ECS fields the root namespace, while vendor specific fields can always be found with the Vendor. prefix.

### Create the basic CPS fields for the parser

```f#
| Cps.version := "1.0.0"
| Parser.version := "0.0.1"
| Vendor := "mywebapp"
| ecs.version := "8.11.0"
| event.kind := "event"
| event.module := "websecurity"
```

additional fields

```f#
| event.dataset := "apache.log"
| observer.type := "application"
| observer.hostname := "www.example.com"
```

### Implement via JSON Parser

```f#
| ...
| parseJson(field="json",prefix="Vendor.", excludeEmpty=true, handleNull=discard)
| ...
```

## Matching against Vendor Codes



```f#
| Vendor.mnemonic match {
    "001" =>
        event.outcome := "failure"
        | array:append(array="event.category[]", values=["configuration"])
        | array:append(array="event.type[]", values=["change"])
        // Parse the 001 Message
        | Vendor.message = /^(?<network.direction>\S+?)\s(?<network.transport>\S+?)\s\w+?\s\w+?\s\w+?\s(?<source.ip>\S+?)\/(?<source.port>\S+?)\s\w+?\s(?<destination.ip>\S+?)\/(?<destination.port>\S+?)\s.*?interface\s(?<observer.ingress.interface.alias>\S+)/
        // normalize some of the fields
        | lower(field="network.direction", as="network.direction")
        | lower(field="network.transport", as="network.transport");
    in(values=[002, 003, 004]) =>
          event.outcome := "success"
          | array:append(array="event.category[]", values=["session","authentication"])
          | array:append(array="event.type[]", values=["connection","info"])
          | Vendor.message = /User=(?<user.name>\S+?),.*?IP=(?<client.ip>\S+?),\s(?<Vendor.sub_message>.*)/
          | case {
              Vendor.sub_message = /adding/
                  | array:drop("event.type[]")
                  | array:append(array="event.type[]", values=["connection","start"]);
              Vendor.sub_message = /removing/
                  | array:drop("event.type[]")
                  | array:append(array="event.type[]", values=["connection","end"]);
              *;
          };

```

## Keeping Repeated Keys, instead of dropping them

Note: the use of the _underscore is used to make the assignments clearer rather than reuse

```f#
createEvents("Foo=A\nBar=Z\nBar=X\nBar=Y\nBaz=1\nBaz=2\nQux=JJ")
// Get the keys (repeated will be the lastseen by default)
| kvParse()

// regex-create new variables for known-multi-array keys
| regex(regex="(?<_Foo>Foo=[^\n]+(?:\nFoo=[^\n]+)*)", repeat=true, field=@rawstring, strict=false, flags=F)
| regex(regex="(?<_Bar>Bar=[^\n]+(?:\nBar=[^\n]+)*)", repeat=true, field=@rawstring, strict=false, flags=F)
| regex(regex="(?<_Baz>Baz=[^\n]+(?:\nBaz=[^\n]+)*)", repeat=true, field=@rawstring, strict=false, flags=F)

// Split the multi-line string into an array[], as targets are Foo[] 
| splitString(by="Foo=", as=Foo, field=_Foo)
| splitString(by="Bar=", as=Bar, field=_Bar)
| splitString(by="Baz=", as=Baz, field=_Baz)

// Drop the original bad columns create by kvParse()
| drop([Foo, Bar, Baz])
// Drop the temporary columns
| drop([_Foo, _Bar, _Baz])

// Get rid of empty Array Values
| array:filter(array="Foo[]", var="x", function={x!=""})
| array:filter(array="Bar[]", var="x", function={x!=""})
| array:filter(array="Baz[]", var="x", function={x!=""})
```

### Collecting the possible keys

* NOT PARSE COMPLIANT (use of `groupby()`).. This is used to help investigate data

```f#
// NOT FOR A PARSER
createEvents("Foo=A\nBar=Z\nBar=X\nBar=Y\nBaz=1\nBaz=2\nQux=JJ")
// Get the keys (repeated will be the lastseen by default)
| kvParse()

| regex("(?<key>[^=\n]+)=(?<value>[^\n]+)", repeat=true)
| values:=splitString(field=value, by=\n)
| groupBy([key])
| drop(["_count"])
```

## Creating tagged fields

Dont add a # to a field, go into "Parser > Settings> Fields" to Tag and add `myFieldName` to the list if you intend to tag the field. The parser script will now produce a field named `#myFieldName` and remove `myFieldName` from the event.

### Yaml Parser Files

In the Yaml parser files, you can define the tag fields on the bottom of the file in a section called `tagFields:`

```yaml
tagFields:
- myFieldName
```

### Keeping the tagged fields Parser CPS Compliant

Implement CPS Compliant Parser tags

```f#
#Cps.version
#Vendor
#ecs.version
#event.dataset
#event.kind
#event.module
#event.outcome
#observer.type
```


## Reference

https://library.humio.com/data-analysis/parsers-create.html