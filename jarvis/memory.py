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
    "spend": {"budget_usd": None, "spent_usd": 0.0, "calls": 0, "log": []},  # owned by spend.py
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


def save(m: dict, keep_spend: bool = True) -> None:
    """keep_spend: spend.py records API costs mid-run, so a caller holding an older copy of memory must not
    overwrite them. Only spend.py passes keep_spend=False."""
    if keep_spend and _file().exists():
        try:
            m["spend"] = json.loads(_file().read_text()).get("spend", m.get("spend"))
        except json.JSONDecodeError:
            pass
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
