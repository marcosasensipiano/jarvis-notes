import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import skill


class T(unittest.TestCase):
    def ctx(self):
        return SimpleNamespace(data=Path(tempfile.mkdtemp()), now=datetime(2026, 1, 2, 9, 30))

    def test_add_and_list(self):
        c = self.ctx()
        self.assertEqual(skill.run("buy milk", c), "Noted: buy milk")
        self.assertIn("2026-01-02 09:30 buy milk", skill.run("", c))

    def test_empty(self):
        self.assertIn("No notes", skill.run("", self.ctx()))


if __name__ == "__main__":
    unittest.main()
