# v0.1.0 Release Checklist

The code, documentation, MIT license, package build, clean-install test, and
GitHub Actions run are complete.

## Publish

- [ ] Make the GitHub repository public.
- [ ] Check the README, animation, plots, and links on GitHub.
- [ ] Create the `v0.1.0` tag and release.

## Final quality gate

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
BSK_SUPPORT_DATA_CACHE=.bsk/support-data uv run pytest
uv build
```

Before tagging, confirm no `.bsk` output, environment, credential, or
machine-specific path is tracked. Numeric claims must link to their assumptions
and tolerances.
