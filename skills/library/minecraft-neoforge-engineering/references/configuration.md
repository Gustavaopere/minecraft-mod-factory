# Configuration

Before adding a config value define:

- server/client/common scope;
- authoritative owner;
- valid range/type;
- default and migration behavior;
- whether runtime reload is supported;
- synchronization needs;
- effect on deterministic tests/world saves.

Do not use client config to control server-authoritative mechanics in multiplayer. Validate numeric ranges and ensure extreme legal values cannot create unbounded loops, enormous queues, or invalid physics.

Avoid exposing internal implementation knobs as public config unless users can reason about them.
