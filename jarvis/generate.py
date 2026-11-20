"""Ask the brain to write a package (a skill or a build), then guard it and prove it with its own tests."""
import re
import shutil
import tempfile
from pathlib import Path
from . import brain, packages, skills

CONTRACT = """\
Write small, safe, standard-library-only Python. A skill package has two files:

skill.py defines: NAME (snake_case str), DESCRIPTION (str), TRIGGERS (non-empty list of lowercase single words
the user types first), EXAMPLES (list of 2-3 command strings), LESSON (markdown teaching the user what it does,
the exact commands, and how it works in plain language), and run(args: str, ctx) -> str.
ctx.data is a pathlib.Path folder you may read/write; ctx.now is a datetime. Return text, never print.
Forbidden: os, sys, subprocess, socket, urllib, http, requests, shutil, importlib, threading, asyncio, eval, exec.
Use pathlib on ctx.data and json for storage.

test_skill.py uses unittest, does `import skill`, builds a ctx with types.SimpleNamespace(data=Path(tempfile.mkdtemp()),
now=datetime(...)), and has at least 3 meaningful tests including an edge case.
"""
SYSTEM = "You are the learning module of a personal assistant called Jarvis. You output only valid JSON."
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,30}$")


def generate_skill(target: str, installed: list, say=print, attempts: int = 2):
    """Return the installed skill's name, or None. `target` describes what to learn."""
    error = None
    for n in range(attempts):
        prompt = (
            f"{CONTRACT}\nAlready installed skills (do not duplicate): {installed}\n"
            f"What to learn: {target}\n"
            'Reply JSON only: {"name":str,"files":{"skill.py":str,"test_skill.py":str}}'
        )
        if error:
            prompt += f"\nYour previous attempt failed with:\n{error[-1500:]}\nFix it."
        try:
            spec = brain.ask_json(prompt, SYSTEM)
            name = spec["name"]
            if not NAME_RE.match(name) or name in installed:
                raise ValueError(f"bad or duplicate skill name: {name!r}")
            stage = Path(tempfile.mkdtemp(prefix="jarvis-skill-"))
            packages.write_package(stage, spec["files"])
            problems = packages.guard_package(stage)
            if problems:
                raise ValueError("guard: " + "; ".join(problems))
            ok, out = packages.run_tests(stage)
            if not ok:
                raise ValueError("tests failed:\n" + out)
            mod = skills.load_skill(stage)
            if mod.NAME != name:
                raise ValueError("NAME does not match folder name")
            dest = skills.paths.skills_dir() / name
            if dest.exists():
                raise ValueError("skill folder already exists")
            shutil.copytree(stage, dest, ignore=shutil.ignore_patterns("__pycache__"))
            return name
        except Exception as e:  # network, JSON, validation: retry once with the error, then give up
            error = f"{type(e).__name__}: {e}"
            say(f"  attempt {n + 1} failed: {error.splitlines()[0][:160]}")
    return None


def generate_build(title: str, why: str, dest: Path, say=print):
    """Implement an idea as a standalone package under builds/. Returns (ok, detail)."""
    prompt = (
        "Implement this idea as a small, self-contained Python project using only the standard library.\n"
        f"Idea: {title}\nWhy: {why}\n"
        "Include a README.md and tests (test_*.py using unittest). Prefer the skill contract below if the idea fits "
        "a command-style skill, otherwise any layout is fine. Forbidden: network, subprocess, eval/exec.\n"
        f"{CONTRACT}\n"
        'Reply JSON only: {"files":{"path":"content",...}}'
    )
    try:
        spec = brain.ask_json(prompt, SYSTEM, max_tokens=8000)
        packages.write_package(dest, spec["files"])
        problems = packages.guard_package(dest)
        if problems:
            return False, "guard: " + "; ".join(problems)
        return packages.run_tests(dest)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def design_upgrade(m: dict):
    """Ask the brain for a new CSS-only visual upgrade."""
    from . import upgrades
    prompt = (
        "Design one new CSS-only visual upgrade for a dark, cyan, JARVIS-style dashboard. Available variables: "
        "--bg --fg --accent --accent-dim --grid --card. Existing classes: .card .reactor .status .constellation. "
        f"Already have: {[u['name'] for u in upgrades.all_upgrades(m)]}. No @import, url(), or scripts. "
        "Respect prefers-reduced-motion for any animation.\n"
        'Reply JSON only: {"id":"snake_case","name":str,"lesson":str (what changed and the CSS idea behind it),"css":str}'
    )
    u = brain.ask_json(prompt, SYSTEM, max_tokens=1500)
    if not (re.match(r"^[a-z_]{3,24}$", u["id"]) and upgrades.safe_css(u["css"])):
        raise ValueError("unsafe or malformed upgrade")
    return {"id": u["id"], "name": str(u["name"]), "lesson": str(u["lesson"]), "css": u["css"]}
