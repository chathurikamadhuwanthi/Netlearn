# How switches work

A **switch** connects devices inside one network and forwards **frames** only to the port where the destination device is. This is what makes a switch much more efficient than the old **hub**, which simply repeated every signal out of every port.

## Hub vs switch

| | Hub (Layer 1) | Switch (Layer 2) |
| --- | --- | --- |
| Forwarding | Repeats data to every port | Sends frames to the correct port |
| Collisions | All ports share one collision domain | Every port is its own collision domain |
| Efficiency | Low | High |
| Today | Obsolete | Standard |

## The MAC address table

A switch keeps a **MAC address table** (also called the CAM table) that maps each MAC address to a port. It builds the table automatically with these rules:

1. **Learn:** when a frame arrives, the switch reads the **source MAC address** and records it with the incoming port.
2. **Forward:** it looks up the **destination MAC address**. If the address is in the table, the frame goes out of that one port only.
3. **Flood:** if the destination is **unknown**, the frame is sent out of every port except the one it arrived on.
4. **Filter:** if the destination is on the same port the frame came from, the switch drops it.
5. **Age:** entries that are not refreshed are removed after a timeout (300 seconds by default on Cisco switches).

Broadcast frames (destination `FFFF.FFFF.FFFF`) are always flooded.

## Example

Three PCs connect to a switch: A on port 1, B on port 2 and C on port 3. The table starts empty.

| Event | What the switch does | Table afterwards |
| --- | --- | --- |
| A sends a frame to B | Learns A on port 1. B is unknown, so it floods ports 2 and 3 | A → port 1 |
| B replies to A | Learns B on port 2. A is known, so it sends only to port 1 | A → 1, B → 2 |
| A sends to B again | Both are known, so it sends only to port 2 | No change |

PC C never sees the traffic between A and B after the first frame.

## Collision and broadcast domains

- Each switch port is a separate **collision domain**, so collisions are no longer a problem on modern switched networks.
- All ports of a switch (in the same VLAN) belong to **one broadcast domain**. A broadcast from one device reaches every other device. **Routers** and **VLANs** are what split broadcast domains.

## Useful commands

~~~
Switch# show mac address-table
Switch# show mac address-table dynamic
Switch# clear mac address-table dynamic
~~~

## Loops and Spanning Tree

Networks often have extra cables for backup. Without protection, a loop would make frames circle forever and flood the network (a **broadcast storm**). The **Spanning Tree Protocol (STP)** blocks some ports automatically so that there is only one active path, and it unblocks them if a link fails.

## Quick recap

- A switch learns source MAC addresses and forwards by destination MAC address.
- Unknown destinations and broadcasts are flooded.
- Every port is a collision domain, but all ports in a VLAN share one broadcast domain.
- STP prevents loops.