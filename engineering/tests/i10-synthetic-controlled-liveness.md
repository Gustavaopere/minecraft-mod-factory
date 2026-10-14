# I10 E2 — Synthetic visibility, native retry, negative control

TRIAL_CLASS=CONTROLLED_SYNTHETIC_SERVER_EXPERIMENT
RESULT=NOT_YET_OBSERVED
NOT_A_PHYSICAL_CHUNK_UNLOAD=true
FIXTURE_TARGET=Minecraft_1.21.1_NeoForge_21.1.250_Java_21
PHYSICAL_MODLIST_TARGET=NeoForge_21.1.248

## Frozen question and falsifiers

E2 asks whether the **unmodified production I10 controller retry algorithm** (except in the deliberately mutated negative variant) autonomously restores a persisted multiblock when its validator reports UNAVAILABLE for an adjacent casing position, without a port capability query. The absence is **synthetic**: the casing chunk remains physically loaded. E2 never claims to satisfy the open requirement to observe a genuinely unavailable neighbor chunk.

- H-positive: while a test-only availability gate reports UNAVAILABLE for casing chunk (9,9), the actual NeoForge server's persisted controller reaches PENDING_REVALIDATION and both formed visuals turn false with the original revision and binding preserved. After release, the regular 20-tick scheduled retry restores FORMED, visuals and binding without any `i10probe status` or capability query beforehand. Falsifier: any missing transition, revision change, early capability probe or timeout.
- H-negative: a clone of the same disposable fixture with **only the revalidate UNAVAILABLE path's scheduled retry call removed** stays PENDING_REVALIDATION at least 60 game ticks after release, with no capability query. Falsifier: the negative mutant autonomously reaches FORMED or loses its revision. The negative mutant is never the canonical golden source.

## Preregistered method

Run exactly two variants in distinct, fresh `.factory-ci/i10/{positive,negative}` directories, without overwriting a world or prior evidence. `engineering/tests/experiments/i10_synthetic_retry_control.py instrument` copies the canonical golden fixture and only then patches the **generated** `MultiblockPattern` to simulate a missing casing chunk through a test environment variable, and adds an explicit release console command. The negative variant additionally removes one scheduled retry call from the generated `revalidate` implementation. Hashes of the original and instrumented Java files are emitted. The factory's golden Java files and all real mod runtime repositories are left untouched.

Both variants first form the four-chunk multiblock, drain 40 actual game ticks, save and observe real complete four-chunk unload. After dedicated-server restart they load the full footprint **physically** but report the single casing chunk synthetically unavailable. `i10probe peek` must observe the required pending state and revision without port capability query. Release the synthetic visibility gate. The positive variant awaits autonomous recovery before its first capability assertion. The negative variant waits at least 60 game ticks without any capability assertion and requires persistent pending. Per-phase dedicated-server logs and JSON evidence are preserved.

Experiment runner: `.github/workflows/factory-engineering-i10-synthetic-retry-control.yml`. Each matrix job is fail-closed; any absent observation fails its job. A workflow with both jobs green supports only `SYNTHETIC_UNAVAILABLE` scheduling evidence, **not** `REAL_UNAVAILABLE` nor the two-real-client physical gate.

## Boundaries and stop rules

- Do not resolve the three P2 discussions from a synthetic PASS alone. The target-exact race / chunk-ticket event observations and subsequent physically unavailable neighbor test remain an independent unresolved requirement.
- Do not use the synthetic test to rebaseline historical physical evidence or promote PR #106 out of Draft.
- If either variant fails compilation, fails its contract, or does not observe the intended transition, retain the raw evidence and label E2 `BLOCKED`. Do not weaken the assertions or mask the failure as a successful test.
- Run the exact unchanged canonical I10 regressions as a separate job. Never put the test visibility hook in the published golden or a mod runtime repository.

## Version-matched API evidence

- NeoForge 1.21.1 / 21.1.250 chunk ticket event: https://aldak.netlify.app/javadoc/1.21.1-21.1.x/net/neoforged/neoforge/event/level/chunkticketlevelupdatedevent
- Minecraft 1.21.1 ChunkLevel methods: https://mappings.dev/1.21.1/net/minecraft/server/level/ChunkLevel.html
