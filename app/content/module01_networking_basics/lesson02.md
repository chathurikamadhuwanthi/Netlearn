# The OSI and TCP/IP models

Sending an email or opening a web page involves many separate jobs: producing the data, breaking it into pieces, choosing a path, addressing it and converting it into signals. To keep this manageable, networking is split into **layers**. Each layer has one clear job and talks only to the layers directly above and below it.

Layering has real benefits. Engineers can fix or improve one layer without changing the others, products from different companies work together, and troubleshooting becomes a step-by-step process.

## The OSI model (7 layers)

| # | Layer | Main job | PDU | Examples |
| --- | --- | --- | --- | --- |
| 7 | Application | Network services used by applications | Data | HTTP, DNS, SMTP |
| 6 | Presentation | Data format, encryption, compression | Data | TLS, JPEG |
| 5 | Session | Starts, keeps and ends conversations | Data | Session setup |
| 4 | Transport | Splits data, ports, reliability | Segment | TCP, UDP |
| 3 | Network | Logical addressing and routing | Packet | IP, routers |
| 2 | Data Link | Delivery inside one network, MAC addresses | Frame | Ethernet, switches |
| 1 | Physical | Bits as electrical, light or radio signals | Bits | Cables, Wi-Fi |

**PDU** stands for Protocol Data Unit. It is the name given to the data at each layer.

Memory trick, from layer 7 down to layer 1: **A**ll **P**eople **S**eem **T**o **N**eed **D**ata **P**rocessing.

## The TCP/IP model (4 layers)

The OSI model is mainly used for learning. The Internet actually runs on the simpler TCP/IP model.

| TCP/IP layer | Matches OSI layers | Examples |
| --- | --- | --- |
| Application | 7, 6, 5 | HTTP, HTTPS, DNS, DHCP |
| Transport | 4 | TCP, UDP |
| Internet | 3 | IP, ICMP |
| Network Access | 2, 1 | Ethernet, Wi-Fi |

## Encapsulation: how data is wrapped

When you send data, each layer adds its own **header** (and the Data Link layer also adds a trailer). This is called **encapsulation**.

~~~
Application data
  + TCP header              = Segment  (Transport)
  + IP header               = Packet   (Network)
  + Ethernet header/trailer = Frame    (Data Link)
  -> sent as Bits           (Physical)
~~~

The receiving device does the reverse. It removes the headers one by one from the bottom up. This is **de-encapsulation**.

## Example: opening a web page

1. **Application:** your browser creates an HTTP request.
2. **Transport:** TCP adds the destination port (443 for HTTPS) and a sequence number.
3. **Network:** IP adds your IP address and the server's IP address.
4. **Data Link:** Ethernet adds the MAC address of your next device (usually the router).
5. **Physical:** the frame is sent as signals over the cable or Wi-Fi.

Each router on the way reads only the Layer 3 information to decide where to send the packet next. Switches read only Layer 2.

## Using layers to troubleshoot

A reliable method is to check from the bottom up:

1. **Physical:** is the cable plugged in, is Wi-Fi connected?
2. **Data Link:** is the link up, is the switch port working?
3. **Network:** does the device have a correct IP address and gateway, and can it ping?
4. **Transport and Application:** is the service running and is its port allowed?

## Quick recap

- OSI has 7 layers and TCP/IP has 4. Both describe the same process.
- Data is encapsulated on the way down and de-encapsulated on the way up.
- PDU names: Data, Segment, Packet, Frame, Bits.
- Routers work at Layer 3 and switches work at Layer 2.
