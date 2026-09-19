# I10 Multiplayer Acceptance Protocol

I10_MULTIPLAYER_ACCEPTANCE_STATE=PENDING_MANUAL_MULTIPLAYER_ACCEPTANCE

## Purpose

This protocol is the manual acceptance authority for the I10 multiblock multiplayer gate.

The acceptance target is Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21. The dedicated server, Client A, and Client B must all run the same I10 materialization produced from the exact commit being accepted.

## Evidence boundary

Only two real Minecraft clients count as multiplayer evidence. Client A and Client B must be distinct Minecraft client processes with distinct player identities connected to the same dedicated server and world.

Fake players are insufficient. Fake players, server-only tests, GameTests, unit tests, a dedicated-server startup by itself, synthetic JSON, replayed logs, or screenshots without matching logs cannot satisfy this gate.

All evidence belongs under `build/i10-multiplayer-acceptance/` for the tested materialized project.

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

Additional raw runtime logs and screenshots may be retained under `build/i10-multiplayer-acceptance/raw/`; they complement but do not replace the canonical evidence files above.

`metadata.json` must record the commit SHA, Minecraft `1.21.1`, NeoForge `21.1.250`, Java `21`, the dedicated-server world identity, Client A identity, Client B identity, and the start/end timestamps of the acceptance session. The two client identities must be different.

## Manual startup handoff

Manual startup is the default physical handoff. A fresh I10 materialization provides:

- `START-I10-SERVER.bat` / `START-I10-SERVER.sh`;
- `START-I10-CLIENT-A.bat` / `START-I10-CLIENT-A.sh`;
- `START-I10-CLIENT-B.bat` / `START-I10-CLIENT-B.sh`;
- `run-i10-manual-process.py` for one-process-at-a-time logging and metadata.

There is intentionally no `START-I10-MULTIPLAYER.bat` or `START-I10-MULTIPLAYER.sh` that launches server and both clients together.

The manual process helper is allowed to:

- start exactly one requested Gradle run: `runServer`, `runClientA`, or `runClientB`;
- isolate Gradle under the package-local `.i10-gradle-user-home`;
- configure the dedicated development server for offline login and accept the EULA;
- preserve `server.log`, `client-a.log`, and `client-b.log`;
- append a later Client B launch to `client-b.log` for reconnect evidence;
- retain underlying Minecraft logs/screenshots under `raw/`;
- write target/commit/session metadata.

The helper does not synthesize formation, invalidation, reconnect observations, screenshots, or PASS.

## Deterministic baseline

Before either client performs an acceptance observation:

1. Start the dedicated server manually from the exact physical artifact.
2. Keep the tested footprint loaded with:
   `forceload add 159 160 161 160`
3. Prepare the canonical structure with:
   `i10probe baseline`
4. The server must report:
   `validation=VALID runtime=UNFORMED revision=0 sentinel=empty count=0 capability=false last_known_formed=false`
5. A subsequent `i10probe status` must remain `VALID + UNFORMED` with capability absent and `last_known_formed=false`.
6. Do not use `i10probe setup` for this multiplayer baseline. The next formation must come from Client A through normal in-game interaction.

`i10probe baseline` is acceptance-only tooling: it clears the canonical footprint, rebuilds the fixed I10 structure, and leaves the new controller unformed with no historical formation state.

## Preconditions

1. Use an exact I10 commit whose contracts, fresh materialization, target-exact build, GameTests, and real chunk acceptance are already green.
2. Materialize I10 from that exact commit. Do not reuse a generated project from another commit.
3. Start the dedicated server with `START-I10-SERVER.bat` or `START-I10-SERVER.sh` and retain its complete log.
4. Prepare and verify the deterministic baseline above.
5. Start Client A and Client B separately from the same materialization/target and retain each complete client output independently.
6. Connect both clients to the same dedicated server and the same world before the multiplayer observations begin.
7. Move both clients so the controller/port are loaded and visible. The generated client runs use identities `I10ClientA` and `I10ClientB`.

## Required physical sequence

Perform the sequence in this order. Evidence from another order does not close the gate.

1. With Client A and Client B connected to the same world, verify that both clients observe UNFORMED. Capture `a-unformed-before-form.png` and `b-unformed-before-form.png` while both clients are online.
2. Client A forms through normal interaction with the controller. The interaction must originate from Client A in the running Minecraft client; a server command, fake player, GameTest helper, direct NBT edit, or synthetic state mutation does not count as the formation action.
3. Wait for the server-authoritative blockstate update and verify that both clients observe FORMED. Capture `a-formed.png` and `b-formed.png` before any invalidation action.
4. From the dedicated-server console, server-authoritatively break one required casing using `i10probe break_required_part`. Retain the corresponding `I10_PROBE` line in the server log.
5. Wait for revalidation. Verify that both clients observe UNFORMED and no port IO is available. Capture `a-unformed-after-break.png` and `b-unformed-after-break.png`. The server log must show the invalidated state and `capability=false`.
6. While Client A remains connected, disconnect Client B completely from the server.
7. Without rebuilding or reforming the structure, start the Client B wrapper again and reconnect Client B to the same dedicated server and world.
8. Verify that Client B receives the current UNFORMED state without historical replay of the prior formed state. Capture `b-unformed-after-reconnect.png`.
9. Stop both clients and the server cleanly and preserve the complete evidence directory unchanged for review.

## Acceptance checks

The evidence reviewer must verify all of the following before any later closeout may promote this gate:

- the recorded commit SHA is the exact commit used by the server and both clients;
- target metadata is Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21;
- Client A and Client B are two distinct real Minecraft client processes and player identities;
- both clients joined the same dedicated-server world;
- the server baseline before client formation was VALID + UNFORMED with port capability absent;
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

If manual execution is required, guide the operator through one manual action at a time and wait for the result before continuing. Do not change this protocol's acceptance state merely because the written procedure or manual wrappers exist; only the real two-client evidence set can authorize the later closeout.
