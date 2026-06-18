"""
Parser for pytest output.

Expects pytest run with verbose flag, e.g.: `pytest -v` or `pytest -v --tb=no`
We parse lines like:
    tests/test_math.py::test_addition PASSED
    tests/test_math.py::test_division FAILED
"""

import re
from typing import Dict, List

# Matches "path::test_name PASSED" / "FAILED" / "ERROR" / "SKIPPED"
PYTEST_LINE_RE = re.compile(r"^(\S+::\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)")


def parse_pytest_output(stdout: str) -> Dict[str, str]:
    """
    Returns {test_name: status} for a single pytest run's stdout.
    status is one of PASSED / FAILED / ERROR / SKIPPED.
    """
    results = {}
    for line in stdout.splitlines():
        match = PYTEST_LINE_RE.match(line.strip())
        if match:
            test_name, status = match.groups()
            results[test_name] = status
    return results


def parse_multiple_runs(stdouts: List[str]) -> Dict[str, List[str]]:
    """
    Given stdout from N runs, returns {test_name: [status_run1, status_run2, ...]}
    Tests that don't appear in every run are still included, with "MISSING"
    for runs where they didn't show up (e.g. test file failed to collect).
    """
    per_run_results = [parse_pytest_output(out) for out in stdouts]

    all_test_names = set()
    for run in per_run_results:
        all_test_names.update(run.keys())

    history: Dict[str, List[str]] = {name: [] for name in all_test_names}
    for run in per_run_results:
        for name in all_test_names:
            history[name].append(run.get(name, "MISSING"))

    return history