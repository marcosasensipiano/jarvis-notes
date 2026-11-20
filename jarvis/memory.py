"""Jarvis's long-term memory. Deliberately stores counters, not raw transcripts:
usage is per-skill counts, and gaps are the (short) requests it could not handle."""
import json
from . import paths

DEFAULT = {
    "day": 0,
    "last_learn": None,
    "skills": {},          # name -> {"learned": date, "origin": seed|library|generated|approved}
    "usage": {},           # name -> count
    "gaps": {},            # request text -> count (things you asked for that no skill handled)
    "ideas": [],           # {"id","title","why","effort","status","date"}
    "upgrades": [],        # ids of unlocked visual upgrades
    "custom_upgrades": [], # CSS-only upgrades Jarvis designed itself
    "failures": [],        # learning attempts that did not pass their tests
}


def _file():
    return paths.data_dir() / "memory.json"


def load() -> dict:
    f = _file()
    m = {}
    if f.exists():
        try:
            m = json.loads(f.read_text())
        except json.JSONDecodeError:
            m = {}
    out = json.loads(json.dumps(DEFAULT))
    out.update(m)
    return out


def save(m: dict) -> None:
    _file().write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")


def record_use(name: str) -> None:
    m = load()
    m["usage"][name] = m["usage"].get(name, 0) + 1
    save(m)


def record_gap(text: str) -> None:
    key = " ".join(text.lower().split()[:8])
    if not key:
        return
    m = load()
    m["gaps"][key] = m["gaps"].get(key, 0) + 1
    save(m)
