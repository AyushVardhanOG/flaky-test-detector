"""
Sample test suite with intentionally different behaviors, to demonstrate
the flaky test detector:

- test_addition: always passes (stable)
- test_subtraction: always fails (stable fail — a real bug, not flaky)
- test_flaky_timing: flaky — depends on system time/randomness
- test_flaky_race: flaky — simulates a race condition using random.choice
"""

import random
import time


def test_addition():
    assert 2 + 2 == 4


def test_subtraction():
    # Deliberately wrong assertion — this is a "real bug", always fails,
    # and should be classified STABLE_FAIL, not FLAKY.
    assert 5 - 3 == 3


def test_flaky_timing():
    # Flaky because it depends on a timing race: sometimes the sleep
    # finishes in time, sometimes it doesn't, simulating real-world
    # flakiness caused by tight timeouts.
    start = time.time()
    time.sleep(random.uniform(0, 0.05))
    elapsed = time.time() - start
    assert elapsed < 0.03  # tight threshold -> sometimes passes, sometimes fails


def test_flaky_race():
    # Flaky because of unseeded randomness simulating a race condition
    # (e.g. two async operations finishing in non-deterministic order).
    outcome = random.choice([True, True, True, False])
    assert outcome is True