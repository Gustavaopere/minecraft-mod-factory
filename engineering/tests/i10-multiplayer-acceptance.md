# I10 Multiplayer Acceptance Protocol

I10_MULTIPLAYER_ACCEPTANCE_STATE=PENDING_MANUAL_MULTIPLAYER_ACCEPTANCE

## Purpose

This protocol is the manual acceptance authority for the I10 multiblock multiplayer gate when no Factory automation harness exists that provides equivalent observations from two real Minecraft clients.

The acceptance target is Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21. The dedicated server, Client A, and Client B must all run the same I10 materialization produced from the exact commit being accepted.

## Evidence boundary

Only two real Minecraft clients count as multiplayer evidence. Client A and Client B must be distinct Minecraft client processes with distinct player identities connected to the same dedicated server and world.

Fake players are insufficient. Fake players, server-only tests, GameTests, unit tests, a dedicated-server startup by itself, synthetic JSON, replayed logs, or screenshots without matching logs cannot satisfy this gate.

All evidence belongs under `build/i10-multiplayer-acceptance/` for the tested materialized project. The evidence set must contain the exact commit SHA and target, the server log, the Client A log, the Client B log, and screenshots for the required client-visible states.

Required evidence layout:

```text
build/i10-multiplayer-acceptance/
├── metadata.json
├── server.log
├── client-a.log
├── client-b.log
└── screenshots/
    ├── a-unformed-before-form.png
    ├── b-unformed-before-form.png
    ├── a-formed.png
    ├── b-formed.png
    ├── a-unformed-after-break.png
    ├── b-unformed-after-break.png
    └── b-unformed-after-reconnect.png
```

`metadata.json` must record the commit SHA, Minecraft `1.21.1`, NeoForge `21.1.250`, Java `21`, the dedicated-server world identity, Client A identity, Client B identity, and the start/end timestamps of the acceptance session. The two client identities must be different.

## Preconditions

1. Use an exact I10 commit whose contracts, fresh materialization, target-exact build, GameTests, and real chunk acceptance are already green.
2. Materialize I10 from that exact commit. Do not reuse a generated project from another commit.
3. Start the dedicated server from that materialization and retain its complete console output as the server log.
4. Start Client A and Client B from that same materialization/target and retain each complete client output independently as the Client A log and Client B log.
5. Connect both clients to the same dedicated server and the same world before the multiplayer observations begin.
6. Build the canonical valid 3×3×3 I10 structure through normal game/world placement while leaving the controller unformed. Controller, rear IO port, hollow interior, casing boundary, facing and rotation must match the I10 canonical pattern. Do not activate the controller while preparing this baseline.

## Required physical sequence

Perform the sequence in this order. Evidence from another order does not close the gate.

1. With Client A and Client B connected to the same world, verify that both clients observe UNFORMED. Capture `a-unformed-before-form.png` and `b-unformed-before-form.png` while both clients are online.
2. Client A forms through normal interaction with the controller. The interaction must originate from Client A in the running Minecraft client; a server command, fake player, GameTest helper, direct NBT edit, or synthetic state mutation does not count as the formation action.
3. Wait for the server-authoritative blockstate update and verify that both clients observe FORMED. Capture `a-formed.png` and `b-formed.png` before any invalidation action.
4. From the dedicated-server console, server-authoritatively break one required casing using the I10 acceptance command `i10probe break_required_part`. Retain the corresponding `I10_PROBE` line in the server log.
5. Wait for revalidation. Verify that both clients observe UNFORMED and no port IO is available. Capture `a-unformed-after-break.png` and `b-unformed-after-break.png`. The server log must show the invalidated state and `capability=false`; no client-side inference may override the server state.
6. While Client A remains connected, disconnect Client B completely from the server.
7. Reconnect Client B to the same dedicated server and world without rebuilding or reforming the structure.
8. Verify that Client B receives the current UNFORMED state without historical replay of the prior formed state. Capture `b-unformed-after-reconnect.png` and retain the reconnect section of the Client B log.
9. Stop both clients and the server cleanly and preserve the complete evidence directory unchanged for review.

## Acceptance checks

The evidence reviewer must verify all of the following before any later closeout may promote this gate:

- the recorded commit SHA is the exact commit used by the server and both clients;
- target metadata is Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21;
- Client A and Client B are two distinct real Minecraft client processes and player identities;
- both clients joined the same dedicated-server world;
- both clients saw the same pre-formation UNFORMED state;
- the formation action originated from Client A through normal interaction;
- both clients received the FORMED transition;
- the required casing was broken server-authoritatively after formation;
- both clients received the post-break UNFORMED transition and the server denied port capability;
- Client B disconnected and reconnected after invalidation;
- Client B received current UNFORMED state after reconnect without historical replay;
- server log, Client A log, Client B log, screenshots, and metadata are all present and temporally consistent.

Any missing, ambiguous, synthetic, replayed, single-client, server-only, or mismatched-commit evidence leaves this protocol in its current pending state. Dedicated-server startup and GameTest success are necessary engineering evidence but are not multiplayer acceptance.

## Execution rule

If manual execution is required, guide the operator through one manual action at a time and wait for the result before continuing. Do not change this protocol's acceptance state merely because the written procedure exists; only the real two-client evidence set can authorize the later closeout.
