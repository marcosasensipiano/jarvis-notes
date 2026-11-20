"""Autonomous building. Jarvis implements small ideas on its own, but only inside builds/.
Nothing reaches your live skills until you run `jarvis approve <slug>`."""
import re
import shutil
from . import brain, generate, packages, paths, skills


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "idea"


def build(m: dict, idea: dict, say=print) -> str:
    dest = paths.builds_dir() / slug(idea["title"])
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    if brain.available():
        ok, detail = generate.generate_build(idea["title"], idea["why"], dest, say)
        idea["status"] = "built" if ok else "failed"
        if not ok:
            (dest / "FAILED.txt").write_text(detail)
        return (f"Built `{dest.name}` in builds/. Tests passed. Review it, then `jarvis approve {dest.name}`."
                if ok else f"Tried to build `{dest.name}` but it failed its checks: {detail.splitlines()[0][:140]}")
    (dest / "PLAN.md").write_text(
        f"# {idea['title']}\n\nWhy: {idea['why']}\nEffort: {idea['effort']}\n\n"
        "No API key was available, so I only drafted a plan. Set ANTHROPIC_API_KEY and I will implement it.\n")
    idea["status"] = "planned"
    return f"Drafted a plan for `{dest.name}` (no API key, so no code yet)."


def build_next(m: dict, say=print):
    cand = [i for i in m["ideas"] if i["status"] == "proposed" and i["effort"] == "S"]
    if not cand:
        return None
    return build(m, cand[0], say)


def approve(m: dict, name: str) -> str:
    src = paths.builds_dir() / name
    if not (src / "skill.py").exists():
        return f"builds/{name} has no skill.py, so there is nothing to install automatically; review it by hand."
    problems = packages.guard_package(src)
    if problems:
        return "Refusing: " + "; ".join(problems)
    ok, out = packages.run_tests(src)
    if not ok:
        return "Refusing: tests do not pass.\n" + out[-500:]
    mod = skills.load_skill(src)
    dest = paths.skills_dir() / mod.NAME
    if dest.exists():
        return f"A skill named {mod.NAME} is already installed."
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "FAILED.txt"))
    from datetime import date
    m["skills"][mod.NAME] = {"learned": date.today().isoformat(), "origin": "approved"}
    for i in m["ideas"]:
        if slug(i["title"]) == name:
            i["status"] = "installed"
    return f"Installed skill '{mod.NAME}'. Try: jarvis {mod.EXAMPLES[0]}"
