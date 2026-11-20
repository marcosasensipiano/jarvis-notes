import io
import json
import unittest
from unittest import mock

from tests.helpers import temp_root


def fake_response(text="{}", inp=1000, out=2000, model="claude-sonnet-5-5"):
    body = json.dumps({"model": model, "content": [{"type": "text", "text": text}],
                       "usage": {"input_tokens": inp, "output_tokens": out}}).encode()
    r = mock.MagicMock()
    r.__enter__.return_value = io.BytesIO(body)
    return r


class Spend(unittest.TestCase):
    def setUp(self):
        temp_root()
        import os
        os.environ["ANTHROPIC_API_KEY"] = "test"

    def test_cost_math_matches_published_prices(self):
        from jarvis import spend
        # Sonnet 5.5: $2/M in, $10/M out -> 1M in + 1M out = $12
        self.assertAlmostEqual(spend.cost("claude-sonnet-5-5", {"input_tokens": 1_000_000, "output_tokens": 1_000_000}), 12.0)
        self.assertAlmostEqual(spend.cost("claude-haiku-5-5", {"input_tokens": 1_000_000, "output_tokens": 1_000_000}), 0.6)
        # unknown model is priced pessimistically, never as free
        self.assertGreater(spend.cost("claude-mystery", {"output_tokens": 1000}), spend.cost("claude-sonnet-5-5", {"output_tokens": 1000}))

    def test_real_call_path_records_spend(self):
        from jarvis import brain, spend
        spend.set_budget(5.0)
        with mock.patch("urllib.request.urlopen", return_value=fake_response(inp=1000, out=2000)):
            brain.ask("hi", max_tokens=3000, purpose="skill")
        s = spend.summary()
        self.assertAlmostEqual(s["spent"], 0.022, places=6)  # 1000*2/1e6 + 2000*10/1e6
        self.assertAlmostEqual(s["left"], 5.0 - 0.022, places=6)
        self.assertEqual((s["calls"], s["last"]["purpose"]), (1, "skill"))

    def test_hard_stop_blocks_call_before_it_is_made(self):
        from jarvis import brain, spend
        spend.set_budget(0.01)
        with mock.patch("urllib.request.urlopen") as op:
            with self.assertRaises(spend.BudgetExhausted):
                brain.ask("hi", max_tokens=6000)  # worst case $0.06 > $0.01 left
        op.assert_not_called()

    def test_exhausted_budget_makes_jarvis_fall_back_offline(self):
        from jarvis import brain, learner, spend
        spend.set_budget(1.0)
        m = __import__("jarvis.memory", fromlist=["x"]).load()
        m["spend"]["spent_usd"] = 1.0
        __import__("jarvis.memory", fromlist=["x"]).save(m, keep_spend=False)
        self.assertFalse(brain.available())
        r = learner.learn_today(force=True, say=lambda *a: None)
        self.assertEqual(r["skill"], "daily_briefing")  # library, not the API

    def test_no_budget_means_no_limit_but_still_tracked(self):
        from jarvis import brain, spend
        with mock.patch("urllib.request.urlopen", return_value=fake_response()):
            brain.ask("hi")
        s = spend.summary()
        self.assertIsNone(s["budget"])
        self.assertIsNone(s["left"])
        self.assertGreater(s["spent"], 0)

    def test_stale_memory_save_cannot_erase_spend(self):
        """learn_today holds an old copy of memory while API calls record spend; its final save must keep the spend."""
        from jarvis import memory, spend
        stale = memory.load()
        spend.record("claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 100_000}, "x")  # $1.00
        memory.save(stale)  # the stale copy still says spent=0
        self.assertAlmostEqual(spend.summary()["spent"], 1.0)

    def test_topup(self):
        from jarvis import spend
        spend.set_budget(2.0)
        spend.add_budget(3.0)
        self.assertEqual(spend.summary()["budget"], 5.0)

    def test_widget_and_cli(self):
        from jarvis import cli, dashboard, memory, spend
        from io import StringIO
        from contextlib import redirect_stdout
        self.assertIn("no budget", dashboard.render(memory.load()))
        buf = StringIO()
        with redirect_stdout(buf):
            self.assertEqual(cli.main(["budget", "5.8"]), 0)
        self.assertIn("LEFT $5.80", buf.getvalue())
        spend.record("claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 50_000}, "x")  # $0.50
        page = dashboard.render(memory.load())
        self.assertIn("$5.30 left", page)
        self.assertIn("spent $0.500 of $5.80", page)
        with redirect_stdout(StringIO()):
            self.assertEqual(cli.main(["budget", "banana"]), 1)

    def test_widget_turns_red_when_low(self):
        from jarvis import dashboard, memory, spend
        spend.set_budget(1.0)
        spend.record("claude-sonnet-5-5", {"output_tokens": 90_000}, "x")  # $0.90 -> 10% left
        self.assertIn('class="bar low"', dashboard.render(memory.load()))


class Profile(unittest.TestCase):
    def setUp(self):
        temp_root()
        import os
        os.environ["JARVIS_HOME"] = str(__import__("tempfile").mkdtemp())

    def test_profile_reaches_the_prompts_for_skills_and_ideas(self):
        from jarvis import generate, ideas, memory, profile
        profile.save({"role": "student of design", "hours": "6", "goal": "earn 500 a month freelancing"})
        self.assertIn("student of design", profile.summary())
        seen = []
        with mock.patch("jarvis.brain.ask_json", side_effect=lambda p, *a, **k: seen.append(p) or []):
            m = memory.load()
            with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "k"}):
                ideas.refresh(m)
        self.assertTrue(any("earn 500 a month freelancing" in p for p in seen))

    def test_learner_target_includes_profile(self):
        from jarvis import learner, memory, profile
        profile.save({"annoyances": "forgetting invoices"})
        seen = []
        m = memory.load()
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "k"}), \
                mock.patch("jarvis.generate.generate_skill", side_effect=lambda t, *a, **k: seen.append(t) or None):
            learner.acquire_skill(m, say=lambda *a: None)
        self.assertIn("forgetting invoices", seen[0])

    def test_empty_profile_is_harmless(self):
        from jarvis import profile
        self.assertEqual(profile.summary(), "")


if __name__ == "__main__":
    unittest.main()
