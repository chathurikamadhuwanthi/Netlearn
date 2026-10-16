# NAT and PAT

There are not enough public IPv4 addresses for every device in the world. Homes and companies therefore use **private** addresses inside, and **NAT (Network Address Translation)** changes them into **public** addresses when traffic goes to the Internet.

## Terms

| Term | Meaning |
| --- | --- |
| Inside local | The private address of an inside device (for example 192.168.1.10) |
| Inside global | The public address that represents that device on the Internet |
| Outside global | The public address of the destination (for example a web server) |

## Types of NAT

| Type | How it works | Use |
| --- | --- | --- |
| **Static NAT** | One private address is always mapped to one fixed public address | Servers that must be reachable from outside |
| **Dynamic NAT** | A private address is mapped to any free address from a pool of public addresses | Rare today |
| **PAT (NAT overload)** | Many private addresses share **one** public address, using different port numbers | Homes and most companies |

## How PAT works

With PAT the router keeps a **translation table** that records which inside device and port belongs to which public port.

| Inside local | Inside global | Destination |
| --- | --- | --- |
| 192.168.1.10:51000 | 203.0.113.1:62001 | 198.51.100.5:443 |
| 192.168.1.11:51000 | 203.0.113.1:62002 | 198.51.100.5:443 |

Both PCs use the same public address. The router tells their replies apart by the **public port number** and sends each reply to the right inside device.

## Configuring PAT on a Cisco router

~~~
Router(config)# access-list 1 permit 192.168.1.0 0.0.0.255

Router(config)# interface gigabitEthernet 0/0
Router(config-if)# ip nat inside

Router(config)# interface gigabitEthernet 0/1
Router(config-if)# ip nat outside

Router(config)# ip nat inside source list 1 interface gigabitEthernet 0/1 overload
~~~

- `ip nat inside` and `ip nat outside` mark which interface faces the private network and which faces the Internet.
- The access list says **which** private addresses may be translated.
- The keyword `overload` is what turns NAT into **PAT**.

### Static NAT example

~~~
Router(config)# ip nat inside source static 192.168.1.50 203.0.113.50
~~~

## Verifying NAT

~~~
Router# show ip nat translations
Router# show ip nat statistics
Router# clear ip nat translation *
~~~

## Benefits and drawbacks

| Benefits | Drawbacks |
| --- | --- |
| Saves public IPv4 addresses | Breaks the end-to-end addressing model |
| Hides the inside addressing scheme | Some applications and protocols need extra support |
| Easy to set up on a home or office router | Adds delay and makes troubleshooting harder |

NAT is **not a firewall**. It may hide inside addresses, but real protection needs firewall rules.

## NAT and IPv6

**IPv6** has enough addresses for every device to have a public address, so NAT is not needed for address saving there. IPv4 and NAT are still everywhere, so you need to understand both.

## Quick recap

- NAT translates private addresses into public addresses.
- Static NAT is one-to-one, dynamic NAT uses a pool, and PAT shares one public address using ports.
- `overload` enables PAT on Cisco routers.
- Mark interfaces with `ip nat inside` and `ip nat outside`.