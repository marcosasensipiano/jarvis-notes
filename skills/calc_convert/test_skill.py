import unittest
from types import SimpleNamespace

import skill

C = SimpleNamespace()


class T(unittest.TestCase):
    def test_calc(self):
        self.assertEqual(skill.run("2*(3+4)", C), "14")
        self.assertEqual(skill.run("1/4", C), "0.25")

    def test_no_code_execution(self):
        self.assertIn("Sorry", skill.run("__import__('os').system('echo hi')", C))
        self.assertIn("Sorry", skill.run("9**9**9", C))

    def test_convert(self):
        self.assertIn("3.107", skill.run("5 km to mi", C))
        self.assertIn("21.11", skill.run("70 f to c", C))
        self.assertIn("Sorry", skill.run("5 km to kg", C))

    def test_zero_division(self):
        self.assertIn("Sorry", skill.run("1/0", C))


if __name__ == "__main__":
    unittest.main()
