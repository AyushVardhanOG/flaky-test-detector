"""
Core test runner — executes a given test command N times and captures
raw stdout/stderr + timing + exit code for each run.

This is intentionally language-agnostic: it doesn't know what "pytest"
or "jest" means. It just runs a shell command repeatedly. The parsing
of *which individual tests* passed/failed happens in parsers/*.py.
"""

import subprocess
import time
import json
import os
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class RunResult:
    run_number: int
    exit_code: int
    duration_seconds: float
    stdout: str
    stderr: str
    timed_out: bool


def run_command_n_times(command: str, n: int, cwd: str = ".", timeout: int = 120) -> List[RunResult]:
    """
    Runs `command` (a shell string, e.g. "pytest -q") `n` times sequentially.
    Returns a list of RunResult, one per execution.

    Sequential (not parallel) on purpose: parallel test runs can introduce
    their OWN flakiness (shared ports, race conditions), which would
    contaminate our flaky-test signal with environment noise.
    """
    results: List[RunResult] = []

    for i in range(1, n + 1):
        start = time.time()
        timed_out = False
        try:
            proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            )
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired as e:
            exit_code = -1
            stdout = (e.stdout or b"").decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = ((e.stderr or b"").decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")) + "\n[TIMED OUT]"
            timed_out = True

        duration = time.time() - start

        results.append(
            RunResult(
                run_number=i,
                exit_code=exit_code,
                duration_seconds=round(duration, 3),
                stdout=stdout,
                stderr=stderr,
                timed_out=timed_out,
            )
        )
        print(f"  Run {i}/{n} — exit={exit_code} — {duration:.2f}s" + (" [TIMEOUT]" if timed_out else ""))

    return results


def save_raw_results(results: List[RunResult], path: str):
    """Dump raw run results to JSON for later parsing/debugging."""
    with open(path, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)