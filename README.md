# Flaky Test Detector

Detects tests that pass and fail inconsistently across identical runs — the
kind of test that quietly erodes trust in a CI pipeline because nobody's
sure if a red build means a real bug or just bad luck.

Supports **pytest**, **Jest**, and **JUnit** test suites. Runs your suite
N times, diffs the results, and tells you which tests are flaky (vs. just
broken). Ships with a web dashboard to visualize results and a GitHub
Action to run automatically on every PR.

## Why this exists

Flaky tests are a well-known, named problem in software engineering —
teams lose hours re-running CI, or worse, start ignoring red builds
because "it's probably just flaky." Most flakiness detection in the wild
is either ad-hoc (re-run and squint) or buried in expensive internal
tooling at big companies. This is a small, free version of that idea that
runs locally or in any GitHub Actions pipeline.

# Live Demo

https://ayushvardhanog.github.io/flaky-test-detector/

## How it works

1. **Run** — executes your test command N times sequentially (not in
   parallel — parallel runs introduce their own environmental noise that
   contaminates the signal)
2. **Parse** — extracts per-test pass/fail from each run's output.
   Each framework gets its own parser:
   - `pytest` — parses `pytest -v` console output
   - `Jest` — parses `jest --json` output (recommended) or console (fallback)
   - `JUnit` — parses standard surefire/Gradle XML reports
3. **Analyze** — computes a **flakiness score** per test: the rate of
   pass↔fail *transitions* across runs, not just raw failure rate

The transition-based score is the key insight. A test that fails
identically every run isn't flaky — it's just broken. A test that
sometimes passes and sometimes fails on identical code is the real
flakiness signal. These are classified separately:

| Classification | Meaning |
|---|---|
| `FLAKY` | Mixed pass/fail across runs — the actual problem |
| `STABLE_FAIL` | Fails every run — a real bug, not flakiness |
| `STABLE_PASS` | Passes every run — healthy |
| `ERRORED` | Had ERROR status — usually an infra/setup issue |

## Quick start

```bash
pip install -r requirements.txt

# pytest project
python detect.py --command "python -m pytest -v" --runs 10 --framework pytest --cwd path/to/project

# Jest project
python detect.py --command "npx jest --json" --runs 10 --framework jest-json --cwd path/to/project

# JUnit / Maven project
python detect.py --command "mvn test" --runs 5 --framework junit --cwd path/to/project --junit-dir target/surefire-reports
```

## Try it on the included examples

```bash
# Python example
python detect.py --command "python -m pytest -v" --runs 15 --framework pytest --cwd examples/python-sample

# JS example
cd examples/js-sample && npm install && cd ../..
python detect.py --command "npx jest --json" --runs 12 --framework jest-json --cwd examples/js-sample
```

Both examples include one test that always passes, one that always fails
(correctly classified as `STABLE_FAIL`, not flaky), and two genuinely
flaky tests — so you can see the classification working correctly out of
the box.

## Web dashboard

Open `docs/index.html` in any browser — no server needed. Drag and
drop a `flakiness_report.json` from a `detect.py` run to visualize
results. Sample data is preloaded so it's not empty on first open.

## GitHub Action

`.github/workflows/flaky-detector.yml` runs the detector on every PR and
posts a comment summarizing any flaky tests found. Set to
`continue-on-error: true` so it reports without blocking the build.

## Project structure

core/runner.py              — runs the test command N times, captures output

core/analyzer.py            — flakiness scoring + classification logic

parsers/pytest_parser.py    — pytest console output parser

parsers/jest_parser.py      — Jest console output parser (fallback)

parsers/jest_json_parser.py — Jest --json output parser (recommended)

parsers/junit_parser.py     — JUnit/surefire XML report parser

detect.py                   — CLI entry point

dashboard/index.html        — visual report viewer

examples/                   — sample projects with intentionally flaky tests

## Bugs found and fixed during development

Real issues caught while building and testing this:

- **Windows PATH issue** — `pytest` not directly callable on Windows;
  fixed by using `python -m pytest` instead
- **Jest JSON schema mismatch** — inner key is `assertionResults` not
  `testResults`; caught by actually running against a real Jest suite
- **Windows encoding bug** — Jest outputs UTF-8 but Windows reads
  subprocess output as `cp1252`; fixed by explicitly setting
  `encoding="utf-8"` in the subprocess call

## Tech stack

Python, JavaScript, HTML/CSS, pytest, Jest, JUnit, GitHub Actions
