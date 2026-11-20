NAME = "tv_control"
DESCRIPTION = "Control your TV in plain language (same actions your gestures trigger)."
TRIGGERS = ["tv"]
EXAMPLES = ["tv volume up", "tv pause", "tv home", "tv off"]
LESSON = """\
**tv_control** lets you drive the TV with words; the gesture system uses the same actions.

- `tv volume up|down`, `tv mute`, `tv play|pause`, `tv home|back`, `tv up|down|left|right|ok`,
  `tv forward|rewind`, `tv on|off`.

How it works: your phrase is mapped to one canonical action (`volume_up`, `play_pause`, ...) and
handed to whichever TV driver is set in `config/devices.json` (Roku, Android/Google/Fire TV via adb,
or HDMI-CEC). Run `jarvis discover` first to find your TV on the Wi-Fi.
"""

PHRASES = {
    "on": "power", "off": "power", "power": "power", "turn on": "power", "turn off": "power",
    "mute": "mute", "unmute": "mute",
    "volume up": "volume_up", "louder": "volume_up", "vol up": "volume_up",
    "volume down": "volume_down", "quieter": "volume_down", "vol down": "volume_down",
    "play": "play_pause", "pause": "play_pause", "play pause": "play_pause", "resume": "play_pause",
    "home": "home", "back": "back",
    "up": "up", "down": "down", "left": "left", "right": "right",
    "ok": "select", "select": "select", "enter": "select",
    "forward": "forward", "fast forward": "forward", "rewind": "rewind",
}


def resolve(text):
    text = " ".join(text.lower().split())
    if text in PHRASES:
        return PHRASES[text]
    for phrase in sorted(PHRASES, key=len, reverse=True):
        if f" {phrase} " in f" {text} ":
            return PHRASES[phrase]
    return None


def run(args, ctx):
    action = resolve(args)
    if action is None:
        return "I know: on/off, volume up/down, mute, play/pause, home, back, arrows, ok, forward, rewind."
    tv = ctx.tv
    if tv is None:
        return "No TV configured yet. Run `jarvis discover`, then copy config/devices.example.json to config/devices.json."
    return tv.send(action)
