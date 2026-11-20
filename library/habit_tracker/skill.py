import json
from datetime import date, timedelta

NAME = "habit_tracker"
DESCRIPTION = "Track daily habits and streaks."
TRIGGERS = ["habit", "habits"]
EXAMPLES = ["habit done gym", "habit read", "habits"]
LESSON = """\
**habit_tracker** turns "I should do X every day" into a streak you can see.

- `habit done gym` (or just `habit gym`) marks today's habit as done.
- `habits` lists every habit with its current streak and whether today is done.

How it works: each habit is a list of ISO dates in `data/habits.json`. A streak counts
consecutive days ending today (or yesterday, so you don't lose it before you've had a chance today).
"""


def _streak(days, today):
    s = set(days)
    cur = today if today.isoformat() in s else today - timedelta(days=1)
    n = 0
    while cur.isoformat() in s:
        n += 1
        cur -= timedelta(days=1)
    return n


def run(args, ctx):
    f = ctx.data / "habits.json"
    habits = json.loads(f.read_text()) if f.exists() else {}
    today = ctx.now.date() if hasattr(ctx.now, "date") else date.today()
    words = args.lower().split()
    if words and words[0] == "done":
        words = words[1:]
    name = " ".join(words)
    if name:
        days = habits.setdefault(name, [])
        if today.isoformat() not in days:
            days.append(today.isoformat())
        f.write_text(json.dumps(habits))
        return f"{name}: done today. Streak {_streak(days, today)}."
    if not habits:
        return "No habits yet. Try: habit done gym"
    return "\n".join(
        f"- {n}: streak {_streak(d, today)}" + (" (done today)" if today.isoformat() in d else "")
        for n, d in sorted(habits.items())
    )
