# VLANs explained

A **VLAN (Virtual LAN)** divides one physical switch into several separate **logical** networks. Devices in the same VLAN can talk to each other directly, as if they were on their own switch. Devices in different VLANs cannot, unless a router connects them.

## Why use VLANs?

- **Smaller broadcast domains.** Each VLAN has its own broadcasts, so traffic and noise go down.
- **Better security.** HR, Finance and guests can be kept apart even when they share the same cables and switches.
- **Flexibility.** Users can be moved to another VLAN by changing a setting, not by moving cables.
- **Easier management.** Networks can be organised by department or function, not by where the cable runs.

## Without and with VLANs

~~~
Without VLANs: one switch = one broadcast domain
With VLANs:    VLAN 10 (Sales) | VLAN 20 (HR) | VLAN 30 (Guest)  -> three broadcast domains
~~~

Each VLAN normally uses its **own IP subnet**, for example:

| VLAN | Name | Subnet |
| --- | --- | --- |
| 10 | Sales | 192.168.10.0/24 |
| 20 | HR | 192.168.20.0/24 |
| 30 | Guest | 192.168.30.0/24 |

## VLAN numbers

- **1** is the default VLAN. All ports start here. Avoid using it for real traffic.
- **2 – 1001** are normal-range VLANs you can create freely.
- **1002 – 1005** are reserved for legacy technologies.
- **1006 – 4094** are extended-range VLANs.

## Access ports

An **access port** belongs to exactly one VLAN and connects an end device such as a PC or printer. The device does not know about VLANs at all.

## Configuring VLANs on a Cisco switch

~~~
Switch(config)# vlan 10
Switch(config-vlan)# name SALES
Switch(config-vlan)# exit

Switch(config)# interface fastEthernet 0/1
Switch(config-if)# switchport mode access
Switch(config-if)# switchport access vlan 10
~~~

Configure a range of ports at once:

~~~
Switch(config)# interface range fastEthernet 0/1 - 12
Switch(config-if-range)# switchport mode access
Switch(config-if-range)# switchport access vlan 10
~~~

## Checking your work

~~~
Switch# show vlan brief
Switch# show interfaces fastEthernet 0/1 switchport
~~~

`show vlan brief` lists each VLAN and the ports that belong to it.

## Good practice

- Give VLANs meaningful names.
- Do not leave unused ports in VLAN 1. Move them to an unused VLAN and shut them down.
- Keep one subnet per VLAN so that addressing stays simple.

## Common mistakes

- Putting a PC in the right VLAN but giving it an IP address from the wrong subnet.
- Forgetting that each VLAN needs its own gateway address.
- Expecting two different VLANs to communicate without a router.

In the next lesson you will see how trunks carry several VLANs over one link and how routing connects the VLANs.