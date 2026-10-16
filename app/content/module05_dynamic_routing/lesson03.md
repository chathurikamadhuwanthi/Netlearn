# OSPF

**OSPF (Open Shortest Path First)** is the most widely used IGP in enterprise networks. It is an open standard, so routers from different vendors can use it together.

## How OSPF is different

- OSPF is a **link-state** protocol. Every router learns about **all the links** in its area and builds the same **map** of the network.
- Each router then runs the **SPF algorithm** (Dijkstra's shortest path algorithm) on that map to calculate the best path to every network.
- OSPF only sends updates when something **changes**, so it converges quickly and uses little bandwidth.
- Its administrative distance is **110**.

## The main steps

1. **Neighbour discovery:** routers send **Hello packets** to find OSPF routers on the same link.
2. **Adjacency:** neighbours that agree on key settings form an adjacency and exchange information.
3. **LSAs and the LSDB:** routers share **Link-State Advertisements (LSAs)**. The collection of LSAs is the **link-state database (LSDB)**. All routers in an area end up with an identical LSDB.
4. **SPF calculation:** each router calculates the shortest path tree from itself to every network.
5. **Routing table:** the best paths are placed in the routing table.

### Hello and dead timers

On broadcast links, Hello packets are sent every **10 seconds** and a neighbour is declared down after **40 seconds** (the dead interval) without hearing from it. Both timers must match for routers to become neighbours.

### Neighbour states

A healthy adjacency passes through states such as Down, Init, 2-Way, ExStart, Exchange and Loading, and ends in **Full**. If a neighbour is stuck in another state, something is wrong.

## OSPF cost

OSPF's metric is **cost**, and it depends on link bandwidth:

~~~
Cost = reference bandwidth / interface bandwidth
Default reference bandwidth = 100 Mbps
~~~

| Link | Cost |
| --- | --- |
| Ethernet 10 Mbps | 10 |
| Fast Ethernet 100 Mbps | 1 |
| Gigabit Ethernet 1 Gbps | 1 (see note below) |

With the default reference bandwidth, Fast Ethernet and Gigabit both get cost 1, so OSPF cannot tell them apart. On modern networks the reference bandwidth is raised with `auto-cost reference-bandwidth`. The total cost of a path is the **sum** of the costs of the outgoing interfaces.

## Areas

OSPF can divide a large network into **areas** to keep the LSDB small. **Area 0** is the **backbone**, and all other areas must connect to it. For a small network, putting everything in area 0 is fine.

## Router ID

Every OSPF router has a unique **router ID** that looks like an IPv4 address. It is chosen from the manually configured ID, otherwise from the highest loopback IP address, otherwise from the highest active interface IP address.

## Configuration

~~~
R1(config)# router ospf 1
R1(config-router)# router-id 1.1.1.1
R1(config-router)# network 192.168.1.0 0.0.0.255 area 0
R1(config-router)# network 10.0.12.0 0.0.0.3 area 0
~~~

- `1` is the **process ID**. It only has meaning on this router.
- The `network` command uses a **wildcard mask**, which is the inverse of a subnet mask: `/24` becomes `0.0.0.255` and `/30` becomes `0.0.0.3`. Any interface whose IP address falls inside the range starts running OSPF.

## Verifying OSPF

~~~
R1# show ip ospf neighbor
R1# show ip route ospf
R1# show ip ospf interface brief
~~~

An OSPF route looks like this:

~~~
O    192.168.3.0/24 [110/3] via 10.0.12.2, 00:05:21, GigabitEthernet0/1
~~~

`[110/3]` means AD 110 and cost 3.

## Multi-access networks: DR and BDR

On a shared Ethernet segment with many routers, OSPF elects a **Designated Router (DR)** and a **Backup DR (BDR)**. The other routers exchange information only with these two, which prevents a huge number of adjacencies.

## RIP vs OSPF

| | RIP | OSPF |
| --- | --- | --- |
| Type | Distance-vector | Link-state |
| Metric | Hop count | Cost (bandwidth) |
| Convergence | Slow | Fast |
| Network size | Small (15 hops) | Large |
| AD | 120 | 110 |

## Quick recap

- OSPF builds a full map (the LSDB) and calculates paths with Dijkstra's SPF algorithm.
- Hello packets discover neighbours, and routers should reach the Full state.
- Cost is based on bandwidth, and the AD is 110.
- Area 0 is the backbone.