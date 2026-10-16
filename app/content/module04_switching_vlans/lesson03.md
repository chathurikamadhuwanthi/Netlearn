# Trunks and inter-VLAN routing

Switches usually connect to other switches and to routers. These links must carry traffic for **many VLANs** at once. A link that does this is called a **trunk**.

## Trunk ports

- An **access port** carries one VLAN and is used for end devices.
- A **trunk port** carries **several VLANs** and connects switches to other switches or to routers.

To keep the VLANs apart on one cable, the switch adds a small label to each frame. The standard that defines this label is **IEEE 802.1Q**.

## 802.1Q tagging

- The tag is **4 bytes** inserted into the Ethernet frame.
- It contains a **12-bit VLAN ID**, which allows VLAN numbers 1 to 4094 to be used.
- The receiving switch reads the tag, delivers the frame only to ports in that VLAN, and removes the tag before sending the frame to an access port.

### The native VLAN

Traffic of one VLAN, the **native VLAN**, is sent over the trunk **without a tag**. By default this is VLAN 1. Both ends of a trunk must use the **same** native VLAN, otherwise frames end up in the wrong VLAN. For security, many networks change it to an unused VLAN such as 99.

## Configuring a trunk

~~~
Switch(config)# interface gigabitEthernet 0/1
Switch(config-if)# switchport mode trunk
Switch(config-if)# switchport trunk allowed vlan 10,20,30
Switch(config-if)# switchport trunk native vlan 99
~~~

On some older Layer 3-capable switches you must first enter `switchport trunk encapsulation dot1q`.

~~~
Switch# show interfaces trunk
~~~

This command shows which ports are trunks, the native VLAN and which VLANs are allowed.

## Why VLANs cannot talk to each other

Each VLAN is a separate network with its own subnet. Moving traffic between two different networks is a **routing** job, so a **Layer 3 device** is needed.

## Method 1: Router-on-a-stick

One physical router interface connects to a switch trunk. The interface is divided into **subinterfaces**, one per VLAN. Each subinterface is the **default gateway** of its VLAN.

~~~
Router(config)# interface gigabitEthernet 0/0
Router(config-if)# no shutdown

Router(config)# interface gigabitEthernet 0/0.10
Router(config-subif)# encapsulation dot1Q 10
Router(config-subif)# ip address 192.168.10.1 255.255.255.0

Router(config)# interface gigabitEthernet 0/0.20
Router(config-subif)# encapsulation dot1Q 20
Router(config-subif)# ip address 192.168.20.1 255.255.255.0
~~~

PCs in VLAN 10 use 192.168.10.1 as their gateway and PCs in VLAN 20 use 192.168.20.1.

## Method 2: Layer 3 switch (SVI)

A Layer 3 switch can route between VLANs by itself using **SVIs** (Switch Virtual Interfaces). It is faster than router-on-a-stick because the traffic does not have to leave the switch.

~~~
Switch(config)# ip routing
Switch(config)# interface vlan 10
Switch(config-if)# ip address 192.168.10.1 255.255.255.0
Switch(config)# interface vlan 20
Switch(config-if)# ip address 192.168.20.1 255.255.255.0
~~~

## Troubleshooting checklist

1. Does the VLAN exist, and is the port in the correct VLAN? (`show vlan brief`)
2. Is the link a trunk, and is the VLAN allowed on it? (`show interfaces trunk`)
3. Do both ends of the trunk use the same native VLAN?
4. Does the PC have an address from the VLAN's subnet and the correct gateway?
5. Does the router subinterface (or SVI) exist, and is it up?

## Quick recap

- Access ports carry one VLAN. Trunks carry many VLANs using 802.1Q tags.
- The native VLAN is untagged and must match on both ends.
- VLANs need a Layer 3 device to communicate: router-on-a-stick or a Layer 3 switch.