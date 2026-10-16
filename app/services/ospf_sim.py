import heapq
import ipaddress
import re

ROUTER_NAMES = ["R1", "R2", "R3"]
INVALID = "% Invalid input detected at '^' marker."
INCOMPLETE = "% Incomplete command."

# interface -> (IP address, mask, default OSPF cost)
TOPO = {
    "R1": {"Gi0/0": ("192.168.1.1", "255.255.255.0", 1),
           "Fa0/1": ("10.0.12.1", "255.255.255.252", 1),
           "Se0/0": ("10.0.13.1", "255.255.255.252", 64)},
    "R2": {"Gi0/0": ("192.168.2.1", "255.255.255.0", 1),
           "Fa0/1": ("10.0.12.2", "255.255.255.252", 1),
           "Fa0/2": ("10.0.23.1", "255.255.255.252", 1)},
    "R3": {"Gi0/0": ("192.168.3.1", "255.255.255.0", 1),
           "Fa0/1": ("10.0.23.2", "255.255.255.252", 1),
           "Se0/0": ("10.0.13.2", "255.255.255.252", 64)},
}
LINKS = [("R1", "Fa0/1", "R2", "Fa0/1"),
         ("R2", "Fa0/2", "R3", "Fa0/1"),
         ("R1", "Se0/0", "R3", "Se0/0")]
HOSTS = {"PC-A": ("192.168.1.10", "R1"), "PC-B": ("192.168.2.10", "R2"), "PC-C": ("192.168.3.10", "R3")}
PAIRS = [("PC-A", "PC-B"), ("PC-B", "PC-A"), ("PC-A", "PC-C"),
         ("PC-C", "PC-A"), ("PC-B", "PC-C"), ("PC-C", "PC-B")]
AD = {"C": 0, "L": 0, "O": 110}
LONG = {"Gi": "GigabitEthernet", "Fa": "FastEthernet", "Se": "Serial"}
MAX_HOPS = 10


# ---------- State and helpers ----------

def new_state():
    return {
        "modes": {r: "user" for r in ROUTER_NAMES},
        "ctx": {r: None for r in ROUTER_NAMES},    # None / ["ospf"] / ["if", "Fa0/1"]
        "ospf": {r: None for r in ROUTER_NAMES},   # {"pid", "rid", "networks", "passive"}
        "cost": {r: {} for r in ROUTER_NAMES},     # interface -> configured OSPF cost
        "down": {r: [] for r in ROUTER_NAMES},     # shut down interfaces
    }


def long_name(n):
    return LONG[n[:2]] + n[2:]


def pick(token, options):
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


def norm_iface(tokens):
    text = "".join(tokens).lower()
    m = re.fullmatch(r"(gigabitethernet|fastethernet|serial|gi|fa|se|g|f|s)(\d+/\d+)", text)
    if not m:
        return None
    k = m.group(1)
    kind = "Gi" if k.startswith("g") else ("Fa" if k.startswith("f") else "Se")
    return kind + m.group(2)


def _area(text):
    if text.isdigit():
        return int(text)
    ip = _ip(text)
    return int(ip) if ip is not None else None


def prompt(state, r):
    mode, ctx = state["modes"][r], state["ctx"][r]
    if mode == "user":
        return f"{r}>"
    if mode == "priv":
        return f"{r}#"
    if ctx is None:
        return f"{r}(config)#"
    return f"{r}(config-router)#" if ctx[0] == "ospf" else f"{r}(config-if)#"


def _options(state, r):
    mode, ctx = state["modes"][r], state["ctx"][r]
    if mode == "user":
        return ["enable", "show", "ping", "exit"]
    if mode == "priv":
        return ["configure", "show", "ping", "disable", "exit"]
    if ctx is None:
        return ["router", "interface", "do", "exit", "end"]
    if ctx[0] == "ospf":
        return ["router-id", "network", "passive-interface", "no", "do", "router", "interface", "exit", "end"]
    return ["ip", "shutdown", "no", "do", "router", "interface", "exit", "end"]


# ---------- OSPF engine ----------

def _rid(state, r):
    cfg = state["ospf"].get(r)
    if cfg and cfg["rid"]:
        return cfg["rid"]
    ips = [v[0] for i, v in TOPO[r].items() if i not in state["down"][r]]
    return max(ips, key=lambda x: int(ipaddress.IPv4Address(x))) if ips else "0.0.0.0"


