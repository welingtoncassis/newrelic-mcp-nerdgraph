# Incident investigation playbook

A sequence that works with the tools in this server. Each step narrows the
search space for the next one.

## 1. Establish what fired

- `list_open_issues` → pick the issue, note `entityGuids` and `conditionName`.
- `list_nrql_conditions` with the policy → read the exact NRQL the alert used.
- Re-run that NRQL through `run_nrql` with `TIMESERIES` to see the shape over time.

## 2. Identify the entity

- `search_entities` by name if you only have a service name.
- `get_entity` for golden metrics, tags (env, team) and upstream/downstream
  relationships.

## 3. Check for a recent change

- `list_deployments` for the entity over the last 24 hours.
- `compare_metric_windows` with `COMPARE WITH 1 DAY AGO` to separate a real
  regression from normal traffic variation.

## 4. Find the failure signature

- `get_recent_errors` for APM errors grouped by class.
- `summarize_log_errors` for log-only failures, which catches things APM does
  not instrument.
- Note a `sample_trace_id` from either result.

## 5. Follow one request end to end

- `get_trace` with that trace id for the span timeline and the services involved.
- `search_logs` with the same trace id for the log lines of that request.

## 6. Form the hypothesis

State the blast radius (which entities, which share of traffic), the first
symptom timestamp, and whether a deploy or dependency change precedes it. If a
step returned nothing, say so explicitly rather than inferring a cause from
missing data.
