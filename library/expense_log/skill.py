import json
import re

NAME = "expense_log"
DESCRIPTION = "Log spending and see the month's total by category."
TRIGGERS = ["spend", "expenses"]
EXAMPLES = ["spend 4.50 coffee", "spend 32 groceries milk and eggs", "expenses"]
LESSON = """\
**expense_log** is a one-line spending diary.

- `spend 4.50 coffee` logs 4.50 under the category "coffee" (first word after the amount).
- `expenses` shows this month's total and a breakdown by category.

How it works: entries live in `data/expenses.json`. Categories are just the first word, so
keep it consistent (`groceries`, `coffee`, `transport`).
"""

_AMOUNT = re.compile(r"^\s*(\d+(?:[.,]\d{1,2})?)\s*(.*)$")


def run(args, ctx):
    f = ctx.data / "expenses.json"
    items = json.loads(f.read_text()) if f.exists() else []
    m = _AMOUNT.match(args)
    if m:
        amount = float(m.group(1).replace(",", "."))
        note = m.group(2).strip() or "misc"
        items.append({"date": ctx.now.date().isoformat(), "amount": amount, "note": note})
        f.write_text(json.dumps(items))
        return f"Logged {amount:.2f} for {note}."
    month = ctx.now.strftime("%Y-%m")
    cur = [i for i in items if i["date"].startswith(month)]
    if not cur:
        return "No spending logged this month. Try: spend 4.50 coffee"
    cats = {}
    for i in cur:
        cat = i["note"].split()[0].lower()
        cats[cat] = cats.get(cat, 0) + i["amount"]
    lines = [f"- {c}: {v:.2f}" for c, v in sorted(cats.items(), key=lambda kv: -kv[1])]
    return "\n".join(lines + [f"Total {month}: {sum(cats.values()):.2f}"])
