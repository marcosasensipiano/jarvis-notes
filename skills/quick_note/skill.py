NAME = "quick_note"
DESCRIPTION = "Capture and list quick notes."
TRIGGERS = ["note", "notes", "remember"]
EXAMPLES = ["note buy oat milk", "note call the dentist friday", "notes"]
LESSON = """\
**quick_note** is the fastest way to get a thought out of your head.

- `note <anything>` appends a timestamped line to `data/notes.md`.
- `notes` (or `note list`) shows everything you saved.

How it works: a plain Markdown file, one bullet per note. No database, so you can open
or edit it anywhere. Other skills (like the daily briefing) read the same file.
"""


def run(args, ctx):
    f = ctx.data / "notes.md"
    text = args.strip()
    if text in ("", "list", "show"):
        return f.read_text().rstrip() if f.exists() else "No notes yet. Try: note buy oat milk"
    with f.open("a") as fh:
        fh.write(f"- {ctx.now:%Y-%m-%d %H:%M} {text}\n")
    return f"Noted: {text}"
