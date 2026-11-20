import json
from datetime import datetime

NAME = "daily_briefing"
DESCRIPTION = "A one-glance morning briefing built from your other skills' data."
TRIGGERS = ["briefing", "brief"]
EXAMPLES = ["briefing"]
LESSON = """\
**daily_briefing** is the first skill that *combines* others.

- `briefing` greets you, then lists your latest notes, timers that are due, and habits you have
  not done yet today.

How it works: it reads the same files the other skills write (`notes.md`, `timers.json`,
`habits.json`). Skills sharing plain data files is how Jarvis composes abilities without them
knowing about each other, and it is the pattern future skills will follow.
"""


def _load(f):
    return json.loads(f.read_text()) if f.exists() else None


def run(args, ctx):
    now = ctx.now
    hello = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 18 else "Good evening"
    out = [f"{hello}. It is {now:%A %d %B}, {now:%H:%M}."]
    notes = ctx.data / "notes.md"
    if notes.exists():
        last = notes.read_text().strip().splitlines()[-3:]
        if last:
            out += ["Recent notes:"] + last
    timers = _load(ctx.data / "timers.json") or []
    due = [t["label"] for t in timers if datetime.fromisoformat(t["due"]) <= now]
    if due:
        out.append("Timers due: " + ", ".join(due))
    habits = _load(ctx.data / "habits.json") or {}
    today = now.date().isoformat()
    todo = [h for h, days in habits.items() if today not in days]
    if todo:
        out.append("Habits still open: " + ", ".join(sorted(todo)))
    if len(out) == 1:
        out.append("Nothing pending. Clear runway.")
    return "\n".join(out)
