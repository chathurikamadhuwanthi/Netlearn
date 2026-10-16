# Subnetting step by step

**Subnetting** means dividing one large network into smaller networks called **subnets**.

## Why subnet?

- **Less broadcast traffic.** Broadcasts stay inside each small subnet.
- **Better security.** Departments such as HR, Finance and IT can be separated.
- **Efficient addressing.** You give each group about as many addresses as it needs.
- **Easier management** and troubleshooting.

## The core idea

To make more subnets, we **borrow bits from the host part**, which makes the prefix longer.

~~~
Borrow n bits          ->  number of subnets = 2^n
Host bits left = h     ->  usable hosts per subnet = 2^h - 2
~~~

## Method A: you know how many subnets you need

**Divide `192.168.10.0/24` into 4 subnets.**

1. 4 subnets = 2², so borrow **2 bits**.
2. New prefix = 24 + 2 = **/26** (mask 255.255.255.192).
3. Block size = 256 − 192 = **64**.
4. Host bits left = 6, so 2⁶ − 2 = **62 usable hosts** per subnet.

| Subnet | Network | Usable range | Broadcast |
| --- | --- | --- | --- |
| 1 | 192.168.10.0/26 | .1 – .62 | .63 |
| 2 | 192.168.10.64/26 | .65 – .126 | .127 |
| 3 | 192.168.10.128/26 | .129 – .190 | .191 |
| 4 | 192.168.10.192/26 | .193 – .254 | .255 |

## Method B: you know how many hosts you need

**Each subnet of `192.168.20.0/24` must hold at least 30 hosts.**

1. Find h so that 2^h − 2 ≥ 30. With h = 5: 32 − 2 = 30, which works.
2. Host bits = 5, so the prefix = 32 − 5 = **/27**.
3. Block size = **32**, and the number of subnets = 2³ = **8**.

The subnets are `192.168.20.0/27`, `.32/27`, `.64/27`, `.96/27` and so on up to `.224/27`.

## A larger example

**Each subnet of `172.16.0.0/16` needs about 500 hosts.**

- 2^9 − 2 = 510, which is at least 500, so 9 host bits are needed.
- Prefix = 32 − 9 = **/23**.
- Subnets created = 2^(23 − 16) = **128**.
- The block size in the third octet is 2, so the subnets are 172.16.0.0, 172.16.2.0, 172.16.4.0 and so on.

## Quick checklist

1. Decide the number of **subnets** or **hosts** you need.
2. Work out the host bits (or borrowed bits).
3. Write the new **prefix** and **mask**.
4. Calculate the **block size**.
5. List the subnets by counting up in steps of the block size.
6. For each subnet write the network, first host, last host and broadcast.

## Practice (answers below)

1. Split `10.0.0.0/24` into 8 subnets. What is the prefix and how many hosts per subnet?
2. `192.168.5.0/24` needs subnets of at least 50 hosts. Which prefix do you use?
3. Which subnet does `192.168.1.77/28` belong to?

**Answers**

1. 8 = 2³, so the prefix is /27 with 30 hosts per subnet.
2. 2^6 − 2 = 62, which is at least 50, so 6 host bits and the prefix is **/26**.
3. The block size is 16 and 77 falls in 64–79. Network 192.168.1.64, broadcast 192.168.1.79, usable .65 – .78.

## What comes next: VLSM

In these examples every subnet had the same size. In real networks one department may need 100 hosts and another only 10. **VLSM (Variable Length Subnet Mask)** lets you use different prefix lengths so that no addresses are wasted.

> Try the examples in the **Subnet Calculator** and compare its table with yours.