"""
CI/CD quality gate for StudyMate AI evaluation (Day 14 bonus).

Runs the 20-pair golden benchmark through the evaluator, then compares the
current run against a committed baseline (baseline_metrics.json) using
BenchmarkRunner.run_regression. Exits non-zero on regression so CI blocks the
deploy — eval as a unit test.

Usage:
    python ci_gate.py                 # gate against existing baseline
    python ci_gate.py --update-baseline   # (re)write the baseline file

Behavior:
    - No baseline file yet  -> writes one from this run and passes (bootstrap).
    - Baseline exists       -> any metric average dropping > 0.05 fails the gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from solution.solution import RAGASEvaluator, BenchmarkRunner
from run_benchmark import build_qa_pairs, simulated_agent

BASELINE_FILE = Path(__file__).parent / "baseline_metrics.json"


def _to_records(results: list) -> list[dict]:
    return [
        {
            "faithfulness": r.faithfulness,
            "relevance": r.relevance,
            "completeness": r.completeness,
        }
        for r in results
    ]


def _load_baseline() -> list:
    data = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    return [SimpleNamespace(**rec) for rec in data]


def main() -> int:
    update = "--update-baseline" in sys.argv

    runner = BenchmarkRunner()
    evaluator = RAGASEvaluator()
    results = runner.run(build_qa_pairs(), simulated_agent, evaluator)
    report = runner.generate_report(results)

    print("=== StudyMate eval report ===")
    print(f"  pass_rate        : {report['pass_rate']:.2%}")
    print(f"  avg_faithfulness : {report['avg_faithfulness']:.3f}")
    print(f"  avg_relevance    : {report['avg_relevance']:.3f}")
    print(f"  avg_completeness : {report['avg_completeness']:.3f}")
    print(f"  failure_types    : {report['failure_types']}")

    if update or not BASELINE_FILE.exists():
        BASELINE_FILE.write_text(
            json.dumps(_to_records(results), indent=2), encoding="utf-8"
        )
        print(f"\n[baseline] wrote {BASELINE_FILE.name} ({len(results)} records).")
        print("GATE: PASS (baseline bootstrap)")
        return 0

    baseline = _load_baseline()
    reg = runner.run_regression(results, baseline)
    print("\n=== Regression vs baseline (drop > 0.05 fails) ===")
    for m in ("faithfulness", "relevance", "completeness"):
        print(f"  {m:13s}: baseline {reg[f'baseline_avg_{m}']:.3f} "
              f"-> new {reg[f'new_avg_{m}']:.3f}")

    if reg["passed"]:
        print("\nGATE: PASS — no regression detected.")
        return 0

    print(f"\nGATE: FAIL — regressed metrics: {reg['regressions']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
