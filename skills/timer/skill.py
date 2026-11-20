import json
import re
from datetime import datetime, timedelta

NAME = "timer"
DESCRIPTION = "Set non-blocking timers and see what is due."
TRIGGERS = ["timer", "timers"]
EXAMPLES = ["timer 10m tea", "timer 1h30m laundry", "timers"]
LESSON = """\
**timer** sets a timer without blocking anything.

- `timer 10m tea` -> remembers "tea" is due in 10 minutes. Units: h, m, s (also `1h30m`).
- `timers` -> lists what is pending and what is DUE.

How it works: timers are saved as due-timestamps in `data/timers.json`. Nothing runs in the
background; each time you (or another skill) look, the remaining time is recomputed. That makes
it robust across restarts.
"""

_UNITS = {"h": 3600, "hr": 3600, "hour": 3600, "hours": 3600,
          "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
          "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1}
_RE = re.compile(r"(\d+)\s*([a-z]+)")


def parse_duration(text):
    total, spans = 0, []
    for m in _RE.finditer(text.lower()):
        if m.group(2) in _UNITS:
            total += int(m.group(1)) * _UNITS[m.group(2)]
            spans.append(m.span())
    label = text
    for a, b in reversed(spans):
        label = label[:a] + label[b:]
    return total, " ".join(label.split())


def _fmt(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return " ".join(p for p in (f"{h}h" if h else "", f"{m}m" if m else "", f"{s}s" if s and not h else "") if p) or "0s"


def run(args, ctx):
    f = ctx.data / "timers.json"
    timers = json.loads(f.read_text()) if f.exists() else []
    secs, label = parse_duration(args)
    if secs:
        due = ctx.now + timedelta(seconds=secs)
        timers.append({"label": label or "timer", "due": due.isoformat()})
        f.write_text(json.dumps(timers))
        return f"Timer '{label or 'timer'}' set for {_fmt(secs)} (due {due:%H:%M})."
    if not timers:
        return "No timers. Try: timer 10m tea"
    lines = []
    for t in sorted(timers, key=lambda t: t["due"]):
        left = (datetime.fromisoformat(t["due"]) - ctx.now).total_seconds()
        lines.append(f"- {t['label']}: " + (f"in {_fmt(left)}" if left > 0 else "DUE"))
    return "\n".join(lines)
