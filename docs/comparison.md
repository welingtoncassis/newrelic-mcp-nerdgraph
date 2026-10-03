# Comparison with the official New Relic MCP server

New Relic ships a hosted MCP server at `https://mcp.newrelic.com/mcp/`. This
page is about when each one fits, not about which is better.

| | Official New Relic MCP | newrelic-mcp-nerdgraph |
|---|---|---|
| Hosting | Remote service operated by New Relic | Local process you run |
| Enablement | Account preview toggles | `pip install` |
| Auth | OAuth or API key; some tools are OAuth-only | User API key |
| AI features | NL→NRQL, generated incident and impact reports | None; the calling model does the reasoning |
| Query visibility | Mostly opaque | Every query is returned with its results |
| Tool selection | Server-side tags (`include-tags`) | Everything local, flags for the risky parts |
| Data path | Telemetry transits New Relic's MCP bridge | Direct to the NerdGraph API |
| Extensibility | Closed | Fork, patch, add a tool |
| Cost | Tied to preview and AI entitlements | Your existing New Relic account |

## When the official server is the better choice

- You want the AI-generated reports (`generate_alert_insights_report`,
  `analyze_deployment_impact`) and the Atlassian or AWS integrations.
- You prefer natural-language querying over writing NRQL.
- Central administration matters more than local control.

## When this project fits better

- You are running agents in CI, a container, or a Cloud Agent where a local
  stdio process is simpler than an OAuth flow.
- You need the queries to be auditable, or to pin exactly what an agent can see.
- Your account does not have the previews enabled, or you do not want the
  entitlement dependency.
- You want to add domain-specific tools for your own stack.

## Capability coverage

Parity with the hosted server's *flows* rather than its tool list:

| Flow | Covered | How |
|---|---|---|
| Entity and account discovery | yes | `search_entities`, `get_entity` |
| Alerts and incidents | yes | `list_open_issues`, `list_alert_policies`, `list_nrql_conditions` |
| Logs | yes | `search_logs`, `summarize_log_errors` |
| Traces | yes | `get_trace` |
| Golden metrics | yes | `get_entity` returns the NRQL, run it with `run_nrql` |
| Deployment correlation | yes | `list_deployments`, `compare_metric_windows` |
| Arbitrary data access | yes | `run_nrql`, `run_nrql_async`, `nerdgraph_query` |
| Natural language to NRQL | no | Out of scope by design |
| AI-generated reports | no | Out of scope by design |
| Trace anomaly detection | not yet | Would need a heuristic; see the issue tracker |
