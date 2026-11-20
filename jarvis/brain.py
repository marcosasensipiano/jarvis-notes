"""Jarvis's optional LLM brain (Claude API, stdlib only). Without ANTHROPIC_API_KEY Jarvis still
learns, but only from its built-in library; with a key it can invent new skills without limit."""
import json
import os
import urllib.request

from . import spend

API = "https://api.anthropic.com/v1/messages"


def model() -> str:
    return os.environ.get("JARVIS_MODEL", "claude-sonnet-5-5")


def available() -> bool:
    """A key is set and, if you gave Jarvis a budget, there is still some left."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    rem = spend.remaining()
    return rem is None or rem > 0.005


def ask(prompt: str, system: str = "", max_tokens: int = 6000, purpose: str = "") -> str:
    spend.check(model(), len(prompt) + len(system), max_tokens)  # raises BudgetExhausted
    body = {
        "model": model(),
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(), method="POST",
        headers={"content-type": "application/json", "anthropic-version": "2023-06-01",
                 "x-api-key": os.environ["ANTHROPIC_API_KEY"]},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    spend.record(data.get("model") or model(), data.get("usage") or {}, purpose)
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def extract_json(text: str):
    """Pull the first JSON object/array out of a model reply (tolerates ``` fences and chatter)."""
    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        raise ValueError("no JSON in reply")
    start = min(starts)
    end = max(text.rfind("}"), text.rfind("]"))
    return json.loads(text[start:end + 1])


def ask_json(prompt: str, system: str = "", max_tokens: int = 6000, purpose: str = ""):
    return extract_json(ask(prompt, system, max_tokens, purpose))
