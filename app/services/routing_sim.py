import ipaddress

MAX_HOPS = 10   # stops routing loops (works like a TTL)

# ---- The sample network used by the simulators ----
# PC-A -- R1 -- R2 -- R3 -- ISP
ROUTERS = {
    "R1": {
        "host": "PC-A", "host_ip": "192.168.1.10",
        "interfaces": {"Gi0/0": "192.168.1.1/24", "Gi0/1": "10.0.12.1/30"},
        "static": [                      # (network, next hop)
            ("192.168.2.0/24", "10.0.12.2"),
            ("192.168.3.0/24", "10.0.12.2"),
            ("10.0.23.0/30", "10.0.12.2"),
            # R1 deliberately has no default route (useful for the labs)
        ],
    },
    "R2": {
        "host": "PC-B", "host_ip": "192.168.2.10",
        "interfaces": {"Gi0/0": "192.168.2.1/24", "Gi0/1": "10.0.12.2/30",
                       "Gi0/2": "10.0.23.1/30"},
        "static": [
            ("192.168.1.0/24", "10.0.12.1"),
            ("192.168.0.0/16", "10.0.23.2"),   # summary route (to demonstrate LPM)
            ("0.0.0.0/0", "10.0.23.2"),        # default route
        ],
    },
    "R3": {
        "host": "PC-C", "host_ip": "192.168.3.10",
        "interfaces": {"Gi0/0": "192.168.3.1/24", "Gi0/1": "10.0.23.2/30",
                       "Gi0/2": "203.0.113.1/30"},
        "static": [
            ("192.168.1.0/24", "10.0.23.1"),
            ("192.168.2.0/24", "10.0.23.1"),
            ("10.0.12.0/30", "10.0.23.1"),
            ("0.0.0.0/0", "203.0.113.2"),      # default route to the ISP
        ],
    },
}

ENDPOINTS = {"203.0.113.2": "ISP (Internet)"}

EXAMPLES = [
    {"label": "PC-A → PC-C", "start": "R1", "dest": "192.168.3.10"},
    {"label": "PC-C → PC-A", "start": "R3", "dest": "192.168.1.10"},
    {"label": "LPM example (R2 → 192.168.1.10)", "start": "R2", "dest": "192.168.1.10"},
    {"label": "Default route (R2 → 8.8.8.8)", "start": "R2", "dest": "8.8.8.8"},
    {"label": "No route (R1 → 8.8.8.8)", "start": "R1", "dest": "8.8.8.8"},
]

IFACES = {
    name: {i: ipaddress.IPv4Interface(a) for i, a in data["interfaces"].items()}
    for name, data in ROUTERS.items()
}


def router_choices():
    return [(n, f"{n} (router of {d['host']}, {d['host_ip']})") for n, d in ROUTERS.items()]


def owner_of(ip):
    """Finds which router owns an interface with this IP address."""
    for name, ifs in IFACES.items():
        if any(f.ip == ip for f in ifs.values()):
            return name
    return None


def build_table(name):
    """Builds a router's routing table: Connected (C) + Static (S / S*)."""
    table = []
    for iname, iface in IFACES[name].items():
        table.append({"code": "C", "network": iface.network, "via": None, "iface": iname})
    for net_text, via_text in ROUTERS[name]["static"]:
        net = ipaddress.IPv4Network(net_text)
        via = ipaddress.IPv4Address(via_text)
        out = next((i for i, f in IFACES[name].items() if via in f.network), "?")
        code = "S*" if net.prefixlen == 0 else "S"
        table.append({"code": code, "network": net, "via": via, "iface": out})
    # Longest prefixes first (like show ip route)
    table.sort(key=lambda r: (-r["network"].prefixlen, int(r["network"].network_address)))
    return table


def _target(r):
    if r["via"] is None:
        return f"directly connected, {r['iface']}"
    return f"via {r['via']}, {r['iface']}"


def _rows(table, matches=(), best=None):
    return [{
        "code": r["code"],
        "network": str(r["network"]),
        "target": _target(r),
        "matched": r in matches,
        "selected": best is not None and r is best,
    } for r in table]


def all_tables():
    out = {}
    for name in ROUTERS:
        out[name] = {
            "interfaces": [f"{i} – {f.with_prefixlen}" for i, f in IFACES[name].items()],
            "rows": _rows(build_table(name)),
        }
    return out


def walk(start, dest_text):
    if start not in ROUTERS:
        raise ValueError("Unknown router.")
    try:
        dest = ipaddress.IPv4Address((dest_text or "").strip())
    except ValueError:
        raise ValueError("Please enter a valid IPv4 address (for example 192.168.3.10).")

    hops = []
    path = [ROUTERS[start]["host"], start]
    current = start
    outcome = None

    for step in range(1, MAX_HOPS + 1):
        table = build_table(current)
        matches = [r for r in table if dest in r["network"]]
        # Longest Prefix Match: the matching route with the longest prefix wins
        best = max(matches, key=lambda r: r["network"].prefixlen) if matches else None

        hop = {
            "step": step,
            "router": current,
            "interfaces": [f"{i} – {f.with_prefixlen}" for i, f in IFACES[current].items()],
            "rows": _rows(table, matches, best),
            "matches": [str(r["network"]) for r in matches],
            "best": str(best["network"]) if best else None,
            "action": "",
        }
        hops.append(hop)

        # 1) No matching route -> drop
        if best is None:
            hop["action"] = "❌ No matching route. The packet is dropped (destination unreachable)."
            outcome = {"kind": "drop",
                       "text": f"❌ {current} has no route to {dest}, so the packet was dropped."}
            break

        # 2) Connected network -> delivery
        if best["code"] == "C":
            o = owner_of(dest)
            if o == current:
                hop["action"] = "✅ The destination IP is one of this router's own interfaces. The packet arrived."
                outcome = {"kind": "ok", "text": f"✅ The packet arrived at router {current}."}
            elif o:
                hop["action"] = (f"✅ The destination is an interface on {o}. "
                                 "It is reached over the directly connected link.")
                outcome = {"kind": "ok", "text": f"✅ The packet reached router {o}."}
                path.append(o)
            else:
                hop["action"] = (f"✅ {best['network']} is directly connected to {current}. "
                                 "The router uses ARP and sends the frame straight to the host.")
                outcome = {"kind": "ok", "text": f"✅ The packet was delivered to host {dest}."}
                path.append(str(dest))
            break

        # 3) Static route -> next hop
        nh = best["via"]
        if str(nh) in ENDPOINTS:
            hop["action"] = (f"➡️ Selected {best['network']} → next hop {nh} "
                             f"({ENDPOINTS[str(nh)]}). The packet leaves for the Internet.")
            extra = " (A private IP address would be dropped by the ISP.)" if dest.is_private else ""
            outcome = {"kind": "isp", "text": f"🌐 The packet was handed to the ISP.{extra}"}
            path.append("ISP (Internet)")
            break

        owner = owner_of(nh)
        if owner is None:
            hop["action"] = f"❌ Next hop {nh} is unreachable → the packet is dropped."
            outcome = {"kind": "drop", "text": f"❌ Next hop {nh} could not be found."}
            break

        hop["action"] = (f"➡️ Selected {best['network']} → next hop {nh} ({owner}) "
                         f"via {best['iface']}.")
        path.append(owner)
        current = owner
    else:
        outcome = {"kind": "ttl",
                   "text": f"🔁 After {MAX_HOPS} hops the packet had still not arrived. "
                           "This looks like a routing loop (TTL expired)."}

    return {"dest": str(dest), "start": start, "hops": hops, "path": path, "outcome": outcome}