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

## E3 observed evidence — 2026-10-14 (append-only, no PASS)

- Immutable source commit: `2617630684c6e2454bf775031097bf9b833ea15a`. [GitHub Actions run 38612734175](https://github.com/Gustavaopere/minecraft-mod-factory/actions/runs/38612734175) completed `SUCCESS` for compilation, tests, physical-version NeoForge 21.1.248 profile conversion, ticket instrumentation, real dedicated server, and result classification.
- [Artifact 11918663641](https://github.com/Gustavaopere/minecraft-mod-factory/actions/runs/38612734175/artifacts/11918663641) `i10-e3-real-ticket-trace-21-1-248`: six files, ZIP CRC passed, ZIP SHA-256 `409da16fda90e49c34656a103dcf69c6e39d92bb56c22642616137a5e9ddca7d`. The archive has two per-phase server logs, command log, conversion provenance, structured JSON result, and initial diagnostic summary.
- The generated project used **Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21**, pinned with the Factory-supported FML 4.0.43 and NeoForge lockfile. Generated `gradle.properties` and lockfile before/after SHA-256 values are in `preflight.json`. Canonical Factory Java golden and mod runtime repositories remain unchanged.
- The NeoForge event subscriber recorded **17 real** `ChunkTicketLevelUpdatedEvent` changes in the staged restart. At game tick 73, target levels transitioned from 45 to 38/39 during scheduling; at tick 74 they converged to `31` for controller/port chunks (9,10)/(10,10) and `32` for both casing chunks (9,9)/(10,9). This directly supports steady-state adjacent chunk ticket propagation, beyond the earlier static model. At tick 679, server stop cleared the tickets back to level 45.
- Passive, per-server-tick `ServerLevel.hasChunkAt` traces: **605 samples**, ticks **75–679**; first sample and last sample have all four chunks present. **0 samples** had both controller and port present with either casing chunk absent. No capability query was made in the event observer. These samples **cannot** exclude a gap before the first recorded tick or a sub-tick transient; they do exclude the sought sustained gap throughout the measured window.
- Passive `i10probe peek`: **50 observations** and **0 `UNAVAILABLE`**. Original staged-reload diagnostic exited **2** (`PENDING_UNREPRODUCED`); analysis produced **`OBSERVED_ALL_ADJACENT_CHUNKS_LOADED`** and `physical_chunk_race_proven=false`, correctly without declaring P2 success.
- Scientific outcome: H1 and H3 corroborated in the sampled real server trace, H2 was not falsified. The specific physically absent-neighbor `UNAVAILABLE → PENDING_REVALIDATION → FORMED` scenario remains **unreproduced**. E2's synthetic retry/no-retry counterfactual is separate and cannot fill this missing physical prerequisite. A physically unavailable-neighbor retry-disabled negative control has **not** been performed.
- Suggested next direction: instrument or control a genuine asynchronous promotion/depromotion boundary rather than repeating persistent level-31 `/forceload` tickets; validate any new approach with target-exact source and an explicit negative control. Do not mutate vanilla tickets or manufacture chunks to assert real physical absence.

**Gates:** 3 P2 discussions OPEN; formal review PENDING; exact-runtime two-real-client physical acceptance PENDING; PR #106 stays DRAFT/UNMERGED; `main` and root STATUS unchanged.
