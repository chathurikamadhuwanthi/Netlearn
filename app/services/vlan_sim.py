import ipaddress
import re

ROUTER_NAMES = ["SW1", "R1", "PC1", "PC2", "PC3", "PC4"]   # every device tab in this lab
SWITCH_PORTS = ["Fa0/1", "Fa0/2", "Fa0/3", "Fa0/4", "Gi0/1"]
TRUNK_PORT = "Gi0/1"
INVALID = "% Invalid input detected at '^' marker."
INCOMPLETE = "% Incomplete command."

PCS = {
    "PC1": {"ip": "192.168.10.11", "mask": "255.255.255.0", "gw": "192.168.10.1", "port": "Fa0/1"},
    "PC2": {"ip": "192.168.10.12", "mask": "255.255.255.0", "gw": "192.168.10.1", "port": "Fa0/2"},
    "PC3": {"ip": "192.168.20.11", "mask": "255.255.255.0", "gw": "192.168.20.1", "port": "Fa0/3"},
    "PC4": {"ip": "192.168.20.12", "mask": "255.255.255.0", "gw": "192.168.20.1", "port": "Fa0/4"},
}
EXPECTED = {"10": ("SALES", "192.168.10.1"), "20": ("HR", "192.168.20.1")}


# ---------- State and helpers ----------

def new_state():
    return {
        "modes": {"SW1": "user", "R1": "user"},
        "ctx": {"SW1": None, "R1": None},   # sub-mode: ["vlan","10"] / ["if","Fa0/1"] / ["range","Fa0/1,Fa0/2"] / ["subif","Gi0/0.10"]
        "vlans": {"1": "default"},
        "ports": {p: {"mode": "access", "vlan": 1, "allowed": None, "native": 1, "up": True}
                  for p in SWITCH_PORTS},
        "r_up": False,                      # R1 GigabitEthernet0/0 starts shut down
        "subifs": {},                       # name -> {"vlan", "ip", "mask"}
    }


def long_name(name):
    return name.replace("Fa", "FastEthernet", 1).replace("Gi", "GigabitEthernet", 1)


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


def norm_iface(tokens):
    """['fastEthernet', '0/1'] or ['fa0/1'] -> 'Fa0/1'. Also Gi0/1 and Gi0/0.10."""
    text = "".join(tokens).lower()
    m = re.fullmatch(r"(fastethernet|fa|f|gigabitethernet|gi|g)(\d+/\d+)(?:\.(\d+))?", text)
    if not m:
        return None
    name = ("Fa" if m.group(1).startswith("f") else "Gi") + m.group(2)
    if m.group(3):
        name += "." + m.group(3)
    return name


def _vlan_id(text):
    if not text.isdigit():
        return None
    v = int(text)
    return v if 1 <= v <= 4094 else None


def _expand(spec):
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            if not (a.isdigit() and b.isdigit()):
                return None
            a, b = int(a), int(b)
            if not (1 <= a <= b <= 4094):
                return None
            out.update(range(a, b + 1))
        elif part.isdigit() and 1 <= int(part) <= 4094:
            out.add(int(part))
        else:
            return None
    return out


