Example Data Schema Exploration
-----------------------------------

### List the columns in the CSV File

```f#
readFile("falconUserIdentityContext.csv") 
| head(1)
| fieldset()
```


Examples of Existing Out of the Box Lookup Files
----------------------------------

### Core 

- aid_master_main.csv 

`SystemManufacturer, aip, Version, event_platform, ProductType, SiteName, SystemProductName, MachineDomain, FirstSeen, AgentVersion, LocalAddressIP4, aid ,Time, ComputerName, OU, cid, MAC`  

- aid_master_details.csv

`ChassisType, ConfigIDBuild, cloud.provider,  User, cloud.instance.id, aid, SystemSerialNumber, HostHiddenStatus, BiosManufacturer, BiosVersion, cloud.account.id, FalconGroupingTags, SensorGroupingTags, cid, cloud.availability_zone`

- cid_name.csv

`name, cid`

### Extended Lookups

- falconUserIdentityContext.csv

`user.active_directory.is_locked, user.active_directory.samaccountname, user.full_name, user.active_directory.guid, user.location, user.last_name, user.active_directory.manager.guid, user.email, user.risk_severity, user.active_directory.is_enabled, user.active_directory.domain, user.is_human, user.active_directory.is_password_compromised, user.active_directory.last_activity_date, user.is_watched, email, user.active_directory.upn, user.department, user.used_assets.guid, user.is_privileged, displayName, user.title, user.first_name, entityID, user.id, user.is_hybrid, user.active_directory.creation_date, user.active_directory.sid, user.used_locations`

- falconEntityEnrichment.csv 

`network.address, hostname, aid`

Additional Definition 
-----------
- falcon/investigate/sid_list.csv
- falcon/investigate/chassis.csv
- falcon/investigate/geo_mappings.csv (
- falcon/investigate/LogonType.csv
- falcon/investigate/macprefix.csv
- falcon/helper/mappings.csv
- falcon/investigate/AsepValue.csv
- falcon/investigate/AsepClass.csv
- falcon/investigate/statusdecimal.csv


Key Syntax Notes
-----------------------------------

- View lookup: `readFile("filename.csv") | head(10)`

- Enrich data: `match(file="filename.csv", field=fieldname, include=[fields], strict=false)`

- CQL uses `match()` for enrichment

- Use `strict=false` to allow non-matching records to pass through

- Use `groupBy()`  for aggregations

- Use `_count` to reference count results from `groupBy()`

- Use `fieldset()` to get the schema of the columns from queries or lookupfiles.
