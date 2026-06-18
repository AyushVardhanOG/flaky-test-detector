"""
Parser for Jest output.

Expects Jest run with --verbose, e.g.: `jest --verbose`
We parse lines like:
    ✓ adds two numbers (3 ms)
    ✕ divides by zero (5 ms)

Jest doesn't print the full test path on each line by default, so we
track the nearest "describe" block (the indented parent line above)
to build a fully-qualified test name like "MathUtils > divides by zero".
"""

import re
from typing import Dict, List

# Matches "✓ test name (3 ms)" or "✕ test name (5 ms)" with leading whitespace
PASS_RE = re.compile(r"^\s*(✓|✔)\s+(.+?)(\s+\(\d+(\.\d+)?\s*m?s\))?$")
FAIL_RE = re.compile(r"^\s*(✕|✗|×)\s+(.+?)(\s+\(\d+(\.\d+)?\s*m?s\))?$")
# describe block headers are indented but have no check/cross mark, e.g. "MathUtils"
DESCRIBE_RE = re.compile(r"^(\s*)([A-Za-z].+)$")


def parse_jest_output(stdout: str) -> Dict[str, str]:
    """
    Returns {test_name: status} for a single Jest run's stdout.
    test_name includes the describe-block prefix when detectable, e.g.
    "MathUtils > divides by zero".
    """
    results = {}
    describe_stack: List[str] = []

    for raw_line in stdout.splitlines():
        if not raw_line.strip():
            continue

        pass_match = PASS_RE.match(raw_line)
        fail_match = FAIL_RE.match(raw_line)

        if pass_match:
            name = pass_match.group(2).strip()
            full_name = " > ".join(describe_stack + [name]) if describe_stack else name
            results[full_name] = "PASSED"
            continue

        if fail_match:
            name = fail_match.group(2).strip()
            full_name = " > ".join(describe_stack + [name]) if describe_stack else name
            results[full_name] = "FAILED"
            continue

        describe_match = DESCRIBE_RE.match(raw_line)
        if describe_match:
            indent = len(describe_match.group(1))
            level = indent // 2
            describe_stack = describe_stack[:level]
            describe_stack.append(describe_match.group(2).strip())

    return results


def parse_multiple_runs(stdouts: List[str]) -> Dict[str, List[str]]:
    """Same shape as pytest_parser.parse_multiple_runs — see that docstring."""
    per_run_results = [parse_jest_output(out) for out in stdouts]

    all_test_names = set()
    for run in per_run_results:
        all_test_names.update(run.keys())

    history: Dict[str, List[str]] = {name: [] for name in all_test_names}
    for run in per_run_results:
        for name in all_test_names:
            history[name].append(run.get(name, "MISSING"))

    return history