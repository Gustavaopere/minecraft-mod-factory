# E4 — OnLoad versus ChunkEvent.Load ordering at physical NeoForge 21.1.248

TRIAL_ID=I10-E4-2026-10-14
TRIAL_CLASS=EXPLORATORY_OBSERVATIONAL
PREREGISTRATION_STATUS=FROZEN_BEFORE_FIRST_RUN
RESULT=NOT_YET_OBSERVED
FIXTURE=Minecraft_1.21.1_NeoForge_21.1.248_Java_21
MODLIST_SHA256=7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00

## Question, predicted observations and falsifiers

E3 observed 17 real ticket updates, including the adjacent casing chunks at level 32 on game tick 74, and **605 post-level-tick snapshots (75–679)** with no casing unavailable. E3 could not observe the controller's `BlockEntity.onLoad` or the pre-FULL `ChunkEvent.Load` events. E4 asks whether an unavailable casing chunk is observable **earlier than the first normal server tick**, while the controller and port are both already loaded.

- H1: `BlockEntity.onLoad` for an already-formed controller occurs with controller/port loaded but at least one adjacent casing chunk absent (`hasChunkAt=false`). A snapshot meeting those conditions would support a real, earlier-than-first-tick availability gap. Falsifier: all recorded qualifying onLoad snapshots show controller, port and both casings present. Absence of an onLoad marker leaves E4 inconclusive.
- H2: native controller `revalidate` may encounter `UNAVAILABLE` after `onLoad` despite all chunks being present at sampled post-ticks. This is measured passively by logging the *actual result of `MultiblockPattern.validate` in revalidate*, not by synthesizing a missing chunk. Falsifier: all observed revalidations were `VALID` (or none observed, which is inconclusive).
- H3: `ChunkEvent.Load` and unload events supply an earlier lifecycle order than the first tick. A missing lifecycle event is an incomplete trace, not proof the chunk never loaded. This lifecycle event can precede FULL and is **never allowed to access the level** inside the event handler.

## Preregistered experiment

Only one new run is permitted without a revised research question. Generate one fresh `.factory-ci/i10/generated` from the Factory I10 golden. Apply E3's existing explicit version-profile conversion to NeoForge 21.1.248 / FML 4.0.43 and its read-only ticket/tick observer. Modify only the **materialized Java copies**, adding logging in the generated controller's real `onLoad` and `revalidate` paths, and `ChunkEvent.Load`/`ChunkEvent.Unload` event handlers that read **only the event's `ChunkAccess#getPos()`** (never the level, chunk creation or a capability). Save before/after hashes. The golden runtime and individual mod repositories remain unchanged.

Run Java 21 Gradle test/build, then exactly one existing real staged unload/reload diagnostic using live vanilla `/forceload`. It may terminate 2 for `PENDING_UNREPRODUCED`. Parse the restart server log and record every chunk lifecycle event, onLoad state and validator result. Incomplete event/onLoad/revalidation evidence must be `INCOMPLETE_EARLY_LIFECYCLE_TRACE` and must fail closed; an observed onLoad gap must be `OBSERVED_REAL_ONLOAD_GAP_REQUIRES_REVIEW`, **not PASS**; a complete trace with no gap is `NO_REAL_ONLOAD_GAP_OBSERVED`. Record absolute game ticks and monotonic clock nanos for ordering.

Even a real onLoad chunk absence would not alone prove autonomous after-retry liveness, and no physically missing-casing retry-disabled negative control is included. A complete P2 proof requires genuine UNAVAILABLE encountered by the actual controller, pending state, autonomous same-revision recovery with stable binding, physical negative control and independent review. Exact-HEAD two-real-client acceptance remains separate.

## Evidence and safety

- NeoForge 1.21.1-21.1.248 `ChunkEvent.Load` may fire before the chunk reaches FULL. Never call `level`, `getChunk`, `getBlockState`, `hasChunkAt` or capability APIs from the chunk event listener. The `ChunkAccess#getPos` accessor only is safe and deterministic: https://aldak.netlify.app/javadoc/1.21.1-21.1.x/net/neoforged/neoforge/event/level/chunkevent
- Java script and source isolation contract: `engineering/tests/experiments/i10_e4_onload_boundary_trace_248.py` and `engineering/tests/test_i10_e4_onload_boundary_trace_248.py`.
- CI: `.github/workflows/factory-engineering-i10-e4-early-load-248.yml`; artifact name `i10-e4-onload-early-real-248`.
- The physical modlist is the authority for NeoForge 21.1.248. This one-mod disposable test is not certification of the full modpack. Three P2 threads remain open; Draft PR #106 remains unmerged; main/STATUS unchanged.
