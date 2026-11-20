"""What Jarvis knows about YOU, so what it learns and proposes is bound to you rather than generic.
Stored in data/profile.json (git-ignored, stays on your machine). When Jarvis uses the API, a short summary of
this is included in its prompts, so only put in what you are comfortable sending to Anthropic."""
import json
from . import paths

FIELDS = [
    ("role", "What do you do (job, studies)?"),
    ("skills", "What are you good at?"),
    ("interests", "What do you enjoy / care about?"),
    ("hours", "How many free hours per week could go into projects?"),
    ("goal", "Your main goal for the next 6 months?"),
    ("money", "Money you could invest in a business (0 is fine)?"),
    ("annoyances", "What wastes your time or annoys you day to day?"),
    ("never", "Anything Jarvis should never do or touch?"),
]


def _file():
    return paths.data_dir() / "profile.json"


def load() -> dict:
    try:
        return json.loads(_file().read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save(p: dict) -> None:
    _file().write_text(json.dumps(p, indent=2, ensure_ascii=False))


def summary() -> str:
    p = load()
    return "; ".join(f"{k}: {p[k]}" for k, _ in FIELDS if p.get(k)) or ""
