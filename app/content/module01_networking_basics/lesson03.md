# IP addresses, MAC addresses and ports

To deliver data, a network needs to answer three questions: **which network device** should receive the frame, **which computer** is the final destination, and **which program** on that computer should get the data. MAC addresses, IP addresses and port numbers answer these three questions.

## MAC address (Layer 2)

- A **physical address** burned into a network card (NIC) by the manufacturer.
- 48 bits long, written as 12 hexadecimal digits, for example `00:1A:2B:3C:4D:5E`.
- The first half identifies the manufacturer and the second half identifies the card.
- Used only **inside one network**. Switches use MAC addresses to forward frames.

## IP address (Layer 3)

- A **logical address** given to a device. It can change when the device moves to another network.
- An IPv4 address is 32 bits, written as four decimal numbers, for example `192.168.1.10`.
- It has a **network part** and a **host part**. The **subnet mask** shows where one ends and the other begins.
- Routers use the IP address to move packets between networks.

### Default gateway

A device sends traffic for other networks to its **default gateway**, which is the router on its own network. At home this is your Wi-Fi router.

### Private and public addresses

| Range | Prefix | Used for |
| --- | --- | --- |
| 10.0.0.0 – 10.255.255.255 | 10.0.0.0/8 | Large private networks |
| 172.16.0.0 – 172.31.255.255 | 172.16.0.0/12 | Medium private networks |
| 192.168.0.0 – 192.168.255.255 | 192.168.0.0/16 | Homes and small offices |

These **private** addresses are not routed on the Internet. Everything else is **public**. Two special cases are worth remembering: `127.0.0.1` (loopback, "this computer") and `169.254.x.x` (a self-assigned address when no DHCP server answers).

## Port numbers (Layer 4)

A computer runs many network programs at once. A **port number** (0 to 65535) tells the computer which program should receive the data.

| Port | Service |
| --- | --- |
| 22 | SSH |
| 25 | SMTP (sending email) |
| 53 | DNS |
| 67 / 68 | DHCP |
| 80 | HTTP |
| 443 | HTTPS |

An IP address plus a port, such as `203.0.113.10:443`, identifies one specific service on one specific device.

## ARP: connecting IP and MAC

A device knows the IP address of its target, but a frame needs a MAC address. **ARP (Address Resolution Protocol)** asks the local network "who has this IP address?" and the owner replies with its MAC address.

## Putting it all together

Your PC (`192.168.1.10`) opens `https://example.com`, whose server is `203.0.113.10`:

| Step | Addresses used | What changes |
| --- | --- | --- |
| PC to router | IP: 192.168.1.10 → 203.0.113.10, port 443, MAC: PC → router | Frame is addressed to the **router's MAC** |
| Router to next router | Same IPs and port | New frame with **new MAC addresses** |
| Last router to server | Same IPs and port | Frame addressed to the **server's MAC** |

The **IP addresses and port stay the same** from end to end (unless NAT is used), while the **MAC addresses change at every hop**.

## Quick recap

| | MAC address | IP address | Port number |
| --- | --- | --- | --- |
| Layer | 2 | 3 | 4 |
| Identifies | A network card | A device on a network | A program or service |
| Scope | One network | End to end | One device |
| Used by | Switches | Routers | The operating system |