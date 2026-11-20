"""TV drivers. One canonical action vocabulary; each driver translates it for a protocol.

Types for config/devices.json -> {"tv": {"type": ..., "host": ...}}:
  roku     Roku TVs and sticks over the LAN (HTTP, port 8060). Volume/power only on Roku TVs.
  adb      Android TV / Google TV / Fire TV / Shield (enable network debugging; needs `adb` installed).
  cec      HDMI-CEC power on/standby via `cec-client` (e.g. a Raspberry Pi plugged into the TV).
  dryrun   Prints actions. Safe for testing gestures.
Samsung (Tizen) and LG (webOS) TVs speak websocket protocols that are not built yet: they are on
Jarvis's learning backlog."""
import json
import shutil
import subprocess
import urllib.request

from .. import paths

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
    if kind == "adb":
        return AdbTV(cfg["host"])
    if kind == "cec":
        return CecTV()
    if kind == "dryrun":
        return DryRunTV()
    raise ValueError(f"unsupported TV type '{kind}' (supported: roku, adb, cec, dryrun)")


def _config():
    f = paths.config_dir() / "devices.json"
    return json.loads(f.read_text()) if f.exists() else {}


def load_tv():
    cfg = _config().get("tv")
    return make_tv(cfg) if cfg else None


def describe_config() -> str:
    cfg = _config().get("tv")
    return f"{cfg.get('type')} @ {cfg.get('host', '-')}" if cfg else "not configured (run `jarvis discover`)"
