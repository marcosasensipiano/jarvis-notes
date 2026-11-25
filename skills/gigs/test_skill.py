import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import skill


class T(unittest.TestCase):
    def test_lists_non_adverts(self):
        root = Path(tempfile.mkdtemp())
        d = root / "gigfinder" / "web" / "data"
        d.mkdir(parents=True)
        (d / "offers.json").write_text(json.dumps({"updated": "2026-01-01T10:00", "offers": [
            {"title": "Se busca pianista", "url": "u1", "kind": "demand", "town": "Sagunto", "distKm": 0, "firstSeen": "2026-01-01"},
            {"title": "Ofrezco violin", "url": "u2", "kind": "advert"}]}))
        out = skill.run("", SimpleNamespace(root=root))
        self.assertIn("Se busca pianista", out)
        self.assertNotIn("Ofrezco", out)

    def test_missing(self):
        self.assertIn("No offers yet", skill.run("", SimpleNamespace(root=Path(tempfile.mkdtemp()))))
