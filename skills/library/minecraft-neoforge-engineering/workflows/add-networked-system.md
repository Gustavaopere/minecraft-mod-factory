# Workflow: add a networked server-authoritative system

1. Model authoritative server state and client projection separately.
2. Define all state transitions before packets.
3. Specify payload directions, IDs, fields, size/range bounds, validation, handler context, and recipient scope.
4. Verify exact NeoForge 1.21.1 networking APIs.
5. Add unit tests for state machine/validation/serialization seams where practical.
6. Implement server logic independent of UI/rendering where possible.
7. Add network adapter and initial/resync flows.
8. Add client projection/render/input adapter.
9. Test invalid/stale requests and reconnect/dimension/tracking transitions as relevant.
10. Run dedicated-server and client/runtime verification.