def _compress(vlans):
    nums = sorted(vlans)
    parts, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        parts.append(str(nums[i]) if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ",".join(parts)


def _allowed(spec, vid):
    if spec is None:
        return True
    return vid in (_expand(spec) if spec else set())


def _names(ctx):
    return [ctx[1]] if ctx[0] == "if" else ctx[1].split(",")


def prompt(state, dev):
    if dev not in ("SW1", "R1"):
        return f"{dev}>"
    mode, ctx = state["modes"][dev], state["ctx"][dev]
    if mode == "user":
        return f"{dev}>"
    if mode == "priv":
        return f"{dev}#"
    if ctx is None:
        return f"{dev}(config)#"
    suffix = {"vlan": "config-vlan", "if": "config-if",
              "range": "config-if-range", "subif": "config-subif"}[ctx[0]]
    return f"{dev}({suffix})#"


def _options(state, dev):
    mode, ctx = state["modes"][dev], state["ctx"][dev]
    if dev == "SW1":
        if mode == "user":
            return ["enable", "show", "exit"]
        if mode == "priv":
            return ["configure", "show", "disable", "exit"]
        if ctx is None:
            return ["vlan", "no", "interface", "do", "exit", "end"]
        if ctx[0] == "vlan":
            return ["name", "vlan", "interface", "do", "exit", "end"]
        return ["switchport", "shutdown", "no", "vlan", "interface", "do", "exit", "end"]
    if mode == "user":
        return ["enable", "show", "ping", "exit"]
    if mode == "priv":
        return ["configure", "show", "ping", "disable", "exit"]
    if ctx is None:
        return ["interface", "do", "exit", "end"]
    return ["encapsulation", "ip", "no", "shutdown", "interface", "do", "exit", "end"]


# ---------- Layer 2 / Layer 3 reachability ----------

def _port_vlan(state, port):
    """VLAN of an access port, or None if the port is down, a trunk, or its VLAN does not exist."""
    p = state["ports"][port]
    if not p["up"] or p["mode"] != "access":
        return None
    return p["vlan"] if str(p["vlan"]) in state["vlans"] else None


def _port_msg(pc):
    return (f"{pc}'s switch port ({PCS[pc]['port']}) is shut down, is not an access port, "
            "or its VLAN does not exist.")


def _trunk_problem(state, vid):
    p = state["ports"][TRUNK_PORT]
    if not p["up"]:
        return f"The trunk port {TRUNK_PORT} is shut down."
    if p["mode"] != "trunk":
        return f"{TRUNK_PORT} is not a trunk. Use 'switchport mode trunk'."
    if str(vid) not in state["vlans"]:
        return f"VLAN {vid} does not exist on the switch."
    if p["native"] == vid:
        return (f"VLAN {vid} is the native VLAN of the trunk, so its frames are untagged "
                "and the router subinterface will not see them.")
    if not _allowed(p["allowed"], vid):
        return f"VLAN {vid} is not in the allowed VLAN list of the trunk."
    return None


def _sub_for_ip(state, ip):
    for name, s in state["subifs"].items():
        if s["ip"] and s["vlan"] is not None:
            if ip in ipaddress.IPv4Interface(f"{s['ip']}/{s['mask']}").network:
                return name, s
    return None


def _router_reach(state, dest):
    """Can R1 reach this address? Returns (ok, tip)."""
    for s in state["subifs"].values():
        if s["ip"] == str(dest):
            return (True, "") if state["r_up"] else (False, "R1's GigabitEthernet0/0 is shut down.")
    if not state["r_up"]:
        return False, "R1's GigabitEthernet0/0 is shut down. Use 'no shutdown' on it."
    found = _sub_for_ip(state, dest)
    if found is None:
        return False, f"R1 has no connected network that contains {dest}. Check the subinterface addresses."
    name, s = found
    host = next((p for p, c in PCS.items() if c["ip"] == str(dest)), None)
    if host is None:
        return False, f"No device has the address {dest}."
    problem = _trunk_problem(state, s["vlan"])
    if problem:
        return False, problem
    hv = _port_vlan(state, PCS[host]["port"])
    if hv is None:
        return False, _port_msg(host)
    if hv != s["vlan"]:
        return False, f"{host} is in VLAN {hv}, but {name} serves VLAN {s['vlan']}."
    return True, ""


def _reach_gateway(state, src):
    pc = PCS[src]
    gw = pc["gw"]
    if not state["r_up"]:
        return False, "R1's GigabitEthernet0/0 is shut down. Use 'no shutdown' on it."
    found = next(((n, s) for n, s in state["subifs"].items() if s["ip"] == gw), None)
    if found is None:
        return False, f"No router subinterface has the gateway address {gw} that {src} uses."
    name, s = found
    if ipaddress.IPv4Address(pc["ip"]) not in ipaddress.IPv4Interface(f"{s['ip']}/{s['mask']}").network:
        return False, f"The subnet mask on {name} does not match {src}'s network."
    sv = _port_vlan(state, pc["port"])
    if sv is None:
        return False, _port_msg(src)
    if sv != s["vlan"]:
        return False, f"{src} is in VLAN {sv}, but its gateway {gw} (on {name}) serves VLAN {s['vlan']}."
    problem = _trunk_problem(state, s["vlan"])
    if problem:
        return False, problem
    return True, ""


def _pc_reach(state, src, dest):
    """Can this PC reach dest? Returns (ok, tip)."""
    pc = PCS[src]
    if str(dest) == pc["ip"]:
        return True, ""
    local = ipaddress.IPv4Interface(f"{pc['ip']}/{pc['mask']}").network
    sv = _port_vlan(state, pc["port"])
    if dest in local:                                   # same network: pure Layer 2
        target = next((p for p, c in PCS.items() if c["ip"] == str(dest)), None)
        if target is None:
            return False, f"No device on this network has the address {dest}."
        if sv is None:
            return False, _port_msg(src)
        tv = _port_vlan(state, PCS[target]["port"])
        if tv is None:
            return False, _port_msg(target)
        if sv != tv:
            return False, (f"{src} is in VLAN {sv} but {target} is in VLAN {tv}. "
                           "Devices in different VLANs cannot talk to each other without a router.")
        return True, ""
    ok, why = _reach_gateway(state, src)                # other network: through the gateway
    if not ok:
        return False, why
    ok, why = _router_reach(state, dest)
    if not ok:
        return False, why
    target = next((p for p, c in PCS.items() if c["ip"] == str(dest)), None)
    if target and target != src:
        ok, why = _reach_gateway(state, target)         # the reply must be able to come back
        if not ok:
            return False, "The request arrives, but the reply cannot return. " + why
    return True, ""


# ---------- Switch ----------

def _sw_show(state, rest, priv):
    if not rest:
        return INCOMPLETE
    sub = pick(rest[0], ["vlan", "interfaces", "running-config"])
    if sub == "vlan":
        lines = ["VLAN Name                             Status    Ports",
                 "---- -------------------------------- --------- -------------------------------"]
        for vid in sorted(state["vlans"], key=int):
            ports = [p for p in SWITCH_PORTS
                     if state["ports"][p]["mode"] == "access" and str(state["ports"][p]["vlan"]) == vid]
            lines.append(f"{vid:<4} {state['vlans'][vid]:<32} active    {', '.join(ports)}")
        return "\n".join(lines)
    if sub == "interfaces":
        if len(rest) < 2 or pick(rest[1], ["trunk"]) != "trunk":
            return INCOMPLETE
        trunks = [p for p in SWITCH_PORTS if state["ports"][p]["mode"] == "trunk"]
        if not trunks:
            return ""
        lines = ["Port        Mode         Encapsulation  Status        Native vlan"]
        for p in trunks:
            c = state["ports"][p]
            status = "trunking" if c["up"] else "not-trunking"
            lines.append(f"{p:<11} {'on':<12} {'802.1q':<14} {status:<13} {c['native']}")
        lines += ["", "Port        Vlans allowed on trunk"]
        for p in trunks:
            a = state["ports"][p]["allowed"]
            lines.append(f"{p:<11} {'1-4094' if a is None else (a or 'none')}")
        return "\n".join(lines)
    if sub == "running-config":
        if not priv:
            return INVALID
        lines = ["Building configuration...", "", "!", "hostname SW1", "!"]
        for vid in sorted(state["vlans"], key=int):
            if vid != "1":
                lines += [f"vlan {vid}", f" name {state['vlans'][vid]}", "!"]
        for p in SWITCH_PORTS:
            c = state["ports"][p]
            lines.append(f"interface {long_name(p)}")
            if c["mode"] == "trunk":
                lines.append(" switchport mode trunk")
                if c["native"] != 1:
                    lines.append(f" switchport trunk native vlan {c['native']}")
                if c["allowed"] is not None:
                    lines.append(f" switchport trunk allowed vlan {c['allowed'] or 'none'}")
            else:
                lines.append(" switchport mode access")
                if c["vlan"] != 1:
                    lines.append(f" switchport access vlan {c['vlan']}")
            if not c["up"]:
                lines.append(" shutdown")
            lines.append("!")
        lines.append("end")
        return "\n".join(lines)
    return INVALID


def _sw_interface(state, rest):
    if not rest:
        return INCOMPLETE
    if pick(rest[0], ["range"]) == "range":
        text = "".join(rest[1:]).lower()
        m = re.fullmatch(r"(?:fastethernet|fa|f)0/(\d+)-(?:(?:fastethernet|fa|f)0/)?(\d+)", text)
        if not m:
            return INVALID
        a, b = int(m.group(1)), int(m.group(2))
        names = [f"Fa0/{i}" for i in range(a, b + 1)]
        if a > b or any(n not in SWITCH_PORTS for n in names):
            return INVALID
        state["ctx"]["SW1"] = ["range", ",".join(names)]
        return ""
    name = norm_iface(rest)
    if name is None or name not in SWITCH_PORTS:
        return INVALID
    state["ctx"]["SW1"] = ["if", name]
    return ""


def _sw_switchport(state, rest):
    ctx = state["ctx"]["SW1"]
    names = _names(ctx)
    if not rest:
        return INCOMPLETE
    sub = pick(rest[0], ["mode", "access", "trunk"])
    if sub == "mode":
        if len(rest) < 2:
            return INCOMPLETE
        m = pick(rest[1], ["access", "trunk"])
        if m is None:
            return INVALID
        for n in names:
            state["ports"][n]["mode"] = m
        return ""
    if sub == "access":
        if len(rest) < 3:
            return INCOMPLETE
        if pick(rest[1], ["vlan"]) != "vlan":
            return INVALID
        vid = _vlan_id(rest[2])
        if vid is None:
            return INVALID
        out = ""
        if str(vid) not in state["vlans"]:
            state["vlans"][str(vid)] = f"VLAN{vid:04d}"
            out = f"% Access VLAN does not exist. Creating vlan {vid}"
        for n in names:
            state["ports"][n]["vlan"] = vid
        return out
    if sub == "trunk":
        if len(rest) < 3:
            return INCOMPLETE
        kind = pick(rest[1], ["allowed", "native"])
        if pick(rest[2], ["vlan"]) != "vlan":
            return INVALID
        args = rest[3:]
        if kind == "native":
            if not args:
                return INCOMPLETE
            vid = _vlan_id(args[0])
            if vid is None:
                return INVALID
            for n in names:
                state["ports"][n]["native"] = vid
            return ""
        if kind == "allowed":
            if not args:
                return INCOMPLETE
            word = args[0].lower()
            if word == "remove":
                return "% 'remove' is not supported in this simulator. Use a full list instead."
            if word == "add":
                if len(args) < 2:
                    return INCOMPLETE
                extra = _expand(args[1])
                if extra is None:
                    return INVALID
                for n in names:
                    cur = state["ports"][n]["allowed"]
                    if cur is not None:
                        state["ports"][n]["allowed"] = _compress((_expand(cur) if cur else set()) | extra)
                return ""
            if word == "all":
                new = None
            elif word == "none":
                new = ""
            else:
                s = _expand("".join(args))
                if s is None:
                    return INVALID
                new = _compress(s)
            for n in names:
                state["ports"][n]["allowed"] = new
            return ""
    return INVALID


def _sw_command(state, cmd, rest, force_priv=False):
    ctx = state["ctx"]["SW1"]
    if cmd == "show":
        return _sw_show(state, rest, priv=force_priv or state["modes"]["SW1"] != "user")
    if cmd == "vlan":
        if not rest:
            return INCOMPLETE
        vid = _vlan_id(rest[0])
        if vid is None:
            return INVALID
        state["vlans"].setdefault(str(vid), f"VLAN{vid:04d}")
        state["ctx"]["SW1"] = ["vlan", str(vid)]
        return ""
    if cmd == "name":
        if ctx is None or ctx[0] != "vlan":
            return INVALID
        if not rest:
            return INCOMPLETE
        state["vlans"][ctx[1]] = rest[0][:32]
        return ""
    if cmd == "interface":
        return _sw_interface(state, rest)
    if cmd == "switchport":
        if ctx is None or ctx[0] not in ("if", "range"):
            return INVALID
        return _sw_switchport(state, rest)
    if cmd == "shutdown":
        if ctx is None or ctx[0] not in ("if", "range"):
            return INVALID
        for n in _names(ctx):
            state["ports"][n]["up"] = False
        return ""
    if cmd == "no":
        if not rest:
            return INCOMPLETE
        sub = pick(rest[0], ["shutdown", "vlan"])
        if sub == "shutdown":
            if ctx is None or ctx[0] not in ("if", "range"):
                return INVALID
            for n in _names(ctx):
                state["ports"][n]["up"] = True
            return ""
        if sub == "vlan":
            if len(rest) < 2:
                return INCOMPLETE
            vid = _vlan_id(rest[1])
            if vid is None or vid == 1:
                return INVALID
            state["vlans"].pop(str(vid), None)
            return ""
    return INVALID


# ---------- Router ----------

def _r_show(state, rest, priv):
    if not rest:
        return INCOMPLETE
    sub = pick(rest[0], ["ip", "running-config"])
    if sub == "running-config":
        if not priv:
            return INVALID
        lines = ["Building configuration...", "", "!", "hostname R1", "!",
                 "interface GigabitEthernet0/0", " no ip address",
                 " no shutdown" if state["r_up"] else " shutdown", "!"]
        for name in sorted(state["subifs"], key=lambda n: int(n.split(".")[1])):
            s = state["subifs"][name]
            lines.append(f"interface {long_name(name)}")
            if s["vlan"] is not None:
                lines.append(f" encapsulation dot1Q {s['vlan']}")
            if s["ip"]:
                lines.append(f" ip address {s['ip']} {s['mask']}")
            lines.append("!")
        lines.append("end")
        return "\n".join(lines)
    if sub == "ip":
        if len(rest) < 2:
            return INCOMPLETE
        what = pick(rest[1], ["interface", "route"])
        if what == "interface":
            if len(rest) < 3 or pick(rest[2], ["brief"]) != "brief":
                return INCOMPLETE
            status = "up" if state["r_up"] else "administratively down"
            proto = "up" if state["r_up"] else "down"
            lines = ["Interface                  IP-Address      OK? Method Status                Protocol",
                     f"{'GigabitEthernet0/0':<26} {'unassigned':<15} YES unset  {status:<21} {proto}"]
            for name in sorted(state["subifs"], key=lambda n: int(n.split(".")[1])):
                s = state["subifs"][name]
                lines.append(f"{long_name(name):<26} {s['ip'] or 'unassigned':<15} YES manual {status:<21} {proto}")
            return "\n".join(lines)
        if what == "route":
            lines = ["Codes: C - connected, L - local", "", "Gateway of last resort is not set", ""]
            if state["r_up"]:
                rows = []
                for name, s in state["subifs"].items():
                    if s["ip"] is None:
                        continue
                    net = ipaddress.IPv4Interface(f"{s['ip']}/{s['mask']}").network
                    key = int(net.network_address)
                    rows.append((key, 0, f"C    {net} is directly connected, {long_name(name)}"))
                    rows.append((key, 1, f"L    {s['ip']}/32 is directly connected, {long_name(name)}"))
                lines += [t for _, _, t in sorted(rows)]
            return "\n".join(lines)
    return INVALID


def _r_ping(state, args):
    if not args:
        return INCOMPLETE
    dest = _ip(args[0])
    if dest is None:
        return "% Unrecognized host or address, or protocol not running."
    ok, tip = _router_reach(state, dest)
    lines = ["Type escape sequence to abort.",
             f"Sending 5, 100-byte ICMP Echos to {dest}, timeout is 2 seconds:",
             "!!!!!" if ok else "....."]
    if ok:
        lines.append("Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms")
    else:
        lines += ["Success rate is 0 percent (0/5)", f"[NetLearn tip] {tip}"]
    return "\n".join(lines)


def _r_interface(state, rest):
    if not rest:
        return INCOMPLETE
    name = norm_iface(rest)
    if name is None or name.split(".")[0] != "Gi0/0":
        return INVALID
    if "." in name:
        sub = name.split(".")[1]
        if not (sub.isdigit() and 1 <= int(sub) <= 4094):
            return INVALID
        state["subifs"].setdefault(name, {"vlan": None, "ip": None, "mask": None})
        state["ctx"]["R1"] = ["subif", name]
    else:
        state["ctx"]["R1"] = ["if", name]
    return ""


def _r_command(state, cmd, rest, force_priv=False):
    ctx = state["ctx"]["R1"]
    if cmd == "show":
        return _r_show(state, rest, priv=force_priv or state["modes"]["R1"] != "user")
    if cmd == "ping":
        return _r_ping(state, rest)
    if cmd == "interface":
        return _r_interface(state, rest)
    if cmd == "encapsulation":
        if ctx is None or ctx[0] != "subif":
            return INVALID
        if not rest:
            return INCOMPLETE
        if rest[0].lower() != "dot1q" or len(rest) < 2:
            return INVALID
        vid = _vlan_id(rest[1])
        if vid is None:
            return INVALID
        state["subifs"][ctx[1]]["vlan"] = vid
        return ""
    if cmd == "ip":
        if ctx is None or ctx[0] != "subif":
            return INVALID
        if not rest or pick(rest[0], ["address"]) != "address":
            return INVALID
        if len(rest) < 3:
            return INCOMPLETE
        ip, mask = _ip(rest[1]), _ip(rest[2])
        if ip is None or mask is None:
            return INVALID
        try:
            ipaddress.IPv4Interface(f"{ip}/{mask}")
        except ValueError:
            return INVALID
        sub = state["subifs"][ctx[1]]
        if sub["vlan"] is None:
            return ("% Configuring IP routing on a LAN subinterface is only allowed if that "
                    "subinterface is already configured as part of an 802.1Q VLAN. "
                    "Use 'encapsulation dot1Q <vlan>' first.")
        sub["ip"], sub["mask"] = str(ip), str(mask)
        return ""
    if cmd == "shutdown":
        if ctx is not None and ctx[0] == "if":
            state["r_up"] = False
        return ""
    if cmd == "no":
        if not rest:
            return INCOMPLETE
        sub = pick(rest[0], ["shutdown", "ip"])
        if sub == "shutdown":
            if ctx is not None and ctx[0] == "if":
                state["r_up"] = True
            return ""
        if sub == "ip" and ctx is not None and ctx[0] == "subif":
            state["subifs"][ctx[1]]["ip"] = None
            state["subifs"][ctx[1]]["mask"] = None
            return ""
    return INVALID


# ---------- PCs ----------

def _pc_execute(state, dev, line):
    tokens = line.split()
    cmd = tokens[0].lower()
    pc = PCS[dev]
    if cmd in ("?", "help"):
        return "Commands: ping <ip address>, ipconfig"
    if cmd == "ipconfig":
        return "\n".join(["Ethernet adapter:",
                          f"   IPv4 Address. . . . . : {pc['ip']}",
                          f"   Subnet Mask . . . . . : {pc['mask']}",
                          f"   Default Gateway . . . : {pc['gw']}"])
    if cmd == "ping":
        if len(tokens) < 2:
            return "Usage: ping <ip address>"
        dest = _ip(tokens[1])
        if dest is None:
            return f"Ping request could not find host {tokens[1]}. Please check the name and try again."
        ok, why = _pc_reach(state, dev, dest)
        lines = [f"Pinging {dest} with 32 bytes of data:", ""]
        lines += [f"Reply from {dest}: bytes=32 time<1ms TTL=128" if ok else "Request timed out."] * 4
        lines += ["", f"Ping statistics for {dest}:",
                  f"    Packets: Sent = 4, Received = {4 if ok else 0}, Lost = {0 if ok else 4} "
                  f"({0 if ok else 100}% loss)"]
        if not ok:
            lines.append(f"[NetLearn tip] {why}")
        return "\n".join(lines)
    return f"'{tokens[0]}' is not recognized as a command. Type ? for help."


# ---------- Entry point used by the lab page ----------

def _common(state, dev, cmd, rest):
    mode = state["modes"][dev]
    if cmd == "enable":
        state["modes"][dev] = "priv"
        return ""
    if cmd == "disable":
        state["modes"][dev] = "user"
        return ""
    if cmd == "end":
        state["modes"][dev], state["ctx"][dev] = "priv", None
        return ""
    if cmd == "exit":
        if mode == "config":
            if state["ctx"][dev] is not None:
                state["ctx"][dev] = None
            else:
                state["modes"][dev] = "priv"
        elif mode == "priv":
            state["modes"][dev] = "user"
        else:
            return "(You cannot log out of user mode in this simulator.)"
        return ""
    if cmd == "configure":
        if not rest:
            return INCOMPLETE
        if pick(rest[0], ["terminal"]) != "terminal":
            return INVALID
        state["modes"][dev], state["ctx"][dev] = "config", None
        return "Enter configuration commands, one per line.  End with CNTL/Z."
    if cmd == "do":
        if not rest:
            return INCOMPLETE
        sub = pick(rest[0], ["show", "ping"])
        if sub is None:
            return INVALID
        if dev == "SW1":
            return _sw_command(state, sub, rest[1:], force_priv=True) if sub == "show" else INVALID
        return _r_command(state, sub, rest[1:], force_priv=True)
    return None


def execute(state, dev, line):
    line = (line or "").strip()
    if not line:
        return ""
    if dev.startswith("PC"):
        return _pc_execute(state, dev, line)
    if line in ("?", "help"):
        return "Available commands: " + ", ".join(_options(state, dev))
    tokens = line.split()
    cmd = pick(tokens[0], _options(state, dev))
    if cmd is None:
        return INVALID
    rest = tokens[1:]
    out = _common(state, dev, cmd, rest)
    if out is not None:
        return out
    return _sw_command(state, cmd, rest) if dev == "SW1" else _r_command(state, cmd, rest)


# ---------- Lab checker ----------

def check(state):
    tasks = []

    def add(label, ok, why=""):
        tasks.append({"label": label, "ok": ok, "why": why})

    for vid, (name, _gw) in EXPECTED.items():
        have = state["vlans"].get(vid)
        add(f"VLAN {vid} exists and is named {name}", have == name,
            f"VLAN {vid} does not exist yet" if have is None else f"Its name is '{have}', expected '{name}'")

    for pc, vid in (("PC1", "10"), ("PC2", "10"), ("PC3", "20"), ("PC4", "20")):
        port = PCS[pc]["port"]
        c = state["ports"][port]
        add(f"{port} ({pc}) is an access port in VLAN {vid}",
            c["mode"] == "access" and str(c["vlan"]) == vid,
            f"It is currently a {c['mode']} port in VLAN {c['vlan']}")

    t = state["ports"][TRUNK_PORT]
    add(f"{TRUNK_PORT} is a trunk that carries VLANs 10 and 20",
        t["mode"] == "trunk" and _allowed(t["allowed"], 10) and _allowed(t["allowed"], 20),
        f"It is currently a {t['mode']} port")

    for vid, (_name, gw) in EXPECTED.items():
        sub = state["subifs"].get(f"Gi0/0.{vid}")
        ok = bool(state["r_up"] and sub and sub["vlan"] == int(vid)
                  and sub["ip"] == gw and sub["mask"] == "255.255.255.0")
        add(f"R1 Gi0/0.{vid} uses dot1Q {vid} with the address {gw}/24", ok,
            "Check that Gi0/0 is up and that the subinterface has the right encapsulation and address")

    for a, b in (("PC1", "PC2"), ("PC3", "PC4"), ("PC1", "PC3"), ("PC4", "PC2")):
        ok, why = _pc_reach(state, a, ipaddress.IPv4Address(PCS[b]["ip"]))
        add(f"{a} can ping {b}", ok, why)

    passed = all(x["ok"] for x in tasks)
    bonus = passed and t["allowed"] == "10,20" and t["native"] == 99
    return {"tasks": tasks, "passed": passed, "bonus": bonus}