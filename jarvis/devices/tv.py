"""TV drivers. One canonical action vocabulary; each driver translates it for a protocol.

Types for config/devices.json -> {"tv": {"type": ..., "host": ...}}:
  roku     Roku TVs and sticks over the LAN (HTTP, port 8060). Volume/power only on Roku TVs.
  adb      Android TV / Google TV / Fire TV / Shield (enable network debugging; needs `adb` installed).
  cec      HDMI-CEC power on/standby via `cec-client` (e.g. a Raspberry Pi plugged into the TV).
  dryrun   Prints actions. Safe for testing gestures.
  samsung  Samsung Tizen TVs (QLED/Neo QLED/Frame/Crystal, 2016+) over a secure WebSocket on port 8002.
           The first command makes the TV ask "Allow?"; the pairing token is then saved in data/.
           Optional "mac" lets `power` wake the TV from standby with Wake-on-LAN.
LG (webOS) is not built yet: it is on Jarvis's learning backlog."""
import base64
import json
import shutil
import socket
import subprocess
import urllib.request
from urllib.parse import quote

from .. import paths
from .wsclient import WebSocket, WSError

ACTIONS = ["power", "volume_up", "volume_down", "mute", "play_pause", "home", "back",
           "up", "down", "left", "right", "select", "forward", "rewind"]


class TV:
    def send(self, action: str) -> str:
        raise NotImplementedError

    def _check(self, action):
        if action not in ACTIONS:
            raise ValueError(f"unknown TV action: {action}")


class DryRunTV(TV):
    def send(self, action):
        self._check(action)
        return f"[dry-run] TV <- {action}"


class RokuTV(TV):
    KEYS = {"power": "Power", "volume_up": "VolumeUp", "volume_down": "VolumeDown", "mute": "VolumeMute",
            "play_pause": "Play", "home": "Home", "back": "Back", "up": "Up", "down": "Down",
            "left": "Left", "right": "Right", "select": "Select", "forward": "Fwd", "rewind": "Rev"}

    def __init__(self, host, port=8060, timeout=3):
        self.base, self.timeout = f"http://{host}:{port}", timeout

    def send(self, action):
        self._check(action)
        req = urllib.request.Request(f"{self.base}/keypress/{self.KEYS[action]}", data=b"", method="POST")
        try:
            urllib.request.urlopen(req, timeout=self.timeout).read()
        except OSError as e:
            return f"Roku didn't answer ({e}). Is it on the same Wi-Fi? Run `jarvis discover`."
        return f"Roku: {action}"


def wake_on_lan(mac: str, broadcast="255.255.255.255"):
    raw = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    if len(raw) != 6:
        raise ValueError("MAC address must have 6 bytes")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(b"\xff" * 6 + raw * 16, (broadcast, 9))


