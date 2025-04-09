# Data Lookup Files

This directory contains lookup files for various data types. The files are used to create events in the system.

## Emoji Flag Lookup

Creates a country code lookup files for ISO3166 - 1 Alpha2 and Alpha3 to Emoji(15.1.0) Country Flags and TLD.

`python create_unicode_emoji.py --output cc_lookup.csv`

This file can be uploaded to the logscale system to create a lookup table for country codes and their corresponding emoji flags.

### cc_lookup.csv | cc_lookup.json

This file contains a list of country codes and their corresponding country names. It is used to map IP addresses to their respective countries.

```csv
char,name,region_name,sub_region_name,ISO3166-1-Alpha-2,ISO3166-1-Alpha-3,tld
🇦🇨,Ascension Island,Africa,Sub-Saharan Africa,AC,ASC,.ac
🇦🇩,Andorra,Europe,Southern Europe,AD,AND,.ad
...
```

## Create IPv4 Entries to test

### Create `createEvents()`

```f#
createEvents(["ipv4=17.32.15.5","ipv4=45.67.89.12","ipv4=23.45.67.89","ipv4=54.32.10.8ipv4=67.89.123.4","ipv4=34.56.78.90","ipv4=98.76.54.32","ipv4=123.45.67.8","ipv4=56.78.90.12","ipv4=78.90.123.4","ipv4=89.123.45.6","ipv4=90.12.34.56","ipv4=12.34.56.78","ipv4=34.78.90.12","ipv4=45.89.123.6","ipv4=67.12.34.56","ipv4=78.45.67.89","ipv4=89.67.12.34","ipv4=90.78.45.67","ipv4=12.89.67.45","ipv4=34.90.78.12","ipv4=45.12.89.67","ipv4=67.34.90.78","ipv4=78.45.12.89","ipv4=89.67.34.90","ipv4=90.78.45.12","ipv4=12.89.67.34","ipv4=34.90.78.45","ipv4=45.12.89.90","ipv4=67.34.12.78"])
```

### Raw

```f#
ipv4=17.32.15.5
ipv4=45.67.89.12
ipv4=23.45.67.89
ipv4=54.32.10.8
ipv4=67.89.123.45
ipv4=34.56.78.90
ipv4=98.76.54.32
ipv4=123.45.67.89
ipv4=56.78.90.12
ipv4=78.90.123.45
ipv4=89.123.45.67
ipv4=90.12.34.56
ipv4=12.34.56.78
ipv4=34.78.90.12
ipv4=45.89.123.67
ipv4=67.12.34.56
ipv4=78.45.67.89
ipv4=89.67.12.34
ipv4=90.78.45.67
ipv4=12.89.67.45
ipv4=34.90.78.12
ipv4=45.12.89.67
ipv4=67.34.90.78
ipv4=78.45.12.89
ipv4=89.67.34.90
ipv4=90.78.45.12
ipv4=12.89.67.34
ipv4=34.90.78.45
ipv4=45.12.89.90
ipv4=67.34.12.78
```

## Create Events

```f#
createEvents(["name=john,ph=555-1234", "name=joe,ph=555-9999", "name=sarah,ph=555-3366", "name=megan,ph=555-2244"])
```

```f#
createEvents(["name=john,product=apples,cnt=12", "name=john,product=bananas,cnt=1", "name=joe,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=sarah,product=apples,cnt=1", "name=holly,product=apples,cnt=1"])
```

