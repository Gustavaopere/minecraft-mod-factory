# Blockbench Live Bridge Protocol

Status: PR2 — read-only transport contract
Protocol version: `1.0.0`
Toolkit baseline: Blockbench Desktop `5.1.6+`

## Purpose

This contract defines the historical Minecraft Mod Factory Asset Toolkit read-only Live Bridge. It connects an MCP stdio sidecar to the Blockbench desktop plugin through an authenticated numeric-loopback WebSocket. It does not authorize asset mutation, exporter execution, arbitrary plugin actions, JavaScript execution, shell commands, arbitrary filesystem access, arbitrary HTTP access, process control, or plugin installation.

## Topology

```text
MCP client
  ↕ stdio
Minecraft Mod Factory Asset MCP sidecar
  ↕ authenticated WebSocket on numeric loopback only
Minecraft Mod Factory Asset Toolkit / Blockbench desktop plugin
  ↕ official Blockbench API + PR1 provider/extension authorities
active Blockbench project
```

The WebSocket endpoint accepts only numeric loopback addresses: `127.0.0.0/8` or `::1`. Hostnames such as `localhost`, wildcard binds, LAN addresses and public addresses are rejected.

## Session and handshake

A sidecar session contains:

- `sessionId`: 16 random bytes encoded as 32 hexadecimal characters;
- `token`: 32 random bytes encoded as 64 hexadecimal characters;
- `protocolVersion`: `1.0.0`;
- `createdAt` and `expiresAt`;
- default TTL: 15 minutes unless explicitly configured by the sidecar.

The token is not part of the WebSocket URL. The plugin sends an authenticated handshake containing only approved read-only capabilities and its session fingerprint. A newer authenticated connection becomes the sole active connection generation; responses from an older connection are rejected as stale. Heartbeats maintain connection liveness and timeout fail-closed.

## Request envelope

Each routed request must contain non-empty strings:

- `protocolVersion`;
- `sessionId`;
- `token`;
- `requestId`;
- `method`;
- `params` object, default `{}`.

`requestId` is limited to 128 characters. A complete encoded message is limited to 64 KiB. Malformed JSON, invalid session/token shapes, oversized messages and unknown methods are rejected before routing.

## Read-only method allowlist

The protocol exposes exactly these methods:

- `blockbench.get_status`
- `blockbench.get_capabilities`
- `blockbench.get_project`
- `blockbench.get_scene_graph`
- `blockbench.get_selection`
- `blockbench.get_bones`
- `blockbench.get_elements`
- `blockbench.get_textures`
- `blockbench.get_animations`
- `blockbench.get_animation`
- `blockbench.compute_bounds`
- `blockbench.validate`
- `blockbench.validate_contract`
- `blockbench.extensions.list`
- `blockbench.extensions.get`
- `blockbench.extensions.get_fingerprint`
- `blockbench.extensions.check_compatibility`
- `blockbench.profiles.list`
- `blockbench.profiles.get`
- `blockbench.profiles.resolve_for_asset`

Any other method is `METHOD_NOT_ALLOWED`.

## Revision and project snapshot

The project snapshot is read-only and produces a deterministic SHA-256 `projectRevision` from normalized project state. Absolute source paths are not exposed; only the source filename may appear in the snapshot. Changes to relevant project state change the revision.

## Idempotency and replay

The request ledger keys by `requestId` and a SHA-256 hash of `{method, params}`:

- repeated identical requests reuse the same result;
- reusing a `requestId` with a different method or params fails with `REPLAY_CONFLICT`;
- failed executions are removed from the ledger and may be retried with a new valid request.

## Fingerprint

The session fingerprint contains only bounded operational evidence:

- Minecraft version;
- loader;
- Java version;
- Blockbench version;
- Toolkit version;
- protocol version;
- installed extension IDs/versions;
- physical provider IDs/versions supplied by the sidecar;
- active provider profile;
- project format;
- project revision.

Bridge secrets (`sessionId`, token) are excluded.

## Explicit non-goals for PR2

PR2 does not provide modeling, rig, UV, texture or animation mutations; Undo transactions; provider-specific export; automatic plugin installation; arbitrary extension actions; remote/tunnel transport; arbitrary JavaScript; shell; unrestricted filesystem/HTTP/process access.

Those capabilities require later, separately reviewed contracts and must not be inferred from the existence of the read-only bridge.
