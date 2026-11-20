import unittest
from types import SimpleNamespace

import skill


class FakeTV:
    def __init__(self):
        self.sent = []

    def send(self, action):
        self.sent.append(action)
        return f"ok {action}"


class T(unittest.TestCase):
    def test_resolve(self):
        self.assertEqual(skill.resolve("volume up"), "volume_up")
        self.assertEqual(skill.resolve("make it louder please"), "volume_up")
        self.assertEqual(skill.resolve("up"), "up")
        self.assertIsNone(skill.resolve("banana"))

    def test_run(self):
        tv = FakeTV()
        self.assertEqual(skill.run("pause", SimpleNamespace(tv=tv)), "ok play_pause")
        self.assertEqual(tv.sent, ["play_pause"])

    def test_no_tv(self):
        self.assertIn("No TV configured", skill.run("home", SimpleNamespace(tv=None)))

    def test_unknown(self):
        self.assertIn("I know", skill.run("dance", SimpleNamespace(tv=FakeTV())))


if __name__ == "__main__":
    unittest.main()