def _running(state, r):
    """{interface: info} for the interfaces of r that run OSPF."""
    cfg = state["ospf"].get(r)
    out = {}
    if not cfg:
        return out
    for iface, (ip, mask, base) in TOPO[r].items():
        if iface in state["down"][r]:
            continue
        ipint = int(ipaddress.IPv4Address(ip))
        for net, wc, area in cfg["networks"]:
            m = int(ipaddress.IPv4Address(wc)) ^ 0xFFFFFFFF
            if ipint & m == int(ipaddress.IPv4Address(net)) & m:
                out[iface] = {"area": area, "passive": iface in cfg["passive"],
                              "cost": state["cost"][r].get(iface, base),
                              "net": ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)}
                break
    return out


def _adjacent(state, link):
    ra, ia, rb, ib = link
    a, b = _running(state, ra).get(ia), _running(state, rb).get(ib)
    return bool(a and b and not a["passive"] and not b["passive"] and a["area"] == b["area"])


def _graph(state):
    g = {r: [] for r in ROUTER_NAMES}
    for link in LINKS:
        if _adjacent(state, link):
            ra, ia, rb, ib = link
            ca = _running(state, ra)[ia]["cost"]
            cb = _running(state, rb)[ib]["cost"]
            g[ra].append((rb, ia, TOPO[rb][ib][0], ca))   # (neighbour, my interface, neighbour IP, cost)
            g[rb].append((ra, ib, TOPO[ra][ia][0], cb))
    return g


def _spf(state, src):
    """Dijkstra's shortest path first: {router: (distance, exit interface, next-hop IP)}."""
    g = _graph(state)
    heap = [(0, 0, src, None, None)]
    seen = {}
    while heap:
        d, _tie, node, ex, nh = heapq.heappop(heap)
        if node in seen:
            continue
        seen[node] = (d, ex, nh)
        for nb, iface, nb_ip, cost in g[node]:
            if nb in seen:
                continue
            if node == src:
                heapq.heappush(heap, (d + cost, int(ipaddress.IPv4Address(nb_ip)), nb, iface, nb_ip))
            else:
                heapq.heappush(heap, (d + cost, int(ipaddress.IPv4Address(nh)), nb, ex, nh))
    return seen


def routes_for(state, r):
    table = []
    for iface, (ip, mask, base) in TOPO[r].items():
        if iface in state["down"][r]:
            continue
        net = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
        table.append({"code": "C", "net": net, "via": None, "iface": iface, "metric": 0})
        table.append({"code": "L", "net": ipaddress.IPv4Network(f"{ip}/32"),
                      "via": None, "iface": iface, "metric": 0})
    if state["ospf"].get(r):
        seen = _spf(state, r)
        advertised = {t: [(i["net"], i["cost"]) for i in _running(state, t).values()]
                      for t in ROUTER_NAMES}
        connected = {t["net"] for t in table if t["code"] == "C"}
        best = {}
        for t, (d, ex, nh) in seen.items():
            if t == r:
                continue
            for net, cost in advertised[t]:
                if net in connected:
                    continue
                cand = (d + cost, int(ipaddress.IPv4Address(nh)), ex, nh)
                if net not in best or cand[:2] < best[net][:2]:
                    best[net] = cand
        for net, (total, _tie, ex, nh) in best.items():
            table.append({"code": "O", "net": net, "via": ipaddress.IPv4Address(nh),
                          "iface": ex, "metric": total})
    return table


def _owner(state, ip):
    for r, ifs in TOPO.items():
        for iface, (addr, _mask, _base) in ifs.items():
            if addr == str(ip) and iface not in state["down"][r]:
                return r
    return None


def _walk(state, start, dest):
    cur = start
    for _ in range(MAX_HOPS):
        matches = [t for t in routes_for(state, cur) if dest in t["net"]]
        if not matches:
            return {"ok": False, "reason": "noroute", "at": cur}
        best = max(matches, key=lambda t: (t["net"].prefixlen, -AD[t["code"]]))
        if best["code"] == "L":
            return {"ok": True, "at": cur}
        if best["code"] == "C":
            host = next((h for h, (hip, hr) in HOSTS.items() if hip == str(dest)), None)
            if host and HOSTS[host][1] == cur:
                return {"ok": True, "at": cur}
            owner = _owner(state, dest)
            if owner and owner != cur:
                return {"ok": True, "at": owner}
            return {"ok": False, "reason": "nohost", "at": cur}
        owner = _owner(state, best["via"])
        if owner is None:
            return {"ok": False, "reason": "noroute", "at": cur}
        cur = owner
    return {"ok": False, "reason": "ttl", "at": cur}