### Raw Events
```f#
name=john,product=apples,price=1.12,organic=false,harvest=1744201562,transactionId=000000012,cnt=12
name=john,product=bananas,price=0.98,organic=false,harvest=1744203262,transactionId=000000013,cnt=1
name=joe,product=apples,price=1.12,organic=false,harvest=1744205232,transactionId=000000014,cnt=1
name=sarah,product=apples,price=1.25,organic=true,harvest=1744215262,transactionId=000000015,cnt=1
name=sarah,product=apples,price=1.25,organic=true,harvest=1744215262,transactionId=000000016,cnt=1
name=holly,product=apples,price=1.12,organic=false,harvest=1744225262,transactionId=000000017,cnt=1
name=john,product=oranges,price=1.50,organic=true,harvest=1744235262,transactionId=000000018,cnt=5
name=jane,product=bananas,price=0.98,organic=false,harvest=1744245262,transactionId=000000019,cnt=3
name=joe,product=grapes,price=2.10,organic=true,harvest=1744255262,transactionId=000000020,cnt=2
name=sarah,product=pears,price=1.75,organic=false,harvest=1744265262,transactionId=000000021,cnt=4
name=holly,product=peaches,price=2.25,organic=true,harvest=1744275262,transactionId=000000022,cnt=6
name=john,product=apples,price=1.12,organic=false,harvest=1744285262,transactionId=000000023,cnt=8
name=john,product=apples,price=1.12,organic=false,harvest=1744201562,transactionId=000000012,cnt=12
name=john,product=bananas,price=0.98,organic=false,harvest=1744203262,transactionId=000000013,cnt=1
name=joe,product=apples,price=1.12,organic=false,harvest=1744205232,transactionId=000000014,cnt=1
name=sarah,product=apples,price=1.25,organic=true,harvest=1744215262,transactionId=000000015,cnt=1
name=sarah,product=apples,price=1.25,organic=true,harvest=1744215262,transactionId=000000016,cnt=1
name=holly,product=apples,price=1.12,organic=false,harvest=1744225262,transactionId=000000017,cnt=1
name=john,product=oranges,price=1.50,organic=true,harvest=1744235262,transactionId=000000018,cnt=5
name=jane,product=bananas,price=0.98,organic=false,harvest=1744245262,transactionId=000000019,cnt=3
name=joe,product=grapes,price=2.10,organic=true,natural=true,harvest=1744255262,transactionId=000000020,cnt=2
name=sarah,product=pears,price=1.75,organic=false,harvest=1744265262,transactionId=000000021,cnt=4
name=holly,product=peaches,price=2.25,organic=true,harvest=1744275262,transactionId=000000022,cnt=6
name=john,product=apples,price=1.12,organic=false,harvest=1744285262,transactionId=000000023,cnt=8
name=jane,product=bananas,price=0.98,organic=false,harvest=1744295262,transactionId=000000024,cnt=2
name=joe,product=apples,price=1.12,organic=false,harvest=1744305262,transactionId=000000025,cnt=1
name=sarah,product=apples,price=1.25,organic=true,natural=true,harvest=1744315262,transactionId=000000026,cnt=3
name=holly,product=apples,price=1.12,organic=false,harvest=1744325262,transactionId=000000027,cnt=2
name=john,product=pears,price=1.75,organic=false,harvest=1744335262,transactionId=000000028,cnt=7
name=jane,product=grapes,price=2.10,organic=true,harvest=1744345262,transactionId=000000029,cnt=4
name=joe,product=peaches,price=2.25,organic=true,harvest=1744355262,transactionId=000000030,cnt=5
name=sarah,product=oranges,price=1.50,organic=true,harvest=1744365262,transactionId=000000031,cnt=6
name=holly,product=bananas,price=0.98,organic=false,harvest=1744375262,transactionId=000000032,cnt=3
name=john,product=apples,price=1.12,organic=false,harvest=1744385262,transactionId=000000033,cnt=9
name=jane,product=pears,price=1.75,organic=false,harvest=1744395262,transactionId=000000034,cnt=2
name=joe,product=oranges,price=1.50,organic=true,harvest=1744405262,transactionId=000000035,cnt=1
name=sarah,product=grapes,price=2.10,organic=true,lowcarbon=true,harvest=1744415262,transactionId=000000036,cnt=4
name=holly,product=peaches,price=2.25,organic=true,harvest=1744425262,transactionId=000000037,cnt=5
```

### Wrap Raw Events in createEvents()

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
```
