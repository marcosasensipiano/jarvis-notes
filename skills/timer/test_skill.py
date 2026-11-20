import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import skill


class T(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(skill.parse_duration("1h30m laundry"), (5400, "laundry"))
        self.assertEqual(skill.parse_duration("90 seconds"), (90, ""))
        self.assertEqual(skill.parse_duration("nothing"), (0, "nothing"))

    def test_set_and_list(self):
        now = datetime(2026, 1, 1, 12, 0)
        c = SimpleNamespace(data=Path(tempfile.mkdtemp()), now=now)
        self.assertIn("due 12:10", skill.run("10m tea", c))
        c.now = now + timedelta(minutes=4)
        self.assertIn("tea: in 6m", skill.run("", c))
        c.now = now + timedelta(minutes=11)
        self.assertIn("tea: DUE", skill.run("", c))

    def test_empty(self):
        c = SimpleNamespace(data=Path(tempfile.mkdtemp()), now=datetime(2026, 1, 1))
        self.assertIn("No timers", skill.run("", c))


if __name__ == "__main__":
    unittest.main()
