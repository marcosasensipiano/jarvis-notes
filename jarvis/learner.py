"""The daily learning loop: learn one skill, upgrade the UI, think up ideas, (optionally) build one,
write a lesson, update the journal and dashboard."""
import re
import shutil
from datetime import date
from . import brain, dashboard, generate, ideas, memory, paths, skills, upgrades

LIBRARY_PRIORITY = ["daily_briefing", "habit_tracker", "focus_session", "expense_log"]


def sync(m: dict) -> dict:
    """Register installed skills in memory (seeds the first time) and return the registry."""
    reg = skills.discover()
    for name in reg:
        m["skills"].setdefault(name, {"learned": date.today().isoformat(), "origin": "seed"})
    return reg


def _library() -> dict:
    return skills.discover(paths.library_dir())


def _pick_from_library(m, installed, gap_words):
    lib = {k: v for k, v in _library().items() if k not in installed}
    for name, mod in lib.items():
        hay = {w for w in re.findall(r"[a-z]+", " ".join(mod.TRIGGERS + [mod.DESCRIPTION, name]).lower()) if len(w) >= 4}
        if gap_words & hay:
            return name, True
    for name in LIBRARY_PRIORITY + sorted(lib):
        if name in lib:
            return name, False
    return None, False


def acquire_skill(m: dict, say=print):
    installed = sync(m)
    gap = max(m["gaps"], key=m["gaps"].get) if m["gaps"] else None
    if brain.available():
        target = (f"The user keeps asking: {gap!r}. Build the skill that handles it." if gap
                  else "Your choice: the most useful small skill that makes the user's day easier, given their usage: "
                       f"{m['usage']}")
        say(f"Learning with the brain: {target[:90]}")
        name = generate.generate_skill(target, sorted(installed), say)
        if name:
            m["skills"][name] = {"learned": date.today().isoformat(), "origin": "generated"}
            if gap:
                m["gaps"].pop(gap, None)
            return name
        m["failures"].append({"date": date.today().isoformat(), "target": target[:120]})
        say("Could not produce a passing skill; falling back to the library.")
    pick, matched = _pick_from_library(m, installed, {w for w in re.findall(r"[a-z]+", gap or "") if len(w) >= 4})
    if not pick:
        say("Library exhausted and no API key set. Set ANTHROPIC_API_KEY so I can invent new skills.")
        return None
    shutil.copytree(paths.library_dir() / pick, paths.skills_dir() / pick,
                    ignore=shutil.ignore_patterns("__pycache__"))
    m["skills"][pick] = {"learned": date.today().isoformat(), "origin": "library"}
    if gap and matched:  # only clear the request if this skill really addresses it
        m["gaps"].pop(gap, None)
    return pick


def unlock_upgrade(m: dict, say=print):
    up = upgrades.next_builtin(m)
    if up is None and brain.available():
        try:
            up = generate.design_upgrade(m)
            m["custom_upgrades"].append(up)
        except Exception as e:
            say(f"  could not design an upgrade: {e}")
            return None
    if up is None:
        return None
    m["upgrades"].append(up["id"])
    return up


def _lesson(m, today, skill_name, up, new_ideas, build):
    reg = skills.discover()
    out = [f"# Day {m['day']} - {today}", ""]
    if skill_name and skill_name in reg:
        s = reg[skill_name]
        out += [f"## New skill: {s.NAME}", "", s.DESCRIPTION, "", s.LESSON.strip(), "", "**Try it now:**", ""]
        out += [f"    jarvis {e}" for e in s.EXAMPLES] + [""]
    else:
        out += ["## No new skill today", "", "I could not learn one (see the journal).", ""]
    if up:
        out += [f"## New look: {up['name']}", "", up["lesson"], "", "Open `dashboard/index.html` to see it.", ""]
    if new_ideas:
        out += ["## Ideas I'd like to build", ""] + [f"- **{i['title']}** ({i['effort']}): {i['why']}" for i in new_ideas]
        out += ["", "Approve one with `jarvis build <id>`.", ""]
    if build:
        out += ["## I built something", "", build, ""]
    f = paths.lessons_dir() / f"day-{m['day']:03d}-{today}.md"
    f.write_text("\n".join(out))
    return f


def learn_today(force=False, build=False, say=print):
    m = memory.load()
    today = date.today().isoformat()
    if m["last_learn"] == today and not force:
        say("Already learned today. Use --force to run again.")
        return None
    m["day"] += 1
    m["last_learn"] = today
    say(f"Day {m['day']}.")
    skill_name = acquire_skill(m, say)
    up = unlock_upgrade(m, say)
    new_ideas = ideas.refresh(m)
    build_note = None
    if build:
        from . import builder
        build_note = builder.build_next(m, say)
    lesson = _lesson(m, today, skill_name, up, new_ideas, build_note)
    with (paths.root() / "JOURNAL.md").open("a") as j:
        j.write(f"- {today} (day {m['day']}): skill={skill_name or 'none'}; look={up['id'] if up else 'none'}; "
                f"ideas={len(new_ideas)}; build={'yes' if build_note else 'no'}\n")
    dashboard.write(m)
    memory.save(m)
    say(f"New skill: {skill_name or 'none'} | New look: {up['name'] if up else 'none'} | Lesson: {lesson}")
    return {"skill": skill_name, "upgrade": up["id"] if up else None, "ideas": new_ideas, "lesson": str(lesson)}
