# RIP

**RIP (Routing Information Protocol)** is one of the oldest routing protocols. It is simple to configure, which makes it a good first dynamic protocol to learn.

## How RIP works

- RIP is a **distance-vector** protocol.
- Its metric is **hop count**: the number of routers a packet passes through.
- A network more than **15 hops** away is **unreachable**. A metric of 16 means "infinity". This limits RIP to small networks.
- Every router sends its **entire routing table** to its neighbours every **30 seconds**.
- Its administrative distance is **120**.

### Example

~~~
PC-A --- R1 --- R2 --- R3 --- PC-C
~~~

R3 tells R2 about the network behind PC-C with a metric of 1. R2 adds 1 and tells R1, which now knows it with a metric of 2. Each router only knows "send it to my neighbour", not the whole path.

## RIPv1 and RIPv2

| | RIPv1 | RIPv2 |
| --- | --- | --- |
| Subnet mask in updates | No (classful) | Yes (classless, supports VLSM) |
| Update sent to | Broadcast 255.255.255.255 | Multicast 224.0.0.9 |
| Authentication | No | Yes |

Always use **RIPv2** today.

## Configuration

~~~
R1(config)# router rip
R1(config-router)# version 2
R1(config-router)# network 192.168.1.0
R1(config-router)# network 10.0.0.0
R1(config-router)# no auto-summary
~~~

- `network` lists the **classful networks** of the interfaces that should run RIP. RIP then advertises those networks and sends updates out of those interfaces.
- `no auto-summary` stops RIP from summarising to classful boundaries, which can break networks that use subnets.

## Verifying RIP

~~~
R1# show ip route rip
R1# show ip protocols
R1# debug ip rip
~~~

A RIP route in the table looks like this:

~~~
R    192.168.3.0/24 [120/2] via 10.0.12.2, 00:00:12, GigabitEthernet0/1
~~~

`[120/2]` means AD 120 and metric 2 (two hops).

## Preventing routing loops

Distance-vector protocols can create loops because routers only trust their neighbours. RIP uses several protections:

- **Split horizon:** a router does not advertise a route back out of the interface it learned it from.
- **Route poisoning:** a failed network is advertised with metric 16 so everyone learns it is gone.
- **Hold-down timers:** after a route fails, the router ignores worse updates for a while.

## Limits of RIP

- Maximum of 15 hops.
- Slow convergence, because it waits for periodic updates.
- Ignores bandwidth. A 2-hop path over slow links beats a 3-hop path over fast links.
- Sends its full table every 30 seconds, which wastes bandwidth.

## Quick recap

- RIP is distance-vector, with hop count as the metric and a limit of 15 hops.
- Use version 2, and add `no auto-summary`.
- Updates go out every 30 seconds and the AD is 120.