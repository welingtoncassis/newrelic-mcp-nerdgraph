# Recipes

Worked examples. Each one shows the prompt, the tool sequence the agent should
take, and what to check in the result.

---

## 1. An alert just fired and you have no context

**Prompt:** "What is firing in New Relic right now?"

1. `list_open_issues` — read `title`, `priority`, `entityGuids`, `conditionName`.
2. `get_entity` on the first GUID — confirms which service and environment.
3. `list_nrql_conditions` filtered by the issue's policy — gives the exact NRQL
   the condition evaluates.
4. `run_nrql` with that query plus `TIMESERIES 5 minutes` — shows whether the
   breach is a spike or a sustained shift.

Watch for: an issue whose entity has `reporting: false`. That is an agent
outage, not an application failure, and the rest of the investigation changes.

---

## 2. A service got slow after a release

**Prompt:** "checkout latency went up this afternoon, was it the deploy?"

1. `search_entities` with `name: "checkout"`, `domain: "APM"`.
2. `list_deployments` for that GUID over `1 DAY AGO`.
3. `compare_metric_windows` with
   `nrql_select: "percentile(duration, 95)"`, `event_type: "Transaction"`,
   `where: "appName = 'checkout'"`.
4. If the delta is real, `run_nrql` faceting by endpoint:

   ```sql
   SELECT percentile(duration, 95) FROM Transaction
   WHERE appName = 'checkout' FACET name SINCE 2 HOURS AGO LIMIT 20
   ```

Watch for: a latency increase that tracks a throughput increase is load, not a
regression. Check `rate(count(*), 1 minute)` over the same window before
blaming the release.

---

## 3. One customer reports an error, you have the trace id

**Prompt:** "Trace 4bf92f3577b34da6 failed, what happened?"

1. `get_trace` with the id — the span timeline and the services involved.
2. `search_logs` with the same `trace_id` — the log lines for that request.
3. If a downstream service appears in `services` but has no spans of its own,
   `search_logs` on that service name around the same window.

Watch for: an empty result usually means the trace aged out of the default
window. Widen `since` before concluding the trace does not exist.

---

## 4. Lambda errors in a serverless stack

**Prompt:** "Why is the order-processor lambda failing?"

1. `search_logs` with `service_name: "order-processor"`, `level: "ERROR"` —
   `faas.name` is matched, so the function name works directly.
2. `summarize_log_errors` for the same service — groups the failures and gives
   you a `sample_trace_id`.
3. `run_nrql` for the invocation picture:

   ```sql
   SELECT count(*), percentage(count(*), WHERE error IS true), average(duration)
   FROM AwsLambdaInvocation WHERE `faas.name` = 'order-processor'
   SINCE 3 HOURS AGO TIMESERIES 10 minutes
   ```

Watch for: timeouts show up as duration at the configured limit rather than as
an error class, so a flat ceiling in the duration series is the signal.

---

## 5. Cross-account health check

**Prompt:** "Error rate for all production services across our accounts."

```
run_nrql with account_ids: [111, 222, 333] and

SELECT percentage(count(*), WHERE error IS true) AS error_rate
FROM Transaction FACET appName, consumerId
SINCE 1 HOUR AGO LIMIT 50
```

Watch for: NerdGraph caps cross-account queries at 30 accounts, and the server
rejects the call before sending it if you pass more. Facet by `consumerId` to
tell which account a row came from.
