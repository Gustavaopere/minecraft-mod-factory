# Blockbench Live Bridge Security

Status: PR2 — read-only security contract

## Trust boundary

The Live Bridge is local tooling, not a remote-control service. The MCP sidecar and the Blockbench desktop plugin communicate only over a numeric-loopback WebSocket. The sidecar remains the authority for session creation, protocol validation, request correlation and MCP exposure. Blockbench remains the authority for the active project state exposed through its official API.

## Fail-closed rules

The bridge must reject rather than guess when any of these conditions occur:

- non-loopback host;
- protocol mismatch;
- expired session;
- wrong session ID;
- wrong token;
- malformed or oversized message;
- unknown or non-read-only method;
- stale connection generation;
- heartbeat timeout;
- replayed request ID with different payload;
- malformed physical-provider identity or extension allowlist entry;
- provider/extension incompatibility reported by the PR1 authority.

## Credentials

Sessions use ephemeral random credentials:

- 128-bit session ID;
- 256-bit token;
- finite TTL.

Session and token comparisons are timing-safe. The token must not appear in the WebSocket URL, session fingerprint, project snapshot, ordinary diagnostic logs or exported QA metadata. Connection descriptors are interactive local input and must not be persisted by the Toolkit.

The executable sidecar has one intentional secret-transfer channel: immediately after creating the local gateway it writes exactly one `RPG_ASSET_MCP_ONE_TIME_DESCRIPTOR=...` record to **stderr**. That record contains the ephemeral token and exists only so the local user can paste the descriptor into the Blockbench Connect action. It must be treated as a secret, must never be written to MCP stdout, and should not be retained or shared. Subsequent status/error logging must not repeat the descriptor or token.

## Network exposure

Allowed hosts are numeric `127.0.0.0/8` and `::1` only.

Explicitly rejected:

- `0.0.0.0` / wildcard binds;
- `localhost` or other hostnames;
- LAN/private-network addresses;
- public addresses;
- tunnels or remote transports.

PR2 does not define a remote-access mode.

## Capability allowlist

Only the 20 operations defined by `BLOCKBENCH-LIVE-BRIDGE-PROTOCOL.md` are routable. Installed extensions do not become MCP-authorized automatically. PR1's Extension Capability Registry remains the authority for recognition, exact-version compatibility and MCP allowlisting.

The following classes of operation are forbidden in PR2:

- arbitrary script/eval execution;
- arbitrary plugin action invocation;
- automatic plugin installation or URL loading;
- model/rig mutation;
- UV/texture mutation;
- animation mutation;
- exporter execution;
- shell commands;
- unrestricted filesystem access;
- arbitrary HTTP/network access;
- process control.

## Blockbench desktop boundary

The Toolkit remains `variant: both` so structural QA can load on Blockbench web and desktop. Live Bridge connection actions are registered only when `Blockbench.isWeb === false`.

The Live Bridge adapter is loaded lazily only when the user selects Connect. The standalone bundle permits only the explicitly audited native module `node:crypto`. Native modules such as `fs`, `node:fs`, `process`, `child_process`, `https`, `net`, `tls` and `electron` are not allowlisted by the Toolkit bundle.

## Connection authority and reconnect

Only one authenticated connection generation has authority at a time. A successful reconnect supersedes the previous generation. Old connections cannot deliver authoritative responses after replacement and are rejected as `STALE_CONNECTION`. Heartbeat expiry fails closed as `CONNECTION_TIMED_OUT`.

## Replay and idempotency

Each request has a bounded `requestId`. The sidecar hashes the method and params deterministically. Identical retries can reuse the original result; reuse of the same ID for a different payload is rejected as `REPLAY_CONFLICT`.

## Runtime context and data minimization

Project snapshots expose only the data required by the read-only methods. Absolute source paths are reduced to a filename. The fingerprint contains versions/IDs/revision metadata but excludes bridge credentials. No physical modlist filesystem scanning occurs in the Blockbench plugin.

Provider/context identity is supplied explicitly to the sidecar. Missing top-level context fields degrade to the explicit string `UNRESOLVED`; malformed provider entries and empty extension IDs are rejected instead of being converted silently into identities. Provider arrays and extension allowlists are bounded to 256 entries.

## Regression evidence

The PR2 test suites cover at minimum:

- exact read-only method allowlist and forbidden methods;
- numeric-loopback rejection;
- ephemeral credential shape and expiration;
- wrong token/session/protocol rejection;
- request replay and conflict handling;
- fingerprint secret exclusion;
- deterministic project revision and absolute-path redaction;
- malformed/oversized message rejection;
- real WebSocket handshake and request/response correlation;
- reconnect/stale-connection behavior;
- timeout failure;
- token absence from the WebSocket URL;
- executable sidecar runtime wiring into the real gateway;
- one-time descriptor compatibility with the Blockbench parser;
- malformed provider/extension runtime-context rejection;
- Blockbench client authentication/heartbeat/reconnect;
- web-mode load without native require or bridge actions;
- standalone bundle native-module allowlist.

Passing mock/unit tests does not constitute real Blockbench smoke or Minecraft runtime QA. Those remain separate gates.
