# Verification

## Separate evidence levels

1. Process success: Python exited normally.
2. Structural evidence: expected tasks, modules, recorders, and connections are
   present before execution.
3. Data integrity: telemetry is finite, ordered, correctly shaped, and starts
   from the configured state.
4. Numerical behavior: conserved quantities, trends, event timing, or reference
   values satisfy justified tolerances.
5. Validation: comparison with authoritative theory, test data, or another
   validated implementation over a stated domain.

Do not describe a lower level as a higher one. Passing `bsk run` alone is not a
physics validation.

## Define useful checks

Each deterministic check should include:

- a stable name;
- actual and expected values;
- a tolerance and comparison rule;
- units, or an explicit dimensionless value;
- enough configuration context to reproduce it.

Choose tolerances from numerical method behavior, analytic approximation error,
input uncertainty, or a calibrated reference run with margin. Avoid arbitrary
round-number tolerances and avoid machine epsilon when the model or platform
variation is much larger.

Use absolute tolerances near zero and relative tolerances for well-scaled
nonzero values. For angles, account for wrapping. For secular trends, fit an
unwrapped history over a duration long enough to separate the trend from
periodic variation.

## Run verification

```bash
bsk verify scenario.py --json
bsk verify .bsk/runs/<run-id> --json
```

Exit code 0 means all declared checks passed, 1 means tool/scenario error, 2
means semantic verification is unsupported, and 3 means at least one check
failed. Inspect individual checks and artifacts even when the overall result is
PASS.

When a model changes, rerun checks that cover the changed physics plus data
integrity checks. Preserve raw telemetry and concise metrics so another person
can audit the conclusion.
