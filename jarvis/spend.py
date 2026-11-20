"""Tracks what Jarvis spends on the API and enforces a hard budget.

The API does not report your remaining prepaid credit to a normal key, so this is an *estimate*:
tokens used (from each reply) x published prices. It only knows about calls Jarvis made; the Anthropic
console is the source of truth. Prices are USD per million tokens (input, output)."""
from datetime import datetime
from . import memory

PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-opus-5-5": (4.0, 20.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-fable-5-2": (8.0, 40.0),
}
UNKNOWN_MODEL_PRICE = (8.0, 40.0)  # unknown model: assume expensive so the guard errs on the safe side


class BudgetExhausted(RuntimeError):
    pass


def price(model: str):
    return PRICES.get(model, UNKNOWN_MODEL_PRICE)


def cost(model: str, usage: dict) -> float:
    pin, pout = price(model)
    return (usage.get("input_tokens", 0) * pin + usage.get("output_tokens", 0) * pout) / 1e6


def _spend(m):
    s = m.setdefault("spend", {})
    s.setdefault("budget_usd", None)
    s.setdefault("spent_usd", 0.0)
    s.setdefault("calls", 0)
    s.setdefault("log", [])
    return s


def record(model: str, usage: dict, purpose: str = "") -> float:
    m = memory.load()
    s = _spend(m)
    c = cost(model, usage)
    s["spent_usd"] = round(s["spent_usd"] + c, 6)
    s["calls"] += 1
    s["log"] = (s["log"] + [{"when": datetime.now().isoformat(timespec="seconds"), "model": model, "usd": round(c, 5),
                             "in": usage.get("input_tokens", 0), "out": usage.get("output_tokens", 0),
                             "purpose": purpose}])[-30:]
    memory.save(m, keep_spend=False)
    return c


def remaining(m=None):
    s = _spend(m or memory.load())
    return None if s["budget_usd"] is None else max(0.0, s["budget_usd"] - s["spent_usd"])


def check(model: str, prompt_chars: int, max_tokens: int) -> None:
    """Refuse a call whose worst case (full max_tokens of output) could exceed what is left."""
    rem = remaining()
    if rem is None:
        return
    pin, pout = price(model)
    worst = (prompt_chars / 3 * pin + max_tokens * pout) / 1e6
    if worst > rem:
        raise BudgetExhausted(f"budget nearly used up: ${rem:.3f} left, this call could cost up to ${worst:.3f}")


def set_budget(total: float) -> None:
    m = memory.load()
    _spend(m)["budget_usd"] = round(float(total), 4)
    memory.save(m, keep_spend=False)


def add_budget(extra: float) -> None:
    m = memory.load()
    s = _spend(m)
    s["budget_usd"] = round((s["budget_usd"] or 0.0) + float(extra), 4)
    memory.save(m, keep_spend=False)


def summary(m=None) -> dict:
    s = _spend(m or memory.load())
    b, sp = s["budget_usd"], s["spent_usd"]
    return {"budget": b, "spent": sp, "left": None if b is None else max(0.0, b - sp), "calls": s["calls"],
            "pct_used": None if not b else min(100.0, 100.0 * sp / b), "last": s["log"][-1] if s["log"] else None}
