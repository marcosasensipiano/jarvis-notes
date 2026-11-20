import unittest

from jarvis.gestures.classifier import SwipeDetector, classify_pose
from jarvis.gestures.engine import GestureEngine, DEFAULT_MAP
from tests.helpers import ALL, hand


class Poses(unittest.TestCase):
    def test_poses(self):
        self.assertEqual(classify_pose(hand(ALL, thumb=True)), "open_palm")
        self.assertEqual(classify_pose(hand()), "fist")
        self.assertEqual(classify_pose(hand(("index",))), "point")
        self.assertEqual(classify_pose(hand(("index", "middle"))), "peace")
        self.assertEqual(classify_pose(hand(thumb=True, thumb_up=True)), "thumbs_up")
        self.assertEqual(classify_pose(hand(thumb=True, thumb_up=False)), "thumbs_down")
        self.assertEqual(classify_pose(hand(("middle", "ring", "pinky"), pinch=True)), "pinch")

    def test_bad_input(self):
        self.assertIsNone(classify_pose([(0, 0)] * 5))


class Swipes(unittest.TestCase):
    def feed(self, pts, dt=0.05):
        d, out = SwipeDetector(), None
        for i, (x, y) in enumerate(pts):
            out = d.update(i * dt, x, y) or out
        return out

    def test_directions(self):
        self.assertEqual(self.feed([(0.3 + 0.06 * i, 0.5) for i in range(7)]), "swipe_right")
        self.assertEqual(self.feed([(0.7 - 0.06 * i, 0.5) for i in range(7)]), "swipe_left")
        self.assertEqual(self.feed([(0.5, 0.7 - 0.06 * i) for i in range(7)]), "swipe_up")
        self.assertEqual(self.feed([(0.5, 0.3 + 0.06 * i) for i in range(7)]), "swipe_down")

    def test_slow_drift_and_diagonal_ignored(self):
        self.assertIsNone(self.feed([(0.3 + 0.005 * i, 0.5) for i in range(30)]))
        self.assertIsNone(self.feed([(0.3 + 0.06 * i, 0.3 + 0.06 * i) for i in range(7)]))


class Engine(unittest.TestCase):
    def engine(self):
        return GestureEngine({"hold_seconds": 0.8, "cooldown_seconds": 1.5, "map": dict(DEFAULT_MAP)})

    def held(self, pose_lm, seconds=4):
        e, fired = self.engine(), []
        for i in range(int(seconds * 30)):
            hit = e.update(i / 30, pose_lm)
            if hit:
                fired.append((i / 30, hit))
        return fired

    def test_held_fist_mutes_once_not_repeatedly(self):
        fired = self.held(hand())
        self.assertEqual([f[1] for f in fired], [("fist", "mute")])
        self.assertGreaterEqual(fired[0][0], 0.8)

    def test_held_thumbs_up_repeats_volume_with_cooldown(self):
        fired = self.held(hand(thumb=True, thumb_up=True))
        self.assertGreaterEqual(len(fired), 2)
        self.assertTrue(all(f[1] == ("thumbs_up", "volume_up") for f in fired))
        self.assertGreaterEqual(fired[1][0] - fired[0][0], 1.5 - 1e-9)

    def test_brief_pose_does_not_fire(self):
        e = self.engine()
        self.assertTrue(all(e.update(i / 30, hand()) is None for i in range(15)))  # 0.5s

    def test_pose_change_resets_hold(self):
        e = self.engine()
        for i in range(20):
            e.update(i / 30, hand())
        for i in range(20, 40):  # switch to peace; hold timer restarts
            self.assertIsNone(e.update(i / 30, hand(("index", "middle"))))

    def test_open_palm_swipe(self):
        e, out = self.engine(), None
        for i in range(8):
            out = e.update(i * 0.05, hand(ALL, thumb=True, wrist=(0.25 + 0.07 * i, 0.9))) or out
        self.assertEqual(out, ("swipe_right", "forward"))

    def test_fist_motion_is_not_a_swipe(self):
        e = self.engine()
        outs = [e.update(i * 0.05, hand(wrist=(0.25 + 0.07 * i, 0.9))) for i in range(8)]
        self.assertTrue(all(o is None for o in outs))

    def test_no_hand_resets(self):
        e = self.engine()
        for i in range(10):
            e.update(i / 30, hand())
        self.assertIsNone(e.update(0.4, None))


if __name__ == "__main__":
    unittest.main()
