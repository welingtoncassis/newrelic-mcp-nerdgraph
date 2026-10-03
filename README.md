# newrelic-mcp-nerdgraph

[![CI](https://github.com/welingtoncassis/newrelic-mcp-nerdgraph/actions/workflows/ci.yml/badge.svg)](https://github.com/welingtoncassis/newrelic-mcp-nerdgraph/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/newrelic-mcp-nerdgraph.svg)](https://pypi.org/project/newrelic-mcp-nerdgraph/)
[![Python](https://img.shields.io/pypi/pyversions/newrelic-mcp-nerdgraph.svg)](https://pypi.org/project/newrelic-mcp-nerdgraph/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

An open source [MCP](https://modelcontextprotocol.io) server that connects AI
agents to New Relic through the public [NerdGraph](https://docs.newrelic.com/docs/apis/nerdgraph/get-started/introduction-new-relic-nerdgraph/)
GraphQL API.

It runs locally over stdio with a standard User API key. There is no hosted
bridge in the path, so every query is one you can read, reproduce in the
NerdGraph GraphiQL explorer, and audit.

## Why this exists

New Relic ships its own hosted MCP server. It is a good product, but it is a
remote service gated behind account previews, and several of its tools require
OAuth rather than an API key. This project targets a different set of
constraints:

- **Local and self-hosted.** Runs as a subprocess of your editor; telemetry
  never transits a third-party bridge.
- **Explicit NRQL instead of opaque translation.** Tools either take NRQL you
  can read or generate NRQL that is returned alongside the results.
- **Read-only by default.** Anything that changes New Relic configuration is
  behind an opt-in flag.
- **No extra cost.** Only the New Relic account you already pay for.

See [docs/comparison.md](docs/comparison.md) for a feature-by-feature
comparison, and [docs/architecture.md](docs/architecture.md) for the design.

## Install

```bash
uv tool install newrelic-mcp-nerdgraph
# or
pipx install newrelic-mcp-nerdgraph
```

## Configure

You need a New Relic [User API key](https://docs.newrelic.com/docs/apis/intro-apis/new-relic-api-keys/)
(`NRAK-...`) and your account id.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `NEW_RELIC_API_KEY` | yes | — | User API key |
| `NEW_RELIC_ACCOUNT_IDS` | recommended | — | Comma-separated defaults, e.g. `123,456` |
| `NEW_RELIC_REGION` | no | `US` | `US` or `EU` |
| `NEW_RELIC_DEFAULT_SINCE` | no | `30 MINUTES AGO` | Time window added to NRQL without one |
| `NEW_RELIC_MAX_RESULT_ROWS` | no | `200` | `LIMIT` added to NRQL without one |
| `NEW_RELIC_MAX_RESPONSE_CHARS` | no | `100000` | Byte budget per tool response |
| `NEW_RELIC_QUERY_TIMEOUT_SECONDS` | no | `30` | Server-side NRQL timeout |
| `NEW_RELIC_MAX_RETRIES` | no | `3` | Retries on 429/5xx |
| `NEW_RELIC_REDACT_SENSITIVE_VALUES` | no | `true` | Mask credential-shaped strings in output |
| `NEW_RELIC_ENABLE_RAW_NERDGRAPH` | no | `false` | Expose the arbitrary-GraphQL tool |
| `NEW_RELIC_ENABLE_MUTATIONS` | no | `false` | Allow write operations |

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "newrelic": {
      "command": "newrelic-mcp",
      "env": {
        "NEW_RELIC_API_KEY": "NRAK-your-key",
        "NEW_RELIC_ACCOUNT_IDS": "1234567"
      }
    }
  }
}
```

### Claude Desktop

`claude_desktop_config.json` uses the same shape. Run without installing:

```json
{
  "mcpServers": {
    "newrelic": {
      "command": "uvx",
      "args": ["newrelic-mcp-nerdgraph"],
      "env": { "NEW_RELIC_API_KEY": "NRAK-your-key", "NEW_RELIC_ACCOUNT_IDS": "1234567" }
    }
  }
}
```

## Tools

| Tool | What it answers |
|---|---|
| `run_nrql` | Any NRQL query, one or many accounts |
| `run_nrql_async` | Long-running query, polled to completion |
| `validate_nrql_query` | Check NRQL and see the clauses the server adds |
| `search_entities` | Find services, hosts and lambdas by name, type or tag |
| `get_entity` | Tags, golden metrics and relationships for one GUID |
| `list_open_issues` | Currently firing alert issues |
| `list_alert_policies` | Alert policies in an account |
| `list_nrql_conditions` | Condition queries and thresholds |
| `search_logs` | Logs by service, level, trace id or message |
| `summarize_log_errors` | Error logs grouped by message pattern |
| `get_trace` | Spans of one distributed trace |
| `get_recent_errors` | Transaction errors grouped by class |
| `list_deployments` | Recent deploys, for change correlation |
| `compare_metric_windows` | An aggregate against the same window in the past |
| `nerdgraph_query` | Arbitrary GraphQL (opt-in) |

Full input schemas: [docs/tools.md](docs/tools.md).

### Resources and prompts

- `newrelic://nrql/cheatsheet` — event types, query patterns, common pitfalls.
- `newrelic://playbook/investigation` — the incident flow these tools are built for.
- `newrelic://config` — active configuration, API key excluded.
- Prompts: `investigate_incident`, `write_nrql`.

## Example session

> "The checkout service is alerting. What happened in the last hour?"

The agent walks `list_open_issues` → `get_entity` → `list_deployments` →
`get_recent_errors` → `get_trace` → `search_logs`, each step narrowing the next.
[docs/recipes.md](docs/recipes.md) has five worked examples.

## Security

- The API key lives in a `SecretStr`, is attached per request, and never
  appears in logs, `repr` output or the config resource.
- Every NRQL string is validated: no stacked statements, no comment markers,
  read-only verbs only. All interpolated values are escaped.
- Credential-shaped strings in results (JWTs, bearer tokens, cloud keys) are
  masked before they reach the model.
- Responses are size-capped so a wide query degrades into a truncated result
  rather than an unusable context.

Note that NRQL guardrails are a correctness and cost control, not an
authorization boundary. The server can only read what the API key can read, so
scope the key to the accounts the agent should see. Report vulnerabilities via
[SECURITY.md](SECURITY.md).

## Development

```bash
uv sync --all-extras
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

Tests mock NerdGraph with `respx`; no account or network access is needed.
See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache-2.0. Not affiliated with or endorsed by New Relic, Inc.