class SamsungTV(TV):
    KEYS = {"power": "KEY_POWER", "volume_up": "KEY_VOLUP", "volume_down": "KEY_VOLDOWN", "mute": "KEY_MUTE",
            "play_pause": "KEY_PLAY", "home": "KEY_HOME", "back": "KEY_RETURN", "up": "KEY_UP", "down": "KEY_DOWN",
            "left": "KEY_LEFT", "right": "KEY_RIGHT", "select": "KEY_ENTER", "forward": "KEY_FF", "rewind": "KEY_REWIND"}
    APP_NAME = "Jarvis"

    def __init__(self, host, mac=None, port=8002, token_file=None, use_ssl=True, timeout=5.0):
        self.host, self.mac, self.port, self.use_ssl, self.timeout = host, mac, port, use_ssl, timeout
        self.token_file = token_file or (paths.data_dir() / "samsung_token.json")
        self.ws = None
        self._playing = True  # Samsung has separate PLAY/PAUSE keys, so we toggle between them

    def _token(self):
        try:
            return json.loads(self.token_file.read_text()).get(self.host)
        except (OSError, ValueError):
            return None

    def _save_token(self, token):
        try:
            data = json.loads(self.token_file.read_text())
        except (OSError, ValueError):
            data = {}
        data[self.host] = token
        self.token_file.write_text(json.dumps(data))

    def _connect(self):
        name = base64.b64encode(self.APP_NAME.encode()).decode()
        path = f"/api/v2/channels/samsung.remote.control?name={quote(name)}"
        if self._token():
            path += f"&token={self._token()}"
        ws = WebSocket(self.host, self.port, path, self.use_ssl, self.timeout)
        ws.connect()
        ev = json.loads(ws.recv_text())  # the TV answers with ms.channel.connect once allowed
        if ev.get("event") != "ms.channel.connect":
            ws.close()
            raise PermissionError(ev.get("event", "unexpected reply"))
        token = (ev.get("data") or {}).get("token")
        if token:
            self._save_token(token)
        self.ws = ws

    def _press(self, key):
        self.ws.send_text(json.dumps({"method": "ms.remote.control", "params": {
            "Cmd": "Click", "DataOfCmd": key, "Option": "false", "TypeOfRemote": "SendRemoteKey"}}))

    def send(self, action):
        self._check(action)
        key = self.KEYS[action]
        if action == "play_pause":
            key = "KEY_PAUSE" if self._playing else "KEY_PLAY"
        try:
            reused = self.ws is not None
            try:
                if self.ws is None:
                    self._connect()
                self._press(key)
            except PermissionError:
                raise
            except OSError:
                if self.ws:
                    self.ws.close()
                self.ws = None
                if not reused:  # a fresh connect failed: the TV is off or unreachable, don't wait twice
                    raise
                self._connect()  # an old connection went stale: reconnect once
                self._press(key)
        except PermissionError:
            return "The TV hasn't allowed Jarvis yet. Look at the TV, choose Allow, then try again."
        except OSError as e:
            if action == "power" and self.mac:
                try:
                    wake_on_lan(self.mac)
                    return "TV unreachable (standby?), sent Wake-on-LAN to power it on."
                except (ValueError, OSError) as w:
                    return f"TV didn't answer ({e}) and Wake-on-LAN failed: {w}"
            return f"Samsung TV didn't answer ({e}). Is it on, on this Wi-Fi? Run `jarvis discover`."
        if action == "play_pause":
            self._playing = not self._playing
        return f"Samsung: {action}"


class AdbTV(TV):
    KEYS = {"power": 26, "volume_up": 24, "volume_down": 25, "mute": 164, "play_pause": 85, "home": 3,
            "back": 4, "up": 19, "down": 20, "left": 21, "right": 22, "select": 66, "forward": 90, "rewind": 89}

    def __init__(self, host, port=5555):
        self.target = f"{host}:{port}"
        self._connected = False

    def _adb(self, *args):
        if not shutil.which("adb"):
            raise RuntimeError("adb is not installed")
        return subprocess.run(["adb", *args], capture_output=True, text=True, timeout=8)

    def send(self, action):
        self._check(action)
        try:
            if not self._connected:
                self._adb("connect", self.target)
                self._connected = True
            r = self._adb("-s", self.target, "shell", "input", "keyevent", str(self.KEYS[action]))
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            return f"adb failed: {e}"
        return f"adb: {action}" if r.returncode == 0 else f"adb error: {r.stderr.strip()}"


class CecTV(TV):
    CMDS = {"power": None}

    def send(self, action):
        self._check(action)
        if action != "power":
            return "HDMI-CEC here only supports power."
        if not shutil.which("cec-client"):
            return "cec-client is not installed."
        r = subprocess.run(["cec-client", "-s", "-d", "1"], input="on 0\n", capture_output=True, text=True, timeout=10)
        return "CEC: power on sent" if r.returncode == 0 else f"CEC error: {r.stderr.strip()}"


def make_tv(cfg: dict):
    kind = (cfg or {}).get("type", "")
    if kind == "roku":
        return RokuTV(cfg["host"])
    if kind == "samsung":
        return SamsungTV(cfg["host"], mac=cfg.get("mac"))
    if kind == "adb":
        return AdbTV(cfg["host"])
    if kind == "cec":
        return CecTV()
    if kind == "dryrun":
        return DryRunTV()
    raise ValueError(f"unsupported TV type '{kind}' (supported: samsung, roku, adb, cec, dryrun)")


def _config():
    f = paths.config_dir() / "devices.json"
    return json.loads(f.read_text()) if f.exists() else {}


def load_tv():
    cfg = _config().get("tv")
    return make_tv(cfg) if cfg else None


def describe_config() -> str:
    cfg = _config().get("tv")
    return f"{cfg.get('type')} @ {cfg.get('host', '-')}" if cfg else "not configured (run `jarvis discover`)"
