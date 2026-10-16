# Static routes and the default route

A **static route** is a route that an administrator types in by hand. It never changes unless someone changes it.

## The command

~~~
Router(config)# ip route <network> <mask> <next-hop>
~~~

## Example network

~~~
PC-A --- R1 ---(10.0.12.0/30)--- R2 ---(10.0.23.0/30)--- R3 --- PC-C
192.168.1.0/24                                       192.168.3.0/24
~~~

Addresses on the links: R1 = 10.0.12.1, R2 = 10.0.12.2 and 10.0.23.1, R3 = 10.0.23.2.

**R1 must reach 192.168.3.0/24 through R2:**

~~~
R1(config)# ip route 192.168.3.0 255.255.255.0 10.0.12.2
~~~

R1 does not need to know the network behind R3 in detail. It only needs to know that the next hop for that network is R2.

## Routes are needed in both directions

A ping works in two steps: the **echo request** goes from PC-A to PC-C, and the **echo reply** must come back. So R3 also needs a route to `192.168.1.0/24`:

~~~
R3(config)# ip route 192.168.1.0 255.255.255.0 10.0.23.1
~~~

If only one side has a route, the request arrives but the reply never returns, and the ping fails. This is the most common static routing mistake.

## The default route

A **default route** matches any destination that has no better match. Its network and mask are `0.0.0.0 0.0.0.0` (written `0.0.0.0/0`).

~~~
R1(config)# ip route 0.0.0.0 0.0.0.0 10.0.12.2
~~~

Typical uses:

- Sending Internet traffic toward the ISP.
- Connecting a small branch office to its head office.

On a Cisco router the routing table then shows **Gateway of last resort is set**.

## Checking your work

~~~
Router# show ip route
Router# ping 192.168.3.10
Router# traceroute 192.168.3.10
~~~

On a Windows PC the traceroute command is `tracert`. It lists every router the packet passes, which makes it easy to see where a path stops.

## Backup routes: floating static routes

If you give a static route a **higher administrative distance**, for example 150, it stays hidden while a better route exists. It is used only if the main route disappears.

~~~
R1(config)# ip route 192.168.3.0 255.255.255.0 10.0.13.2 150
~~~

## Advantages and disadvantages

| Advantages | Disadvantages |
| --- | --- |
| Simple and easy to understand | Hard to manage in large networks |
| Uses almost no CPU or bandwidth | Does not adapt when a link fails |
| Predictable and secure | Mistakes are easy to make by hand |

## Common mistakes

- Missing the **return route**.
- Typing the wrong next-hop address (it must be on a directly connected network).
- Using the wrong mask, for example `255.255.255.0` instead of `255.255.0.0`.

> Practise in the **Router Lab**: configure R1, R2 and R3, then press **Check my work**.