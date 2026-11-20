import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import skill


class T(unittest.TestCase):
    def test_log_and_total(self):
        c = SimpleNamespace(data=Path(tempfile.mkdtemp()), now=datetime(2026, 5, 10))
        self.assertEqual(skill.run("4,50 coffee", c), "Logged 4.50 for coffee.")
        skill.run("32 groceries milk", c)
        skill.run("3 coffee again", c)
        out = skill.run("", c)
        self.assertIn("groceries: 32.00", out)
        self.assertIn("coffee: 7.50", out)
        self.assertIn("Total 2026-05: 39.50", out)

    def test_other_month_excluded(self):
        data = Path(tempfile.mkdtemp())
        skill.run("10 x", SimpleNamespace(data=data, now=datetime(2026, 4, 30)))
        self.assertIn("No spending", skill.run("", SimpleNamespace(data=data, now=datetime(2026, 5, 1))))


if __name__ == "__main__":
    unittest.main()
