"""Visual upgrades. Jarvis unlocks one per learning day and teaches you what changed.
After the built-ins run out, Jarvis (with an API key) designs CSS-only upgrades itself."""
import re

UPGRADES = [
    {"id": "glow", "name": "Neon glow edges",
     "lesson": "Cards now have a soft cyan glow. It is a `box-shadow` with the accent colour; the second, larger, fainter shadow is what makes it feel like light rather than a border.",
     "css": ".card{box-shadow:0 0 0 1px var(--accent-dim),0 0 18px -4px var(--accent)}"},
    {"id": "scanlines", "name": "CRT scanlines",
     "lesson": "A faint horizontal line pattern sits over the page using a `repeating-linear-gradient` on a fixed pseudo-element. `pointer-events:none` keeps it from blocking clicks.",
     "css": "body::after{content:'';position:fixed;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(255,255,255,.03) 0 1px,transparent 1px 3px)}"},
    {"id": "reactor", "name": "Arc reactor",
     "lesson": "The header now has a rotating ring. Two concentric circles are drawn with `border`, and a CSS `@keyframes` animation spins the dashed one; `prefers-reduced-motion` turns it off for accessibility.",
     "css": ".reactor{display:inline-block;width:46px;height:46px;border-radius:50%;border:3px solid var(--accent);position:relative;vertical-align:middle;margin-right:14px;box-shadow:0 0 14px var(--accent)}.reactor::before{content:'';position:absolute;inset:6px;border-radius:50%;border:3px dashed var(--accent);animation:spin 6s linear infinite}.reactor::after{content:'';position:absolute;inset:16px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px var(--accent)}@keyframes spin{to{transform:rotate(360deg)}}@media(prefers-reduced-motion:reduce){.reactor::before{animation:none}}"},
    {"id": "grid", "name": "Holographic grid",
     "lesson": "The background gained a fine grid made from two crossed `linear-gradient`s sized with `background-size`. Changing that one number zooms the grid.",
     "css": "body{background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);background-size:36px 36px}"},
    {"id": "constellation", "name": "Skill constellation",
     "lesson": "Your skills are now drawn as stars around a core. Each skill's angle is `360 / count * index`, converted to x/y with sine and cosine. New skills appear automatically as nodes.",
     "css": ".constellation{width:100%;max-width:420px;display:block;margin:auto}.constellation circle.node{fill:var(--accent);filter:drop-shadow(0 0 6px var(--accent))}.constellation line{stroke:var(--accent-dim)}.constellation text{fill:var(--fg);font-size:9px;text-anchor:middle}"},
    {"id": "pulse", "name": "Pulsing status light",
     "lesson": "A status dot pulses to show Jarvis is alive. The trick is animating `box-shadow` spread with `@keyframes`, so no layout work happens.",
     "css": ".status{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--accent);animation:pulse 2s ease-out infinite}@keyframes pulse{0%{box-shadow:0 0 0 0 var(--accent)}100%{box-shadow:0 0 0 12px transparent}}@media(prefers-reduced-motion:reduce){.status{animation:none}}"},
]
_BAD_CSS = re.compile(r"@import|url\(|expression\(|</|javascript:|behavior:", re.I)


def all_upgrades(m: dict) -> list:
    return UPGRADES + list(m.get("custom_upgrades", []))


def unlocked(m: dict) -> list:
    got = set(m.get("upgrades", []))
    return [u for u in all_upgrades(m) if u["id"] in got]


def next_builtin(m: dict):
    got = set(m.get("upgrades", []))
    return next((u for u in UPGRADES if u["id"] not in got), None)


def safe_css(css: str) -> bool:
    return isinstance(css, str) and len(css) < 4000 and not _BAD_CSS.search(css)


def theme_vars(m: dict) -> str:
    return ":root{--bg:#04101a;--fg:#cfeaf5;--accent:#2ee6ff;--accent-dim:#14566a;--grid:rgba(46,230,255,.06);--card:#071b29}"
