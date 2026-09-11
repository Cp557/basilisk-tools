# V1 Release Checklist

The repository is a tested release candidate. Complete these external and
project-owner decisions before calling it a public v1 release.

## Completed

- [x] Add the MIT license.
- [x] Create the GitHub repository and add its URL to package metadata and the
  README.
- [x] Add the repository-specific GitHub Actions badge.

## Required

- Push the release candidate and confirm the first GitHub Actions run is green.
- Run the 16 controlled agent evaluations: four cases, two agents, and baseline
  versus skill conditions.
- Human-score the saved explanations and commit the complete selected raw result
  directories used in the comparison.
- Summarize results and limitations without claiming statistical significance.
- Review the README and demo from a browser on the public repository.

## Quality gates

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
BSK_SUPPORT_DATA_CACHE=.bsk/support-data uv run pytest
uv build
```

Then install the source archive in a clean directory and rerun `bsk doctor`,
`bsk inspect`, `bsk run`, and `bsk verify` before creating the `v0.1.0` tag.

## Portfolio review

- The first screen explains the problem, the solution, and the verified result.
- The animation and plots render correctly on GitHub.
- Every numeric claim links to its model assumptions and tolerance.
- Pending agent evidence is visibly labeled rather than implied.
- No `.bsk` run directory, local environment, credential, or machine-specific
  path is accidentally committed outside an intentional evaluation result.
