"""Hand-pose and swipe classification from 21 MediaPipe-style landmarks. Pure Python, no camera needed.

Landmark indices: 0 wrist; 1-4 thumb; 5-8 index; 9-12 middle; 13-16 ring; 17-20 pinky (tip is the last of each).
A finger counts as extended when its tip is clearly farther from the wrist than its middle joint, which
works whatever way the hand is rotated."""
import math


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def hand_size(lm):
    return _d(lm[0], lm[9]) or 1e-6


def finger_states(lm) -> dict:
    wrist = lm[0]
    st = {name: _d(lm[tip], wrist) > _d(lm[pip], wrist) * 1.1
          for name, tip, pip in (("index", 8, 6), ("middle", 12, 10), ("ring", 16, 14), ("pinky", 20, 18))}
    st["thumb"] = _d(lm[4], lm[17]) > _d(lm[2], lm[17]) * 1.2
    return st


def classify_pose(lm):
    """Return one of: open_palm, fist, point, peace, thumbs_up, thumbs_down, pinch, or None."""
    if len(lm) != 21:
        return None
    s = finger_states(lm)
    four = [s["index"], s["middle"], s["ring"], s["pinky"]]
    if _d(lm[4], lm[8]) < 0.3 * hand_size(lm) and s["middle"] and s["ring"] and s["pinky"]:
        return "pinch"
    if all(four):
        return "open_palm"
    if not any(four):
        if not s["thumb"]:
            return "fist"
        if lm[4][1] < lm[0][1]:
            return "thumbs_up"
        return "thumbs_down"
    if s["index"] and not (s["middle"] or s["ring"] or s["pinky"]):
        return "point"
    if s["index"] and s["middle"] and not (s["ring"] or s["pinky"]):
        return "peace"
    return None


class SwipeDetector:
    """Detects a fast, mostly-straight wrist movement. Coordinates are as the user sees them
    (the runtime mirrors the camera), so +x is the user's right."""

    def __init__(self, window=0.45, min_dist=0.25, dominance=1.8, cooldown=0.9):
        self.window, self.min_dist, self.dominance, self.cooldown = window, min_dist, dominance, cooldown
        self.hist, self.blocked_until = [], 0.0

    def reset(self):
        self.hist = []

    def update(self, t, x, y):
        self.hist.append((t, x, y))
        self.hist = [h for h in self.hist if t - h[0] <= self.window]
        if t < self.blocked_until or len(self.hist) < 3:
            return None
        dx, dy = self.hist[-1][1] - self.hist[0][1], self.hist[-1][2] - self.hist[0][2]
        ax, ay = abs(dx), abs(dy)
        if max(ax, ay) < self.min_dist:
            return None
        if ax >= ay * self.dominance:
            ev = "swipe_right" if dx > 0 else "swipe_left"
        elif ay >= ax * self.dominance:
            ev = "swipe_down" if dy > 0 else "swipe_up"
        else:
            return None
        self.hist, self.blocked_until = [], t + self.cooldown
        return ev
