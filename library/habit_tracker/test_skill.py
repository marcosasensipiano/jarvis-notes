import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import skill


class T(unittest.TestCase):
    def test_streak_over_days(self):
        data = Path(tempfile.mkdtemp())
        day = datetime(2026, 3, 1, 8)
        for i in range(3):
            out = skill.run("done gym", SimpleNamespace(data=data, now=day + timedelta(days=i)))
        self.assertIn("Streak 3", out)
        listing = skill.run("", SimpleNamespace(data=data, now=day + timedelta(days=3)))
        self.assertIn("gym: streak 3", listing)
        self.assertNotIn("done today", listing)

    def test_idempotent(self):
        c = SimpleNamespace(data=Path(tempfile.mkdtemp()), now=datetime(2026, 3, 1))
        skill.run("read", c)
        self.assertIn("Streak 1", skill.run("read", c))

    def test_empty(self):
        c = SimpleNamespace(data=Path(tempfile.mkdtemp()), now=datetime(2026, 3, 1))
        self.assertIn("No habits", skill.run("", c))


if __name__ == "__main__":
    unittest.main()
