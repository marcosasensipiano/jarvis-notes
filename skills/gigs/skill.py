import json
import subprocess
import sys
from pathlib import Path

NAME = "gigs"
DESCRIPTION = "Piano/violin gig offers around Sagunto, from the Gig Finder app."
TRIGGERS = ["gigs", "gig", "offers", "ofertas"]
EXAMPLES = ["gigs", "gigs new", "gigs refresh"]
LESSON = """\
**gigs** connects Jarvis to the Gig Finder app (`gigfinder/`).

- `gigs` -> top offers where someone is looking for a pianist/violinist near Sagunto.
- `gigs new` -> only offers found in the last 24 hours.
- `gigs refresh` -> run a new search now (otherwise the app updates itself hourly).

It only reads `gigfinder/web/data/offers.json`; the app does the searching.
"""


def _file(ctx):
    root = Path(getattr(ctx, "root", None) or Path(__file__).resolve().parents[2])
    return root / "gigfinder" / "web" / "data" / "offers.json"


def run(args, ctx):
    f = _file(ctx)
    if args.strip() == "refresh":
        script = f.parents[2] / "src" / "run.js"
        try:
            subprocess.run(["node", str(script)], timeout=600, check=True, capture_output=True)
        except Exception as e:
            return f"Refresh failed ({e}). Is Node.js installed?"
    if not f.exists():
        return "No offers yet. Start the app: gigfinder/start.bat (or `gigs refresh`)."
    data = json.loads(f.read_text())
    offers = [o for o in data.get("offers", []) if o.get("kind") != "advert"]
    if args.strip() == "new":
        from datetime import datetime, timedelta, timezone
        cut = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        offers = [o for o in offers if o.get("firstSeen", "") > cut]
    if not offers:
        return "No matching offers right now."
    lines = [f"{len(offers)} offers (updated {data.get('updated', '?')[:16]}):"]
    for o in offers[:8]:
        where = f" [{o['town']}, {o['distKm']} km]" if o.get("town") else ""
        lines.append(f"- {o['title'][:80]}{where}\n  {o['url']}")
    return "\n".join(lines)
