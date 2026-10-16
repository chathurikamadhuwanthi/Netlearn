# DNS

People remember names like `example.com`, while computers use IP addresses. **DNS (Domain Name System)** translates names into IP addresses. Think of it as the phone book of the Internet.

## The domain name hierarchy

A domain name is read from right to left:

~~~
www.example.com.
 |     |     |  |
 |     |     |  +-- root (usually hidden)
 |     |     +----- top-level domain (TLD): .com
 |     +----------- second-level domain: example
 +----------------- subdomain / host: www
~~~

A complete name such as `www.example.com` is called a **fully qualified domain name (FQDN)**.

## How a name is resolved

When you type `www.example.com` in a browser:

1. The browser checks its **own cache**, then the operating system checks its cache and the `hosts` file.
2. If the name is not found, the device asks its configured **recursive resolver** (usually given by DHCP, for example your ISP's server or a public one such as 8.8.8.8).
3. The resolver asks a **root server**, which points to the **.com TLD servers**.
4. A TLD server points to the **authoritative server** for `example.com`.
5. The authoritative server returns the IP address.
6. The resolver gives the answer to your device and **caches** it for the length of its **TTL** (time to live).

Caching makes most lookups fast, because the resolver often already knows the answer.

## DNS records

| Record | Purpose | Example |
| --- | --- | --- |
| A | Name → IPv4 address | www.example.com → 203.0.113.10 |
| AAAA | Name → IPv6 address | www.example.com → 2001:db8::10 |
| CNAME | Alias to another name | blog.example.com → www.example.com |
| MX | Mail servers for the domain | example.com → mail.example.com |
| NS | The domain's name servers | example.com → ns1.example.com |
| PTR | IP address → name (reverse lookup) | 203.0.113.10 → www.example.com |
| TXT | Free text, often used for verification | SPF and domain checks |

## Ports and protocol

DNS normally uses **UDP port 53**. It switches to **TCP port 53** for large answers and for zone transfers between DNS servers.

## Tools

~~~
nslookup www.example.com
nslookup -type=MX example.com
ipconfig /displaydns
ipconfig /flushdns
~~~

On Linux and macOS the `dig` command gives more detail.

## Troubleshooting with DNS in mind

A very common situation:

- `ping 8.8.8.8` **works**, but `ping www.example.com` **fails**.

That means the network path is fine, but **name resolution** is not working. Check:

1. Does the device have a DNS server address? (`ipconfig /all`)
2. Is that DNS server reachable?
3. Does `nslookup` return an answer for the name?
4. Is a stale record cached? Try `ipconfig /flushdns`.

## Quick recap

- DNS translates names into IP addresses.
- The resolver walks root → TLD → authoritative server, then caches the answer for the TTL.
- A records map names to IPv4 addresses, and MX records point to mail servers.
- DNS uses port 53.