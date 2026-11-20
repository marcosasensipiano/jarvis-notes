"""Jarvis's optional LLM brain (Claude API, stdlib only). Without ANTHROPIC_API_KEY Jarvis still
learns, but only from its built-in library; with a key it can invent new skills without limit."""
import json
import os
import urllib.request

API = "https://api.anthropic.com/v1/messages"


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def ask(prompt: str, system: str = "", max_tokens: int = 6000) -> str:
    body = {
        "model": os.environ.get("JARVIS_MODEL", "claude-sonnet-5-5"),
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
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def extract_json(text: str):
    """Pull the first JSON object/array out of a model reply (tolerates ``` fences and chatter)."""
    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        raise ValueError("no JSON in reply")
    start = min(starts)
    end = max(text.rfind("}"), text.rfind("]"))
    return json.loads(text[start:end + 1])


def ask_json(prompt: str, system: str = "", max_tokens: int = 6000):
    return extract_json(ask(prompt, system, max_tokens))
