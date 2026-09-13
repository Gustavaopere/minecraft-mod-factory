# I10 — Multiblock Foundation Reference — Design

## Status

Architecture option A was approved operationally in chat on 2026-09-13 by the user's explicit instruction to proceed after the I10 decision gate. This document is the design artifact only. It does not authorize implementation until the user reviews and approves this spec.

## Canonical authorities

- Engineering plan: `plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md`
- Art/asset plan: `plans/PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md`
- Current status authority: root `STATUS.md`
- Physical modlist snapshot SHA-256: `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`
- Target: Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`
- Current I10 base: `e7f92897f3492cc64e14c27b827b419a33bb2e5d`
- Current asset handoff contract: `engineering/schemas/asset-handoff.schema.json`, schema version `2`

The engineering plan defines the I10 multiblock vertical slice gate as controller, parts, orientation, formation, invalidation, unload/reload, IO capability, visual formed state, asset manifest, GameTest, persistence, and multiplayer. The plan also places multiblock runtime authority in the generated mod while Repo Textura remains authority for multiblock visual contracts and assets.

## Problem statement

I9 proves a target-exact single-block machine reference. I10 must prove that the Factory can materialize a new, independent Golden project containing a real multiblock lifecycle without coupling that reference to the I9 machine runtime, without expanding I8 into a multiblock generator, and without violating the Engineering × Repo Textura authority boundary.

The reference must demonstrate bounded structure validation, horizontal rotation, safe formation/dissolution, chunk-aware reload behavior, capability delegation through a part, persistent controller state, synchronized visual state, and multiplayer-observable correctness on the physical NeoForge target.

## Architectural decision

Use a **new compositional I10 Golden**, generated from a fresh canonical I3 scaffold plus an I10-owned overlay.

The I10 overlay may reuse proven patterns from I9 for deterministic materialization, capability registration, BlockEntity persistence, GameTest layout, dedicated-server gates, and evidence collection, but it must not depend on the I9 Golden's runtime classes or materialized project.

Rejected alternatives:

1. **Transform the I9 Golden into the I10 Golden** — rejected because it couples I10 identity and lifecycle to the machine reference and makes independent regression boundaries harder to preserve.
2. **Add multiblock as an I8 generic feature** — rejected because I8 is a deterministic feature-skeleton generator, while I10 is a composed runtime reference with cross-block lifecycle behavior.
3. **Extract a generic Golden compositor before I10** — rejected because only one stable composed runtime reference exists today. Premature extraction would expand blast radius before a second composition proves the abstraction boundary.

## Scope

I10 must implement and prove all twelve gate items:

1. controller;
2. parts;
3. orientation;
4. formation;
5. invalidation;
6. unload/reload;
7. IO capability;
8. visual formed state;
9. asset manifest;
10. GameTest;
11. persistence;
12. multiplayer.

I10 also inherits I3/I4/I5 target identity, validation, build, GameTest-server, dedicated-server, security, and evidence behavior where applicable.

## Non-goals

I10 does not include:

- recipe processing;
- energy processing;
- fluids;
- machine GUI/menu/screen;
- logistics graph or routing (I11);
- provider adapter framework (I12);
- release tooling (I13);
- the I14 full end-to-end Golden;
- animated provider-specific multiblock rendering;
- automatic Blockbench authoring;
- arbitrary-size or data-driven multiblock schemas;
- nested multiblocks;
- cross-dimensional structures;
- chunk loading/ticket creation;
- moving contraptions;
- Create/Flywheel integration;
- a generic production multiblock API intended for direct reuse by every mod.

The Golden proves the engineering capability. It does not become the runtime authority for future production mods.

## Reuse and provenance

Pre-I10 audit found no reusable generic multiblock implementation in the Factory or historical RPG source that should be migrated instead of authored.

Reuse boundaries:

- **I3 scaffolder**: canonical project/build/bootstrap base.
- **I4 validators**: project/resource/side/security validation.
- **I5 test harness**: unit, GameTest-server, dedicated-server, artifact/evidence execution.
- **I6 handoff**: schema/validator authority for the visual asset manifest.
- **I9**: implementation patterns only; no Java/runtime dependency and no I9 materialized project dependency.

## Reference structure

The I10 Golden contains one fixed `3 × 3 × 3` hollow multiblock.

Local coordinate frame:

- controller local coordinate: `(0, 1, 0)`;
- local `+Y`: world up;
- controller `FACING`: outward normal of the front face;
- local `+Z`: inward depth direction, equal to `FACING.getOpposite()`;
- local `+X`: controller-right in the horizontal plane;
- local coordinate ranges: `X=-1..1`, `Y=0..2`, `Z=0..2`.

Required layout:

- controller at `(0, 1, 0)`;
- IO port at `(0, 1, 2)` on the center of the rear face;
- casing at every other boundary coordinate;
- air at the single interior coordinate `(0, 1, 1)`.

Therefore the formed structure contains:

- `1` controller;
- `1` IO port;
- `24` casing blocks;
- `1` required interior air cell.

The fixed size keeps every validation scan bounded to at most `27` positions and creates an orientation-sensitive shape because controller and IO port occupy opposite face centers.

## Registered runtime surface

The I10 overlay registers only the surfaces necessary for the reference:

- multiblock controller block;
- multiblock casing block;
- multiblock IO port block;
- controller BlockEntity type;
- IO port BlockEntity type.

The casing is intentionally not a BlockEntity. The reference must not create 24 persistent part entities solely to remember controller ownership.

## Orientation contract

The controller supports the four horizontal directions only: north, south, east, west.

Rules:

- orientation is established from controller placement state;
- vertical facings are invalid/unrepresentable;
- the validator transforms the fixed local coordinate set into world coordinates from the controller position and facing;
- validation logic must use one canonical transform function shared by formation, invalidation targeting, tests, and visual part-map generation;
- rotation is not implemented as four duplicated hard-coded patterns.

Changing controller orientation after placement is outside the baseline. If a later implementation introduces a rotate action, it requires an explicit invalidation/reformation contract and new tests.

## Controller ownership and state model

The controller BlockEntity is the sole gameplay authority for the structure.

Authoritative persistent state:

- `lastKnownFormed: boolean`;
- `formationRevision: long`, non-negative;
- one controller-owned item slot used only to prove delegated IO capability.

Runtime-only validation state:

- `UNFORMED`;
- `PENDING_REVALIDATION`;
- `FORMED`.

Semantics:

- a fresh controller starts `UNFORMED`;
- successful validation enters `FORMED`;
- structural mismatch enters `UNFORMED`;
- load or temporary chunk unavailability enters `PENDING_REVALIDATION` without treating unavailable positions as structural corruption;
- only `FORMED` is operational and capability-active.

`lastKnownFormed` is persistence evidence, not permission to operate before runtime revalidation.

## Formation trigger

Baseline formation is explicit and server-authoritative.

A player uses the controller block. On the logical server the controller performs one bounded validation of the fixed 27-position pattern.

On a valid pattern:

1. increment `formationRevision`;
2. set runtime state to `FORMED`;
3. set `lastKnownFormed=true`;
4. bind the IO port to controller position + revision;
5. publish formed visual state;
6. mark mutated BlockEntities changed;
7. emit normal block updates needed for clients to observe formed state.

On invalid structure:

- remain or become `UNFORMED`;
- do not bind IO capability;
- do not partially mark the structure formed;
- return no successful formation outcome.

No full structure scan runs every server tick.

## Invalidation model

Invalidation is local, bounded, and fail-closed.

Controller/casing/IO-port placement or removal must schedule revalidation for any I10 controller that can geometrically own the changed position. Because the reference footprint is fixed, the candidate-controller search is bounded; it must not scan arbitrary loaded chunks or maintain a global graph.

The implementation may choose the exact target-1.21.1 block lifecycle callback/event after API verification, but the behavioral contract is fixed:

- one structural mutation schedules at most bounded candidate checks;
- affected formed controllers enter `PENDING_REVALIDATION` before they can continue exposing operational IO;
- scheduled validation returns `VALID`, `INVALID`, or `UNAVAILABLE`;
- `INVALID` dissolves the structure;
- `UNAVAILABLE` suspends operation without destructive dissolution;
- repeated adjacent updates may be coalesced into one scheduled recheck;
- no per-tick full validation loop.

Dissolution clears the runtime formed state and visual formed state. The IO port link may remain persisted as historical data, but capability delegation must fail unless the linked controller currently exists, is `FORMED`, and the formation revision matches.

## Chunk and unload/reload behavior

The validator is chunk-aware.

For every required world position it must distinguish:

- loaded and matching;
- loaded and mismatching;
- unavailable because the required chunk is not loaded.

Rules:

- I10 must not force-load chunks;
- an unavailable required position yields `UNAVAILABLE`, not `INVALID`;
- unloading a chunk containing any part does not permanently dissolve an otherwise valid persisted structure;
- controller unload does not mutate neighboring chunks merely to clear visual state;
- controller load enters `PENDING_REVALIDATION` and schedules a bounded recheck;
- when all required positions become available, revalidation restores `FORMED` only if the exact pattern and port binding are valid;
- while `PENDING_REVALIDATION`, controller IO is inactive and port capability delegation returns absent;
- if the reloaded structure is actually broken, the first complete validation dissolves it.

This prevents both false destruction at chunk boundaries and unsafe operation from stale persisted `formed=true` state.

## IO capability architecture

I10 proves capability aggregation/delegation with one item slot owned by the controller.

Controller storage:

- one stable `ItemStackHandler` instance;
- capacity: one normal item stack according to item max stack semantics;
- accepts normal insertion/extraction;
- persisted by the controller.

Capability exposure:

- controller position does **not** expose the Golden's public IO capability;
- the rear IO port exposes `Capabilities.ItemHandler.BLOCK` only while it is bound to a currently loaded `FORMED` controller with matching `formationRevision`;
- the port delegates to the controller-owned handler rather than copying storage;
- when unformed, pending, stale, controller-missing, wrong-dimension, or revision-mismatched, the port returns no item capability;
- capability queries never force-load the controller chunk.

The stable controller handler remains the data owner. The IO port is a guarded view/route, not storage authority.

## IO port binding and persistence

The IO port BlockEntity persists:

- linked controller position when a binding has been formed;
- linked `formationRevision`.

Binding rules:

- only the controller may establish/refresh a binding after successful complete validation;
- a random port cannot self-authorize by writing a nearby controller coordinate;
- capability lookup verifies both controller position and revision against the live controller;
- new formation at the same world position gets a new revision and therefore cannot accidentally reuse a stale port binding;
- a newly placed controller with revision `0` cannot authorize a stale nonzero port binding until a successful formation writes a fresh link.

## Persistence contract

Controller persistence must round-trip:

- `lastKnownFormed`;
- `formationRevision`;
- item handler contents.

Port persistence must round-trip:

- linked controller position, when present;
- linked formation revision.

Load validation:

- negative formation revisions are rejected or normalized fail-closed according to the target serialization strategy chosen during implementation;
- malformed controller links do not create capability access;
- persisted `lastKnownFormed=true` always transitions through `PENDING_REVALIDATION` before runtime returns to `FORMED`;
- item storage survives reload independently of formed state.

A real serialization/load test is required; assigning fields directly in a unit test is insufficient evidence.

## Visual formed state

Engineering publishes a minimal provider-neutral visual contract. Repo Textura remains authority for the authored visuals.

Required runtime visual inputs:

- `formed: bool` — true only in runtime `FORMED`;
- `facing: string` — one of the four horizontal facing names.

Baseline rendering may use simple generated blockstate/model resources sufficient for target-exact runtime and GameTest loading. It must not claim animated or provider-specific visual QA.

The controller and port must expose observable formed/unformed blockstate or synchronized presentation state so connected clients receive deterministic transitions after formation and dissolution. The implementation must avoid a client-only inferred scan as visual authority.

## Asset handoff manifest

I10 must consume the existing I6 schema version `2`; it must not create a parallel multiblock-only manifest schema unless implementation proves the current contract cannot represent the handoff.

The I10 Golden asset handoff manifest must:

- use `source_authority="Repo Textura"`;
- identify the Factory as source repository;
- identify the generated I10 Golden as runtime authority;
- preserve native source paths/formats for any authored visual source;
- declare provider profile(s) actually used by the baseline asset;
- bind `formed` and `facing` as explicit `visual_inputs` to concrete runtime bindings;
- declare controller/part artifacts and their delivery paths;
- record hashes/evidence through the existing I6 validator contract;
- record conversion as not performed unless a real explicit conversion occurs;
- remain `PENDING` for visual/runtime evidence that has not actually been produced.

No field may claim visual QA, Blockbench QA, or provider runtime proof merely because the structural engineering Golden passes.

## Visual part map

The spec-level part map is deterministic and derived from the same local coordinate definition as validation:

- controller anchor: local `(0,1,0)`;
- IO anchor: local `(0,1,2)`;
- casing role: every other boundary coordinate;
- required interior void: `(0,1,1)`;
- assembly bounds: local `[-1,0,0]..[1,2,2]` inclusive;
- orientation source: controller facing.

If Repo Textura later supplies a unified formed model, hidden-part behavior or expanded culling bounds must be added by an explicit handoff revision rather than inferred by Engineering.

## Multiplayer contract

Multiplayer evidence is required because formation and visual state are observable shared-world behavior.

Required semantics:

- formation authority executes on the server only;
- two connected clients observing the same controller converge on the same formed visual state;
- a client interaction cannot locally form a structure without server acceptance;
- breaking a required part on the server dissolves/suspends the structure for all tracking clients;
- port item capability state follows server formation state and cannot be enabled by client-only state;
- a later-joining/reconnecting client receives the current formed/unformed presentation from authoritative world/BlockEntity state rather than requiring the original formation interaction packet;
- no custom packet is introduced if ordinary BlockState/BlockEntity/menu synchronization is sufficient.

Implementation must choose the minimum synchronization mechanism supported by target-exact evidence. A custom payload requires a separate protocol/security justification and is not assumed by this design.

## GameTest design

Target NeoForge GameTests must cover the multiblock lifecycle with at least the following required tests:

1. **north formation** — exact north-facing layout forms successfully;
2. **rotation** — at least east and south rotated layouts form through the same canonical transform, proving no north-only hard-code;
3. **missing casing** — one required casing prevents formation;
4. **blocked interior** — non-air at the required interior cell prevents formation;
5. **wrong port position** — misplaced IO port prevents formation;
6. **invalidation** — breaking a required casing after formation transitions away from `FORMED` and disables port capability;
7. **repair + reformation** — repairing the part allows explicit formation again with a new revision;
8. **IO delegation** — item inserted/extracted through the rear port mutates the controller-owned slot, and the capability is absent while unformed;
9. **persistence** — controller state, revision, item contents, and port binding survive real serialization/load while runtime returns through `PENDING_REVALIDATION` before `FORMED`;
10. **stale binding** — a revision-mismatched port cannot expose controller storage;
11. **unavailable-chunk validator unit/fixture test** — chunk-unavailable input yields `UNAVAILABLE`, not `INVALID`, without requiring a fragile GameTest to unload the GameTest structure chunk;
12. **visual state** — successful formation and invalidation update the authoritative formed presentation state.

The exact split between GameTest and pure/unit tests may change where NeoForge's GameTest harness cannot safely unload its own structure chunk. The unload/reload acceptance gate still requires a target-exact runtime test or controlled server integration proving the lifecycle; a pure mock alone cannot close that gate.

## Unload/reload runtime acceptance

Because chunk unload/reload is a core I10 gate, implementation must add a controlled target-exact runtime test beyond ordinary static GameTests if the GameTest API cannot safely exercise chunk availability.

Acceptable evidence must prove:

1. form a valid structure;
2. persist controller and port state;
3. unload/reload the relevant world/chunk through a real server lifecycle or controlled test harness;
4. observe `PENDING_REVALIDATION` before operational recovery;
5. reload all required positions;
6. revalidate to `FORMED` without duplicating items or changing revision solely because of reload;
7. break a required part while persisted state says previously formed;
8. reload again and prove the first complete validation dissolves rather than trusting stale persistence.

If the existing I5 harness cannot express this, I10 may extend the Golden-specific test harness narrowly. It must not weaken the gate or mark unload/reload `PASS` from serialization-only evidence.

## Multiplayer acceptance test

I10 requires one controlled target-exact multiplayer integration test or equivalent server + two-client automation if the existing harness supports it.

Minimum proof:

1. server hosts one valid I10 structure;
2. client A and client B both observe initial unformed state;
3. client A requests formation through normal interaction;
4. server forms the structure;
5. both clients observe formed state;
6. a required part is removed server-authoritatively;
7. both clients observe loss of formed state;
8. reconnecting one client receives current unformed state without replaying the historical interaction.

If automated two-client execution is unavailable in the current Factory, the implementation plan must establish a reproducible manual/runtime acceptance gate and keep `I10_STATE` non-PASS until that evidence exists. Dedicated-server startup alone is not multiplayer proof.

## Golden materialization

The I10 Golden remains independent and reproducible:

1. generate a fresh I3 project;
2. apply the I10 overlay deterministically;
3. validate I10-owned paths and exact bootstrap wiring mutation;
4. validate the I6 asset handoff manifest with the canonical schema/validator;
5. run structural/unit contracts;
6. run target-exact `test build`;
7. run `runGameTestServer` with all required I10 GameTests;
8. run the unload/reload acceptance path;
9. run I5 dedicated-server smoke;
10. run multiplayer acceptance evidence;
11. collect artifacts/evidence without mutating canonical source outputs.

The materializer must not materialize I9 first and then patch it into I10.

## Determinism and overwrite policy

- Unrelated scaffold files are never overwritten silently.
- Shared I3 files change only through their owning contract if target-exact evidence proves a defect.
- I10-owned files are deterministic.
- Main-class/bootstrap wiring uses bounded exact-anchor mutation and fails on zero/multiple matches.
- Duplicate overlay paths fail closed.
- Path traversal and symlink escape fail closed.
- Asset handoff paths must satisfy existing I6 containment rules.
- Re-running the materializer against the same fresh scaffold yields byte-identical I10-owned output.

## Error handling

Fail closed on:

- unsupported Minecraft/NeoForge/Java target;
- invalid controller facing;
- wrong structure dimensions or part role;
- multiple/incorrect ports;
- interior obstruction;
- unavailable required chunk during operational capability query;
- stale/malformed port link;
- revision mismatch;
- malformed persisted state;
- missing capability registration;
- asset manifest schema/validator failure;
- unauthorized source conversion;
- test template mismatch;
- build/run drift;
- unintended overwrite or unsafe path.

Temporary chunk unavailability is a suspended state, not a structural error.

## Test strategy and quality gates

Implementation follows RED → GREEN with objective evidence.

Minimum pre-merge gates:

- I10 structural/unit contracts pass;
- relevant I3/I4/I5/I6/I8/I9 regressions pass;
- fresh I10 materialization is deterministic;
- canonical asset handoff validator passes for the I10 manifest;
- target-exact `gradlew test build` passes;
- target-exact `gradlew runGameTestServer` exits `0` with all required I10 GameTests passing;
- unload/reload acceptance evidence passes;
- I5 dedicated-server smoke passes;
- multiplayer acceptance evidence passes;
- whitespace passes;
- Sonar Quality Gate passes;
- review findings are either fixed with regression evidence or proven non-applicable;
- no pending/failing required checks immediately before merge.

Post-merge gates before root `STATUS.md` records `I10_STATE=PASS`:

- current `main` contains the merge;
- all required post-merge workflows complete with no failures/cancellations/pending jobs counted as success;
- main Sonar Quality Gate passes;
- fresh target-exact I10 materialization remains green from `main`;
- unload/reload and multiplayer evidence remain linked and reproducible.

No skipped runtime job counts as PASS.

## First RED sequence after spec + implementation-plan approval

1. **I10 composition RED** — require I10 fixture manifest/materializer/owned-path contract before implementation exists.
2. **Structure surface RED** — require controller, casing, port, BlockEntities, orientation transform, and bootstrap registrations.
3. **Formation lifecycle RED** — add formation, invalidation, rotation, and stale-binding tests before runtime completion.
4. **Capability + persistence RED** — add IO delegation and serialization/reload contracts before production behavior.
5. **Asset handoff RED** — require schema-valid manifest with explicit `formed`/`facing` bindings before completing asset packaging.
6. **Chunk lifecycle RED** — require tri-state validation and real unload/reload acceptance path.
7. **Multiplayer RED** — require the chosen reproducible multiplayer acceptance harness/evidence before I10 can pass.
8. **Workflow RED** — require permanent I10 CI orchestration and evidence collection.

## Security and quality constraints

- No arbitrary filesystem write surface.
- No arbitrary remote code or asset execution.
- No user-controlled path becomes write authority without containment validation.
- No capability lookup force-loads chunks.
- No client state becomes formation authority.
- No client-only render result becomes gameplay state.
- No provider conversion is implicit.
- No asset finality is claimed from structural export alone.
- New production Python/JavaScript tooling participates in Sonar coverage according to existing repository policy.
- Runtime correctness is proven by target-exact execution; static analysis is complementary evidence.

## Twelve-item acceptance matrix

| Gate | Required evidence |
|---|---|
| Controller | real registered controller BlockEntity owns structure state |
| Parts | casing + IO port layout validated from canonical local part map |
| Orientation | one transform supports four horizontal facings; rotated runtime tests pass |
| Formation | explicit server-side bounded validation forms exact structure atomically |
| Invalidation | part mutation suspends/revalidates/dissolves without per-tick full scan |
| Unload/reload | real server lifecycle proves pending revalidation and safe recovery/dissolution |
| IO capability | port delegates NeoForge item capability only to live matching formed controller |
| Visual formed state | authoritative server state reaches connected/reconnecting clients |
| Asset manifest | canonical I6 schema v2 + validator passes with `formed`/`facing` bindings |
| GameTest | required structure/capability/lifecycle GameTests pass target-exact |
| Persistence | real serialization round-trip covers controller, revision, storage, and port link |
| Multiplayer | server + two-client evidence proves shared formed/unformed convergence and reconnect |

## Acceptance boundary

I10 is complete only when a fresh canonical I3 scaffold can independently materialize the I10 Golden and the resulting Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21 project proves all twelve multiblock gate items with target-exact evidence.

The I10 Golden remains a reference capability. It does not become a generic runtime library, does not make the Factory a mega-mod, does not make I8 multiblock-aware, does not depend on I9 runtime identity, and does not transfer visual-authoring authority away from Repo Textura.
