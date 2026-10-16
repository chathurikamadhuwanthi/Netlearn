import ipaddress
from .routing_sim import IFACES, owner_of

ROUTER_NAMES = ["R1", "R2", "R3"]
MAX_HOPS = 10
INVALID = "% Invalid input detected at '^' marker."

# PCs and their gateway routers
HOSTS = {"PC-A": "192.168.1.10", "PC-B": "192.168.2.10", "PC-C": "192.168.3.10"}
HOST_GATEWAY = {"192.168.1.10": "R1", "192.168.2.10": "R2", "192.168.3.10": "R3"}

# Ping pairs checked by the lab (both directions)
PAIRS = [("PC-A", "PC-B"), ("PC-B", "PC-A"), ("PC-A", "PC-C"),
         ("PC-C", "PC-A"), ("PC-B", "PC-C"), ("PC-C", "PC-B")]

# Commands available in each mode
MODE_CMDS = {
    "user": ["enable", "ping", "show", "exit"],
    "priv": ["configure", "show", "ping", "disable", "exit"],
    "config": ["ip", "no", "do", "exit", "end"],
}

AD = {"C": 0, "L": 0, "S": 1, "S*": 1}   # Administrative Distance


# ---------- State and helpers ----------

def new_state():
    return {"modes": {r: "user" for r in ROUTER_NAMES},
            "routes": {r: [] for r in ROUTER_NAMES}}   # [network, mask, next_hop]


def prompt(state, router):
    mode = state["modes"][router]
    return {"user": f"{router}>", "priv": f"{router}#",
            "config": f"{router}(config)#"}[mode]


def long_name(iface):
    return iface.replace("Gi", "GigabitEthernet", 1)


def pick(token, options):
    """Expands a short form (conf, sh, int ...) into the full command."""
    token = token.lower()
    if token in options:
        return token
    found = [o for o in options if o.startswith(token)]
    return found[0] if len(found) == 1 else None


def _ip(text):
    try:
        return ipaddress.IPv4Address(text)
    except ValueError:
        return None


# ---------- Routing table and forwarding ----------

def build_table(state, router):
    table = []
    for iname, f in IFACES[router].items():
        table.append({"code": "C", "net": f.network, "via": None, "iface": iname})
        table.append({"code": "L", "net": ipaddress.IPv4Network(f"{f.ip}/32"),
                      "via": None, "iface": iname})
    for net, mask, nh in state["routes"][router]:
        network = ipaddress.IPv4Network(f"{net}/{mask}")
        via = ipaddress.IPv4Address(nh)
        out = next((i for i, f in IFACES[router].items() if via in f.network), None)
        if out is None:
            continue   # a route whose next hop is not reachable is not installed
        code = "S*" if network.prefixlen == 0 else "S"
        table.append({"code": code, "net": network, "via": via, "iface": out})
    return table


def lookup(table, dest):
    """Longest Prefix Match."""
    matches = [r for r in table if dest in r["net"]]
    if not matches:
        return None
    return max(matches, key=lambda r: (r["net"].prefixlen, -AD[r["code"]]))


def _walk(state, start, dest):
    """Forwards a packet from the start router towards dest."""
    current = start
    path = [start]
    for _ in range(MAX_HOPS):
        best = lookup(build_table(state, current), dest)
        if best is None:
            return {"ok": False, "reason": "noroute", "at": current, "path": path}
        if best["code"] == "L":                       # one of the router's own IPs
            return {"ok": True, "at": current, "path": path}
        if best["code"] == "C":                       # directly connected network
            if HOST_GATEWAY.get(str(dest)) == current:
                return {"ok": True, "at": current, "path": path}
            owner = owner_of(dest)                    # router on the other end of the link
            if owner and owner != current:
                path.append(owner)
                return {"ok": True, "at": owner, "path": path}
            return {"ok": False, "reason": "nohost", "at": current, "path": path}
        nh = best["via"]                              # static route
        if str(nh) == "203.0.113.2":
            return {"ok": False, "reason": "isp", "at": current, "path": path}
        owner = owner_of(nh)
        if owner is None:
            return {"ok": False, "reason": "noroute", "at": current, "path": path}
        current = owner
        path.append(owner)
    return {"ok": False, "reason": "ttl", "at": current, "path": path}


# ---------- Commands ----------

