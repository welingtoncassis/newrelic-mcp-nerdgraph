# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-03

First release.

### Added

- MCP server over stdio, SSE and streamable HTTP, built on the NerdGraph
  GraphQL API and authenticated with a New Relic User API key.
- Data access tools: `run_nrql`, `run_nrql_async`, `validate_nrql_query`.
- Entity tools: `search_entities`, `get_entity`.
- Alerting tools: `list_open_issues`, `list_alert_policies`,
  `list_nrql_conditions`.
- Log tools: `search_logs`, `summarize_log_errors`.
- Trace and change-correlation tools: `get_trace`, `get_recent_errors`,
  `list_deployments`, `compare_metric_windows`.
- Opt-in `nerdgraph_query` escape hatch, gated behind
  `NEW_RELIC_ENABLE_RAW_NERDGRAPH` and refusing mutations unless
  `NEW_RELIC_ENABLE_MUTATIONS` is set.
- Resources `newrelic://nrql/cheatsheet`, `newrelic://playbook/investigation`
  and `newrelic://config`, plus the `investigate_incident` and `write_nrql`
  prompts.
- NRQL validation and escaping, credential redaction in results, response size
  caps, cross-account support and retry with backoff.

[Unreleased]: https://github.com/welingtoncassis/newrelic-mcp-nerdgraph/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/welingtoncassis/newrelic-mcp-nerdgraph/releases/tag/v0.1.0
