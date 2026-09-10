# Networking

Use networking only for state that genuinely crosses client/server boundaries.

## Design

For every payload/message define:

- direction;
- sender trust model;
- payload ID/versioning expectations;
- fields and size bounds;
- serialization/stream codec;
- handler execution context;
- server validation;
- recipient scope;
- resynchronization behavior.

For client → server requests, validate that the sender may perform the action: distance, current item/menu/state, cooldown, permissions, dimensions, referenced entity/block existence, numeric ranges, and rate limits as applicable.

For server → client synchronization, send the smallest projection the client needs. Do not mirror entire server state by default.

Plan initial synchronization for join/rejoin, tracking start, dimension change, menu open, or state creation as appropriate.

NeoForge 1.21.1 official networking docs use payload registration through `RegisterPayloadHandlersEvent`. Verify exact registrar/payload/codec APIs against the resolved 21.1.x version before coding.