def _help(mode):
    if mode == "user":
        return ("Commands: enable, ping <ip>, show ip route, show ip interface brief, exit\n"
                "(Use 'enable' first to configure the router)")
    if mode == "priv":
        return ("Commands: configure terminal, show ip route, show ip interface brief,\n"
                "          show running-config, ping <ip> [source <ip>], disable, exit")
    return ("Commands: ip route <network> <mask> <next-hop>\n"
            "          no ip route <network> <mask> <next-hop>\n"
            "          do show ip route, do ping <ip>, exit, end")


def _show_route(state, router):
    table = build_table(state, router)
    default = next((r for r in table if r["code"] == "S*"), None)
    lines = ["Codes: C - connected, S - static, L - local, * - candidate default", ""]
    if default:
        lines.append(f"Gateway of last resort is {default['via']} to network 0.0.0.0")
    else:
        lines.append("Gateway of last resort is not set")
    lines.append("")
    for r in sorted(table, key=lambda r: (int(r["net"].network_address), r["net"].prefixlen)):
        if r["code"] in ("C", "L"):
            lines.append(f"{r['code']:<3} {r['net']} is directly connected, {long_name(r['iface'])}")
        else:
            lines.append(f"{r['code']:<3} {r['net']} [1/0] via {r['via']}")
    return "\n".join(lines)


def _show_int_brief(router):
    lines = ["Interface              IP-Address      OK? Method Status                Protocol"]
    for iname, f in IFACES[router].items():
        lines.append(f"{long_name(iname):<22} {str(f.ip):<15} YES manual up                    up")
    return "\n".join(lines)


def _running_config(state, router):
    lines = ["Building configuration...", "", "Current configuration:", "!",
             f"hostname {router}", "!"]
    for iname, f in IFACES[router].items():
        lines += [f"interface {long_name(iname)}", f" ip address {f.ip} {f.netmask}",
                  " no shutdown", "!"]
    for net, mask, nh in state["routes"][router]:
        lines.append(f"ip route {net} {mask} {nh}")
    lines += ["!", "end"]
    return "\n".join(lines)


def _show(state, router, rest, mode):
    if not rest:
        return "% Incomplete command."
    sub = pick(rest[0], ["ip", "running-config"])
    if sub == "running-config":
        return INVALID if mode == "user" else _running_config(state, router)
    if sub == "ip":
        if len(rest) < 2:
            return "% Incomplete command."
        what = pick(rest[1], ["route", "interface"])
        if what == "route":
            return _show_route(state, router)
        if what == "interface":
            if len(rest) < 3 or pick(rest[2], ["brief"]) != "brief":
                return "% Incomplete command."
            return _show_int_brief(router)
    return INVALID


def _ip_cmd(state, router, rest, negate):
    if not rest or pick(rest[0], ["route"]) != "route":
        return INVALID
    args = rest[1:]
    if len(args) < 3:
        return "% Incomplete command."
    if len(args) > 3:
        return INVALID

    net, mask, nh = _ip(args[0]), _ip(args[1]), _ip(args[2])
    if net is None or mask is None or nh is None:
        return INVALID
    try:
        network = ipaddress.IPv4Network(f"{net}/{mask}", strict=True)
    except ValueError:
        return "%Inconsistent address and mask"

    entry = [str(network.network_address), str(network.netmask), str(nh)]
    routes = state["routes"][router]

    if negate:
        if entry in routes:
            routes.remove(entry)
            return ""
        return "% No matching route to delete"

    if entry not in routes:
        routes.append(entry)
    if not any(nh in f.network for f in IFACES[router].values()):
        return (f"[NetLearn tip] Next hop {nh} is not on a network directly connected to {router}, "
                "so the route is not installed in the routing table. Check the IP address.")
    return ""


def _fail_text(fw, origin, dest):
    reason, at = fw["reason"], fw["at"]
    if reason == "noroute":
        if at == origin:
            return ".....", (f"{origin} has no route to {dest} (no matching entry in its routing table). "
                             "Try `show ip route`.")
        return "U.U.U", (f"The packet reached {at}, but {at} has no route to {dest}, so it was "
                         "dropped and a 'U' (unreachable) came back.")
    if reason == "nohost":
        return ".....", f"{dest} is not a host or interface on that network, so there was no reply."
    if reason == "isp":
        return ".....", "The packet was sent to the ISP, but the simulated ISP does not reply."
    return ".....", "Routing loop detected (TTL expired)."


