# Security policy

## Reporting a vulnerability

Report privately through
[GitHub Security Advisories](https://github.com/welingtoncassis/newrelic-mcp-nerdgraph/security/advisories/new).
Do not open a public issue for a vulnerability.

Include the version, a reproduction, and the impact as you see it. Expect an
acknowledgement within 72 hours and an assessment within seven days. Fixes are
released as a patch version with a published advisory and credit to the
reporter unless you prefer otherwise.

## Supported versions

While the project is pre-1.0, only the latest release receives fixes.

## Threat model

### What the server protects

**Credential exposure.** The API key is held in a `SecretStr`, read only when a
request is signed, and excluded from the `newrelic://config` resource. It does
not appear in logs, `repr` output or exception messages.

**Credential leakage through telemetry.** Log messages and custom attributes
frequently contain tokens. Results are scanned for credential-shaped strings
(New Relic keys, JWTs, bearer tokens, AWS and GitHub keys) and for attribute
names that imply a secret, and those values are masked before the payload
leaves the server.

**Query injection.** Values interpolated into NRQL are escaped. The finished
query is rejected if it contains stacked statements, comment markers, or a verb
other than `SELECT`, `FROM` or `SHOW`.

**Context exhaustion.** Responses are capped by byte budget and queries without
an explicit `LIMIT` get one. A query that matches too much degrades into a
truncated result with an explanation rather than an unusable response.

**Unintended writes.** No tool mutates New Relic unless
`NEW_RELIC_ENABLE_MUTATIONS=true`. The raw GraphQL tool is not registered at
all unless `NEW_RELIC_ENABLE_RAW_NERDGRAPH=true`, and even then refuses
`mutation` documents while the mutations flag is off.

### What it does not protect

**The permissions of the key.** The server can read everything the API key can
read. NRQL guardrails are a correctness and cost control, not an authorization
boundary. Scope the key to the accounts the agent should see.

**Prompt injection via telemetry.** Log lines are attacker-influenced data. A
model reading them can be steered by their content. Redaction removes
credentials, not instructions. Treat tool output as untrusted input, and do not
wire this server to an agent with unsupervised write access to other systems.

**The host.** Environment variables and `.env` files are readable by any
process running as your user.

## Operational guidance

- Prefer a key scoped to the smallest set of accounts that is useful.
- Keep `NEW_RELIC_ENABLE_MUTATIONS` and `NEW_RELIC_ENABLE_RAW_NERDGRAPH` off
  unless a specific workflow needs them.
- Rotate the key if it ever appears in a shell history, a CI log or a shared
  configuration file.
- In CI, pass the key as a masked secret, never as a committed `.env`.
