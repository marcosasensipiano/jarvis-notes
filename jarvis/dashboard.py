"""Static HTML dashboard. What it looks like depends on which visual upgrades Jarvis has unlocked."""
import html
import math
from . import paths, skills, spend, upgrades

BASE_CSS = """
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 ui-monospace,Menlo,Consolas,monospace;padding:24px 16px}
main{max-width:960px;margin:auto}h1{letter-spacing:.3em;font-weight:400;margin:0 0 4px}h2{font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin:0 0 10px}
.sub{opacity:.7;margin-bottom:24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--accent-dim);border-radius:10px;padding:16px}.stat{font-size:34px;color:var(--accent)}
.bar{height:8px;border-radius:4px;background:var(--accent-dim);overflow:hidden;margin:10px 0 6px}.bar span{display:block;height:100%;background:var(--accent)}.bar.low span{background:#ff6b6b}
ul{padding-left:18px;margin:0}li{margin:4px 0}code{color:var(--accent)}.muted{opacity:.6}
"""


def _constellation(names):
    if not names:
        return ""
    pts = []
    for i, n in enumerate(names):
        a = 2 * math.pi * i / len(names) - math.pi / 2
        pts.append((n, 150 + 105 * math.cos(a), 150 + 105 * math.sin(a)))
    lines = "".join(f'<line x1="150" y1="150" x2="{x:.1f}" y2="{y:.1f}"/>' for _, x, y in pts)
    dots = "".join(f'<circle class="node" cx="{x:.1f}" cy="{y:.1f}" r="5"/><text x="{x:.1f}" y="{y + 16:.1f}">{html.escape(n)}</text>'
                   for n, x, y in pts)
    return f'<svg class="constellation" viewBox="0 0 300 300" role="img" aria-label="Skill constellation">{lines}<circle class="node" cx="150" cy="150" r="9"/>{dots}</svg>'


def _budget_card(m):
    b = spend.summary(m)
    if b["budget"] is None:
        body = ('<div class="stat">no budget</div><div class="muted">Spent $%.3f so far. Set one with '
                '<code>jarvis budget 5.8</code>.</div>' % b["spent"])
    else:
        low = " low" if b["left"] < 0.2 * b["budget"] else ""
        body = (f'<div class="stat">${b["left"]:.2f} left</div><div class="bar{low}"><span style="width:{100 - b["pct_used"]:.0f}%"></span></div>'
                f'<div class="muted">spent ${b["spent"]:.3f} of ${b["budget"]:.2f} · {b["calls"]} calls</div>')
    return f'<section class="card"><h2>Brain budget</h2>{body}<div class="muted">estimate; the Anthropic console is the source of truth</div></section>'


def render(m: dict) -> str:
    ups = upgrades.unlocked(m)
    ids = {u["id"] for u in ups}
    esc = html.escape
    css = upgrades.theme_vars(m) + BASE_CSS + "\n".join(u["css"] for u in ups)
    reactor = '<span class="reactor"></span>' if "reactor" in ids else ""
    status = '<span class="status"></span> ' if "pulse" in ids else ""
    skill_items = "".join(
        f"<li><code>{esc(n)}</code> <span class=muted>{esc(i['origin'])}, {esc(i['learned'])}</span></li>"
        for n, i in sorted(m["skills"].items()))
    idea_items = "".join(f"<li>#{i['id']} <b>{esc(i['title'])}</b> <span class=muted>[{esc(i['effort'])}, {esc(i['status'])}]</span></li>"
                         for i in m["ideas"][-8:]) or "<li class=muted>none yet</li>"
    gap_items = "".join(f"<li>{esc(g)} <span class=muted>x{c}</span></li>"
                        for g, c in sorted(m["gaps"].items(), key=lambda kv: -kv[1])[:6]) or "<li class=muted>nothing, I can do everything you asked</li>"
    up_items = "".join(f"<li>{esc(u['name'])}</li>" for u in ups) or "<li class=muted>base look</li>"
    cons = f'<section class="card"><h2>Constellation</h2>{_constellation(sorted(m["skills"]))}</section>' if "constellation" in ids else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jarvis Dashboard</title><style>{css}</style></head><body><main>
<h1>{reactor}J.A.R.V.I.S.</h1><div class="sub">{status}Day {m['day']} · {len(m['skills'])} skills · {len(ups)} visual upgrades</div>
<div class="grid">
<section class="card"><h2>Days learning</h2><div class="stat">{m['day']}</div></section>
<section class="card"><h2>Skills</h2><div class="stat">{len(m['skills'])}</div></section>
{_budget_card(m)}
<section class="card"><h2>Look</h2><ul>{up_items}</ul></section>
{cons}
<section class="card"><h2>Skills I have</h2><ul>{skill_items}</ul></section>
<section class="card"><h2>Ideas</h2><ul>{idea_items}</ul></section>
<section class="card"><h2>Things you asked that I can't do yet</h2><ul>{gap_items}</ul></section>
</div></main></body></html>"""


def write(m: dict):
    f = paths.dashboard_dir() / "index.html"
    f.write_text(render(m))
    return f
