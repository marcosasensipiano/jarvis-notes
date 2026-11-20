"""Wi-Fi/LAN awareness: who is on the network, and which of them look like a TV.
Read-only discovery. Jarvis does not join networks, scan ports or touch devices it doesn't own."""
import re
import shutil
import socket
import subprocess
import time


def parse_ssdp(data: bytes) -> dict:
    headers = {}
    for line in data.decode("utf-8", "replace").split("\r\n")[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return headers


def classify(text: str) -> str:
    t = text.lower()
    for key, kind in (("roku", "roku"), ("samsung", "samsung"), ("webos", "lg"), ("lge", "lg"),
                      ("android", "android_tv"), ("googlecast", "cast"), ("chromecast", "cast"),
                      ("amazon", "fire_tv"), ("sonos", "sonos"), ("philips", "hue")):
        if key in t:
            return kind
    return "unknown"


def ssdp_discover(timeout: float = 3.0) -> dict:
    msg = "\r\n".join(["M-SEARCH * HTTP/1.1", "HOST: 239.255.255.250:1900", 'MAN: "ssdp:discover"',
                       "MX: 2", "ST: ssdp:all", "", ""]).encode()
    found = {}
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(0.5)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(msg, ("239.255.255.250", 1900))
    except OSError:
        return found
    end = time.time() + timeout
    while time.time() < end:
        try:
            data, (ip, _) = sock.recvfrom(65507)
        except socket.timeout:
            continue
        except OSError:
            break
        h = parse_ssdp(data)
        blob = " ".join(h.values())
        cur = found.setdefault(ip, {"kind": "unknown", "server": "", "location": ""})
        kind = classify(blob)
        if kind != "unknown":
            cur["kind"] = kind
        cur["server"] = cur["server"] or h.get("server", "")
        cur["location"] = cur["location"] or h.get("location", "")
    sock.close()
    return found


_IP_NEIGH = re.compile(r"^(\d+\.\d+\.\d+\.\d+)\s.*?lladdr\s+([0-9a-f:]{17})", re.I)
_ARP = re.compile(r"\((\d+\.\d+\.\d+\.\d+)\) at ([0-9a-f:]{11,17})", re.I)


def parse_neighbors(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = _IP_NEIGH.match(line) or _ARP.search(line)
        if m:
            out[m.group(1)] = m.group(2).lower()
    return out


def _run(*cmd):
    if not shutil.which(cmd[0]):
        return ""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def neighbors() -> dict:
    return parse_neighbors(_run("ip", "-4", "neigh") or _run("arp", "-an"))


def wifi_status() -> dict:
    ssid = _run("iwgetid", "-r").strip()
    if not ssid:
        for line in _run("nmcli", "-t", "-f", "active,ssid", "dev", "wifi").splitlines():
            if line.startswith("yes:"):
                ssid = line[4:]
    if not ssid:
        out = _run("networksetup", "-getairportnetwork", "en0")
        ssid = out.split(": ", 1)[1].strip() if ": " in out else ""
    return {"ssid": ssid or "unknown"}
