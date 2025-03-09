name: webapp
tests:
- 'Feb 15 12:17:41 dnsmasq[633]: /etc/pihole/custom.list api.localtest.test is 192.168.1.201'
- 'Feb 12 17:45:41 dnsmasq[633]: Apple iCloud Private Relay domain mask.icloud.com
  is NXDOMAIN'
- 'Feb 12 18:11:32 dnsmasq[633]: gravity blocked events.statsigapi.net is 0.0.0.0'
- 'Feb 12 17:45:10 dnsmasq[633]: read /etc/hosts - 8 names'
- 'Feb 12 17:45:10 dnsmasq[633]: read /etc/pihole/custom.list - 6 names'
- 'Feb 12 17:45:10 dnsmasq[633]: read /etc/pihole/local.list - 0 names'
- 'Feb 12 18:00:55 dnsmasq[633]: Pi-hole hostname pi.hole is 192.168.1.148'
- 'Feb 12 17:36:04 dnsmasq[633]: special domain mask.icloud.com is NXDOMAIN'
- 'Feb 12 17:34:47 dnsmasq[633]: reply gateway.fe2.apple-dns.net is 17.248.213.70'
- 'Feb 11 18:46:24 dnsmasq[633]: cached time.g.aaplimg.com is 17.253.14.251'
- 'Feb 11 18:46:24 dnsmasq[633]: gravity blocked telemetry-in.battle.net is NODATA'
- 'Feb 11 18:46:07 dnsmasq[633]: forwarded pihole.it-runs.de to 208.67.220.220'
- 'Feb 11 18:43:49 dnsmasq[633]: query[A] app.warp.dev from 192.168.1.174'
fieldsToBeRemovedBeforeParsing: []
$schema: https://schemas.humio.com/parser/v0.2.0
script: |-
/*
			parser: webapp
			version 0.0.1
			app: webapp
			app-version: 1.0
      Author: shadowbq
      Date: 05/01/2001

      Description:
      ------------
      To use this parser, blah..
			Basic tagfield without extra parsing

      Collect the logs via HumioLogCollector
      
			sources:
        var_log:
          type: file
          include: /var/log/webapp/webapp.log
          sink: logscale

      To work properly, add the user to the pihole group via:
      sudo usermod -a -G www-user humio-log-collector

      Changelog:
      ----------

      v0.0.1: - Inital parser

			The CrowdStrike Parsing Standard (CPS) 1.0 builds upon the Elastic Common Schema (ECS) version 8. CPS-compliant parsers use tags for additional fields like #ecs.version, #event.dataset, #event.kind, #event.module, and #observer.type

   */

  //remove carriage returns and new lines this causes issues parsing JSON
  replace(regex="\n", replacement="")|
  replace(regex="\r", replacement="")|
  
  Parser.version := "0.0.1"
  | Vendor := "webapp"
  | ecs.version := "8.11.0"
  | event.module := "websecurity"
  | Cps.version := "1.0.0"
  | event.kind := "event"

  case {

    // query logs
    log_type := "query" | regex("^(?<timestamp>\\w+\\s+\\d+\\s+\\d+:\\d+:\\d+)\\s+dnsmasq\\[(?<process_id>\\d+)\\]:\\s+(?<type>(?:gravity blocked|cached|config|forwarded|reply|special|query\\[(?<query_type>\\w+)\\]))\\s+(?<domain_name>[^\\s]+)(?:\\s+is\\s+|\\s+from\\s+|\\s+to\\s+)(?<dns_response>[^\\s]+(?:\\s+[^\\s]+)?)");

    // domain is
    log_type := "special" | regex("^(?<timestamp>\\w+\\s+\\d+\\s+\\d+:\\d+:\\d+)\\s+dnsmasq\\[(?<process_id>\\d+)\\]:\\s+(?<special_name>.*?)\\sdomain\\s(?<domain>[^\\s]+)\\sis\\s(?<special_response>.+)$");


    // other
    log_type := "other" | regex("^(?<timestamp>\\w+\\s+\\d+\\s+\\d+:\\d+:\\d+)\\s+dnsmasq\\[(?<process_id>\\d+)\\]:\\s+Pi-hole\\s+hostname\\s+(?<hostname>.+?)\\s+is\\s+(?<ip_address>\\d+\\.\\d+\\.\\d+\\.\\d+)$");

  }
tagFields:
- log_type
- Cps.version
- Vendor
- ecs.version
- event.kind
- event.module
