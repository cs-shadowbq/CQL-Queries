# CQL Notes

Filter | Aggregate | Format

## Reference: 

https://library.humio.com/

https://github.com/CrowdStrike/logscale-community-content


## Optimizing steps

When writing queries, it is best to follow the following process in order:

    Time |      Narrow down the search timeframe as much as possible

    Tags |      Narrow down the result set starting with tagged fields (those starting with #)

    Filter |    Continue to filter the dataset with remaining Field Values that exist

    Negative Filter | After you have filtered what you want to see, filter what you don't want to see

    Regex |     Utilize any regex needed to filter down the data further, or for unparsed fields

    Functions | Transform your data how you would like with functions like Math, Evaluation, format, etc.

    Aggregate | Aggregate your data utilizing any aggregate functions, such as a sum(), top(), or a groupBy()

    Rename | Rename fields prior to the view 

    Join Data | Merge data from multiple queries together using adhox tables, or join statements

    View |      Perform any final visualization processing such as sorting or table functions.


## Examples

### Get all available fields in the query

```f#
... | fieldset() | sort(field)
```

### Deduplicate Lines

```f#
... | groupBy([ComputerName], function=[tail(1)]) | ...
```

### common sort & timestamp

```f#
| sort(field=timestamp, order=asc, limit=10000)
| timestamp := formatTime("%Y-%m-%d %H:%M:%S", field=timestamp, locale=en_US, timezone=Z)
```

### get just date from timestamp

```f#
| date := formatTime("%Y-%m-%d", field=@timestamp, locale=en_US, timezone=Z)
```

there are some functions that will grab the day of the only builtin

### testing for a value as a filter, more than regex or equal

```f#
| test(myFieldName<5)
```

### `table()` vs `select()`

 Network Events - Example

```f#
 #event_simpleName = Network*
| groupBy([ComputerName], function=[tail(1)]) 
| table([CommunityID, #event_simpleName, ComputerName, aip, LocalIP, LocalPort, RemoteIP, RemotePort, Protocol]) | rename(field="aip", as="ExternalIP")
```

Using `select()` instead of `table()` doesnt limit to 200 like `table()`.

They look extremely similar, but table() is actually and aggregation where select is a pluck.

```f#
#event_simpleName = Network*
| groupBy([ComputerName], function=[tail(1)]) 
| select([CommunityID, #event_simpleName, ComputerName, aip, LocalIP, LocalPort, RemoteIP, RemotePort, Protocol]) | rename(field="aip", as="ExternalIP")
```

## Groupby Example

### Groupby() with implied Count() 

CrowdStrike Detections 

```f# 
EventType="Event_ExternalApiEvent" 
| ExternalApiType="Event_DetectionSummaryEvent"
| groupBy("DetectId", function=(tail(1)))
| groupBy([SeverityName])
| sort(field=_count, order=desc)
```

### Groupby() with collect()
Detections with collection to show additional data without `_count`

```f#
EventType="Event_ExternalApiEvent" 
| ExternalApiType="Event_DetectionSummaryEvent"
| groupBy("DetectId", function=(tail(1)))
| groupBy([SeverityName], function=collect([ComputerName, Tactic, Technique]))
| sort(field=_count, order=desc)
```

### GroupBy() with explict count()

```f#
"#event_simpleName" = DnsRequest
| GroupBy(field=event_platform, function=(count()))
```

### Groupby() with `count()` and `collect()` functions

```f#
#event_simpleName=ProcessRollup2 
| event_platform=Win
| ImageFileName=/\\Device\\HarddiskVolume\d+(?<ShortFilePath>\\.+\\)(?<FileName>.+$)/
| select([FileName, ShortFilePath, ImageFileName])
| ShortFilePath=/Users.*Desktop/
| groupBy([FileName], function=([count(FileName), collect([ShortFilePath, ImageFileName])]))
| sort(_count)
```

## Enrichments

### enrichment via case

if fieldName value is equal to regex (AND n more matches) then do X (often assign a value)

```f#
| case {
       FileName=/net1?\.exe/ AND netFlag="start" | behaviorWeight := "4" ;
       FileName=/net1?\.exe/ AND netFlag="stop" AND CommandLine=/falcon/i | behaviorWeight := "25" ;
       FileName=/sc\.exe/ AND netFlag="start" | behaviorWeight := "4" ;
       FileName=/sc\.exe/ AND netFlag="stop" | behaviorWeight := "4" ;
       FileName=/sc\.exe/ AND netFlag=/(query|stop)/i AND CommandLine=/csagent/i | behaviorWeight := "25" ;
       FileName=/net1?\.exe/ AND netFlag="share" | behaviorWeight := "2" ;
       FileName=/net1?\.exe/ AND netFlag="user" AND CommandLine=/\/delete/i | behaviorWeight := "10" ;
       FileName=/net1?\.exe/ AND netFlag="localgroup" AND CommandLine=/\/delete/i | behaviorWeight := "10" ;
       FileName=/ipconfig\.exe/ | behaviorWeight := "3" ;
 * }
| default(field=behaviorWeight, value=1)
```

### enrichment with match

`severity` of 3 means "error" so put that text in a new field `severity_level`

```f#
| severity match { 
    0 => severity_level:="emergency" ;
    1 => severity_level:="alert" ;
    2 => severity_level:="critical" ;
    3 => severity_level:="error" ;
    4 => severity_level:="warning" ;
    5 => severity_level:="notification" ;
    6 => severity_level:="informational" ;
    7 => severity_level:="debug" ;
    * => * ;
  }
```

### enrichment via match file

file with single column of relevant data

```f#
// enrich events with severity name
| match("list.csv",field="cisco_severity")
```

```f#
// Enrich required fields from large csv
| aid=~match(file="aid_master_main.csv", column=[aid], include=[ProductType, Version, MAC, SystemManufacturer, SystemProductName, FirstSeen, Time], strict=false)
```

#### Country Code Lookup

Use [cc_lookup.csv](./data-lookupfiles/cc_lookup.csv) to enrich with Emoji Flags

```f#
createEvents(["ipv4=17.32.15.5","ipv4=45.67.89.12","ipv4=23.45.67.89","ipv4=54.32.10.8","ipv4=67.89.123.4","ipv4=34.56.78.90","ipv4=98.76.54.32","ipv4=123.45.67.8","ipv4=56.78.90.12","ipv4=78.90.123.4","ipv4=89.123.45.6","ipv4=90.12.34.56","ipv4=12.34.56.78","ipv4=34.78.90.12","ipv4=45.89.123.6","ipv4=67.12.34.56","ipv4=78.45.67.89","ipv4=89.67.12.34","ipv4=90.78.45.67","ipv4=12.89.67.45","ipv4=34.90.78.12","ipv4=45.12.89.67","ipv4=67.34.90.78","ipv4=78.45.12.89","ipv4=89.67.34.90","ipv4=90.78.45.12","ipv4=12.89.67.34","ipv4=34.90.78.45","ipv4=45.12.89.90","ipv4=67.34.12.78"]) | kvParse()
| !cidr(ipv4, subnet=["224.0.0.0/4", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "169.254.0.0/16", "0.0.0.0/32"])
| ipLocation(ipv4)
| match(file="cc_lookup.csv", column="ISO3166-1-Alpha-2", field=ipv4.country, include=["char", "name"], ignoreCase=true, strict=false)
| rename(field="char", as="FlagCountry")
| rename(field="name", as="Country")
| select([@timestamp, ipv4, FlagCountry, Country])
```

![Screenshot 2025-04-08 at 4 55 34 PM](https://github.com/user-attachments/assets/15d0144a-8bc0-42f0-9f08-20e7f3c17253)


Group by Country

```f#
createEvents(["ipv4=17.32.15.5","ipv4=45.67.89.12","ipv4=23.45.67.89","ipv4=54.32.10.8","ipv4=67.89.123.4","ipv4=34.56.78.90","ipv4=98.76.54.32","ipv4=123.45.67.8","ipv4=56.78.90.12","ipv4=78.90.123.4","ipv4=89.123.45.6","ipv4=90.12.34.56","ipv4=12.34.56.78","ipv4=34.78.90.12","ipv4=45.89.123.6","ipv4=67.12.34.56","ipv4=78.45.67.89","ipv4=89.67.12.34","ipv4=90.78.45.67","ipv4=12.89.67.45","ipv4=34.90.78.12","ipv4=45.12.89.67","ipv4=67.34.90.78","ipv4=78.45.12.89","ipv4=89.67.34.90","ipv4=90.78.45.12","ipv4=12.89.67.34","ipv4=34.90.78.45","ipv4=45.12.89.90","ipv4=67.34.12.78"]) | kvParse()
| !cidr(ipv4, subnet=["224.0.0.0/4", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "169.254.0.0/16", "0.0.0.0/32"])
| ipLocation(ipv4)
| match(file="cc_lookup.csv", column="ISO3166-1-Alpha-2", field=ipv4.country, include=["char", "name"], ignoreCase=true, strict=false)
| rename(field="char", as="FlagCountry")
| rename(field="name", as="Country")
| select([@timestamp, ipv4, FlagCountry, Country])
| groupBy([Country], function=([count(Country), collect([Country, FlagCountry, _count])]))
| sort(_count)
```

![Screenshot 2025-04-08 at 4 46 52 PM](https://github.com/user-attachments/assets/daed9fcf-f465-47c3-baf1-d86e9b2cc002)


### enrichment via join & lookup file

```f#
| join(query={
    readFile("list.csv")
    | rename("domainName", as="tld")
}, field=[tld], include=[*])
```

### using in() to ensure the value is present?

```f#
#repo="falcon_for_it" 
| event_type=ITQueryResult  
| execution_id="49fe4e0aa6b145c88c014778dc41ce5b" 
| in(aid, values=[*], ignoreCase=true) 
| in(hostname, values=[*], ignoreCase=true) 
| groupBy([@id], function=tail(1),limit=10000)
```

```f#
// Narrow search to only include Linux, Container, and K8 systems
| in(field="event_platform", values=[Lin, Win])
```

### Enrichment with if .. then .. else ..

Unlike a case or match statement, the if() can be embedded into other functions and expressions.

```f#
| statusClass :=
if(regex("^1", field=statuscode), then="informational", else=
if(regex("^2", field=statuscode), then="successful", else=
if(regex("^3", field=statuscode), then="redirection", else=
if(regex("^4", field=statuscode), then="client error", else=
if(regex("^5", field=statuscode), then="server error", else=
"unknown")))))

| success := if(status < 500, then=if(status!=404, then=1, else=0), else=0)

| critical_status := if((in(status, values=["500", "404"])), then="Critical", else="Non-Critical")
```

## Formatting

### Human Readable numbers (kb,mb,gb,tb)

```f#
| case {
    SumSize>=1099511627776 | Transfered:=unit:convert(SumSize, to=T) | format("%,.2f TB",field=["Transfered"], as="Transfered");
    SumSize>=1073741824 | Transfered:=unit:convert(SumSize, to=G) | format("%,.2f GB",field=["Transfered"], as="Transfered");
    SumSize>=1048576| Transfered:=unit:convert(SumSize, to=M) | format("%,.2f MB",field=["Transfered"], as="Transfered");
    SumSize>=1024 | Transfered:=unit:convert(SumSize, to=k) | format("%,.2f KB",field=["Transfered"], as="Transfered");
    * | Transfered:=format("%,.2f Bytes",field=["SumSize"]);
}
```

## Mask sensitive data

### Using hashrewrite() and hashmatch

* Replace the value in the `sensitivefield` field with the hash of the existing value, also replacing it in `@rawstring`

Hide it in parsing

```f#
...
| hashRewrite(sensitivefield, salt="mysalt")
```

Search for it in query

```f#
...
| sensitivefield =~ hashMatch("SecretData", salt="mysalt")
```

ref: https://library.humio.com/data-analysis/functions-hashrewrite.html

### Using format() with `*`

print a bunch of * then the last five characters of the string

```f#
| regex("^.*(?<last5char>.{5}$)", field=myFieldName)
| format(format="*********%s", field=[last5char], as=myFieldName)
```

### Using crypto()

calculate a field you may want to save the hash the data for comparing or grouping

* note `@rawstring` still has the `api_keys` value in this case. 

```f#
| crypto:sha256([api_keys], as=key_hash)
```

## Negative Queries / Negation

### Regex and Then negative Filter then Filter.. (seems backwards can test this) 2s 482ms

```f#
#event_simpleName=DnsRequest
| DomainName=/\./
| DomainName != "*.bind"
| RequestType=16
| tld := splitString(field=DomainName, by="\.")
| _outLength := array:length("tld[]")
| lastIndex := _outLength-1
| lastValue := getField(format("tld[%s]", field=[lastIndex]))
| lastButOneIndex := _outLength-2
| lastButOneValue := getField(format("tld[%s]", field=[lastButOneIndex]))
| array:drop("tld[]")
| tld := format("%s.%s", field=[lastButOneValue, lastValue])
| drop([lastIndex, lastButOneIndex, lastButOneValue, lastValue, _outLength])
| groupBy([tld])
```

ReOrder for Effeciency 1s 800ms .. better :-)

```f#
#event_simpleName=DnsRequest
| RequestType=16
| DomainName != "*.bind"
| DomainName=/\./
| tld := splitString(field=DomainName, by="\.")
| _outLength := array:length("tld[]")
| lastIndex := _outLength-1
| lastValue := getField(format("tld[%s]", field=[lastIndex]))
| lastButOneIndex := _outLength-2
| lastButOneValue := getField(format("tld[%s]", field=[lastButOneIndex]))
| array:drop("tld[]")
| tld := format("%s.%s", field=[lastButOneValue, lastValue])
| drop([lastIndex, lastButOneIndex, lastButOneValue, lastValue, _outLength])
| groupBy([tld])
```

## Using example data with pre-aggregated fields to cast to Array from String

SanKey Chart

```f#
createEvents(["src=john,dst=apples,cnt=12", "src=john,dst=bananas,cnt=1", "src=joe,dst=apples,cnt=1", "src=sarah,dst=apples,cnt=1", "src=sarah,dst=apples,cnt=1", "src=sarah,dst=apples,cnt=1"])| kvParse()
| sankey(source="src", target="dst", weight=(sum(cnt)))
```

![sankey](https://github.com/user-attachments/assets/2d2ba074-0fb1-41d8-87fa-856c11130a24)


if you wanted to get the Event Table values instead of a SANKEY

```f#
createEvents(["src=john,dst=apples,cnt=12", "src=john,dst=bananas,cnt=1", "src=joe,dst=apples,cnt=1", "src=sarah,dst=apples,cnt=1", "src=sarah,dst=apples,cnt=1", "src=sarah,dst=apples,cnt=1"])| kvParse()
| groupBy([dst, src], function=([sum(cnt), collect([dst, src])]))
```
![groupby](https://github.com/user-attachments/assets/ceb491c3-93ed-4ed8-9028-4d775c994ad4)


## Chained functions() network asn geoip rdns as builtins

using default(), and test()

```f# 
// Get ASN Details
| asn(OriginSourceIpAddress, as=asn)
// Omit ZScaler infra
| asn.org!=/ZSCALER/
//Get IP Location
| ipLocation(OriginSourceIpAddress)
// Get geohash; precision can be adjusted as desired
| geoHash := geohash(lat=OriginSourceIpAddress.lat, lon=OriginSourceIpAddress.lon, precision=2)
// Get RDNS value if available
| rdns(OriginSourceIpAddress, as=rdns)
//Set default values for blank fields
| default(value="Unknown Country", field=[OriginSourceIpAddress.country])
| default(value="Unknown City", field=[OriginSourceIpAddress.city])
| default(value="Unknown ASN", field=[asn.org])
| default(value="Unknown RDNS", field=[rdns])
// Create unified IP details field
| format(format="%s (%s, %s) [%s] - %s", field=[OriginSourceIpAddress, OriginSourceIpAddress.country, OriginSourceIpAddress.city, asn.org, rdns], as=ipDetails)
// Aggregate by UserId and geoHash
| groupBy([UserId, geoHash], function=([count(as=logonCount), min(@timestamp, as=firstLogon), max(@timestamp, as=lastLogon), collect(ipDetails)]))
// Look for geohashes with fewer than 5 logins; can be adjusted as desired
| test(logonCount<5)
```

## Adhoc Tables Joining data - `defineTable()` vs `join()`

In many scenarios, ad-hoc tables can be used in place of the join() function. However, LogScale generally recommends using ad-hoc tables.

good for using against from repos. 

```f#
defineTable(query={*}, name="custom_tablename", include=[field1, field2])
```

### Find Apple Farmers Name and Phone in the Unites States

```f#
defineTable(name="USFarmers",query={country=UnitedStates},include=[name, ph])
| #repo=Fruits
| products=Apples
| ...
| match(table=USFarmers, field=name, strict=false)
| select([name, ph])
```



With createEvent() data.. 

```f#
// Users_Table
createEvents(["name=john,ph=555-1234", "name=joe,ph=555-9999", "name=sarah,ph=555-3366", "name=megan,ph=555-2244"])| kvParse()
```
![Screenshot 2025-03-31 at 4 19 05 PM](https://github.com/user-attachments/assets/3263fbd1-98dc-4058-81e4-c9798353b956)

```f#
// Logs or Product_Table
createEvents(["name=john,product=apples,cnt=12", "name=john,product=bananas,cnt=1", "name=joe,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=holly,product=apples,cnt=1"])| kvParse()`
```
![Screenshot 2025-03-31 at 4 18 56 PM](https://github.com/user-attachments/assets/7aaeb311-7385-4200-abbf-7aa3210f371f)


#### Left Join() as a defineTables()

* `strict=false` will return `holly` even though she does not have a `ph`

```f#
defineTable(name="users_table",query={createEvents(["name=john,ph=555-1234", "name=joe,ph=555-9999", "name=sarah,ph=555-3366", "name=megan,ph=555-2244"])| kvParse() |ph=*},include=[name, ph])
| createEvents(["name=john,product=apples,cnt=12", "name=john,product=bananas,cnt=1", "name=joe,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=holly,product=apples,cnt=1"])
| kvParse()
| match(table=users_table, field=name, strict=false)
```
![Screenshot 2025-03-31 at 1 13 50 PM](https://github.com/user-attachments/assets/23c541a7-6e74-4463-ab43-d1e85a59fe6f)


#### Right Join() as a definedTables()

* `strict=false` will return `megan` even though she does not have a `product`
* Note: `readFile()` is used to load the dataTable. This is necessary because 2 x `defineTable()` are created.
* Lack of: There is NO longer a `@timestamp`, `@timestamp.nanos` or `@rawstring` because two tables are now being joined.

```f#
defineTable(name="users_table",query={createEvents(["name=john,ph=555-1234", "name=joe,ph=555-9999", "name=sarah,ph=555-3366", "name=megan,ph=555-2244"])| kvParse() |ph=*},include=[name, ph])
| defineTable(name="product_table", query={createEvents(["name=john,product=apples,cnt=12", "name=john,product=bananas,cnt=1", "name=joe,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=holly,product=apples,cnt=1"])| kvParse()},include=[name,product,cnt] )
| readFile("users_table")
| match(table=product_table, field=name, strict=false)
| table(fields=[name,ph,product])
```

![Screenshot 2025-03-31 at 3 23 32 PM](https://github.com/user-attachments/assets/214798f1-6707-4388-9df3-d9da045b2728)

#### Inner Join() as a defineTable()

* we going to use `name=john` as the inner join filter

```f#
defineTable(name="users_table",query={createEvents(["name=john,ph=555-1234", "name=joe,ph=555-9999", "name=sarah,ph=555-3366", "name=megan,ph=555-2244"])| kvParse() |name=john},include=[name, ph])
| createEvents(["name=john,product=apples,cnt=12", "name=john,product=bananas,cnt=1", "name=joe,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=holly,product=apples,cnt=1"])| kvParse()
| name=john
| match(table=users_table, field=name, strict=false)
```

![Screenshot 2025-03-31 at 4 16 06 PM](https://github.com/user-attachments/assets/bc858f0e-ed21-4dc5-b9b1-9ca958c08d06)


https://library.humio.com/data-analysis/query-joins-methods-adhoc-tables.html#query-joins-methods-adhoc-tables-join

## Complex Query

* Negative Indexes
* format two field's value into a new field and value
* drops
* join
* readfile
* splitstring into array

```f#
#event_simpleName=DnsRequest
| select([@timestamp, aid, LocalAddressIP4, RemoteAddressIP4, ComputerName, DomainName, HttpHost, HttpPath, ContextBaseFileName])
// Drop DNS to match the tld xxx.yyy
| tld := splitString(field=DomainName, by="\.")
| _outLength := array:length("tld[]")
| lastIndex := _outLength-1
| lastValue := getField(format("tld[%s]", field=[lastIndex]))
| lastButOneIndex := _outLength-2
| lastButOneValue := getField(format("tld[%s]", field=[lastButOneIndex]))
| array:drop("tld[]")
| tld := format("%s.%s", field=[lastButOneValue, lastValue])
| drop([lastIndex, lastButOneIndex, lastButOneValue, lastValue, _outLength])
//
| join(query={
    readFile("ai-list.csv")
    | rename("domainName", as="tld")
}, field=[tld], include=[*])
```

## Subquery Comparison 

```f#
createEvents(["name=john,product=apples,price=1.12,organic=false,harvest=1744201562,transactionId=000000012,cnt=12",
"name=john,product=bananas,price=0.98,organic=false,harvest=1744203262,transactionId=000000013,cnt=1",
"name=joe,product=apples,price=1.12,organic=false,harvest=1744205232,transactionId=000000014,cnt=1",
"name=sarah,product=apples,price=1.25,organic=true,harvest=1744215262,transactionId=000000015,cnt=1",
"name=sarah,product=apples,price=1.25,organic=true,harvest=1744215262,transactionId=000000016,cnt=1",
"name=holly,product=apples,price=1.12,organic=false,harvest=1744225262,transactionId=000000017,cnt=1",
"name=john,product=oranges,price=1.50,organic=true,harvest=1744235262,transactionId=000000018,cnt=5",
"name=jane,product=bananas,price=0.98,organic=false,harvest=1744245262,transactionId=000000019,cnt=3",
"name=joe,product=grapes,price=2.10,organic=true,natural=true,harvest=1744255262,transactionId=000000020,cnt=2",
"name=sarah,product=pears,price=1.75,organic=false,harvest=1744265262,transactionId=000000021,cnt=4",
"name=holly,product=peaches,price=2.25,organic=true,harvest=1744275262,transactionId=000000022,cnt=6",
"name=john,product=apples,price=1.12,organic=false,harvest=1744285262,transactionId=000000023,cnt=8",
"name=jane,product=bananas,price=0.98,organic=false,harvest=1744295262,transactionId=000000024,cnt=2",
"name=joe,product=apples,price=1.12,organic=false,harvest=1744305262,transactionId=000000025,cnt=1",
"name=sarah,product=apples,price=1.25,organic=true,natural=true,harvest=1744315262,transactionId=000000026,cnt=3",
"name=holly,product=apples,price=1.12,organic=false,harvest=1744325262,transactionId=000000027,cnt=2",
"name=john,product=pears,price=1.75,organic=false,harvest=1744335262,transactionId=000000028,cnt=7",
"name=jane,product=grapes,price=2.10,organic=true,harvest=1744345262,transactionId=000000029,cnt=4",
"name=joe,product=peaches,price=2.25,organic=true,harvest=1744355262,transactionId=000000030,cnt=5",
"name=sarah,product=oranges,price=1.50,organic=true,harvest=1744365262,transactionId=000000031,cnt=6",
"name=holly,product=bananas,price=0.98,organic=false,harvest=1744375262,transactionId=000000032,cnt=3",
"name=john,product=apples,price=1.12,organic=false,harvest=1744385262,transactionId=000000033,cnt=9",
"name=jane,product=pears,price=1.75,organic=false,harvest=1744395262,transactionId=000000034,cnt=2",
"name=joe,product=oranges,price=1.50,organic=true,harvest=1744405262,transactionId=000000035,cnt=1",
"name=sarah,product=grapes,price=2.10,organic=true,lowcarbon=true,harvest=1744415262,transactionId=000000036,cnt=4",
"name=holly,product=peaches,price=2.25,organic=true,harvest=1744425262,transactionId=000000037,cnt=5"]) | kvParse() | findTimestamp(field=harvest)
| head()
| name=*
| groupBy(
    name, 
    function = slidingTimeWindow(
            function=
                {
                    [
                        {if(regex("true", field=organic), then="1",else="0", as=q[1])|r[1]:=max(q[1])},
                        {if(regex("true", field=natural),then="1",else="0", as=q[2])|r[2]:=max(q[2])},
                        {if(regex("true", field=lowcarbon),then="1",else="0", as=q[3])|r[3]:=max(q[3])},
                        {if(regex(".*", field=FAKE),then="1",else="0", as=q[4])|r[4]:=max(q[4])},
                        {if(regex(".*", field=EMPTY),then="1",else="0", as=q[5])|r[5]:=max(q[5])}
                    ]
                    | rulesHit:=r[1]+r[2]+r[3]+r[4]+r[5]
                }, span=1h
    )    
)
| rulesHit >= 2
| table(fields=[@timestamp, rulesHit, name, cnt, organic, lowcarbon, natural, price])
```

### Explanation of the above query:

Using `if()` to ensure the value of `q[x]` is set to 1 or 0.

```f#
|if(regex(".*", field=organic),then="1",else="0", as=q[1])
```

`stats()` over subqueries with setting `r[x]` via `max()` for the aggregate required.

    * `r[x]` is stating that the value of query is true for the given field, roughly rule_1 rule_2 rule_3 etc
    * `q[x]` is the value placeholder, roughly query_1 query_2 query_3 etc
    * `rulesHit` is the sum of all the rules that were hit, so you can make a test against it. >,>=,<,<=,==,!= etc..

```f#
...|
[
    {if(regex("true", field=organic), then="1",else="0", as=q[1])|r[1]:=max(q[1])},
    {if(regex("true", field=natural),then="1",else="0", as=q[2])|r[2]:=max(q[2])},
    {if(regex("true", field=lowcarbon),then="1",else="0", as=q[3])|r[3]:=max(q[3])},
    {if(regex(".*", field=FAKE),then="1",else="0", as=q[4])|r[4]:=max(q[4])},
    {if(regex(".*", field=EMPTY),then="1",else="0", as=q[5])|r[5]:=max(q[5])}
]
| rulesHit:=r[1]+r[2]+r[3]+r[4]+r[5]
```


* `head()` is used to order and limit the results.
* `name=*` is used to ensure all rows that have names are included.
* `groupBy()` is using `field=name` and the `slidingTimeWindow()` function to aggregate the data over a `1h` hour window.
* `rulesHit >= 2` is the final filter to only show the results that have hit 2 or more of the rules.

* `table()` is used to show the results in a table format with the fields specified.

## metaprogramming

use format(), setfield(), getfield(), and sometimes eval()

```f#
| tld := format("%s.%s", field=[lastButOneValue, lastValue])
| item := 4
| setField(target="foo", value=item + 10)
| setField(target="baaz", value=if(item == 4, then="OK", else="not OK"))

// on the fly function
| eval(itembytes = item * 1024)

// last index of array
| index := array:length("foo[]")-1
| fieldName := format("foo[%s]", field=[index])
| result := getField(fieldName)
```
