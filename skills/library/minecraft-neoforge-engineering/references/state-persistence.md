# State and persistence

Choose storage by ownership and lifetime, not convenience.

Possible patterns include entity/player attachments or project abstractions for per-owner state, block-entity state for block-bound behavior, and level/server SavedData for broader persistent state. Verify exact 1.21.1 APIs.

For persistent state define:

- stable key/ID;
- default/absence behavior;
- serializer/codec;
- dirty/change tracking if required;
- migration/defaulting for old saves;
- unload/reload and restart behavior;
- cloning/respawn semantics for player data;
- authoritative synchronization if clients need a projection.

Never store a live world/entity reference in persistent serialized data. Persist stable identifiers/coordinates/resource keys and re-resolve safely.

Collections tied to chunks/entities/players need explicit retirement to prevent memory leaks after unload/logout/death.