def _why_not(state, link):
    ra, ia, rb, ib = link
    for r, i in ((ra, ia), (rb, ib)):
        if state["ospf"].get(r) is None:
            return f"OSPF is not running on {r}. Start it with 'router ospf 1'."
        if i in state["down"][r]:
            return f"{r} {long_name(i)} is shut down."
        if i not in _running(state, r):
            return (f"{r} does not advertise {long_name(i)} ({TOPO[r][i][0]}). "
                    "Add a network statement that covers it.")
    a, b = _running(state, ra)[ia], _running(state, rb)[ib]
    if a["passive"] or b["passive"]:
        return "One side has this interface set as passive, so no neighbour can form."
    if a["area"] != b["area"]:
        return "The two ends use different OSPF areas."
    return "Unknown problem."


# ---------- Output helpers ----------

def _show_route(state, r, ospf_only):
    table = [t for t in routes_for(state, r) if (t["code"] == "O" or not ospf_only)]
    lines = ["Codes: C - connected, L - local, O - OSPF", "", "Gateway of last resort is not set", ""]
    for t in sorted(table, key=lambda t: (int(t["net"].network_address), t["net"].prefixlen)):
        if t["code"] in ("C", "L"):
            lines.append(f"{t['code']:<4} {t['net']} is directly connected, {long_name(t['iface'])}")
        else:
            lines.append(f"{t['code']:<4} {t['net']} [110/{t['metric']}] via {t['via']}, {long_name(t['iface'])}")
    return "\n".join(lines)


def _show_neighbors(state, r):
    nbrs = _graph(state)[r]
    if not nbrs:
        return ""
    lines = ["Neighbor ID     Pri   State           Dead Time   Address         Interface"]
    for nb, iface, nb_ip, _cost in nbrs:
        lines.append(f"{_rid(state, nb):<15} {1:>3}   {'FULL/  -':<15} {'00:00:35':<11} {nb_ip:<15} {long_name(iface)}")
    return "\n".join(lines)


def _show_protocols(state, r):
    cfg = state["ospf"].get(r)
    if not cfg:
        return ""
    lines = [f'Routing Protocol is "ospf {cfg["pid"]}"', f"  Router ID {_rid(state, r)}",
             "  Routing for Networks:"]
    for net, wc, area in cfg["networks"]:
        lines.append(f"    {net} {wc} area {area}")
    if cfg["passive"]:
        lines.append("  Passive Interface(s):")
        lines += [f"    {long_name(i)}" for i in cfg["passive"]]
    lines.append("  Distance: (default is 110)")
    return "\n".join(lines)


def _running_config(state, r):
    lines = ["Building configuration...", "", "!", f"hostname {r}", "!"]
    for iface, (ip, mask, _base) in TOPO[r].items():
        lines += [f"interface {long_name(iface)}", f" ip address {ip} {mask}"]
        if iface in state["cost"][r]:
            lines.append(f" ip ospf cost {state['cost'][r][iface]}")
        if iface in state["down"][r]:
            lines.append(" shutdown")
        lines.append("!")
    cfg = state["ospf"].get(r)
    if cfg:
        lines.append(f"router ospf {cfg['pid']}")
        if cfg["rid"]:
            lines.append(f" router-id {cfg['rid']}")
        for net, wc, area in cfg["networks"]:
            lines.append(f" network {net} {wc} area {area}")
        for i in cfg["passive"]:
            lines.append(f" passive-interface {long_name(i)}")
        lines.append("!")
    lines.append("end")
    return "\n".join(lines)


def _show(state, r, rest, priv):
    if not rest:
        return INCOMPLETE
    sub = pick(rest[0], ["ip", "running-config"])
    if sub == "running-config":
        return _running_config(state, r) if priv else INVALID
    if sub == "ip":
        if len(rest) < 2:
            return INCOMPLETE
        what = pick(rest[1], ["route", "interface", "ospf", "protocols"])
        if what == "route":
            return _show_route(state, r, len(rest) > 2 and pick(rest[2], ["ospf"]) == "ospf")
        if what == "interface":
            if len(rest) < 3 or pick(rest[2], ["brief"]) != "brief":
                return INCOMPLETE
            lines = ["Interface              IP-Address      OK? Method Status                Protocol"]
            for iface, (ip, _m, _b) in TOPO[r].items():
                up = iface not in state["down"][r]
                lines.append(f"{long_name(iface):<22} {ip:<15} YES manual "
                             f"{'up' if up else 'administratively down':<21} {'up' if up else 'down'}")
            return "\n".join(lines)
        if what == "ospf":
            if len(rest) > 2 and pick(rest[2], ["neighbor"]) == "neighbor":
                return _show_neighbors(state, r)
            return INCOMPLETE
        if what == "protocols":
            return _show_protocols(state, r)
    return INVALID


