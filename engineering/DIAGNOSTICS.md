# Factory Diagnostics Contract

Status: reusable operational diagnostics policy for Factory tooling and generated-project infrastructure.

Factory-owned tooling messages should use a stable prefix of the form:

`[mod-factory/<domain>/<event>]`

`<domain>` identifies the subsystem such as `engineering`, `art`, `provider`, `migration`, `scaffolder`, `validation` or `release`. `<event>` is a stable `lower_snake_case` identifier.

Generated mods do not inherit the Factory prefix as their runtime logging namespace. Each runtime repository owns its own logger taxonomy.

## Severity

- `INFO`: bounded lifecycle/success summaries useful to operators.
- `WARN`: execution can continue safely but a capability is degraded, unavailable or intentionally skipped.
- `ERROR`: an expected operation failed or a correctness-sensitive transition cannot be completed. Fail closed rather than logging and accepting partial state.

## Evidence rules

Diagnostics used as CI evidence must be deterministic enough to grep by event ID and must state the failing subject/reason when known. Do not log secrets, tokens, full private filesystem paths, unbounded user payloads or large state dumps. Hot-path diagnostics must be bounded or rate-limited.

Provider errors must distinguish `not installed`, `installed but unsupported`, `API not proven`, `runtime failure` and `authorization denied` where those states are materially different. A warning never upgrades presence into compatibility.
