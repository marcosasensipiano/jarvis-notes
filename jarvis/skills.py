"""Skill registry. A skill is a folder with skill.py (+ test_skill.py) exposing:

    NAME: str            DESCRIPTION: str       TRIGGERS: list[str]   (lowercase first words)
    EXAMPLES: list[str]  LESSON: str (markdown) run(args: str, ctx) -> str
"""
import importlib.util
from datetime import datetime
from pathlib import Path
from . import paths

REQUIRED = ("NAME", "DESCRIPTION", "TRIGGERS", "EXAMPLES", "LESSON", "run")


class Ctx:
    """What a skill gets to work with: a data folder, the clock, and (lazily) the TV."""

    def __init__(self, data=None, now=None, tv=None):
        self.data = Path(data) if data else paths.data_dir()
        self.data.mkdir(parents=True, exist_ok=True)
        self.now = now or datetime.now()
        self._tv = tv

    @property
    def tv(self):
        if self._tv is None:
            from .devices import tv as tvmod
            self._tv = tvmod.load_tv()
        return self._tv

    @tv.setter
    def tv(self, value):
        self._tv = value


def load_skill(path):
    path = Path(path)
    f = path / "skill.py" if path.is_dir() else path
    spec = importlib.util.spec_from_file_location(f"jarvis_skill_{f.parent.name}", f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    missing = [r for r in REQUIRED if not hasattr(mod, r)]
    if missing:
        raise ValueError(f"{f.parent.name}: missing {', '.join(missing)}")
    if not isinstance(mod.TRIGGERS, (list, tuple)) or not mod.TRIGGERS:
        raise ValueError(f"{f.parent.name}: TRIGGERS must be a non-empty list")
    return mod


def discover(directory=None, errors=None) -> dict:
    d = Path(directory) if directory else paths.skills_dir()
    found = {}
    for p in sorted(d.iterdir()):
        if not p.is_dir() or p.name.startswith(("_", ".")) or not (p / "skill.py").exists():
            continue
        try:
            mod = load_skill(p)
            found[mod.NAME] = mod
        except Exception as e:  # a broken skill must never take Jarvis down
            if errors is not None:
                errors[p.name] = str(e)
    return found


def route(text: str, skills: dict):
    """Return (skill, args) for the best-matching skill, or (None, text)."""
    low = text.lower().strip()
    words = low.split()
    best, best_score, best_trigger = None, 0, ""
    for s in skills.values():
        for t in s.TRIGGERS:
            t = t.lower()
            if low == t or low.startswith(t + " "):
                score = 10 + len(t)
            elif t in words:
                score = 1
            else:
                continue
            if score > best_score:
                best, best_score, best_trigger = s, score, t
    if best is None:
        return None, text
    args = text.strip()[len(best_trigger):].strip() if best_score >= 10 else text.strip()
    return best, args
