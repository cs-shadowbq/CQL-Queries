parseJson()

| fname:= some.deep.field.fname
| parseTimestamp("dd/MM/yyyy hh:mm:ss a", field=datetime,timezone="UTC")

// enrichment
| case {
    // Apply when the src_ip is a non-RFC1918 IP address. 
    !cidr(src_ip, subnet=["224.0.0.0/4", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "169.254.0.0/16", "0.0.0.0/32"])
      | ipLocation(src_ip)
      | ioc:lookup(["src_ip"], type="ip_address") ;
    * ;
  }
| case {
    // Apply when the dst_ip is a non-RFC1918 IP address. 
    !cidr(dst_ip, subnet=["224.0.0.0/4", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "169.254.0.0/16", "0.0.0.0/32"])
      | ipLocation(dst_ip)
      | ioc:lookup(["dst_ip"], type="ip_address") ;
    * ;
  }