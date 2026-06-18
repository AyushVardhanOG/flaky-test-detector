// Sample test suite for Jest demonstrating the same patterns as the
// Python sample: stable pass, stable fail, and two flaky tests.

test("adds two numbers", () => {
  expect(2 + 2).toBe(4);
});

test("subtracts two numbers (deliberately wrong)", () => {
  expect(5 - 3).toBe(3); // always fails on purpose — a real bug, not flaky
});

test("flaky timing test", () => {
  // Simulates a tight timing assertion without actually waiting in real
  // time (avoids Jest's test timeout) — the flakiness comes from
  // comparing a random "elapsed time" against a tight threshold, which
  // mirrors real flaky timing tests without slowing the suite down.
  const simulatedElapsedMs = Math.random() * 40;
  expect(simulatedElapsedMs).toBeLessThan(20); // tight threshold -> sometimes fails
});

test("flaky race condition", () => {
  const outcome = Math.random() > 0.25; // 75% true, 25% false
  expect(outcome).toBe(true);
});