# ---------- Ping ----------

def _ping(state, r, args):
    if not args:
        return INCOMPLETE
    dest = _ip(args[0])
    if dest is None:
        return "% Unrecognized host or address, or protocol not running."
    own = {ipaddress.IPv4Address(v[0]) for i, v in TOPO[r].items() if i not in state["down"][r]}
    src = None
    if len(args) == 3 and "source".startswith(args[1].lower()):
        src = _ip(args[2])
        if src is None or src not in own:
            return "% Invalid source address. (Use one of the router's own interface IPs.)"
    elif len(args) != 1:
        return INVALID
    if src is None:
        matches = [t for t in routes_for(state, r) if dest in t["net"]]
        if matches:
            best = max(matches, key=lambda t: (t["net"].prefixlen, -AD[t["code"]]))
            src = dest if best["code"] == "L" else ipaddress.IPv4Address(TOPO[r][best["iface"]][0])
    ok, tip = False, ""
    if src is None:
        seq, tip = ".....", f"{r} has no route to {dest}. Try 'show ip route'."
    else:
        fw = _walk(state, r, dest)
        if not fw["ok"]:
            seq = "....."
            tip = (f"The packet was dropped at {fw['at']}: no route to {dest}."
                   if fw["reason"] == "noroute" else f"{dest} did not answer.")
        else:
            ret = _walk(state, fw["at"], src)
            if ret["ok"]:
                seq, ok = "!!!!!", True
            else:
                seq = "....."
                tip = (f"The request reached {dest}, but for the reply {ret['at']} has no route "
                       f"back to {src}. Routes are needed in both directions.")
    lines = ["Type escape sequence to abort.",
             f"Sending 5, 100-byte ICMP Echos to {dest}, timeout is 2 seconds:", seq]
    if ok:
        lines.append("Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms")
    else:
        lines += ["Success rate is 0 percent (0/5)", f"[NetLearn tip] {tip}"]
    return "\n".join(lines)


# ---------- Commands ----------

def _network_cmd(state, r, rest, negate):
    if len(rest) < 4:
        return INCOMPLETE
    ip, wc = _ip(rest[0]), _ip(rest[1])
    if ip is None or wc is None or pick(rest[2], ["area"]) != "area":
        return INVALID
    w = int(wc)
    if w & (w + 1) != 0:
        return INVALID
    area = _area(rest[3])
    if area is None:
        return INVALID
    entry = [str(ip), str(wc), area]
    nets = state["ospf"][r]["networks"]
    if negate:
        if entry in nets:
            nets.remove(entry)
        return ""
    if entry not in nets:
        nets.append(entry)
    return ""


def _command(state, r, cmd, rest, force_priv=False):
    ctx = state["ctx"][r]
    if cmd == "show":
        return _show(state, r, rest, priv=force_priv or state["modes"][r] != "user")
    if cmd == "ping":
        return _ping(state, r, rest)
    if cmd == "router":
        if not rest or pick(rest[0], ["ospf"]) != "ospf":
            return INVALID
        if len(rest) < 2 or not rest[1].isdigit() or not (1 <= int(rest[1]) <= 65535):
            return INCOMPLETE if len(rest) < 2 else INVALID
        pid = int(rest[1])
        cfg = state["ospf"][r]
        if cfg and cfg["pid"] != pid:
            return "% This simulator supports one OSPF process per router."
        if not cfg:
            state["ospf"][r] = {"pid": pid, "rid": None, "networks": [], "passive": []}
        state["ctx"][r] = ["ospf"]
        return ""
    if cmd == "interface":
        name = norm_iface(rest) if rest else None
        if not rest:
            return INCOMPLETE
        if name is None or name not in TOPO[r]:
            return INVALID
        state["ctx"][r] = ["if", name]
        return ""
    if cmd == "router-id":
        if not rest:
            return INCOMPLETE
        rid = _ip(rest[0])
        if rid is None:
            return INVALID
        state["ospf"][r]["rid"] = str(rid)
        return ""
    if cmd == "network":
        return _network_cmd(state, r, rest, negate=False)
    if cmd == "passive-interface":
        name = norm_iface(rest) if rest else None
        if not rest:
            return INCOMPLETE
        if name is None or name not in TOPO[r]:
            return INVALID
        if name not in state["ospf"][r]["passive"]:
            state["ospf"][r]["passive"].append(name)
        return ""
    if cmd == "ip":
        if ctx is None or ctx[0] != "if":
            return INVALID
        if not rest:
            return INCOMPLETE
        sub = pick(rest[0], ["ospf", "address"])
        if sub == "address":
            return "% IP addresses are already configured in this lab."
        if sub == "ospf":
            if len(rest) < 3 or pick(rest[1], ["cost"]) != "cost":
                return INCOMPLETE if len(rest) < 3 else INVALID
            if not rest[2].isdigit() or not (1 <= int(rest[2]) <= 65535):
                return INVALID
            state["cost"][r][ctx[1]] = int(rest[2])
            return ""
        return INVALID
    if cmd == "shutdown":
        if ctx is None or ctx[0] != "if":
            return INVALID
        if ctx[1] not in state["down"][r]:
            state["down"][r].append(ctx[1])
        return ""
    if cmd == "no":
        if not rest:
            return INCOMPLETE
        sub = pick(rest[0], ["network", "passive-interface", "shutdown", "ip"])
        if sub == "network" and ctx is not None and ctx[0] == "ospf":
            return _network_cmd(state, r, rest[1:], negate=True)
        if sub == "passive-interface" and ctx is not None and ctx[0] == "ospf":
            name = norm_iface(rest[1:]) if len(rest) > 1 else None
            if name in state["ospf"][r]["passive"]:
                state["ospf"][r]["passive"].remove(name)
            return ""
        if sub == "shutdown" and ctx is not None and ctx[0] == "if":
            if ctx[1] in state["down"][r]:
                state["down"][r].remove(ctx[1])
            return ""
        if sub == "ip" and ctx is not None and ctx[0] == "if":
            state["cost"][r].pop(ctx[1], None)
            return ""
    return INVALID


