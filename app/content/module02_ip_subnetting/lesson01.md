# IPv4 addresses and binary

Computers store everything as **binary**: only 0s and 1s. Subnetting only makes sense once you are comfortable switching between binary and decimal, so this lesson builds that skill.

## Structure of an IPv4 address

An IPv4 address has **32 bits**, split into **4 octets** of 8 bits each. We write each octet in decimal and separate the octets with dots.

~~~
192      .168      .1        .10
11000000 .10101000 .00000001 .00001010
~~~

Each octet can hold values from 0 to 255 (00000000 to 11111111).

## Place values in one octet

Every bit has a value that doubles as you move left:

| 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Binary to decimal

Add up the place values where the bit is `1`.

- `11000000` = 128 + 64 = **192**
- `10101000` = 128 + 32 + 8 = **168**
- `00001010` = 8 + 2 = **10**

## Decimal to binary

Go from left to right. If the place value fits into what is left, write `1` and subtract it. Otherwise write `0`.

Convert **172**:

1. 128 fits → 1, remainder 44
2. 64 does not fit → 0
3. 32 fits → 1, remainder 12
4. 16 does not fit → 0
5. 8 fits → 1, remainder 4
6. 4 fits → 1, remainder 0
7. 2 and 1 do not fit → 0, 0

So 172 = `10101100`.

## Values worth memorising

These octets appear in almost every subnet mask:

| Decimal | Binary | Ones from the left |
| --- | --- | --- |
| 128 | 10000000 | 1 |
| 192 | 11000000 | 2 |
| 224 | 11100000 | 3 |
| 240 | 11110000 | 4 |
| 248 | 11111000 | 5 |
| 252 | 11111100 | 6 |
| 254 | 11111110 | 7 |
| 255 | 11111111 | 8 |

## Practice (answers below)

1. Convert `10.0.5.1` to binary.
2. Convert `11000000.10101000.00001010.01100100` to decimal.
3. What decimal value is `11111000`?

**Answers**

1. `00001010.00000000.00000101.00000001`
2. `192.168.10.100`
3. 248

## IPv4 classes (history)

| Class | First octet | Original default mask |
| --- | --- | --- |
| A | 1 – 126 | /8 |
| B | 128 – 191 | /16 |
| C | 192 – 223 | /24 |
| D | 224 – 239 | Multicast |
| E | 240 – 255 | Experimental |

Modern networks use **CIDR prefixes** instead of classes, but classes still appear in exams and interviews.

## Special addresses

| Address | Meaning |
| --- | --- |
| 127.0.0.0/8 | Loopback: traffic to your own device |
| 169.254.0.0/16 | APIPA: self-assigned when DHCP fails |
| 0.0.0.0 | "No address" or "any address" |
| 255.255.255.255 | Limited broadcast |
| 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 | Private ranges |

> **Tip:** if a PC shows an address starting with `169.254`, it asked for an address from DHCP and got no answer.