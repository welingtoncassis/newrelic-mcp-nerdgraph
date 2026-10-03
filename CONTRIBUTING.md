# Contributing

Thanks for helping out. Issues, bug reports and new tools are all welcome.

## Setup

```bash
git clone https://github.com/welingtoncassis/newrelic-mcp-nerdgraph
cd newrelic-mcp-nerdgraph
uv sync --all-extras
uv run pre-commit install
```

No New Relic account is needed. Tests mock NerdGraph with `respx`.

## Checks

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run bandit -c pyproject.toml -r src -q
```

CI runs all of these on Python 3.10 through 3.13, and fails if coverage drops
below 85%.

## Adding a tool

Tools are the public API of this project, so the bar is a little higher than
for internal code.

1. **Put the query in `services/`.** Services do not import MCP types; that is
   what makes them directly testable.
2. **Escape every interpolated value** with `security.nrql_guard.escape_nrql_string`.
   Never format user input into NRQL yourself.
3. **Register it in `tools/`** with `@mcp.tool(annotations=READ_ONLY)` and
   `@tool_errors`. Write the docstring for a model deciding whether to call it:
   say what question it answers and when a different tool is a better fit.
4. **Test the query you actually send**, not just the parsed result. Assert on
   the request body like the existing tests do.
5. **Update the docs**: the table in `README.md`, the reference in
   `docs/tools.md`, and `EXPECTED_TOOLS` in `tests/test_server.py`.

A tool that needs a mutation must be gated on `settings.enable_mutations` and
must not carry read-only annotations.

## Pull requests

- One logical change per PR.
- Add a `CHANGELOG.md` entry under `## Unreleased`.
- Describe how you verified the behaviour. If you ran it against a real
  account, say which flows you exercised; never paste real telemetry.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`,
`docs:`, `refactor:`, `test:`, `chore:`.

## Releasing

Maintainers only. Bump the version in `pyproject.toml`, move the `Unreleased`
section in `CHANGELOG.md` under the new version, then tag:

```bash
git tag -a v0.2.0 -m "v0.2.0" && git push origin v0.2.0
```

The release workflow builds the distributions and publishes to PyPI with
Trusted Publishing. No token is stored anywhere.

## Code of conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
