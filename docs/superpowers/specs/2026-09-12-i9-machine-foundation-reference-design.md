# I9 — Machine Foundation Reference — Design

## Status

Design approved in chat on 2026-09-12. This document defines the architectural boundary for PR I9 before implementation.

## Canonical authorities

- Engineering plan: `plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md`
- Art/asset plan: `plans/PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md`
- Current status authority: root `STATUS.md`
- Physical target authority: project-supplied modlist snapshot with SHA-256 `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`
- Target: Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`

The engineering plan defines I9 as a reference implementation in a dedicated Golden fixture, not forced into every mod, covering inventory, energy, recipe, progress, persistence, sync, menu, and GameTest.

## Problem statement

I8 proves deterministic generation of block/item/BlockEntity/menu/network/recipe skeletons. I9 must prove that the Factory can assemble those lower-level primitives into a coherent, server-authoritative machine reference with real NeoForge behavior. The reference must be reproducible and testable without turning the Factory into a mega-mod or changing the generic I8 generator into a machine runtime generator.

## Decision

Use a **compositional dedicated Golden**.

The I9 Golden is produced from a fresh canonical I3 scaffold plus an I9-owned overlay/reference layer. The I9 layer contains only machine-specific runtime code, tests, resources, and any narrowly required build configuration delta. Common scaffold/build metadata remains owned by I3.

Rejected alternatives:

1. **Standalone duplicated Golden** — rejected because it duplicates I3 build/scaffold authority and increases drift risk.
2. **Add a `machine` feature to I8** — rejected because I9 is a reference composition, while I8 is generic feature scaffolding. Mixing them expands blast radius and makes the machine reference implicitly normative for all generated mods.

## Scope

I9 must implement and prove all of the following in one reference machine:

- inventory;
- energy;
- recipe lookup and consumption;
- progress lifecycle;
- persistence;
- synchronization needed by the menu/runtime contract;
- menu backend;
- GameTest coverage.

I9 also inherits target validation, build, GameTest-server, dedicated-server and evidence behavior from the existing I3/I5 infrastructure where applicable.

## Non-goals

I9 does not include:

- custom visual screen art, sprites, textures, animation, VFX or GUI visual design;
- multiblock behavior (I10);
- logistics graph/transfer networks (I11);
- provider adapter framework (I12);
- release tooling (I13);
- a full production mod or the I14 end-to-end Golden;
- fluid handling unless a later canonical requirement explicitly adds it;
- upgrades, tiers, sides/configuration UX, redstone modes or automation policy beyond what is necessary to prove item/energy capabilities;
- a custom recipe serializer/type unless required by target-exact evidence.

The art plan remains authoritative for the visual package. Engineering owns the Java menu/runtime logic; Repo Textura owns GUI visual assets and handoff.

## Reuse and provenance

The pre-I9 audit found no equivalent reusable Machine Foundation in the historical RPG repository. I9 is therefore new Factory engineering work built on proven Factory infrastructure, not a reimplementation of a migrated historical capability.

Reuse boundaries:

- **I3 scaffolder**: canonical project/bootstrap/build base.
- **I5 test harness**: allowlisted `test`, `runGameTestServer`, and dedicated-server smoke execution.
- **I8 feature generator**: reference for target-exact registry, BlockEntity, menu and recipe skeleton conventions only. I9 must not make I8 machine-aware in this PR.

## Reference machine model

The Golden contains one single-block processing machine with two machine item slots:

- slot `0`: input;
- slot `1`: output.

The machine consumes stored energy while processing an accepted recipe. It accumulates progress server-side, consumes the input when the recipe completes, and inserts the result into the output slot.

The machine must fail closed when:

- no matching recipe exists;
- stored energy is insufficient for the current processing step;
- the output cannot accept the recipe result;
- the input no longer matches while progress is in flight.

When processing preconditions cease to hold, progress resets deterministically to the documented baseline rather than silently completing stale work.

## Recipe integration

The first Golden should use an existing vanilla recipe type that can be resolved through `RecipeManager`, rather than introducing a custom recipe serializer/type. This keeps I9 focused on machine composition and avoids pulling I8/I13-style registry/serialization scope into the machine reference.

The exact vanilla recipe selected during implementation must satisfy all of these constraints:

- available in Minecraft 1.21.1;
- server-side lookup through the target `RecipeManager` API;
- deterministic single-input to output transformation suitable for GameTest;
- no custom serializer required;
- no ambiguity that would make the GameTest depend on unrelated modpack content.

If target-exact compilation shows that no candidate meets these constraints cleanly, implementation must stop and amend this design before adding a custom recipe type.

## Inventory architecture

Use NeoForge's `ItemStackHandler` as the backing store and expose the machine inventory via `Capabilities.ItemHandler.BLOCK` registered for the machine BlockEntity type.

The machine owns slot policy:

- input accepts only items that can participate in the selected reference recipe;
- output rejects manual insertion;
- extraction from output is allowed;
- no additional slots are added in I9.

The menu consumes an `IItemHandler` view and uses `SlotItemHandler`; the menu must not become the data holder.

Capability registration must use NeoForge's block-entity capability registration path. If a capability object can change at runtime, capability invalidation must be performed according to NeoForge rules. The baseline design should avoid swapping handler instances after construction so no unnecessary invalidation path is introduced.

## Energy architecture

Expose energy through `Capabilities.EnergyStorage.BLOCK` using an `IEnergyStorage` implementation owned by the machine.

The reference energy store has fixed constants for:

- capacity;
- maximum receive rate;
- extraction policy;
- energy cost per processing tick or per completed operation.

These constants must be explicit in code and covered by tests. The machine reference should accept external energy and should not generate energy itself.

Energy mutation that affects machine state must mark the BlockEntity changed so persistence is not dependent on unrelated inventory mutations.

## Processing state machine

Processing runs on the logical server only.

Per server tick:

1. Read the current input and output state.
2. Resolve the selected recipe against the server `RecipeManager`.
3. Verify result capacity/output compatibility.
4. Verify required energy.
5. If all preconditions hold, consume the configured energy quantum and increment progress.
6. On reaching `maxProgress`, consume the recipe input, insert the result, then reset progress.
7. If preconditions fail, reset progress to the baseline defined by the implementation contract.
8. Mark the BlockEntity changed whenever persistent state changes.

Client-side ticking must not mutate inventory, energy or progress.

## Persistence

The BlockEntity persists all state needed to resume deterministically after reload:

- item handler contents;
- stored energy;
- current progress;
- `maxProgress` only if it is not a compile-time/runtime invariant.

For an owned BlockEntity, use direct BlockEntity NBT persistence through the target 1.21.1 `loadAdditional` / `saveAdditional` lifecycle, matching NeoForge guidance.

Loading malformed/out-of-range machine-owned numeric values must fail closed to valid bounds instead of creating negative energy/progress or values above capacity.

## Synchronization

Synchronization is deliberately minimal.

The menu synchronizes integer machine state required for presentation through `ContainerData` / `DataSlot` semantics. At minimum, the menu contract exposes progress and energy values needed by a future screen without introducing screen code in I9.

Item stacks synchronize through menu slots.

BlockEntity update packets/tags are added only if GameTest or non-menu runtime behavior proves they are required. I9 must not duplicate the same state through both menu synchronization and custom networking without a demonstrated need.

## Menu backend

Implement an `AbstractContainerMenu` with:

- client constructor using dummy/safe local references;
- server constructor receiving the real machine item handler and synchronized integer data;
- machine input/output slots first;
- player inventory and hotbar afterward;
- `stillValid` based on `ContainerLevelAccess` and the machine block;
- complete `quickMoveStack` behavior for machine-to-player and player-to-machine movement;
- output slot insertion restrictions preserved during shift-click.

The block opens the menu on the logical server using the target NeoForge/Minecraft menu-opening path. No `AbstractContainerScreen` is part of I9.

## Registry and bootstrap

The I9 overlay registers only the objects required by the Golden:

- machine block;
- machine block item;
- machine BlockEntity type;
- machine menu type.

The overlay must integrate through the canonical mod event bus/bootstrap pattern already established by I3/I8. It must not replace the canonical main class with an unrelated bootstrap architecture.

## GameTest design

Use NeoForge 1.21.1 GameTest APIs with a dedicated I9 test holder and a structure template under `data/<namespace>/structure`.

Required GameTests:

1. **inventory capability** — block exposes item capability and enforces input/output rules;
2. **energy capability** — block exposes energy capability and respects capacity/receive policy;
3. **successful processing** — valid input + sufficient energy advances progress and produces the expected output;
4. **insufficient energy** — machine does not complete work and follows the documented progress reset behavior;
5. **blocked output** — machine does not consume input or produce overflow when output cannot accept the result;
6. **persistence** — machine state survives the target save/load or BlockEntity serialization path exercised by the test fixture;
7. **progress reset** — invalidated processing conditions reset progress deterministically.

GameTests are required tests, not optional informational tests.

## Build configuration requirement

The existing I3 build configuration already defines a `gameTestServer` run and the namespace property. NeoForge 1.21.1 documentation states that NeoGradle's default force-exit behavior can make `runGameTestServer` report failure and recommends `setForceExit false` on the Game Test Server run configuration.

I9 must begin with a RED contract that proves whether the current I3-generated project is missing this required target-exact setting. If RED reproduces the documented failure/contract gap, the narrowest owner-correct fix must be applied. Because the setting belongs to scaffold/run configuration rather than machine runtime, the preferred ownership is I3 scaffold output plus its Golden, with regression coverage. I9 must not carry a private divergent buildscript workaround if the shared scaffold is objectively wrong.

## Golden materialization

The Golden must remain compositional and reproducible.

Expected flow:

1. Generate a fresh mod project with the canonical I3 scaffolder.
2. Apply the I9 reference overlay deterministically.
3. Validate that only declared I9-owned paths/build deltas are introduced.
4. Run structural contract tests.
5. Run Gradle build/tests.
6. Run the Game Test Server.
7. Run the I5 dedicated-server smoke when EULA handling is satisfied by the controlled CI fixture.

The implementation plan will choose the exact checked-in fixture/overlay paths after inspecting the current tree. This design does not prescribe a historical directory merely because earlier plans used one.

## Determinism and overwrite policy

Applying or materializing the I9 reference must be deterministic.

- Existing unrelated project files are not overwritten silently.
- Shared scaffold files may be changed only through their owning I3 contract and tests.
- I9-owned files may be regenerated only when byte-equivalent to the declared reference or under an explicit update path covered by tests.
- Any file mutation that changes an existing non-I9 artifact requires explicit ownership evidence and regression coverage.

## Error handling

The reference must fail closed on:

- unsupported target identity;
- missing required registry/bootstrap state;
- malformed persistent numeric state;
- recipe lookup failure;
- output overflow/incompatibility;
- missing capability registration;
- GameTest structure/template mismatch;
- build/run configuration drift.

Tests should assert externally observable behavior and contract boundaries rather than incidental private implementation details.

## Test strategy and gates

Implementation follows RED → GREEN with objective evidence.

Minimum gates before I9 can merge:

- new I9 structural/unit contract tests pass;
- any I3 buildscript regression introduced by the GameTest-server correction passes;
- relevant I3/I4/I5/I8 regressions pass;
- target-exact `gradlew test build` passes;
- target-exact `gradlew runGameTestServer` passes with all required I9 GameTests;
- I5 dedicated-server smoke passes in the controlled fixture;
- whitespace gate passes;
- Sonar Quality Gate passes;
- PR review findings are either fixed with regression evidence or explicitly shown non-applicable;
- no pending/failing required checks remain immediately before merge;
- post-merge workflows and main-branch Sonar pass before `STATUS.md` records `I9_STATE=PASS`.

## First RED sequence

The implementation plan should begin with the smallest evidence-producing failures, in this order:

1. **GameTest run-config RED** — assert the canonical I3 scaffold contains the target-required `gameTestServer { setForceExit false }` behavior; this is expected to fail on the current scaffold and establishes ownership before machine code exists.
2. **I9 Golden contract RED** — assert the dedicated I9 fixture/overlay and required machine surfaces do not yet exist.
3. **Machine behavior RED** — after the project compiles, add required GameTests for capabilities and processing behavior before completing runtime logic.

Do not skip the first RED by editing `build.gradle` preemptively.

## Security and quality constraints

- No arbitrary filesystem write surface is introduced.
- No user-provided path becomes a write authority without existing Factory containment rules.
- No secrets or remote credentials are required by the Golden runtime.
- CI actions should follow repository pinning conventions.
- New Python/JavaScript tooling, if any, must be included in Sonar coverage according to the existing fail-closed coverage workflow.
- Java runtime behavior is verified primarily by real target-exact Gradle/GameTest execution; Sonar remains a quality gate, not a substitute for runtime proof.

## Source references checked for this design

Canonical plan statements are sourced from the two repository plans listed above. Target-exact API assumptions were checked against NeoForge documentation for the 1.21–1.21.1 line:

- Capabilities: https://docs.neoforged.net/docs/1.21.1/inventories/capabilities/
- Containers / `ItemStackHandler`: https://docs.neoforged.net/docs/1.21.1/inventories/container/
- Block entities / persistence: https://docs.neoforged.net/docs/1.21.1/blockentities/
- Menus: https://docs.neoforged.net/docs/1.21.1/gui/menus/
- Game Tests: https://docs.neoforged.net/docs/1.21.1/misc/gametest/

## Acceptance boundary

I9 is complete only when a fresh canonical scaffold can materialize the dedicated machine reference and the resulting NeoForge 1.21.1 project proves, with target-exact automated evidence, inventory + energy + recipe + progress + persistence + sync + menu + GameTest behavior. The reference remains a Golden/reference capability and is not automatically injected into every generated mod.
