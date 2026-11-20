import json
import unittest
from unittest import mock

from tests.helpers import REPO, temp_root


class Guard(unittest.TestCase):
    def test_blocks_dangerous_code(self):
        from jarvis import guard
        self.assertTrue(guard.check_source("import subprocess"))
        self.assertTrue(guard.check_source("from os import system"))
        self.assertTrue(guard.check_source("eval('1')"))
        self.assertTrue(guard.check_source("x = ().__class__.__bases__"))
        self.assertTrue(guard.check_source("def ("))
        self.assertEqual(guard.check_source("import json\nfrom pathlib import Path\n"), [])

    def test_shipped_skills_pass_their_own_guard_and_tests(self):
        from jarvis import packages
        for group in ("skills", "library"):
            for d in sorted((REPO / group).iterdir()):
                if d.is_dir():
                    self.assertEqual(packages.guard_package(d), [], d.name)
                    ok, out = packages.run_tests(d)
                    self.assertTrue(ok, f"{d.name}: {out}")

    def test_write_package_rejects_traversal(self):
        from jarvis import packages
        import tempfile
        from pathlib import Path
        d = Path(tempfile.mkdtemp())
        for bad in ("../x.py", "/etc/x.py", "a.sh"):
            with self.assertRaises(ValueError):
                packages.write_package(d, {bad: "x"})


class Routing(unittest.TestCase):
    def test_route(self):
        root = temp_root()
        from jarvis import skills
        reg = skills.discover()
        s, args = skills.route("note buy milk", reg)
        self.assertEqual((s.NAME, args), ("quick_note", "buy milk"))
        s, args = skills.route("tv volume up", reg)
        self.assertEqual((s.NAME, args), ("tv_control", "volume up"))
        s, _ = skills.route("can you make a note of this", reg)  # trigger word inside a sentence
        self.assertEqual(s.NAME, "quick_note")
        self.assertIsNone(skills.route("order a pizza", reg)[0])

    def test_broken_skill_does_not_break_jarvis(self):
        root = temp_root()
        (root / "skills" / "broken").mkdir()
        (root / "skills" / "broken" / "skill.py").write_text("raise RuntimeError('x')")
        from jarvis import skills
        errors = {}
        reg = skills.discover(errors=errors)
        self.assertIn("quick_note", reg)
        self.assertIn("broken", errors)


class DailyLoop(unittest.TestCase):
    def test_offline_learning_over_several_days(self):
        root = temp_root()
        from jarvis import cli, learner, memory
        quiet = lambda *a, **k: None
        self.assertEqual(cli.main(["order", "a", "pizza"]), 1)  # unmet request becomes a gap
        self.assertEqual(memory.load()["gaps"], {"order a pizza": 1})
        learned = []
        for _ in range(4):
            r = learner.learn_today(force=True, say=quiet)
            learned.append(r["skill"])
            self.assertTrue((root / "lessons").glob("*.md"))
        self.assertEqual(sorted(learned), ["daily_briefing", "expense_log", "focus_session", "habit_tracker"])
        self.assertEqual(memory.load()["gaps"], {"order a pizza": 1})  # unrelated skills must not clear it
        self.assertEqual(len(set(learned)), 4)
        m = memory.load()
        self.assertEqual(m["day"], 4)
        self.assertEqual(len(m["upgrades"]), 4)
        self.assertTrue((root / "dashboard" / "index.html").exists())
        self.assertTrue((root / "JOURNAL.md").read_text().count("\n") == 4)
        # library exhausted, no key: it says so honestly instead of pretending
        r = learner.learn_today(force=True, say=quiet)
        self.assertIsNone(r["skill"])

    def test_once_per_day(self):
        temp_root()
        from jarvis import learner
        self.assertIsNotNone(learner.learn_today(say=lambda *a: None))
        self.assertIsNone(learner.learn_today(say=lambda *a: None))

    def test_gap_steers_library_choice(self):
        temp_root()
        from jarvis import cli, learner
        from jarvis import memory
        m = memory.load()
        m["gaps"]["track my spending money"] = 3
        memory.save(m)
        r = learner.learn_today(force=True, say=lambda *a: None)
        self.assertEqual(r["skill"], "expense_log")
        self.assertEqual(memory.load()["gaps"], {})

    def test_dashboard_reflects_upgrades_and_escapes_html(self):
        temp_root()
        from jarvis import dashboard
        m = {"day": 3, "skills": {"<b>x</b>": {"origin": "seed", "learned": "d"}}, "ideas": [], "gaps": {"<script>": 1},
             "upgrades": ["reactor", "constellation"], "custom_upgrades": []}
        out = dashboard.render(m)
        self.assertIn('class="reactor"', out)
        self.assertIn("constellation", out)
        self.assertNotIn("<script>", out)
        self.assertNotIn("<b>x</b>", out)


