# I9 — Machine Foundation Reference — Design

## Status

Design approved in chat on 2026-09-12 and reconciled during target-exact implementation audit on 2026-09-12/13. The reconciliation preserves the approved I9 architecture but removes one buildscript assumption that the physical NeoGradle stack disproved.

## Canonical authorities

- Engineering plan: `plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md`
- Art/asset plan: `plans/PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md`
- Current status authority: root `STATUS.md`
- Physical modlist snapshot SHA-256: `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`
- Target: Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`
- Physical build plugin: `net.neoforged.gradle.userdev` `7.1.26`

The engineering plan defines I9 as a reference implementation in a dedicated Golden fixture, not forced into every mod, covering inventory, energy, recipe, progress, persistence, sync, menu, and GameTest.

## Problem statement

I8 proves deterministic generation of block/item/BlockEntity/menu/network/recipe skeletons. I9 must prove that the Factory can assemble lower-level primitives into a coherent, server-authoritative machine reference with real NeoForge behavior. The reference must be reproducible and testable without turning the Factory into a mega-mod or changing the generic I8 generator into a machine runtime generator.

## Decision

Use a **compositional dedicated Golden**.

The I9 Golden is produced from a fresh canonical I3 scaffold plus an I9-owned overlay/reference layer. The I9 layer contains only machine-specific runtime code, tests, resources, and narrowly required composition metadata. Common scaffold/build metadata remains owned by I3.

Rejected alternatives:

1. **Standalone duplicated Golden** — duplicates I3 build/scaffold authority and increases drift risk.
2. **Add a `machine` feature to I8** — mixes a reference composition into generic feature scaffolding and expands blast radius.

## Target-exact GameTest buildscript reconciliation

NeoForge GameTest documentation recommends `setForceExit false` for a Game Test Server run. The physical I9 target, however, uses NeoGradle userdev `7.1.26`. A TDD probe was executed before machine implementation:

- RED run `34733484481`: the newly added contract failed because the canonical I3 scaffold did not contain `setForceExit false`.
- Experimental correction HEAD `7e9b2bcbc44e827df13bbc5e13b3543b9d641af3` added that directive to I3.
- Target-exact I3 run `34733610517` then passed all `20/20` Python I3/security tests but failed while evaluating the generated project: `Could not find method setForceExit() ... RunImpl`.
- The same unsupported buildscript directive propagated to I8 and caused its generated-project build gate to fail.
- NeoGradle `NG_7.1` run DSL inspection does not expose a `forceExit` property/method on the physical `Run` contract.

Therefore, `setForceExit false` is **not part of the I9/I3 contract for NeoGradle 7.1.26**. The experimental I3 change must be reverted. The authoritative GameTest gate is the real target-exact command `./gradlew runGameTestServer --no-daemon`. If that command fails once actual I9 GameTests exist, the failure must be diagnosed from the physical runtime/build logs; no unsupported ForgeGradle-style directive may be invented or copied into NeoGradle.

This reconciliation is evidence-driven and does not weaken the requirement that GameTests must run successfully before I9 can pass.

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

I9 inherits target validation, build, GameTest-server, dedicated-server, and evidence behavior from I3/I5 where applicable.

## Non-goals

I9 does not include:

- custom visual screen art, sprites, textures, animation, VFX, or GUI visual design;
- multiblock behavior (I10);
- logistics graph/transfer networks (I11);
- provider adapter framework (I12);
- release tooling (I13);
- the I14 end-to-end Golden;
- fluid handling;
- upgrades, tiers, side-configuration UX, redstone modes, or automation policy beyond proving item/energy capabilities;
- a custom recipe serializer/type.

Engineering owns Java menu/runtime logic; Repo Textura owns GUI visual assets and handoff.

## Reuse and provenance

The pre-I9 audit found no equivalent reusable Machine Foundation in the historical RPG repository. I9 is new Factory engineering built on proven Factory infrastructure.

Reuse boundaries:

- **I3 scaffolder**: canonical project/bootstrap/build base.
- **I5 test harness**: allowlisted `test`, `runGameTestServer`, and dedicated-server smoke execution.
- **I8 feature generator**: reference for target-exact registry, BlockEntity, menu, and recipe skeleton conventions only. I9 must not make I8 machine-aware.

## Reference machine model

The Golden contains one single-block processing machine with two item slots:

- slot `0`: input;
- slot `1`: output.

Fixed I9 constants:

- energy capacity: `10_000`;
- maximum external receive per call: `1_000`;
- external extraction: disabled (`0`);
- processing energy cost: `20` energy units per server tick;
- processing duration: `100` server ticks.

The machine consumes stored energy while processing an accepted recipe, accumulates progress server-side, consumes input only on completion, and inserts the result into output.

The machine fails closed when no matching recipe exists, energy is insufficient, output cannot accept the result, or the input changes during processing. When preconditions cease to hold, progress resets to `0` without stale completion.

## Recipe integration

The I9 Golden uses vanilla `minecraft:smelting`.

Reference GameTest transformation:

- input: `minecraft:raw_iron`;
- expected result: `minecraft:iron_ingot`.

Lookup is server-side through `RecipeManager` with `SingleRecipeInput`; result assembly uses server registry access. I9 keeps its own fixed `100`-tick duration rather than inheriting furnace cooking time.

If target-exact compilation disproves an assumed recipe API signature, implementation must amend this design before substituting another API or adding a custom recipe type.

## Inventory architecture

Use NeoForge `ItemStackHandler` as the backing store and expose inventory with `Capabilities.ItemHandler.BLOCK` registered for the machine BlockEntity type.

Policy:

- input accepts only items matching a vanilla smelting recipe in the current server `RecipeManager`;
- output rejects manual insertion;
- output extraction is allowed;
- no additional machine slots.

The menu consumes an `IItemHandler` view and uses `SlotItemHandler`; the menu is never the data holder. The handler instance remains stable for the lifetime of the BlockEntity.

## Energy architecture

Expose energy through `Capabilities.EnergyStorage.BLOCK` using an `IEnergyStorage` implementation owned by the machine.

The store accepts external energy up to fixed receive/capacity bounds, rejects external extraction, and exposes current/max energy. Internal processing has an explicit machine-owned consumption path. Real energy mutations call `setChanged()` through the owning BlockEntity so persistence cannot depend on inventory mutation.

## Processing state machine

Processing mutates state on the logical server only.

Per server tick:

1. Read input/output.
2. Resolve the vanilla smelting recipe using `SingleRecipeInput`.
3. Assemble the result using server registry access.
4. Verify output capacity/compatibility.
5. Verify at least `20` stored energy.
6. Consume `20` energy and increment progress by `1` when all preconditions hold.
7. At progress `100`, consume one input, insert the result, and reset progress to `0`.
8. On any failed precondition, reset progress to `0` without consuming input or creating output.
9. Mark persistent state changed whenever it mutates.

Client-side ticking must not mutate inventory, energy, or progress.

## Persistence

Persist:

- item handler contents;
- stored energy;
- current progress.

Fixed constants are not persisted. Use target 1.21.1 BlockEntity `loadAdditional` / `saveAdditional` lifecycle with registry-aware serialization where required.

Load bounds:

- energy: `0..10_000`;
- progress: `0..99`.

A loaded value must never trigger an unearned completion tick.

## Synchronization

Synchronization is deliberately minimal.

The menu exposes exactly three integer values through `ContainerData`:

1. current progress;
2. maximum progress (`100`);
3. current energy.

Items synchronize through menu slots. BlockEntity update packets/tags are excluded from the baseline unless runtime evidence demonstrates a non-menu need. I9 must not duplicate the same state through menu sync plus custom networking without evidence.

## Menu backend

Implement an `AbstractContainerMenu` with:

- safe client constructor;
- server constructor receiving real machine `IItemHandler`, synchronized integer data, and `ContainerLevelAccess`;
- machine input/output slots first;
- player inventory and hotbar afterward;
- `stillValid` based on the machine block and access position;
- complete `quickMoveStack` behavior;
- no shift-click path that inserts into output.

The block opens the menu only on the logical server. No `AbstractContainerScreen` is part of I9.

## Registry and bootstrap

The I9 overlay registers only:

- machine block;
- machine block item;
- machine BlockEntity type;
- machine menu type.

Registration integrates through the canonical mod event bus/bootstrap pattern established by I3/I8. It must not replace the canonical main class with unrelated bootstrap architecture.

## GameTest design

Use target NeoForge GameTest APIs with an I9 test holder and structure template under `data/<namespace>/structure`.

Required GameTests:

1. **inventory capability** — capability exists and input/output rules hold;
2. **energy capability** — capacity `10_000`, max receive `1_000`, external extraction `0`;
3. **successful processing** — raw iron + at least `2_000` energy produces one iron ingot after `100` processing ticks and consumes one raw iron;
4. **insufficient energy** — work cannot complete and progress returns to `0`;
5. **blocked output** — no input consumption or overflow when output rejects result;
6. **persistence** — inventory, energy, and in-flight progress survive real serialization/load;
7. **progress reset** — invalidating input after progress starts resets to `0` without output.

All seven are required tests.

## Golden materialization

The Golden remains compositional and reproducible:

1. Generate a fresh I3 project.
2. Apply the I9 overlay deterministically.
3. Validate declared I9-owned paths and the exact main-class wiring mutation.
4. Run structural/unit contracts.
5. Run `test build`.
6. Run `runGameTestServer` on the physical target.
7. Prepare `run/server/eula.txt` with `eula=true` only inside the controlled generated CI fixture, then run I5 dedicated-server smoke.

No historical directory is prescribed when the current tree supports a better location.

## Determinism and overwrite policy

- Unrelated existing project files are never overwritten silently.
- Shared scaffold files can change only under their owning I3 contract with a proven target-exact defect.
- I9-owned files are copied/generated deterministically.
- Main-class wiring uses one exact anchor and fails on zero/multiple matches.
- Any mutation to a non-I9 artifact requires ownership evidence and regression coverage.

## Error handling

Fail closed on:

- unsupported target identity;
- missing registry/bootstrap state;
- malformed/out-of-range persisted state;
- recipe lookup failure;
- output overflow/incompatibility;
- missing capability registration;
- GameTest template mismatch;
- build/run configuration drift;
- path traversal, symlink escape, unknown manifest fields, duplicate overlay paths, or unintended overwrite.

## Test strategy and gates

Implementation follows RED → GREEN with objective evidence.

Minimum gates before merge:

- I9 structural/unit contracts pass;
- relevant I3/I4/I5/I8 regressions pass;
- target-exact `gradlew test build` passes;
- target-exact `gradlew runGameTestServer` exits `0` with all seven required I9 GameTests passing;
- I5 dedicated-server smoke passes;
- whitespace passes;
- Sonar Quality Gate passes;
- review findings are fixed through regression evidence or proven non-applicable;
- no pending/failing required checks immediately before merge;
- post-merge workflows and main Sonar pass before `STATUS.md` records `I9_STATE=PASS`.

## First RED sequence

The corrected implementation sequence is:

1. **I9 Golden composition RED** — assert fixtures exist but materializer/manifest/overlay surfaces do not yet exist.
2. **Machine surface RED** — require registry, block, BlockEntity, menu, inventory, and energy surfaces before adding them.
3. **Machine behavior RED** — add required GameTests before completing runtime behavior.
4. **Workflow RED** — require the permanent I9 workflow contract before expanding it to full gates.

The prior `setForceExit` probe remains recorded as target-exact audit evidence but is not retained as an I3 contract.

## Security and quality constraints

- No arbitrary filesystem write surface.
- No user-provided path becomes write authority without containment validation.
- No secrets or remote credentials required by Golden runtime.
- CI actions follow repository pinning conventions.
- New production Python/JavaScript tooling must participate in Sonar coverage.
- Runtime correctness is proven by real target-exact Gradle/GameTest execution; Sonar is a quality gate, not a runtime substitute.

## Acceptance boundary

I9 is complete only when a fresh canonical scaffold can materialize the dedicated machine reference and the resulting NeoForge 1.21.1 / NeoForge 21.1.248 / Java 21 project proves inventory + energy + recipe + progress + persistence + sync + menu + GameTest behavior with target-exact automated evidence. The machine remains a Golden/reference capability and is not automatically injected into every generated mod.
