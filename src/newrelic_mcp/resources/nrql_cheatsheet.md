# NRQL cheat sheet

Reference for composing queries to pass to `run_nrql`.

## Shape

```
SELECT <aggregations|attributes>
FROM <EventType>
[WHERE <conditions>]
[FACET <attribute>]
[SINCE <time>] [UNTIL <time>]
[TIMESERIES <interval>]
[COMPARE WITH <time>]
[LIMIT <n|MAX>]
```

## Event types you will use most

| Event type | Holds |
|---|---|
| `Transaction` | APM web/non-web transactions, `duration`, `appName`, `name` |
| `TransactionError` | Captured errors, `error.class`, `error.message` |
| `Span` | Distributed tracing spans, `trace.id`, `service.name`, `duration.ms` |
| `Log` | Log lines, `message`, `level`, `trace.id` |
| `Metric` | Dimensional metrics, queried with `newrelic.timeslice.value` or metric names |
| `Deployment` | Change tracking / deployment markers |
| `AwsLambdaInvocation` | Lambda invocations, `faas.name`, `duration`, `error` |

## Patterns

Error rate over time:

```sql
SELECT percentage(count(*), WHERE error IS true) FROM Transaction
WHERE appName = 'my-service' SINCE 3 HOURS AGO TIMESERIES 5 minutes
```

Latency percentiles per endpoint:

```sql
SELECT percentile(duration, 50, 95, 99) FROM Transaction
WHERE appName = 'my-service' FACET name SINCE 1 HOUR AGO LIMIT 20
```

Before/after a deploy:

```sql
SELECT average(duration) FROM Transaction
WHERE appName = 'my-service' SINCE 30 MINUTES AGO COMPARE WITH 1 DAY AGO
```

Logs for one request:

```sql
SELECT timestamp, level, message FROM Log
WHERE `trace.id` = 'abc123' SINCE 3 HOURS AGO ORDER BY timestamp ASC LIMIT 200
```

Slowest spans in a trace:

```sql
SELECT name, `service.name`, `duration.ms` FROM Span
WHERE `trace.id` = 'abc123' SINCE 3 HOURS AGO ORDER BY `duration.ms` DESC LIMIT 20
```

Lambda cold starts and errors:

```sql
SELECT count(*), average(duration) FROM AwsLambdaInvocation
WHERE provider.coldStart IS true FACET `faas.name` SINCE 1 DAY AGO
```

## Gotchas

- Attributes containing dots need backticks: `` `trace.id` ``.
- `FACET` is capped at 2000 unique values; use `LIMIT MAX` deliberately.
- `TIMESERIES` and `COMPARE WITH` cannot be combined with an automatic `LIMIT`;
  this server leaves those queries unbounded on purpose.
- Cross-account queries accept at most 30 accounts.
- String comparison is case sensitive; use `LIKE '%value%'` for fuzzy matching.
