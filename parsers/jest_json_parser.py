"""
Robust Jest parser using `jest --json` output instead of scraping
console text. This is the RECOMMENDED parser to use — console text
scraping (jest_parser.py) is kept as a fallback for cases where you
can't control how the test command is invoked.

Run tests with: jest --json --outputFile=results.json
Or pipe directly: jest --json (then this parses the stdout JSON blob)
"""

import json
from typing import Dict, List


def parse_jest_json(json_str: str) -> Dict[str, str]:
    """
    Parses a single `jest --json` output blob.
    Returns {test_full_name: status} where status is PASSED/FAILED/SKIPPED.
    """
    results = {}
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return results  # malformed/empty output for this run

    for test_file in data.get("testResults", []):
        for assertion in test_file.get("assertionResults", []):
            full_name = assertion.get("fullName", assertion.get("title", "unknown"))
            status = assertion.get("status", "unknown").upper()  # passed/failed/pending -> PASSED/FAILED/PENDING
            results[full_name] = status

    return results


def parse_multiple_runs(json_strs: List[str]) -> Dict[str, List[str]]:
    """Same shape as other parsers — see pytest_parser.parse_multiple_runs."""
    per_run_results = [parse_jest_json(s) for s in json_strs]

    all_test_names = set()
    for run in per_run_results:
        all_test_names.update(run.keys())

    history: Dict[str, List[str]] = {name: [] for name in all_test_names}
    for run in per_run_results:
        for name in all_test_names:
            history[name].append(run.get(name, "MISSING"))

    return history