import json
from datetime import timedelta

NAME = "focus_session"
DESCRIPTION = "Log focus sessions and see today's deep-work total."
TRIGGERS = ["focus"]
EXAMPLES = ["focus 25 write report", "focus 50", "focus log"]
LESSON = """\
**focus_session** keeps you honest about deep work.

- `focus 25 write report` starts a 25-minute session (and tells you when it ends).
- `focus` or `focus log` shows today's sessions and the total minutes.

How it works: each session is stored with its start, length and label in `data/focus.json`.
Pair it with `timer 25m focus` if you want a reminder when it ends.
"""


def run(args, ctx):
    f = ctx.data / "focus.json"
    sessions = json.loads(f.read_text()) if f.exists() else []
    parts = args.split()
    if parts and parts[0].isdigit():
        mins = int(parts[0])
        sessions.append({"start": ctx.now.isoformat(), "minutes": mins, "label": " ".join(parts[1:])})
        f.write_text(json.dumps(sessions))
        return f"Focus for {mins} min. Ends at {ctx.now + timedelta(minutes=mins):%H:%M}. Go."
    today = ctx.now.date().isoformat()
    todays = [s for s in sessions if s["start"][:10] == today]
    if not todays:
        return "No focus sessions today. Try: focus 25 write report"
    lines = [f"- {s['start'][11:16]} {s['minutes']}m {s['label']}".rstrip() for s in todays]
    return "\n".join(lines + [f"Total today: {sum(s['minutes'] for s in todays)} min"])
