# E3 — Real ticket-level and per-tick availability trace on NeoForge 21.1.248

TRIAL_CLASS=EXPLORATORY_OBSERVATIONAL
TRIAL_ID=I10-E3-2026-10-14
RESULT=NOT_YET_OBSERVED
FIXTURE=Minecraft_1.21.1_NeoForge_21.1.248_Java_21
PHYSICAL_MODLIST_SHA256=7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00
CANONICAL_GOLDEN_JAVA_MODIFIED=NO
PR106_REVIEW_AND_PHYSICAL_GATES=PENDING

## Frozen question and falsifiers

E1 showed no observed unavailable casing chunk with staged `forceload`. E2 demonstrated autonomous recovery and a retry-disabled control under *synthetically* unavailable casing. E3 asks: **which actual ticket levels and per-tick chunk-presence states occur during the same staged unload/reload against the physically listed NeoForge 21.1.248?**

- H1: after only the controller/port chunks are forced, the two adjacent casing chunks receive ticket levels at or below 33, with controller/port also at or below 33. Predicted event transitions for casing chunks 9,9 and 10,9 eventually include new level 32. Falsifier: actual event trace contradicts these ticket levels or lacks sufficient events; a missing observation is inconclusive.
- H2: when the controller and port chunks are simultaneously loaded, both casing chunks are also accessible at each sampled full server tick. Falsifier: at least one server tick reports controller=true, port=true and casing_a=false or casing_b=false. A found gap is a *physical availability observation*, not yet proof of eventual retry recovery.
- H3: passive `i10probe peek` does not see `UNAVAILABLE` under this steady-state ticket configuration. Falsifier: at least one passive peek with validation=UNAVAILABLE. If that happens, P2 liveness still requires separate same-revision recovery, binding, and a retry-disabled negative-control physical experiment.

## Frozen method E3 and stop rules

1. Materialize exactly one **fresh** disposable `.factory-ci/i10/generated` I10 project from the canonical Factory golden. Before Gradle resolution, use the Factory's own supported-target conversion `_render_target_exact` to modify only generated `gradle.properties` and generated `gradle.lockfile` from NeoForge 21.1.250/FML 4.0.44 to NeoForge **21.1.248/FML 4.0.43**, preserving input/output SHA-256. Do not touch the canonical template, mod specs, goldens or mod repositories.
2. Add only a read-only, disposable Java event subscriber under the generated project. Capture `ChunkTicketLevelUpdatedEvent` old/new ticket levels per chunk for exactly four footprint chunks; also capture `LevelTickEvent.Post` server ticks using `ServerLevel.hasChunkAt` on four positions. Neither listener calls `getChunk`, a capability, or any ticket-mutating API. The corresponding event and `ChunkPos.getX/getZ` signatures have been verified against NeoForge 1.21.1-21.1.248 Javadoc.
3. Execute the already-established E1 two-phase staged real-server diagnostic **once** on the 21.1.248 fixture. Its return code 2 remains `PENDING_UNREPRODUCED`, never PASS. Preserve the actual server logs and command output.
4. Audit per-chunk ticket transitions and per-game-tick availability independently of the E1 passive `peek` sample rate. Produce structured JSON with every ticket transition, number of per-tick samples, count of simultaneous controller+port loaded with missing casing, and `UNAVAILABLE` peek count. Emit `TRACE_INCOMPLETE` if events/peeks are missing; `OBSERVED_ALL_ADJACENT_CHUNKS_LOADED` for no gap; or `OBSERVED_REAL_PARTIAL_AVAILABILITY_NEEDS_REVIEW` if the tick trace sees a gap. Never print `PASS` or close P2.

Stopping condition: one dedicated-server run with two restart phases, no repeats unless the first result motivates a separately frozen hypothesis. Any compile/runtime error is a blocker, not a negative scientific result. A successful GitHub Actions job means the trace was collected and classified, not the physical P2 acceptance gate.

## Version-exact external API evidence (consulted 2026-10-14)

- NeoForge `ChunkTicketLevelUpdatedEvent` for 1.21.1-21.1.248, server bus and getters: https://aldak.netlify.app/javadoc/1.21.1-21.1.x/net/neoforged/neoforge/event/level/chunkticketlevelupdatedevent
- NeoForge `ChunkEvent` for 1.21.1-21.1.248: https://aldak.netlify.app/javadoc/1.21.1-21.1.x/net/neoforged/neoforge/event/level/chunkevent
- Minecraft 1.21.1 `ChunkPos.getX/getZ(long)` signatures: https://lexxie.dev/neoforge/1.21.1/net/minecraft/world/level/ChunkPos.html
- Minecraft 1.21.1 `LevelTickEvent.Post` hook and call sites: https://aldak.netlify.app/javadoc/1.21.1-21.1.x/net/neoforged/neoforge/event/eventhooks
- Factory supported loader profiles: `engineering/tooling/scaffolder/scaffold_mod.py`, versions 21.1.248 => FML 4.0.43, 21.1.250 => FML 4.0.44. These local pins govern the experiment.

## Boundaries

- This is an **observational fixture**, not modpack-wide testing. A dedicated server with I10 only at loader 21.1.248 does not test the full 595-mod physical modpack.
- H2 can be falsified at individual ticks even if passive half-second peeks never observe it; an observed tick gap still needs same-revision liveness and physical retry-disabled control.
- Three P2 discussions, exact-commit two-real-client multiplayer acceptance, formal technical review and merge remain blocked.
