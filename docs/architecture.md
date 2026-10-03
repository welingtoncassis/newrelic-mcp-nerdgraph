# Architecture

## Layers

```
MCP client (Cursor, Claude Desktop, custom agent)
        │  stdio / streamable-http
        ▼
server.py            tools, resources, prompts
        ▼
tools/*              input schemas, error translation, payload shaping
        ▼
services/*           NRQL composition, GraphQL field selection
        ▼
nerdgraph/client.py  HTTP, retry, GraphQL error normalisation
        ▼
https://api.newrelic.com/graphql
```

Each layer has one job, and dependencies only point downward.

- **`tools/`** owns everything the model sees: argument schemas, descriptions,
  annotations, and the translation of internal exceptions into `ToolError` so
  the message survives the trip back to the client.
- **`services/`** owns the queries. A service never touches MCP types, which is
  why the test suite can exercise them without a server.
- **`nerdgraph/`** owns transport. It knows nothing about NRQL or entities.
- **`security/`** is pure functions, called from both services and formatting.

`context.py` is the composition root. It builds one `AppContext` per process and
hands it to the tools through a provider callable, which keeps `create_server`
free of global state and makes injecting a mocked HTTP client a one-liner.

## Why tools return JSON strings

A tool could return a dict and let the SDK serialise it. Returning a string
instead puts `formatting.finalize` on every path, so redaction and the response
size cap cannot be skipped by a new tool that forgets to call them.

## Request lifecycle

1. The SDK validates arguments against the schema derived from the annotated
   signature.
2. `tool_errors` wraps the call so `NewRelicMCPError` and `ValueError` become
   `ToolError` with their original message.
3. The service composes NRQL. User-supplied fragments pass through
   `escape_nrql_string`; the finished query passes through `validate_nrql`.
4. `apply_defaults` appends `SINCE` and `LIMIT` when the query lacks them.
5. The client POSTs to NerdGraph, retrying 429 and 5xx with exponential backoff
   and honouring `Retry-After`.
6. `finalize` redacts credential-shaped strings, serialises, and truncates the
   largest list in the payload if the result exceeds the byte budget.

## Design decisions

**Read-only by default.** Mutations and the raw GraphQL tool are behind separate
flags. An agent that goes off the rails can waste queries but cannot change an
alert policy unless an operator opted in.

**Generated NRQL is returned with the results.** Every tool echoes the query it
ran. The model can show its work, and a human can paste the query into the New
Relic UI to verify it.

**No natural-language-to-NRQL layer.** Translating intent is what the calling
model is for. Adding a second translation step here would hide errors behind a
component that cannot explain itself.

**Async NRQL is a separate tool, not a fallback.** Silently switching to polling
would make a fast tool unpredictably slow. The model picks the trade-off.

## Adding a tool

1. Add the query to `services/`, with a test that asserts the NRQL or GraphQL
   actually sent.
2. Register it in `tools/`, annotated and described well enough that a model
   can choose it without reading the source.
3. Add it to the tables in `README.md` and `docs/tools.md`.
4. Add the tool name to `EXPECTED_TOOLS` in `tests/test_server.py`.
