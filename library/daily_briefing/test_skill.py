import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import skill


class T(unittest.TestCase):
    def test_empty(self):
        c = SimpleNamespace(data=Path(tempfile.mkdtemp()), now=datetime(2026, 6, 1, 8))
        out = skill.run("", c)
        self.assertIn("Good morning", out)
        self.assertIn("Clear runway", out)

    def test_combines_data(self):
        d = Path(tempfile.mkdtemp())
        (d / "notes.md").write_text("- a\n- b\n- c\n- d\n")
        (d / "timers.json").write_text(json.dumps([{"label": "tea", "due": "2026-06-01T07:00:00"}]))
        (d / "habits.json").write_text(json.dumps({"gym": ["2026-05-31"], "read": ["2026-06-01"]}))
        out = skill.run("", SimpleNamespace(data=d, now=datetime(2026, 6, 1, 13)))
        self.assertIn("Good afternoon", out)
        self.assertNotIn("- a", out)
        self.assertIn("- d", out)
        self.assertIn("Timers due: tea", out)
        self.assertIn("Habits still open: gym", out)


if __name__ == "__main__":
    unittest.main()
