import ast
import operator
import re

NAME = "calc_convert"
DESCRIPTION = "Safe calculator and unit converter."
TRIGGERS = ["calc", "convert"]
EXAMPLES = ["calc 2*(3+4)", "convert 5 km to mi", "convert 70 f to c"]
LESSON = """\
**calc_convert** does maths and unit conversions.

- `calc 2*(3+4)` -> 14. Supports + - * / // % ** and parentheses.
- `convert 5 km to mi` -> 3.107 mi. Lengths, weights, volumes and temperatures.

How it works: expressions are parsed into an AST and evaluated by walking only allowed
operators, so it never uses `eval`. Units convert through a base unit (metres, kilograms,
litres); temperatures are handled separately because they are not simple ratios.
"""

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
        ast.Pow: operator.pow}
_BASE = {
    "length": {"m": 1, "km": 1000, "cm": 0.01, "mm": 0.001, "mi": 1609.344, "ft": 0.3048, "in": 0.0254, "yd": 0.9144},
    "mass": {"kg": 1, "g": 0.001, "lb": 0.45359237, "oz": 0.028349523},
    "volume": {"l": 1, "ml": 0.001, "gal": 3.785411784, "cup": 0.2365882365},
}
_CONV = re.compile(r"^\s*(-?[\d.]+)\s*([a-z]+)\s+(?:to|in|into)\s+([a-z]+)\s*$", re.I)


def safe_eval(expr):
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            return -ev(n.operand) if isinstance(n.op, ast.USub) else ev(n.operand)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 100:
                raise ValueError("exponent too large")
            return _OPS[type(n.op)](a, b)
        raise ValueError("unsupported expression")
    return ev(ast.parse(expr.strip(), mode="eval"))


def _temp(v, a, b):
    c = {"c": v, "f": (v - 32) * 5 / 9, "k": v - 273.15}[a]
    return {"c": c, "f": c * 9 / 5 + 32, "k": c + 273.15}[b]


def convert(value, a, b):
    a, b = a.lower(), b.lower()
    if a in "cfk" and b in "cfk" and len(a) == len(b) == 1:
        return _temp(value, a, b)
    for table in _BASE.values():
        if a in table and b in table:
            return value * table[a] / table[b]
    raise ValueError(f"can't convert {a} to {b}")


def run(args, ctx):
    text = args.strip()
    if not text:
        return "Try: calc 2*(3+4)  or  convert 5 km to mi"
    m = _CONV.match(text)
    try:
        if m:
            out = convert(float(m.group(1)), m.group(2), m.group(3))
            return f"{float(m.group(1)):g} {m.group(2)} = {out:.4g} {m.group(3)}"
        out = safe_eval(text)
        return f"{out:.10g}" if isinstance(out, float) else str(out)
    except (ValueError, ZeroDivisionError, SyntaxError, KeyError) as e:
        return f"Sorry, I couldn't do that: {e}"
