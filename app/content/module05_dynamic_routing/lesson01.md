# Static vs dynamic routing

In the last module you typed static routes by hand. That works for small networks, but imagine 50 routers: every new network would need changes on many routers, and a failed link would stay broken until someone fixes it. **Dynamic routing** solves this.

## What is dynamic routing?

With **dynamic routing**, routers run a **routing protocol** to talk to each other. They share what they know, work out the best paths and update the routing table automatically.

Almost every routing protocol follows the same steps:

1. **Find neighbours:** routers discover the routers directly connected to them.
2. **Exchange information:** they share the networks they know about.
3. **Calculate the best path:** each router picks the best route to every network using a **metric**.
4. **React to changes:** when a link fails or a new network appears, they update their tables. The time this takes is called **convergence**.

## Static vs dynamic

| | Static routing | Dynamic routing |
| --- | --- | --- |
| Set up by | Administrator, by hand | Protocol, automatically |
| Link failure | No reaction | Finds another path |
| Best for | Small or simple networks, default routes | Medium and large networks |
| CPU and bandwidth | Almost none | Some, for protocol messages |
| Mistakes | Easy to make as the network grows | Fewer, but protocol knowledge is needed |

In real networks both are used together, for example a static default route towards the Internet and a dynamic protocol inside the company.

## Types of routing protocols

### By where they are used

- **IGP (Interior Gateway Protocol):** used **inside** one organisation. Examples: RIP, OSPF, EIGRP.
- **EGP (Exterior Gateway Protocol):** used **between** organisations on the Internet. The example is **BGP**.

### By how they work

- **Distance-vector** protocols (such as RIP) share their routing table with neighbours and only know the way "through" those neighbours. They are simple but slow to react.
- **Link-state** protocols (such as OSPF) share the state of every link, so every router builds a **complete map** and calculates the best path itself. They are faster and scale better.

## Metrics

A **metric** is the value a protocol uses to compare routes. A lower metric is better.

| Protocol | Metric |
| --- | --- |
| RIP | Hop count (number of routers on the way) |
| OSPF | Cost, based on link bandwidth |
| EIGRP | A combination of bandwidth and delay (by default) |

## Administrative distance again

When two **different** sources offer a route to the same network, the router trusts the one with the lower **AD**: static (1) beats OSPF (110), which beats RIP (120). The metric is only compared between routes learned from the **same** protocol.

## Quick recap

- Dynamic routing lets routers learn routes and adapt to changes without human help.
- IGPs work inside an organisation and EGPs work between organisations.
- Distance-vector protocols share routes. Link-state protocols share link information and build a map.
- The metric compares routes within one protocol. AD compares different sources.