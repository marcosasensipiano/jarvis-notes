"""Build ideas. With an API key Jarvis reads how you use it and invents ideas; offline it draws from
a curated bank, personalised by what you use and what you keep asking for that it cannot do yet."""
from datetime import date
from . import brain, profile

BANK = [
    ("Morning scene", "One gesture or phrase runs the briefing on screen and turns the TV to your first app.", "M"),
    ("Gesture shortcuts you define", "Record a custom hand pose and bind it to any skill, not just the TV.", "M"),
    ("Weekly review", "Every Sunday, summarise habits, focus minutes and spending into one page.", "S"),
    ("Voice capture", "Say a note aloud and have it transcribed into quick_note.", "M"),
    ("Smart reminders", "Turn notes that contain a day or time into timers automatically.", "S"),
    ("Wi-Fi device roster", "Name every device on your network and flag new ones that appear.", "S"),
    ("Focus mode", "Starting a focus session mutes the TV and logs distractions.", "S"),
    ("Skill suggestions from habits", "If you log the same thing 5 times, Jarvis offers to build a skill for it.", "S"),
    ("Dashboard on the TV", "Cast the Jarvis dashboard to the TV as an always-on ambient display.", "L"),
    ("Spending insights", "Spot categories that grew month over month and say why it matters.", "S"),
    ("Two-hand gestures", "Use both hands for fine control, such as a volume dial.", "L"),
    ("Daily reading digest", "Collect links you saved in notes and summarise them each morning.", "M"),
]


def _next_id(m):
    return max((i["id"] for i in m["ideas"]), default=0) + 1


def refresh(m: dict, n: int = 3) -> list:
    have = {i["title"].lower() for i in m["ideas"]}
    new = []
    if brain.available():
        try:
            prompt = (
                "You are Jarvis, a personal assistant. Propose %d NEW build ideas that would make your user's day "
                "easier (include at least one that could earn them money if their profile allows). Installed skills: %s. "
                "Usage counts: %s. Unmet requests: %s. Already proposed: %s. About the user: %s.\n"
                'Reply with JSON only: [{"title":str,"why":str,"effort":"S|M|L"}]'
                % (n, sorted(m["skills"]), m["usage"], m["gaps"], sorted(have), profile.summary() or "unknown")
            )
            for i in brain.ask_json(prompt, max_tokens=1200, purpose="ideas")[:n]:
                new.append((str(i["title"]), str(i["why"]), str(i.get("effort", "M"))[:1].upper()))
        except Exception:
            new = []
    if not new:
        for gap in sorted(m["gaps"], key=m["gaps"].get, reverse=True)[:1]:
            new.append((f"Skill for: {gap}", f"You asked for this {m['gaps'][gap]}x and Jarvis could not do it.", "S"))
        new += list(BANK)
    out = []
    for title, why, effort in new:
        if title.lower() in have or len(out) >= n:
            continue
        idea = {"id": _next_id(m), "title": title, "why": why, "effort": effort if effort in "SML" else "M",
                "status": "proposed", "date": date.today().isoformat()}
        m["ideas"].append(idea)
        have.add(title.lower())
        out.append(idea)
    return out
