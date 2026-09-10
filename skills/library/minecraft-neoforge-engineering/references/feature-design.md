# Feature design

Use for gameplay systems spanning multiple classes, persistent state, simulation, networking, worldgen, or cross-mod integration.

## Define observable behavior

Write acceptance criteria in terms of what a player/server/world can observe. Replace "realistic", "smooth", "balanced", or "optimized" with measurable rules whenever feasible.

## State model

Determine:

- state owner: player/entity/block entity/chunk/level/dimension/server/global;
- authority: usually server for gameplay state;
- lifetime: transient/session/persistent;
- creation/update/retirement points;
- serialization/versioning needs;
- synchronization projection to clients;
- behavior on death, clone, respawn, logout, reconnect, dimension change, chunk unload/load, server restart, or datapack reload where relevant.

## Event/lifecycle model

Select the narrowest authoritative trigger. Avoid global ticking if an event, scheduled queue, indexed set, or state transition can represent the same behavior.

## Performance budget

State complexity and an explicit upper bound for hot paths. Examples: max nodes processed per tick, max pending effects per level, max propagation radius, max retries, cache eviction/retirement policy.

## Failure behavior

Define what happens when data is missing/corrupt/old, an optional mod disappears, chunks unload, network input is invalid, or upstream API is unavailable.

## Verification

Map each acceptance criterion to unit test, GameTest/integration test, server smoke, client/manual scenario, or static evidence.

Use `assets/FEATURE_SPEC_TEMPLATE.md` for major features.
