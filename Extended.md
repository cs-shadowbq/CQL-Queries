# Extended - CrowdStrike NGSIEM

These queries are useful, but may use specific subqueries or helpers specific to CrowdStrike dataset, or NGSIEM.

## Helpers

There are a few helpers in Falcon NGSIEM that go beyond CQL LogScale. 

```f#
readFile(file="aid_master_main.csv")
| $falcon/helper:enrich(field=ProductType)
```

### Enricher fields supported

You can get all of the fields for this helper `$falcon/helper:enrich()` with this query

```f#
readFile(file="falcon/helper/mappings.csv")
| groupBy([Event])
```


| Field | Value Instances|
|---|---|
|AccountStatus|3|
|ActiveDirectoryAuditActionType|7|
|ActiveDirectoryAuthenticationMethod|6|
|ActiveDirectoryDataProtocol|3|
|ActiveDirectoryGroupScope|3|
|AsepClass|26|
|AsepFlags|8|
|AsepValueType|6|
|AuthenticationFailureMsErrorCode|13|
|AuthenticationId|5|
|AzureErrorCode|241|
|CloudErrorCode|8|
|CloudPlatform|3|
|ConnectType|13|
|ConnectionCipher|7|
|ConnectionDirection|4|
|ConnectionExchange|50|
|ConnectionFlags|15|
|ConnectionHash|4|
|ConnectionProtocol|12|
|CpuVendor|4|
|CreateProcessType|6|
|DnsResponseType|3|
|DriverLoadFlags|3|
|DualRequest|2|
|EfiSupported|2|
|EtwProviders|23|
|ExclusionSource|5|
|ExclusionType|2|
|ExitCode|11839|
|FileAttributes|14|
|FileCategory|10|
|FileMode|6|
|FileSubType|13|
|FileWrittenFlags|4|
|HTTPMethod|10|
|HTTPStatus|69|
|HashAlgorithm|17|
|HookId|15|
|IP.country|249|
|IcmpType|11|
|ImageSubsystem|6|
|IntegrityLevel|7|
|IsAndroidAppContainerized|2|
|IsDebugPath|2|
|IsEcho|2|
|IsNorthBridgeSupported|2|
|IsOnNetwork|2|
|IsOnRemovableDisk|2|
|IsSouthBridgeSupported|2|
|IsTransactedFile|2|
|KDCOptions|15|
|KerberosAnomaly|12|
|LanguageId|187|
|LdapSearchQueryClassification|18|
|LdapSearchScope|3|
|LdapSecurityType|4|
|LinuxSensorBackend|2|
|LogonType|11|
|MachOSubType|8|
|MappedFromUserMode|2|
|NamedPipeImpersonationType|5|
|NamedPipeOperationType|3|
|NetworkContainmentState|2|
|NetworkProfile|5|
|NewFileAttributesLinux|21|
|NtlmAvFlags|3|
|ObjectAccessOperationType|7|
|ObjectType|3|
|OciContainerHostConfigReadOnlyRootfs|2|
|OciContainerPhase|5|
|OktaErrorCode|91|
|PolicyRuleSeverity|4|
|PreviousFileAttributesLinux|21|
|PrimaryModule|2|
|ProductType|3|
|Protocol|4|
|ProvisionState|2|
|RebootRequired|2|
|RegOperationType|11|
|RegType|12|
|RemoteAccount|2|
|RequestType|82|
|RpcOpClassification|12|
|RuleAction|3|
|SecurityInformationLinux|3|
|SensorStateBitMap|2|
|ServiceCurrentState|8|
|ServiceType|7|
|ShowWindowFlags|12|
|SignInfoFlagFailedCertCheck|2|
|SignInfoFlagNoEmbeddedCert|2|
|SignInfoFlagNoSignature|2|
|SourceAccountType|3|
|SourceEndpointHostNameResolutionMethod|7|
|SourceEndpointIpReputation|9|
|SourceEndpointNetworkType|5|
|SsoEventSource|4|
|Status|50|
|SubStatus|24|
|TargetAccountType|2|
|TargetServiceAccessClassification|13|
|TcpConnectErrorCode|9|
|ThreadExecutionControlType|11|
|TlsVersion|4|
|TokenType|3|
|UserIsAdmin|2|
|WellKnownTargetFunction|6|
|ZoneIdentifier|5|

### TlsVersion

Simply understand the lookup. If you want to know what is supported for `TlsVersion`

```f#
...
| $falcon/helper:enrich(field=TlsVersion)
...
```

```f#
readFile(file="falcon/helper/mappings.csv")
| Event = "TlsVersion"
```

|Event|Key|KeyValue|Value|
|---|---|---|---|
|TlsVersion|TlsVersion_0|v1.0|0|
|TlsVersion|TlsVersion_1|v1.1|1|
|TlsVersion|TlsVersion_2|v1.2|2|
|...|



### IntegrityLevel 

Show the CLI commands and the Integrity Level which they execute.

```f# 
// Filter for ProcessRollup2 or ImageHash events where the FileName matches the executable Name
(#event_simpleName=/ProcessRollup2/iF OR #event_simpleName=/ImageHash/iF) FileName=/\.exe/iF
| FileName != "*updater.exe"
| FileName != "*svchost.exe"
| FileName != "*CSFalconContainer.exe"
| CommandLine != "/k echo*"
| CommandLine != "*osquery*"

// Enrich data with IntegrityLevel information
| $falcon/helper:enrich(field=IntegrityLevel)
// Group results by ImageFileName and ComputerName, counting unique aid values and collecting IntegrityLevel and CommandLine
| groupBy([ImageFileName, ComputerName], function=[count(CommandLine, distinct=true, as=DistinctExecutions), collect([LocalIP, aip, IntegrityLevel, UserName, CommandLine])], limit=20000)
// Sort results by aidCount in descending order
| sort(DistinctExecutions, order=desc)
```

### groupby() with subqueries{} enriched by `falcon/helper:enrich(xx)`

Using the `aid_master_main.csv` lookup, and using the helper to swap the decimal of `ProductType` to a string.

```f#
#repo=base_sensor 
| event_platform="Win" 
| ComputerName="*"
| #event_simpleName=ProcessRollup2 OR #event_simpleName=SensorHeartbeat OR #event_simpleName=ResourceUtilization 
| groupby([cid, aid], function=([
  { #event_simpleName=ResourceUtilization | count(as=TotalRU)},
  { #event_simpleName=ProcessRollup2 | count(as=TotalPR2)},
  { #event_simpleName=SensorHeartbeat | count(as=TotalSH)}, max(as=max,@timestamp)
]), limit=max)
| Last_Seen:=formatTime(format="%F %T", field="max")
// Lookup File
| aid=~match(file="aid_master_main.csv", column=[aid], include=[ComputerName, FirstSeen, Version,ProductType], strict=false)
// Filter only those with ComputerName, strict=true would be similar 
| ComputerName="*"
// Builtin Enricher "$falcon/helper:enrich()"
| $falcon/helper:enrich(field=ProductType)
| First_Seen:=formatTime(format="%F %T", field="FirstSeen")
| drop(fields=[cid, max, FirstSeen])
```