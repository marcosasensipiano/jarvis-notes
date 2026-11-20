"""Turns a stream of hand landmarks into TV actions, with the safety rails that make gesture control livable:
a pose must be held still before it fires, every action has a cooldown, and swipes only count with an open palm."""
import json
from .. import paths
from .classifier import SwipeDetector, classify_pose

DEFAULT_MAP = {"open_palm": "play_pause", "fist": "mute", "peace": "home", "thumbs_up": "volume_up",
               "thumbs_down": "volume_down", "swipe_up": "volume_up", "swipe_down": "volume_down",
               "swipe_left": "rewind", "swipe_right": "forward"}


# Only these keep firing while you hold the pose (hold thumbs-up to keep raising volume).
# Everything else (mute, play/pause, home...) fires once, then waits for the pose to change.
REPEATABLE = {"volume_up", "volume_down"}


def load_config() -> dict:
    cfg = {"hold_seconds": 0.8, "cooldown_seconds": 1.5, "map": dict(DEFAULT_MAP)}
    f = paths.config_dir() / "gestures.json"
    if f.exists():
        user = json.loads(f.read_text())
        cfg.update({k: v for k, v in user.items() if k != "map"})
        cfg["map"] = {**cfg["map"], **user.get("map", {})}
    return cfg


class GestureEngine:
    def __init__(self, cfg=None):
        self.cfg = cfg or load_config()
        self.swipe = SwipeDetector()
        self.pose, self.pose_since, self.last_pos = None, 0.0, None
        self.fired_until = 0.0
        self.latched = False

    def update(self, t, lm):
        """Feed one frame (lm = 21 (x, y) points as the user sees them, or None if no hand).
        Returns (gesture, action) when something fires, else None."""
        if lm is None:
            self.pose, self.last_pos = None, None
            self.swipe.reset()
            return None
        pose = classify_pose(lm)
        wrist = lm[0]
        moved = self.last_pos is not None and ((wrist[0] - self.last_pos[0]) ** 2 + (wrist[1] - self.last_pos[1]) ** 2) ** 0.5 > 0.04
        self.last_pos = wrist
        if pose == "open_palm":
            ev = self.swipe.update(t, wrist[0], wrist[1])
            if ev and ev in self.cfg["map"] and t >= self.fired_until:
                self.fired_until = t + self.cfg["cooldown_seconds"]
                self.pose = None
                return ev, self.cfg["map"][ev]
        else:
            self.swipe.reset()
        if pose != self.pose or moved:
            self.pose, self.pose_since, self.latched = pose, t, False
            return None
        if (pose and pose in self.cfg["map"] and not self.latched
                and t - self.pose_since >= self.cfg["hold_seconds"] and t >= self.fired_until):
            action = self.cfg["map"][pose]
            self.fired_until = t + self.cfg["cooldown_seconds"]
            self.pose_since = t
            self.latched = action not in REPEATABLE
            return pose, action
        return None
