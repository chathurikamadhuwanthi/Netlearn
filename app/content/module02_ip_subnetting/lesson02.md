# Subnet masks and CIDR

Every IP address has two parts: the **network part** (which network the device is in) and the **host part** (which device inside that network). The **subnet mask** tells us where the split is.

## How a mask works

In the mask, every `1` marks a **network bit** and every `0` marks a **host bit**. The ones always come first, then the zeros.

~~~
IP address : 192.168.1.10   = 11000000.10101000.00000001.00001010
Mask       : 255.255.255.0  = 11111111.11111111.11111111.00000000
                              |------- network (24) -------|host(8)|
~~~

## CIDR notation

Instead of writing the whole mask, we count the ones and write `/` followed by that number. This is the **prefix length**. For example, `255.255.255.0` is `/24`.

## Finding the network address with AND

The network address is found by a bitwise **AND** between the IP address and the mask (1 AND 1 = 1, everything else = 0).

For `192.168.1.130/26` only the last octet matters, because the first three octets of the mask are all ones:

~~~
130 = 10000010
192 = 11000000   (mask octet)
AND = 10000000 = 128
~~~

So the network address is `192.168.1.128`.

## Common prefixes

| Prefix | Mask | Host bits | Usable hosts | Block size |
| --- | --- | --- | --- | --- |
| /24 | 255.255.255.0 | 8 | 254 | 256 |
| /25 | 255.255.255.128 | 7 | 126 | 128 |
| /26 | 255.255.255.192 | 6 | 62 | 64 |
| /27 | 255.255.255.224 | 5 | 30 | 32 |
| /28 | 255.255.255.240 | 4 | 14 | 16 |
| /29 | 255.255.255.248 | 3 | 6 | 8 |
| /30 | 255.255.255.252 | 2 | 2 | 4 |

## How many hosts fit?

~~~
Usable hosts = 2^(host bits) - 2
~~~

The **minus 2** removes two addresses that cannot be given to devices:

- the **network address** (all host bits 0), which names the network itself
- the **broadcast address** (all host bits 1), which reaches every device in the network

Example: /26 has 6 host bits, so 2^6 = 64 and 64 − 2 = **62 usable hosts**.

## The block size method

This is the fastest way to work by hand.

**Block size = 256 − the interesting octet of the mask**

Example: `192.168.1.130 /26`

1. The mask is `255.255.255.192`, so block size = 256 − 192 = **64**.
2. Subnets start at 0, 64, **128**, 192.
3. 130 falls in the block that starts at 128.
4. **Network** = 192.168.1.128
5. **Broadcast** = one below the next network = 192.168.1.191
6. **Usable range** = 192.168.1.129 to 192.168.1.190

## Special cases

- **/31** is used on point-to-point links between two routers (2 addresses, no broadcast).
- **/32** is a single host, for example a router loopback address.

## Common mistakes

- Forgetting to subtract 2 from the number of hosts.
- Using the block size on the wrong octet. Always find the octet where the mask is not 0 or 255.
- Confusing the broadcast address with the last address of the **next** block.

> Check your answers with the **Subnet Calculator** tool.