def _ping(state, router, args):
    if not args:
        return "% Incomplete command."
    dest = _ip(args[0])
    if dest is None:
        return "% Unrecognized host or address, or protocol not running."

    own = {f.ip for f in IFACES[router].values()}
    src = None
    if len(args) == 3 and "source".startswith(args[1].lower()):
        src = _ip(args[2])
        if src is None or src not in own:
            return "% Invalid source address. (Use one of the router's own interface IPs.)"
    elif len(args) != 1:
        return INVALID

    if src is None:   # default source = the IP of the exit interface
        best = lookup(build_table(state, router), dest)
        if best is not None:
            src = dest if best["code"] == "L" else IFACES[router][best["iface"]].ip

    ok, tip = False, ""
    if src is None:
        seq = "....."
        tip = (f"{router} has no route to {dest} (no matching entry in its routing table). "
               "Try `show ip route`.")
    else:
        fw = _walk(state, router, dest)
        if not fw["ok"]:
            seq, tip = _fail_text(fw, router, dest)
        else:
            ret = _walk(state, fw["at"], src)   # the reply travelling back
            if ret["ok"]:
                seq, ok = "!!!!!", True
            else:
                seq = "....."
                if ret["reason"] == "noroute":
                    tip = (f"The echo request reached {dest} ✅, but for the reply to come back "
                           f"{ret['at']} needs a route to {src} ❌. Routes are needed in both directions!")
                else:
                    tip = "The reply could not return (routing loop or missing host)."

    lines = ["Type escape sequence to abort.",
             f"Sending 5, 100-byte ICMP Echos to {dest}, timeout is 2 seconds:", seq]
    if ok:
        lines.append("Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms")
    else:
        lines.append("Success rate is 0 percent (0/5)")
        lines.append(f"[NetLearn tip] {tip}")
    return "\n".join(lines)


def execute(state, router, line):
    line = (line or "").strip()
    if not line:
        return ""
    mode = state["modes"][router]
    if line in ("?", "help"):
        return _help(mode)

    tokens = line.split()
    cmd = pick(tokens[0], MODE_CMDS[mode])
    if cmd is None:
        return INVALID
    rest = tokens[1:]

    if cmd == "enable":
        state["modes"][router] = "priv"
        return ""
    if cmd == "disable":
        state["modes"][router] = "user"
        return ""
    if cmd == "exit":
        if mode == "config":
            state["modes"][router] = "priv"
        elif mode == "priv":
            state["modes"][router] = "user"
        else:
            return "(You cannot log out of user mode in this simulator.)"
        return ""
    if cmd == "end":
        state["modes"][router] = "priv"
        return ""
    if cmd == "configure":
        if not rest:
            return "% Incomplete command."
        if pick(rest[0], ["terminal"]) != "terminal":
            return INVALID
        state["modes"][router] = "config"
        return "Enter configuration commands, one per line.  End with CNTL/Z."
    if cmd == "show":
        return _show(state, router, rest, mode)
    if cmd == "ping":
        return _ping(state, router, rest)
    if cmd == "do":
        if not rest:
            return "% Incomplete command."
        sub = pick(rest[0], ["show", "ping"])
        if sub == "show":
            return _show(state, router, rest[1:], "priv")
        if sub == "ping":
            return _ping(state, router, rest[1:])
        return INVALID
    if cmd == "ip":
        return _ip_cmd(state, router, rest, negate=False)
    if cmd == "no":
        if not rest or pick(rest[0], ["ip"]) != "ip":
            return INVALID
        return _ip_cmd(state, router, rest[1:], negate=True)
    return INVALID


# ---------- Lab checker ----------

def pc_ping(state, src_name, dst_name):
    src_ip, dst_ip = _ip(HOSTS[src_name]), _ip(HOSTS[dst_name])
    fw = _walk(state, HOST_GATEWAY[HOSTS[src_name]], dst_ip)
    if not fw["ok"]:
        return False, f"The request stopped at {fw['at']}: it has no route to {dst_ip}"
    ret = _walk(state, fw["at"], src_ip)
    if not ret["ok"]:
        return False, f"The request arrived, but for the reply {ret['at']} has no route to {src_ip}"
    return True, "reachable"


def check(state):
    tasks = []
    for a, b in PAIRS:
        ok, why = pc_ping(state, a, b)
        tasks.append({"label": f"{a} → {b}", "ok": ok, "why": why})
    passed = all(t["ok"] for t in tasks)
    r1 = state["routes"]["R1"]
    bonus = passed and len(r1) == 1 and r1[0][0] == "0.0.0.0" and r1[0][1] == "0.0.0.0"
    return {"tasks": tasks, "passed": passed, "bonus": bonus}