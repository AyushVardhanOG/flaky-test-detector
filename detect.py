#!/usr/bin/env python3
"""
Flaky Test Detector — CLI entry point.

Usage:
    python detect.py --command "pytest -v" --runs 10 --framework pytest
    python detect.py --command "npx jest --json" --runs 10 --framework jest-json
    python detect.py --command "mvn test" --runs 5 --framework junit --junit-dir target/surefire-reports

Outputs:
    - Console summary (which tests are flaky, ranked)
    - results/raw_runs.json (raw output from every run, for debugging)
    - results/flakiness_report.json (structured report — this is what the dashboard reads)
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))

from core.runner import run_command_n_times, save_raw_results
from core.analyzer import analyze, reports_to_json, print_summary
from parsers.pytest_parser import parse_multiple_runs as parse_pytest
from parsers.jest_parser import parse_multiple_runs as parse_jest_console
from parsers.jest_json_parser import parse_multiple_runs as parse_jest_json
from parsers.junit_parser import parse_multiple_run_dirs


def main():
    parser = argparse.ArgumentParser(description="Detect flaky tests by running your suite multiple times.")
    parser.add_argument("--command", required=True, help='Test command to run, e.g. "pytest -v"')
    parser.add_argument("--runs", type=int, default=10, help="Number of times to run the suite (default: 10)")
    parser.add_argument("--framework", required=True, choices=["pytest", "jest-console", "jest-json", "junit"])
    parser.add_argument("--cwd", default=".", help="Working directory to run the command in")
    parser.add_argument("--junit-dir", default="target/surefire-reports", help="JUnit XML reports dir (junit only)")
    parser.add_argument("--output-dir", default="results", help="Where to write JSON output")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Running '{args.command}' {args.runs} times in '{args.cwd}'...\n")

    if args.framework == "junit":
        run_report_dirs = []
        for i in range(1, args.runs + 1):
            os.system(f'cd "{args.cwd}" && {args.command} > /dev/null 2>&1')
            snapshot_dir = os.path.join(args.output_dir, f"junit_run_{i}")
            full_junit_path = os.path.join(args.cwd, args.junit_dir)
            if os.path.exists(full_junit_path):
                shutil.copytree(full_junit_path, snapshot_dir, dirs_exist_ok=True)
                run_report_dirs.append(snapshot_dir)
            print(f"  Run {i}/{args.runs} done")

        history = parse_multiple_run_dirs(run_report_dirs)

    else:
        results = run_command_n_times(args.command, args.runs, cwd=args.cwd)
        save_raw_results(results, os.path.join(args.output_dir, "raw_runs.json"))
        stdouts = [r.stdout for r in results]

        if args.framework == "pytest":
            history = parse_pytest(stdouts)
        elif args.framework == "jest-console":
            history = parse_jest_console(stdouts)
        elif args.framework == "jest-json":
            history = parse_jest_json(stdouts)

    reports = analyze(history)
    reports_to_json(reports, os.path.join(args.output_dir, "flakiness_report.json"))
    print_summary(reports)

    flaky_count = sum(1 for r in reports if r.classification == "FLAKY")
    print(f"Full report written to {args.output_dir}/flakiness_report.json")

    sys.exit(1 if flaky_count > 0 else 0)


if __name__ == "__main__":
    main()