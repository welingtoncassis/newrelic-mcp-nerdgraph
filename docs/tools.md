# Tool reference

Every tool returns a JSON string. Queries that generate NRQL echo it back under
`query`, so you can verify or rerun it in the New Relic UI.

Arguments marked *default accounts* fall back to `NEW_RELIC_ACCOUNT_IDS` when
omitted.

---

## Data access

### `run_nrql`

| Argument | Type | Default |
|---|---|---|
| `query` | string | required |
| `account_ids` | int[] | default accounts |
| `timeout_seconds` | int (1–120) | `NEW_RELIC_QUERY_TIMEOUT_SECONDS` |

Runs any NRQL query. `SINCE` and `LIMIT` are appended when absent, except for
`TIMESERIES` and `COMPARE WITH` queries, which are left unbounded.

Rejected: stacked statements, comment markers, anything not starting with
`SELECT`, `FROM` or `SHOW`.

### `run_nrql_async`

| Argument | Type | Default |
|---|---|---|
| `query` | string | required |
| `account_ids` | int[] | default accounts |

Starts an asynchronous query and polls until it completes, up to 20 polls.
Returns `polls` alongside the results.

### `validate_nrql_query`

| Argument | Type | Default |
|---|---|---|
| `query` | string | required |

Returns `{"valid": true, "prepared_query": ...}` or `{"valid": false, "reason": ...}`
without contacting New Relic.

---

## Entities

### `search_entities`

| Argument | Type | Default |
|---|---|---|
| `name` | string | — |
| `domain` | string (`APM`, `BROWSER`, `INFRA`, `SYNTH`, `MOBILE`, `EXT`) | — |
| `entity_type` | string (`APPLICATION`, `HOST`, `AWSLAMBDAFUNCTION`, …) | — |
| `account_id` | int | — |
| `tags` | map | — |
| `cursor` | string | — |

At least one criterion is required. `name` matches with `LIKE`; tags match exactly.

### `get_entity`

| Argument | Type | Default |
|---|---|---|
| `guid` | string | required |

Returns tags, golden metrics (with their NRQL), relationships and alert severity.

---

## Alerting

### `list_open_issues`

| Argument | Type | Default |
|---|---|---|
| `account_id` | int | default account |
| `only_open` | bool | `true` |
| `priority` | string (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) | — |
| `cursor` | string | — |

### `list_alert_policies`

| Argument | Type | Default |
|---|---|---|
| `account_id` | int | default account |
| `cursor` | string | — |

### `list_nrql_conditions`

| Argument | Type | Default |
|---|---|---|
| `account_id` | int | default account |
| `policy_id` | string | all policies |
| `cursor` | string | — |

Returns each condition's NRQL and thresholds, which is how you reproduce what
an alert saw when it fired.

---

## Logs

### `search_logs`

| Argument | Type | Default |
|---|---|---|
| `service_name` | string | — |
| `entity_guid` | string | — |
| `level` | string | — |
| `trace_id` | string | — |
| `message_contains` | string | — |
| `since` | string | `NEW_RELIC_DEFAULT_SINCE` |
| `limit` | int (1–500) | `50` |
| `account_ids` | int[] | default accounts |

`service_name` is matched against `service.name`, `entity.name` and `faas.name`,
so it works for APM services and Lambda functions alike.

### `summarize_log_errors`

| Argument | Type | Default |
|---|---|---|
| `service_name` | string | — |
| `since` | string | `1 HOUR AGO` |
| `limit` | int (1–100) | `20` |
| `account_ids` | int[] | default accounts |

Facets `ERROR`/`FATAL`/`CRITICAL` logs on the first 120 characters of the
message, which collapses lines that differ only by ids. Each group carries a
`sample_trace_id` to feed into `get_trace`.

---

## Traces and change correlation

### `get_trace`

| Argument | Type | Default |
|---|---|---|
| `trace_id` | string | required |
| `since` | string | `3 HOURS AGO` |
| `limit` | int (1–1000) | `200` |
| `account_ids` | int[] | default accounts |

Returns spans in chronological order plus `span_count` and the distinct
`services` involved.

### `get_recent_errors`

| Argument | Type | Default |
|---|---|---|
| `service_name` | string | — |
| `since` | string | `1 HOUR AGO` |
| `limit` | int (1–100) | `20` |
| `account_ids` | int[] | default accounts |

### `list_deployments`

| Argument | Type | Default |
|---|---|---|
| `entity_guid` | string | — |
| `since` | string | `7 DAYS AGO` |
| `limit` | int (1–200) | `50` |
| `account_ids` | int[] | default accounts |

### `compare_metric_windows`

| Argument | Type | Default |
|---|---|---|
| `nrql_select` | string | required |
| `event_type` | string | required |
| `where` | string | — |
| `since` | string | `1 HOUR AGO` |
| `compare_with` | string | `1 DAY AGO` |
| `account_ids` | int[] | default accounts |

---

## Escape hatch

### `nerdgraph_query`

Registered only when `NEW_RELIC_ENABLE_RAW_NERDGRAPH=true`.

| Argument | Type | Default |
|---|---|---|
| `query` | string | required |
| `variables` | map | — |

Runs an arbitrary GraphQL document. `mutation` documents are refused unless
`NEW_RELIC_ENABLE_MUTATIONS=true`. Not annotated as read-only, so clients will
prompt before calling it.
