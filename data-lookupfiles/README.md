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

```
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