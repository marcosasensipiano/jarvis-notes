import os
import shutil
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def temp_root():
    """A scratch copy of the repo's skills + library, with JARVIS_ROOT pointing at it."""
    root = Path(tempfile.mkdtemp())
    for d in ("skills", "library"):
        shutil.copytree(REPO / d, root / d, ignore=shutil.ignore_patterns("__pycache__"))
    os.environ["JARVIS_ROOT"] = str(root)
    os.environ.pop("JARVIS_HOME", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    return root


def hand(fingers=(), thumb=False, thumb_up=True, pinch=False, wrist=(0.5, 0.9)):
    """Synthetic upright right-hand landmarks. `fingers` = subset of index/middle/ring/pinky that are extended."""
    wx, wy = wrist
    lm = [None] * 21
    lm[0] = (wx, wy)
    xs = {"index": 0.42, "middle": 0.5, "ring": 0.58, "pinky": 0.65}
    base = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}
    for name, b in base.items():
        x = wx + (xs[name] - 0.5)
        lm[b] = (x, wy - 0.3)                 # mcp
        lm[b + 1] = (x, wy - 0.35)            # pip
        lm[b + 2] = (x, wy - 0.45 if name in fingers else wy - 0.27)
        lm[b + 3] = (x, wy - 0.6 if name in fingers else wy - 0.25)  # tip
    lm[1], lm[2], lm[3] = (wx - 0.1, wy - 0.1), (wx - 0.13, wy - 0.2), (wx - 0.2, wy - 0.3)
    if thumb:
        lm[4] = (wx - 0.3, wy - 0.45) if thumb_up else (wx - 0.3, wy + 0.2)
    else:
        lm[4] = (wx - 0.04, wy - 0.28)
    if pinch:
        lm[8] = lm[4] = (wx - 0.08, wy - 0.5)
    return lm


ALL = ("index", "middle", "ring", "pinky")
