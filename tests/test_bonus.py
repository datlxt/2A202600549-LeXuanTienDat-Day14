"""
Day 14 — BONUS tests for the custom metric (evaluate_conciseness).

Run from the day folder:
    pytest tests/ -v
"""

import importlib.util
import sys
import unittest
from pathlib import Path

DAY_DIR = Path(__file__).parent.parent
SOLUTION_DIR = DAY_DIR / "solution"


def _load(path: Path, unique_name: str):
    spec = importlib.util.spec_from_file_location(unique_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = mod
    spec.loader.exec_module(mod)
    return mod


if (SOLUTION_DIR / "solution.py").exists():
    _m = _load(SOLUTION_DIR / "solution.py", f"{DAY_DIR.name}.bonus_solution")
else:
    _m = _load(DAY_DIR / "template.py", f"{DAY_DIR.name}.bonus_template")

RAGASEvaluator = getattr(_m, "RAGASEvaluator")


class TestConcisenessMetric(unittest.TestCase):
    def setUp(self):
        self.ev = RAGASEvaluator()

    def test_concise_answer_scores_one(self):
        # Same length / shorter than reference -> fully concise.
        score = self.ev.evaluate_conciseness(
            "Paris is the capital", "Paris is the capital of France"
        )
        self.assertEqual(score, 1.0)

    def test_verbose_answer_is_penalized(self):
        expected = "Overfitting means the model memorizes training data"
        verbose = (
            "Overfitting means the model memorizes training data and also it "
            "happens a lot in deep neural networks with many layers and tons "
            "of parameters and very little regularization across many epochs "
            "during a long training procedure performed on small datasets"
        )
        concise = "Overfitting means the model memorizes training data badly"
        self.assertLess(
            self.ev.evaluate_conciseness(verbose, expected),
            self.ev.evaluate_conciseness(concise, expected),
        )

    def test_in_range(self):
        score = self.ev.evaluate_conciseness("some long answer here", "short")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_empty_is_one(self):
        self.assertEqual(self.ev.evaluate_conciseness("", "expected"), 1.0)
        self.assertEqual(self.ev.evaluate_conciseness("answer", ""), 1.0)


if __name__ == "__main__":
    unittest.main()
