# Routing and the routing table

**Routing** is the process of choosing the path a packet takes from its source to its destination. It is the main job of a **router** (a Layer 3 device).

## What a router does with every packet

1. It reads the **destination IP address** in the packet.
2. It looks for the best matching entry in its **routing table**.
3. It sends the packet out of the correct interface to the **next hop**, or straight to the host if the network is directly connected.
4. If nothing matches, the packet is **dropped**.

A router does not know the whole path. It only decides the **next hop**, and each router along the way makes its own decision.

## What is in a routing table?

| Field | Meaning |
| --- | --- |
| Network (prefix) | The destination network, for example `192.168.3.0/24` |
| Next hop | The IP address of the next router on the way |
| Exit interface | The interface the packet leaves through, for example `Gi0/1` |
| Administrative distance (AD) | How trustworthy the source of the route is (lower is better) |
| Metric | The cost of the route within one routing protocol |

## Where do routes come from?

| Source | Code | How it gets there |
| --- | --- | --- |
| Connected | `C` and `L` | Created automatically when an interface has an IP address and is up |
| Static | `S` | Typed in by the administrator |
| Dynamic | `O` (OSPF), `R` (RIP) | Learned from other routers using a routing protocol |

### Default administrative distances

| Source | AD |
| --- | --- |
| Connected | 0 |
| Static | 1 |
| OSPF | 110 |
| RIP | 120 |

If two sources offer a route to the same network, the **lower AD wins**.

## Reading `show ip route`

~~~
Router# show ip route
C    192.168.1.0/24 is directly connected, GigabitEthernet0/0
L    192.168.1.1/32 is directly connected, GigabitEthernet0/0
S    192.168.3.0/24 [1/0] via 10.0.12.2
S*   0.0.0.0/0 [1/0] via 10.0.12.2
~~~

- `C`: the network attached to this interface.
- `L`: the router's own address on that interface.
- `S`: a static route. `[1/0]` means AD 1 and metric 0.
- `S*`: a **default** static route.

## What changes as a packet moves?

At every hop the router builds a **new frame**:

- **IP addresses** stay the same from source to destination (unless NAT is used).
- **MAC addresses** change on every link.
- The **TTL** value in the IP header goes down by 1, and the packet is discarded when it reaches 0. This stops packets from circling forever in a routing loop.

> Open the **Packet Walk** tool and send a packet from PC-A to PC-C. Look at the routing table at every hop.