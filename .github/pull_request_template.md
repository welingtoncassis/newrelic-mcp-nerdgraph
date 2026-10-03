## What changed

<!-- One paragraph. Link the issue if there is one. -->

## Why

<!-- The problem this solves, not a restatement of the diff. -->

## Verification

<!-- How you know it works. If you ran it against a real account, say which
     flows you exercised. Never paste real telemetry or an API key. -->

## Checklist

- [ ] `uv run pytest` passes
- [ ] `uv run ruff check . && uv run ruff format --check .` passes
- [ ] `uv run mypy` passes
- [ ] Docs updated (`README.md`, `docs/tools.md`) if the tool surface changed
- [ ] `CHANGELOG.md` entry added under `## Unreleased`
- [ ] New tools are read-only, or gated behind `enable_mutations`
