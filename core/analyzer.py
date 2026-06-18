"""
Core flakiness analysis.

Takes the {test_name: [status_run1, status_run2, ...]} history produced
by any parser, and computes a flakiness score + classification per test.

Classification logic:
- STABLE_PASS: passed every run
- STABLE_FAIL: failed every run (consistently broken, NOT flaky — this
  distinction matters: a test that always fails is a real bug, not flakiness)
- FLAKY: mixed PASSED/FAILED across runs — this is the interesting case
- ERRORED: had ERROR status in any run (often infra/setup issues, flagged separately)
"""

from dataclasses import dataclass
from typing import Dict, List
import json


@dataclass
class FlakinessReport:
    test_name: str
    classification: str  # STABLE_PASS / STABLE_FAIL / FLAKY / ERRORED
    flakiness_score: float  # 0.0 (never flips) to 1.0 (flips every run)
    pass_count: int
    fail_count: int
    total_runs: int
    history: List[str]


def compute_flakiness_score(history: List[str]) -> float:
    """
    Score = number of PASS<->FAIL transitions / (total_runs - 1).
    A test that goes PASS,PASS,PASS,PASS scores 0.0 (stable).
    A test that goes PASS,FAIL,PASS,FAIL scores 1.0 (maximally flaky).
    A test that goes PASS,PASS,FAIL,PASS scores 0.67 (2 transitions / 3 gaps).

    This catches flakiness better than a simple "pass rate" metric would:
    a test that fails the SAME way every time (e.g. always fails on a
    specific assertion) has a 0% pass rate but ISN'T flaky — it's just
    broken. Flakiness is about INCONSISTENCY, not failure rate.
    """
    # Only count PASSED/FAILED for transitions; ignore SKIPPED/MISSING/ERROR
    relevant = [s for s in history if s in ("PASSED", "FAILED")]
    if len(relevant) < 2:
        return 0.0

    transitions = sum(
        1 for i in range(1, len(relevant)) if relevant[i] != relevant[i - 1]
    )
    return round(transitions / (len(relevant) - 1), 3)


def classify_test(history: List[str]) -> str:
    statuses = set(history)

    if "ERROR" in statuses:
        return "ERRORED"
    if statuses == {"PASSED"}:
        return "STABLE_PASS"
    if statuses == {"FAILED"}:
        return "STABLE_FAIL"
    if "PASSED" in statuses and "FAILED" in statuses:
        return "FLAKY"
    return "UNKNOWN"


def analyze(history: Dict[str, List[str]]) -> List[FlakinessReport]:
    """
    Main entry point. Takes the {test_name: [statuses]} dict and returns
    a sorted list of FlakinessReport, most flaky first.
    """
    reports = []
    for test_name, statuses in history.items():
        score = compute_flakiness_score(statuses)
        classification = classify_test(statuses)
        reports.append(
            FlakinessReport(
                test_name=test_name,
                classification=classification,
                flakiness_score=score,
                pass_count=statuses.count("PASSED"),
                fail_count=statuses.count("FAILED"),
                total_runs=len(statuses),
                history=statuses,
            )
        )

    # Sort: FLAKY tests first (by score descending), then everything else
    reports.sort(key=lambda r: (r.classification != "FLAKY", -r.flakiness_score))
    return reports


def reports_to_json(reports: List[FlakinessReport], path: str):
    with open(path, "w") as f:
        json.dump([r.__dict__ for r in reports], f, indent=2)


def print_summary(reports: List[FlakinessReport]):
    flaky = [r for r in reports if r.classification == "FLAKY"]
    stable_fail = [r for r in reports if r.classification == "STABLE_FAIL"]
    errored = [r for r in reports if r.classification == "ERRORED"]

    print(f"\n{'='*60}")
    print(f"FLAKINESS REPORT")
    print(f"{'='*60}")
    print(f"Total tests analyzed: {len(reports)}")
    print(f"  Flaky:        {len(flaky)}")
    print(f"  Stable fail:  {len(stable_fail)} (consistently broken, not flaky)")
    print(f"  Errored:      {len(errored)}")
    print(f"{'='*60}\n")

    if flaky:
        print("⚠️  FLAKY TESTS (sorted by severity):\n")
        for r in flaky:
            print(f"  [{r.flakiness_score:.2f}] {r.test_name}")
            print(f"        {r.pass_count} passed / {r.fail_count} failed / {r.total_runs} runs")
            print(f"        history: {' → '.join(r.history)}")
            print()
    else:
        print("No flaky tests detected. ✅")