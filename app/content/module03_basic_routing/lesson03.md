# Longest Prefix Match (LPM)

A destination address can match **more than one** route in the routing table. The router then chooses the **most specific** one, which is the route with the **longest prefix length**. This rule is called **Longest Prefix Match**.

## Example

Destination: `10.1.2.50`

| Network | Does it match? | Prefix |
| --- | --- | --- |
| 10.0.0.0/8 | Yes | /8 |
| 10.1.0.0/16 | Yes | /16 |
| 10.1.2.0/24 | Yes | /24 |
| 172.16.0.0/16 | No | |
| 0.0.0.0/0 | Yes | /0 |

Four routes match. The longest prefix is /24, so the router uses `10.1.2.0/24`.

## How does a router check for a match?

It compares only the **network bits** of each route with the same bits of the destination.

For `10.1.0.0/16` the first 16 bits (`10.1`) are compared:

~~~
Destination 10.1.2.50  ->  10.1.  (first 16 bits)
Route       10.1.0.0   ->  10.1.  (first 16 bits)   = match
~~~

For `172.16.0.0/16` the first 16 bits are `172.16`, which differ from `10.1`, so there is no match.

## The full decision order

1. **Longest prefix** (the most specific route)
2. If the prefixes are equal: lowest **administrative distance**
3. If the AD is equal too: lowest **metric**

## Why choose the most specific route?

A specific route describes exactly where a network is. A short prefix covers a large range and is more general. Using the most specific route lets administrators send most traffic one way and a smaller part somewhere else.

## Summary routes

Suppose R2 has these two routes:

~~~
192.168.0.0/16  via R3      (summary: everything in 192.168.x.x)
192.168.1.0/24  via R1      (specific: PC-A's network)
~~~

A packet for `192.168.1.10` matches both, but /24 is longer than /16, so it goes to **R1**. A packet for `192.168.3.10` matches only the /16 route, so it goes to **R3**.

## The default route and LPM

`0.0.0.0/0` has prefix length **0**, the shortest possible. It is chosen **only when nothing else matches**.

## Practice (answers below)

Routes: `10.0.0.0/8`, `10.20.0.0/16`, `10.20.30.0/24`, `0.0.0.0/0`

1. Where does `10.20.30.99` go?
2. Where does `10.20.99.1` go?
3. Where does `10.99.1.1` go?
4. Where does `8.8.8.8` go?

**Answers**

1. `10.20.30.0/24`
2. `10.20.0.0/16`
3. `10.0.0.0/8`
4. `0.0.0.0/0`

## Common mistakes

- Choosing the first matching route instead of the longest one.
- Thinking a **smaller** prefix number means a more specific route. A **bigger** number (like /24) is more specific than /8.
- Forgetting that the default route matches everything but loses to any other match.

> Use **Packet Walk** with the "LPM example" button. The matching routes are highlighted and the longest one is selected for you.