from . import cli_sim, ospf_sim, vlan_sim

DEFAULT_HELP = "(To configure: enable → configure terminal)"


def _help(devices, **special):
    h = {d: DEFAULT_HELP for d in devices}
    h.update(special)
    return h


LABS = {
    1: {
        "n": 1, "sim": cli_sim, "short": "Lab 1 · Static Routing",
        "badge": "Lab 1 · Static routing", "title": "Static Routing Lab",
        "intro": ("Type Cisco-style commands to configure static routes on three routers, then test the "
                  "result with ping. This is a concept simulator, not real Cisco IOS. It supports a handful "
                  "of commands, but the routing logic is real."),
        "topology": "tools/_topology.html",
        "extra": "",
        "tasks": [
            "Right now R1, R2 and R3 only know their <strong>connected networks</strong>. On every router, add a static route for each remote LAN",
            "Use <code>show ip route</code> to confirm the routes are installed",
            "Test with commands like <code>ping 192.168.3.10 source 192.168.1.1</code>",
            "Click <strong>Check my work</strong>",
        ],
        "bonus": "On R1, replace the two static routes with a single <strong>default route</strong> and pass again",
        "tab_help": _help(cli_sim.ROUTER_NAMES),
        "cheat": [
            ("enable", "Enter privileged mode (R1#)"),
            ("configure terminal (conf t)", "Enter configuration mode (R1(config)#)"),
            ("ip route <network> <mask> <next-hop>", "Add a static route"),
            ("no ip route ...", "Remove a route"),
            ("end / exit", "Leave the current mode"),
            ("show ip route", "Display the routing table"),
            ("show ip interface brief", "Display interfaces and IP addresses"),
            ("show running-config", "Display what you have configured"),
            ("ping <ip> [source <ip>]", "Run a ping test"),
            ("?", "List the commands available in the current mode"),
        ],
        "hint": """R1:
enable
configure terminal
ip route 192.168.2.0 255.255.255.0 10.0.12.2
ip route 192.168.3.0 255.255.255.0 10.0.12.2
end

R2:
ip route 192.168.1.0 255.255.255.0 10.0.12.1
ip route 192.168.3.0 255.255.255.0 10.0.23.2

R3:
ip route 192.168.1.0 255.255.255.0 10.0.23.1
ip route 192.168.2.0 255.255.255.0 10.0.23.1

Bonus (R1):
no ip route 192.168.2.0 255.255.255.0 10.0.12.2
no ip route 192.168.3.0 255.255.255.0 10.0.12.2
ip route 0.0.0.0 0.0.0.0 10.0.12.2

On each router, start with enable and configure terminal.""",
    },

    2: {
        "n": 2, "sim": vlan_sim, "short": "Lab 2 · VLANs & Trunking",
        "badge": "Lab 2 · VLANs and trunking", "title": "VLAN Lab",
        "intro": ("Switch SW1 connects four PCs and the router R1. Create two VLANs, assign the access ports, "
                  "configure a trunk to the router and enable inter-VLAN routing with router-on-a-stick. "
                  "Every PC has its own console, so you can ping from the PCs themselves."),
        "topology": "tools/_topo_vlan.html",
        "extra": """<div class="table-wrap"><table class="result-table route-table">
<tr><th>Device</th><th>Port on SW1</th><th>IP address</th><th>Gateway</th><th>Belongs in</th></tr>
<tr><td>PC1</td><td>Fa0/1</td><td>192.168.10.11/24</td><td>192.168.10.1</td><td>VLAN 10 (SALES)</td></tr>
<tr><td>PC2</td><td>Fa0/2</td><td>192.168.10.12/24</td><td>192.168.10.1</td><td>VLAN 10 (SALES)</td></tr>
<tr><td>PC3</td><td>Fa0/3</td><td>192.168.20.11/24</td><td>192.168.20.1</td><td>VLAN 20 (HR)</td></tr>
<tr><td>PC4</td><td>Fa0/4</td><td>192.168.20.12/24</td><td>192.168.20.1</td><td>VLAN 20 (HR)</td></tr>
<tr><td>R1</td><td>Gi0/1 (trunk)</td><td>Gi0/0.10 = 192.168.10.1<br>Gi0/0.20 = 192.168.20.1</td><td>-</td><td>-</td></tr>
</table></div>""",
        "tasks": [
            "On <strong>SW1</strong> create <strong>VLAN 10 (SALES)</strong> and <strong>VLAN 20 (HR)</strong>",
            "Make Fa0/1 and Fa0/2 access ports in VLAN 10, and Fa0/3 and Fa0/4 access ports in VLAN 20",
            "Make <strong>Gi0/1</strong> a <strong>trunk</strong> towards the router",
            "On <strong>R1</strong> bring up Gi0/0 and create the subinterfaces <code>Gi0/0.10</code> and <code>Gi0/0.20</code> with <code>encapsulation dot1Q</code> and the addresses from the table",
            "Open the PC tabs: ping inside a VLAN first, then across VLANs. Verify with <code>show vlan brief</code> and <code>show interfaces trunk</code>",
            "Click <strong>Check my work</strong>",
        ],
        "bonus": "On the trunk, allow only VLANs 10 and 20 and change the native VLAN to 99",
        "tab_help": _help(vlan_sim.ROUTER_NAMES,
                          PC1="(Try: ipconfig, then ping <ip address>)", PC2="(Try: ipconfig, then ping <ip address>)",
                          PC3="(Try: ipconfig, then ping <ip address>)", PC4="(Try: ipconfig, then ping <ip address>)"),
        "cheat": [
            ("enable / configure terminal", "Enter privileged mode, then configuration mode"),
            ("vlan 10", "Create a VLAN and enter VLAN configuration"),
            ("name SALES", "Name the VLAN (inside VLAN configuration)"),
            ("interface fa0/1", "Select one switch port (short forms work)"),
            ("interface range fa0/1 - 2", "Select several ports at once"),
            ("switchport mode access", "Make the port an access port"),
            ("switchport access vlan 10", "Put the access port into VLAN 10"),
            ("switchport mode trunk", "Make the port a trunk"),
            ("switchport trunk allowed vlan 10,20", "Limit the VLANs carried on the trunk"),
            ("switchport trunk native vlan 99", "Change the native (untagged) VLAN"),
            ("show vlan brief", "List VLANs and their access ports (SW1)"),
            ("show interfaces trunk", "Show trunk ports, native VLAN and allowed VLANs (SW1)"),
            ("R1: interface g0/0.10", "Create a subinterface (router-on-a-stick)"),
            ("R1: encapsulation dot1Q 10", "Tag the subinterface with VLAN 10"),
            ("R1: ip address 192.168.10.1 255.255.255.0", "Give the subinterface its gateway address"),
            ("R1: no shutdown (on g0/0)", "Bring the physical interface up"),
            ("show ip interface brief / show ip route", "Check R1's interfaces and routes"),
            ("PC: ping <ip> / ipconfig", "Test connectivity from a PC"),
        ],
        "hint": """SW1:
enable
configure terminal
vlan 10
name SALES
vlan 20
name HR
interface range fastEthernet 0/1 - 2
switchport mode access
switchport access vlan 10
interface range fastEthernet 0/3 - 4
switchport mode access
switchport access vlan 20
interface gigabitEthernet 0/1
switchport mode trunk
end

R1:
enable
configure terminal
interface gigabitEthernet 0/0
no shutdown
interface gigabitEthernet 0/0.10
encapsulation dot1Q 10
ip address 192.168.10.1 255.255.255.0
interface gigabitEthernet 0/0.20
encapsulation dot1Q 20
ip address 192.168.20.1 255.255.255.0
end

Bonus (SW1, interface gigabitEthernet 0/1):
switchport trunk allowed vlan 10,20
switchport trunk native vlan 99""",
    },

    3: {
        "n": 3, "sim": ospf_sim, "short": "Lab 3 · OSPF Routing",
        "badge": "Lab 3 · Dynamic routing", "title": "OSPF Routing Lab",
        "intro": ("Three routers are connected in a triangle. All IP addresses are already configured, but no "
                  "routing protocol is running yet. Enable OSPF so that every PC can reach every other PC, "
                  "then use OSPF cost to change the path a packet takes."),
        "topology": "tools/_topo_ospf.html",
        "extra": """<div class="table-wrap"><table class="result-table route-table">
<tr><th>Router</th><th>LAN (Gi0/0)</th><th>Link (Fa0/1)</th><th>Second link</th></tr>
<tr><td>R1</td><td>192.168.1.1/24</td><td>10.0.12.1/30 to R2</td><td>Se0/0: 10.0.13.1/30 to R3 (cost 64)</td></tr>
<tr><td>R2</td><td>192.168.2.1/24</td><td>10.0.12.2/30 to R1</td><td>Fa0/2: 10.0.23.1/30 to R3</td></tr>
<tr><td>R3</td><td>192.168.3.1/24</td><td>10.0.23.2/30 to R2</td><td>Se0/0: 10.0.13.2/30 to R1 (cost 64)</td></tr>
</table></div>""",
        "tasks": [
            "On R1, R2 and R3 start OSPF with <code>router ospf 1</code> and advertise <strong>every interface</strong> in <strong>area 0</strong> using the <code>network</code> command",
            "Check the neighbours with <code>show ip ospf neighbor</code> and the learned routes with <code>show ip route</code>",
            "Ping across the network, for example <code>ping 192.168.3.10 source 192.168.1.1</code> from R1",
            "Click <strong>Check my work</strong>",
        ],
        "bonus": "R1 reaches 192.168.3.0/24 through R2 (total cost 3). Change an OSPF <strong>cost</strong> on R1 so that it uses the direct serial link to R3 instead",
        "tab_help": _help(ospf_sim.ROUTER_NAMES),
        "cheat": [
            ("enable / configure terminal", "Enter privileged mode, then configuration mode"),
            ("router ospf 1", "Start OSPF process 1 (enters router configuration)"),
            ("router-id 1.1.1.1", "Set the router ID manually (optional)"),
            ("network 192.168.1.0 0.0.0.255 area 0", "Run OSPF on interfaces inside this range (wildcard mask)"),
            ("network 0.0.0.0 255.255.255.255 area 0", "Shortcut: run OSPF on every interface"),
            ("passive-interface g0/0", "Advertise a LAN but do not form neighbours on it"),
            ("interface fa0/1", "Select an interface"),
            ("ip ospf cost 100", "Set the OSPF cost of the interface"),
            ("show ip ospf neighbor", "List OSPF neighbours and their state"),
            ("show ip route [ospf]", "Display the routing table (only OSPF routes)"),
            ("show ip protocols", "Summary of the OSPF configuration"),
            ("ping <ip> [source <ip>]", "Run a ping test"),
        ],
        "hint": """R1:
enable
configure terminal
router ospf 1
network 192.168.1.0 0.0.0.255 area 0
network 10.0.12.0 0.0.0.3 area 0
network 10.0.13.0 0.0.0.3 area 0
end

R2: networks 192.168.2.0 0.0.0.255, 10.0.12.0 0.0.0.3 and 10.0.23.0 0.0.0.3
R3: networks 192.168.3.0 0.0.0.255, 10.0.23.0 0.0.0.3 and 10.0.13.0 0.0.0.3

Shortcut on any router:
network 0.0.0.0 255.255.255.255 area 0

Bonus (R1):
interface fastEthernet 0/1
ip ospf cost 100""",
    },
}