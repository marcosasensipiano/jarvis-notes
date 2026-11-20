import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import skill


class T(unittest.TestCase):
    def test_log(self):
        c = SimpleNamespace(data=Path(tempfile.mkdtemp()), now=datetime(2026, 2, 2, 9, 0))
        self.assertIn("Ends at 09:25", skill.run("25 write report", c))
        skill.run("50", c)
        out = skill.run("log", c)
        self.assertIn("Total today: 75 min", out)
        self.assertIn("write report", out)

    def test_other_day_not_counted(self):
        data = Path(tempfile.mkdtemp())
        skill.run("30", SimpleNamespace(data=data, now=datetime(2026, 2, 1, 9)))
        self.assertIn("No focus", skill.run("", SimpleNamespace(data=data, now=datetime(2026, 2, 2, 9))))


if __name__ == "__main__":
    unittest.main()