class WithBrain(unittest.TestCase):
    """The brain is mocked: we test Jarvis's validation of what it returns, not the model."""

    GOOD = {"name": "coin_flip", "files": {
        "skill.py": ('import random\nNAME="coin_flip"\nDESCRIPTION="Flip a coin."\nTRIGGERS=["flip"]\nEXAMPLES=["flip"]\n'
                     'LESSON="Flips a coin."\ndef run(args, ctx):\n    return random.choice(["heads","tails"])\n'),
        "test_skill.py": ('import unittest\nimport skill\nclass T(unittest.TestCase):\n    def test_a(self):\n'
                          '        self.assertIn(skill.run("", None), ("heads","tails"))\nif __name__=="__main__":\n    unittest.main()\n')}}

    def test_generated_skill_is_installed_after_passing(self):
        root = temp_root()
        from jarvis import generate
        with mock.patch("jarvis.brain.ask_json", return_value=self.GOOD):
            self.assertEqual(generate.generate_skill("coin", [], say=lambda *a: None), "coin_flip")
        self.assertTrue((root / "skills" / "coin_flip" / "skill.py").exists())

    def test_dangerous_generation_is_rejected(self):
        root = temp_root()
        from jarvis import generate
        bad = json.loads(json.dumps(self.GOOD))
        bad["files"]["skill.py"] = "import subprocess\n" + bad["files"]["skill.py"]
        with mock.patch("jarvis.brain.ask_json", return_value=bad):
            self.assertIsNone(generate.generate_skill("coin", [], say=lambda *a: None))
        self.assertFalse((root / "skills" / "coin_flip").exists())

    def test_failing_tests_are_rejected_then_retry_can_succeed(self):
        root = temp_root()
        from jarvis import generate
        bad = json.loads(json.dumps(self.GOOD))
        bad["files"]["test_skill.py"] = bad["files"]["test_skill.py"].replace('("heads","tails")', '("x",)')
        with mock.patch("jarvis.brain.ask_json", side_effect=[bad, self.GOOD]):
            self.assertEqual(generate.generate_skill("coin", [], say=lambda *a: None), "coin_flip")

    def test_css_upgrade_validation(self):
        from jarvis import upgrades
        self.assertTrue(upgrades.safe_css(".a{color:red}"))
        self.assertFalse(upgrades.safe_css("@import 'x';"))
        self.assertFalse(upgrades.safe_css(".a{background:url(http://evil)}"))
        self.assertFalse(upgrades.safe_css("</style><script>"))

    def test_build_and_approve_flow(self):
        root = temp_root()
        from jarvis import builder, memory
        m = memory.load()
        idea = {"id": 1, "title": "Coin flip", "why": "fun", "effort": "S", "status": "proposed", "date": "x"}
        m["ideas"].append(idea)
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "k"}), \
                mock.patch("jarvis.brain.ask_json", return_value={"files": self.GOOD["files"]}):
            msg = builder.build(m, idea)
        self.assertIn("Tests passed", msg)
        self.assertFalse((root / "skills" / "coin_flip").exists())  # nothing live until approved
        self.assertIn("Installed", builder.approve(m, "coin-flip"))
        self.assertTrue((root / "skills" / "coin_flip").exists())
        self.assertEqual(idea["status"], "installed")


if __name__ == "__main__":
    unittest.main()