def execute(state, r, line):
    line = (line or "").strip()
    if not line:
        return ""
    if line in ("?", "help"):
        return "Available commands: " + ", ".join(_options(state, r))
    tokens = line.split()
    cmd = pick(tokens[0], _options(state, r))
    if cmd is None:
        return INVALID
    rest = tokens[1:]
    mode = state["modes"][r]

    if cmd == "enable":
        state["modes"][r] = "priv"
        return ""
    if cmd == "disable":
        state["modes"][r] = "user"
        return ""
    if cmd == "end":
        state["modes"][r], state["ctx"][r] = "priv", None
        return ""
    if cmd == "exit":
        if mode == "config":
            if state["ctx"][r] is not None:
                state["ctx"][r] = None
            else:
                state["modes"][r] = "priv"
        elif mode == "priv":
            state["modes"][r] = "user"
        else:
            return "(You cannot log out of user mode in this simulator.)"
        return ""
    if cmd == "configure":
        if not rest:
            return INCOMPLETE
        if pick(rest[0], ["terminal"]) != "terminal":
            return INVALID
        state["modes"][r], state["ctx"][r] = "config", None
        return "Enter configuration commands, one per line.  End with CNTL/Z."
    if cmd == "do":
        if not rest:
            return INCOMPLETE
        sub = pick(rest[0], ["show", "ping"])
        if sub is None:
            return INVALID
        return _command(state, r, sub, rest[1:], force_priv=True)
    return _command(state, r, cmd, rest)


# ---------- Lab checker ----------

def pc_ping(state, a, b):
    src_ip, src_router = HOSTS[a]
    dst_ip = HOSTS[b][0]
    fw = _walk(state, src_router, ipaddress.IPv4Address(dst_ip))
    if not fw["ok"]:
        return False, f"The request stopped at {fw['at']}: it has no route to {dst_ip}"
    ret = _walk(state, fw["at"], ipaddress.IPv4Address(src_ip))
    if not ret["ok"]:
        return False, f"The request arrived, but for the reply {ret['at']} has no route to {src_ip}"
    return True, "reachable"


def check(state):
    tasks = []
    for link in LINKS:
        ra, _ia, rb, _ib = link
        ok = _adjacent(state, link)
        tasks.append({"label": f"{ra} and {rb} are OSPF neighbours", "ok": ok,
                      "why": "" if ok else _why_not(state, link)})
    for a, b in PAIRS:
        ok, why = pc_ping(state, a, b)
        tasks.append({"label": f"{a} → {b}", "ok": ok, "why": why})
    passed = all(t["ok"] for t in tasks)
    route = next((t for t in routes_for(state, "R1")
                  if t["code"] == "O" and str(t["net"]) == "192.168.3.0/24"), None)
    bonus = bool(passed and route is not None and str(route["via"]) == "10.0.13.2")
    return {"tasks": tasks, "passed": passed, "bonus": bonus}