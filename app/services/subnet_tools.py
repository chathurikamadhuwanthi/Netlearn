import ipaddress
import re
from itertools import islice

MAX_SUBNETS_SHOWN = 64   # If there are many subnets, only the first 64 are shown


def parse_address(text):
    """Accepts both '192.168.1.10/24' and '192.168.1.10 255.255.255.0'."""
    text = re.sub(r"\s*/\s*", "/", (text or "").strip())
    if not text:
        raise ValueError("Please enter an IP address.")

    if "/" in text:
        raw = text
    else:
        parts = text.split()
        if len(parts) != 2:
            raise ValueError("Invalid format. Example: 192.168.1.10/24 or 192.168.1.10 255.255.255.0")
        raw = f"{parts[0]}/{parts[1]}"

    try:
        return ipaddress.IPv4Interface(raw)
    except ValueError:
        raise ValueError("Not a valid IPv4 address / mask. (Example: 192.168.1.10/24)")


def ip_class(ip):
    first = int(str(ip).split(".")[0])
    if first == 0:
        return "N/A"
    if first <= 126:
        return "Class A"
    if first == 127:
        return "Loopback"
    if first <= 191:
        return "Class B"
    if first <= 223:
        return "Class C"
    if first <= 239:
        return "Class D (Multicast)"
    return "Class E (Experimental)"


def ip_type(ip):
    if ip.is_loopback:
        return "Loopback"
    if ip.is_link_local:
        return "Link-local (APIPA)"
    if ip.is_multicast:
        return "Multicast"
    if ip.is_private:
        return "Private"
    if ip.is_unspecified or ip.is_reserved:
        return "Reserved / Special"
    return "Public"


def colored_binary(addr, prefix):
    """Split the binary form into 4 octets and separate network bits from host bits."""
    out = []
    for i, octet in enumerate(str(addr).split(".")):
        bits = f"{int(octet):08b}"
        n = max(0, min(8, prefix - i * 8))   # Number of network bits in this octet
        out.append({"net": bits[:n], "host": bits[n:]})
    return out


def _range(net):
    """Calculate the key addresses of a network."""
    p = net.prefixlen
    if p == 32:     # A single host
        a = str(net.network_address)
        return {"network": a, "broadcast": "—", "first": a, "last": a, "usable": 1}
    if p == 31:     # Point-to-point link (RFC 3021)
        return {"network": str(net.network_address), "broadcast": "—",
                "first": str(net.network_address), "last": str(net.broadcast_address), "usable": 2}
    return {
        "network": str(net.network_address),
        "broadcast": str(net.broadcast_address),
        "first": str(net.network_address + 1),
        "last": str(net.broadcast_address - 1),
        "usable": net.num_addresses - 2,    # Subtract the network and broadcast addresses
    }


def analyze(text, new_prefix_text=""):
    iface = parse_address(text)
    net = iface.network
    prefix = net.prefixlen
    info = _range(net)

    notes = []
    if prefix == 32:
        notes.append("/32 is a single host address only (e.g. a router loopback).")
    if prefix == 31:
        notes.append("/31 is used for point-to-point links between two routers (there is no broadcast address).")

    result = {
        "ip": str(iface.ip),
        "prefix": prefix,
        "mask": str(net.netmask),
        "wildcard": str(net.hostmask),
        "host_bits": 32 - prefix,
        "total": net.num_addresses,
        "ip_class": ip_class(iface.ip),
        "ip_type": ip_type(iface.ip),
        "ip_bits": colored_binary(iface.ip, prefix),
        "mask_bits": colored_binary(net.netmask, prefix),
        "notes": notes,
        "split": None,
        **info,
    }

    # If the user wants to split into subnets
    new_prefix_text = (new_prefix_text or "").strip().lstrip("/")
    if new_prefix_text:
        if not new_prefix_text.isdigit():
            raise ValueError("The new prefix must be a number. (Example: 26)")
        new_prefix = int(new_prefix_text)
        if not (prefix < new_prefix <= 32):
            raise ValueError(f"The new prefix must be larger than /{prefix} and at most 32.")

        rows = []
        for sn in islice(net.subnets(new_prefix=new_prefix), MAX_SUBNETS_SHOWN):
            r = _range(sn)
            r["cidr"] = f"{sn.network_address}/{new_prefix}"
            rows.append(r)

        result["split"] = {
            "new_prefix": new_prefix,
            "new_mask": str(ipaddress.IPv4Network(f"0.0.0.0/{new_prefix}").netmask),
            "total": 2 ** (new_prefix - prefix),
            "shown": len(rows),
            "usable": rows[0]["usable"],
            "rows": rows,
        }

    return result