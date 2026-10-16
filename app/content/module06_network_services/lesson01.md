# DHCP

Every device needs an **IP address**, a **subnet mask**, a **default gateway** and a **DNS server** before it can use a network. Typing these on every device would be slow and error-prone. **DHCP (Dynamic Host Configuration Protocol)** hands them out automatically.

## What DHCP provides

- IP address
- Subnet mask
- Default gateway
- DNS server address(es)
- **Lease time**: how long the device may keep the address

At home, your Wi-Fi router is the DHCP server. In companies it is usually a router or a dedicated server.

## The DORA process

DHCP uses **UDP**. The server listens on port **67** and the client uses port **68**.

| Step | Message | Description |
| --- | --- | --- |
| 1 | **D**iscover | The client has no address, so it **broadcasts** "Is there a DHCP server?" (source 0.0.0.0, destination 255.255.255.255) |
| 2 | **O**ffer | A server replies with an address it can lend |
| 3 | **R**equest | The client broadcasts that it accepts that offer (so other servers know to withdraw theirs) |
| 4 | **A**cknowledge | The server confirms the lease and sends the settings |

## Leases

An address is **leased**, not given forever. Around **half-way** through the lease the client asks the server to renew it. If the device leaves the network, the lease expires and the address returns to the pool, so addresses are not wasted.

## DHCP relay

Broadcasts do not cross routers, so a DHCP server on one subnet cannot hear a client on another subnet. A **DHCP relay** agent on the router receives the broadcast and forwards it to the server as a normal packet.

~~~
Router(config)# interface gigabitEthernet 0/0
Router(config-if)# ip helper-address 192.168.100.10
~~~

Here `192.168.100.10` is the DHCP server's address.

## Configuring a DHCP server on a Cisco router

~~~
Router(config)# ip dhcp excluded-address 192.168.10.1 192.168.10.20
Router(config)# ip dhcp pool SALES
Router(dhcp-config)# network 192.168.10.0 255.255.255.0
Router(dhcp-config)# default-router 192.168.10.1
Router(dhcp-config)# dns-server 8.8.8.8
~~~

- `excluded-address` keeps a range free for servers, printers and the router itself.
- `network` is the pool of addresses to hand out.

## Verifying and troubleshooting

~~~
Router# show ip dhcp binding
Router# show ip dhcp pool
~~~

On a Windows PC:

~~~
ipconfig /all
ipconfig /release
ipconfig /renew
~~~

| Problem | Likely cause |
| --- | --- |
| PC shows 169.254.x.x | It could not reach any DHCP server (cable, VLAN or relay problem) |
| Two devices with the same address | A static address is inside the DHCP pool and was not excluded |
| Wrong gateway or DNS | The pool is configured incorrectly |

## Quick recap

- DHCP assigns an address, mask, gateway, DNS and a lease automatically.
- DORA: Discover, Offer, Request, Acknowledge.
- Use a relay (`ip helper-address`) when the server is on another subnet.
- A 169.254.x.x address means DHCP failed.