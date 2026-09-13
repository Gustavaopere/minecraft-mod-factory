# I9 Machine Foundation Reference Implementation Plan

> **Execution method:** TDD with target-exact verification. No production surface is accepted before its failing contract is observed, and no task is marked complete without the corresponding build/runtime/CI evidence. Physical target: Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21 / NeoGradle userdev 7.1.26.

**Goal:** materialize a reproducible dedicated Machine Foundation Golden proving inventory, energy, vanilla-smelting recipe lookup, progress, persistence, menu synchronization/backend, seven required GameTests, and dedicated-server compatibility without making I8 machine-aware.

**Architecture:** fresh canonical I3 scaffold + deterministic I9-owned overlay for synthetic mod `i9_machine`, package `dev.example.i9machine`. Shared scaffold remains I3 authority. I9 owns only composition metadata, overlay runtime/resources, I9 contracts, and I9 CI.

**Spec:** `docs/superpowers/specs/2026-09-12-i9-machine-foundation-reference-design.md`

## Fixed contract

- Machine slots: input `0`, output `1`.
- Energy capacity: `10_000`.
- Maximum external receive per call: `1_000`.
- External extraction: `0`.
- Processing cost: `20` energy/server tick.
- Processing duration: `100` server ticks.
- Recipe domain: vanilla `minecraft:smelting`.
- Canonical transform: `minecraft:raw_iron` -> `minecraft:iron_ingot`.
- Menu sync: exactly three integers — progress, max progress, energy.
- No custom recipe type, fluids, visual screen, multiblock, logistics, provider adapter, release tooling, or I14 end-to-end scope.
- I8 remains generic.
- `STATUS.md` changes only in a dedicated post-merge closeout.

## Execution reconciliation

This plan was written before target-exact implementation and is now reconciled against the real repository tree and recorded CI evidence. The following execution facts override stale assumptions from the original draft:

- NeoGradle userdev `7.1.26` does **not** expose `setForceExit false`; the experimental probe was reverted and the authoritative runtime gate is `./gradlew runGameTestServer --no-daemon`.
- The canonical I3 constructor is `public I9MachineMod(IEventBus modBus, ModContainer container)`, not the earlier one-argument draft assumption.
- The actual I9 main-class patch intentionally uses fully-qualified machine wiring so the overlay does not add imports to the I3-owned main class.
- The I9 workflow was expanded incrementally when objective compile/runtime evidence became necessary during Tasks 3 and 7. Task 9 finalized the permanent regression + I5 gate after its own workflow-contract RED; it did not retroactively own the earlier proof steps.
- `engineering/tests/test_i9_machine_foundation_composition.py` is a permanent I9 contract and is part of the final regression set.
- The checked-in GameTest structure is native `.nbt` source authority. Its SHA-256 is pinned in the I9 manifest and revalidated by the materializer/contracts.
- Task 8 used a temporary proof workflow only to exercise the unchanged canonical I5 harness. That workflow was deleted after evidence capture; comparison proved no net temporary-workflow diff remained.

## Target-exact prerequisite audit — COMPLETE

- [x] Experimental RED requiring `setForceExit false`: run `34733484481`, `19 PASS / 1 FAIL`, expected missing directive.
- [x] Experimental I3 directive applied only for the probe.
- [x] Target-exact rejection captured in run `34733610517`: Python I3/security tests passed, generated Gradle evaluation failed because `RunImpl` has no `setForceExit` method.
- [x] I8 inherited the same experimental scaffold failure, proving shared-owner blast radius.
- [x] NeoGradle `NG_7.1` run DSL audit found no physical force-exit API to substitute.
- [x] Design reconciled: do not retain unsupported `setForceExit`; real GameTest server execution is authority.
- [x] `engineering/tests/test_i3_mod_scaffolder.py`, `engineering/templates/neoforge-mod/build.gradle.tmpl`, and `engineering/tests/golden/i3-golden-mod/build.gradle` restored byte-for-byte to canonical `main` blobs.
- [x] Final compare proved no net I3 prerequisite diff against `main`; record `TARGET_EXACT_NO_I3_CHANGE_REQUIRED`.
- [x] Final I9 permanent regression job re-runs I3 contracts and final global I1/Governance/Full Skill/Sonar gates are green.

## Materialized files

I9 creates/owns:

- `engineering/tests/fixtures/i9-machine-mod-spec.json`
- `engineering/tests/fixtures/i9-machine-scaffold-config.json`
- `engineering/tests/test_i9_machine_foundation.py`
- `engineering/tests/test_i9_machine_foundation_composition.py`
- `engineering/tooling/machine-foundation/materialize_i9.py`
- `engineering/tests/golden/i9-machine-foundation/manifest.json`
- `engineering/tests/golden/i9-machine-foundation/overlay/README.md`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/I9MachineContent.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlock.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineEnergyStorage.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineMenu.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/gametest/I9MachineGameTests.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/resources/data/i9_machine/structure/machine_test.nbt`
- `.github/workflows/factory-engineering-i9-machine-foundation.yml`

Shared `.github/workflows/factory-sonar-ci.yml` was changed only after real Sonar evidence proved imported I9 Python coverage was required.

---

## Task 1 — Restore and verify canonical I3 prerequisite — COMPLETE

- [x] Restore I3 test/template/Golden to canonical `main` bytes.
- [x] Prove the restored files are byte-identical to `main` and absent from the net PR diff.
- [x] Preserve target-exact evidence that the experimental directive is incompatible with NeoGradle `7.1.26`.
- [x] Record `TARGET_EXACT_NO_I3_CHANGE_REQUIRED` rather than claiming the experimental change as retained work.

No artificial commit was created merely to force a redundant I3 workflow after the final restoration produced no net I3 diff. Relevant I3 contracts are included again in the final permanent I9 regression job.

---

## Task 2 — I9 composition authority — COMPLETE

### RED

- [x] RED fixtures/test/minimal workflow created before materializer/manifest/overlay.
- [x] Run `34734426490`: expected failure caused by missing I9 composition authority.

### GREEN

`materialize_i9(output_dir)` now:

1. requires output inside the current workspace and not equal to workspace root;
2. rejects an existing output;
3. generates a fresh canonical I3 project from fixed I9 fixtures;
4. validates closed manifest keys and canonical fixed mapping authority;
5. rejects unsafe relative paths, duplicates, traversal, absolute paths, backslashes/drive syntax, symlink components, escapes, and overwrite collisions;
6. copies overlay files byte-for-byte;
7. validates pinned SHA-256 for the native GameTest structure;
8. patches exactly one canonical I3 constructor anchor;
9. stages work in a workspace-contained temp directory and publishes only after validation;
10. cleans staging on failure and preserves deterministic output.

Canonical main-class result:

```java
public I9MachineMod(IEventBus modBus, ModContainer container) {
    dev.example.i9machine.machine.I9MachineContent.register(modBus);
    modBus.addListener(dev.example.i9machine.machine.I9MachineContent::registerCapabilities);
}
```

- [x] Composition/security suite added, including traversal, absolute path, symlink, duplicate path, closed manifest, overwrite, anchor drift, authority delegation, and determinism coverage.
- [x] Sonar security/coverage remediation completed without exclusions.
- [x] Final Task 2 I9 run `34735084187`: SUCCESS.
- [x] Final Task 2 Sonar run `34735084205`: SUCCESS / Quality Gate PASS.

---

## Task 3 — Registry and capability surfaces — COMPLETE

- [x] RED required exact registry/capability source surfaces before Java implementation.
- [x] Register one `machine` block and block item.
- [x] Register `MachineBlockEntity` and `MachineMenu` types.
- [x] Register stable `Capabilities.ItemHandler.BLOCK` and `Capabilities.EnergyStorage.BLOCK` via `RegisterCapabilitiesEvent#registerBlockEntity`.
- [x] `MachineBlock` extends `BaseEntityBlock` and creates the machine BE.
- [x] No screen class added.
- [x] Target-exact compile mismatch in `MachineMenu` was handled only after compiler evidence.
- [x] Final Task 3 run `34735815829`: contracts/materialization/NeoForge `test build`/whitespace SUCCESS.

---

## Task 4 — Inventory and energy — COMPLETE

Fixed constants:

```text
ENERGY_CAPACITY = 10_000
MAX_RECEIVE = 1_000
ENERGY_PER_TICK = 20
MAX_PROGRESS = 100
INPUT_SLOT = 0
OUTPUT_SLOT = 1
```

- [x] Stable `ItemStackHandler(2)`.
- [x] Inventory changes mark BE changed.
- [x] Output rejects insertion.
- [x] Input validates vanilla smelting against server `RecipeManager` and fails closed before server attachment.
- [x] Direct `IEnergyStorage` implementation.
- [x] Receive bounded by request, `1_000`, and remaining capacity.
- [x] External extraction always `0`; `canExtract=false`; `canReceive=true`.
- [x] Explicit internal consume and clamped-load paths.
- [x] Energy mutation marks BE changed.
- [x] RED run `34736148946`: expected inventory/energy contract failure.
- [x] GREEN run `34736188157`: contracts/materialization/target-exact build/whitespace SUCCESS.

---

## Task 5 — Smelting, progress, persistence, sync — COMPLETE

- [x] Server-only processing uses `SingleRecipeInput`, `RecipeType.SMELTING`, `getRecipeFor`, and recipe `assemble` with registry access.
- [x] Validate recipe/output/energy before consuming energy or input.
- [x] Consume `20` energy and increment progress each valid server tick.
- [x] At `100`, consume one input, insert result, reset progress.
- [x] Any failed precondition resets progress without input/output mutation.
- [x] Persist inventory, energy, progress with target-exact registry-aware item-handler serialization.
- [x] Clamp energy `0..10_000` and progress `0..99` on load.
- [x] `ContainerData` exposes exactly progress/max progress/energy and cannot mutate server-owned energy from menu data.
- [x] RED run `34736388850`: expected processing/persistence/sync contract failure.
- [x] GREEN run `34736531827`: `15/15` I9 contracts, materialization, target-exact build, whitespace SUCCESS.

---

## Task 6 — Menu and block interaction — COMPLETE

Menu index contract:

```text
0 input
1 output
2..28 player inventory
29..37 hotbar
```

- [x] `SlotItemHandler`, `SimpleContainerData(3)`, `checkContainerDataCount(data, 3)`, `ContainerLevelAccess`.
- [x] Client constructor uses dummy handler/data and `ContainerLevelAccess.NULL`.
- [x] Server constructor receives real handler/data/access.
- [x] Machine-to-player shift-click targets `[2, 38)`.
- [x] Player-to-machine shift-click targets input `[0, 1)` only.
- [x] Output never accepts player shift-click.
- [x] Real `stillValid` against registered machine block.
- [x] Block opens menu only on logical server.
- [x] Server ticker delegates to `MachineBlockEntity::serverTick` for the correct BE type.
- [x] RED run `34736715057`: expected menu/block contract failure.
- [x] Final Task 6 run `34737111300`: `16/16` contracts, materialization, target-exact build, whitespace SUCCESS.

---

## Task 7 — Seven required GameTests — COMPLETE

Checked-in source authorities:

- `I9MachineGameTests.java`
- native `machine_test.nbt`

Required methods implemented:

- `inventoryCapability`
- `energyCapability`
- `successfulProcessing`
- `insufficientEnergy`
- `blockedOutput`
- `persistence`
- `progressReset`

The holder uses `@GameTestHolder(I9MachineMod.MOD_ID)` and `@PrefixGameTestTemplate(false)`; each test uses literal `template = "machine_test"`.

The native NBT SHA-256 is:

```text
75b23fb80317d88bbde1a2aff7121cfd903b8a1010878e0327ce26fd4d3f1c99
```

- [x] RED run `34738355723`: `16 PASS / 1 FAIL`, expected missing GameTest Java/NBT authorities.
- [x] Structural/build GREEN reached before runtime gate.
- [x] Permanent runtime-gate RED required `./gradlew runGameTestServer --no-daemon`.
- [x] First runtime execution discovered exactly seven tests; five passed and two failed because the test fixture incorrectly treated cobblestone as non-smeltable.
- [x] Test data corrected to `minecraft:diamond`; machine runtime was not altered for that fixture error.
- [x] Final Task 7 run `34739324935`: SUCCESS; log records `7 GAME TESTS COMPLETE` and `All 7 required tests passed :)`.

---

## Task 8 — I5 dedicated-server proof — COMPLETE

The canonical I5 harness remained unchanged.

For the generated fixture only:

```bash
mkdir -p run/server
printf 'eula=true\n' > run/server/eula.txt
python3 engineering/tooling/test-harness/run_test_harness.py --project .factory-ci/i9/generated
```

- [x] Temporary branch-local proof workflow used only to execute the unchanged I5 harness.
- [x] Task 8 proof run `34739552054`: SUCCESS.
- [x] Manifest target exact: Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`.
- [x] Manifest suites: `unit=PASS`, `gametest=PASS`, `dedicated_server=PASS`, `overall_state=PASS`.
- [x] Harness printed `I5 test harness: PASS`.
- [x] Temporary proof workflow deleted after evidence capture; compare showed no net temporary-workflow file diff.

---

## Task 9 — Permanent I9 CI and Sonar gates — COMPLETE

The permanent workflow evolved incrementally to provide objective target-exact evidence as earlier tasks required it. Task 9 then finalized the complete regression/I5 contract after a dedicated workflow-contract RED.

Final workflow requirements:

- [x] repository-pinned actions;
- [x] Java 21;
- [x] relevant I3/I4/I5/I8/I9 regressions;
- [x] both permanent I9 Python suites;
- [x] fresh I9 materialization;
- [x] `test build`;
- [x] `runGameTestServer`;
- [x] fixture-only EULA;
- [x] canonical I5 harness;
- [x] strict I5 manifest verification;
- [x] `git diff --check`.

Final Python set:

```bash
python3 -m unittest \
  engineering/tests/test_i3_mod_scaffolder.py \
  engineering/tests/test_i3_security_review.py \
  engineering/tests/test_i4_engineering_validators.py \
  engineering/tests/test_i5_test_harness.py \
  engineering/tests/test_i8_feature_generator.py \
  engineering/tests/test_i8_feature_generator_neoforge.py \
  engineering/tests/test_i9_machine_foundation.py \
  engineering/tests/test_i9_machine_foundation_composition.py
```

- [x] Workflow-contract RED run `34739858451`: `18 PASS / 1 FAIL`, failure only because final regressions/I5 proof were not yet permanent.
- [x] Final workflow run `34739906134`: SUCCESS; `87` regression tests PASS, target-exact build PASS, `7/7` GameTests PASS, I5 `unit/gametest/dedicated_server/overall=PASS`, whitespace PASS.
- [x] Final Sonar run `34739906197`: SUCCESS; log records `QUALITY GATE STATUS: PASSED`.
- [x] Final I1 run `34739906152`: SUCCESS.
- [x] Final Governance run `34739906143`: SUCCESS.
- [x] Final Full Skill Migration run `34739906183`: SUCCESS.

---

## Task 10 — PR, review, merge, post-merge, STATUS closeout — IN PROGRESS

Before making PR #99 ready for review:

- [x] Revalidate current `main`: `e768a73cfd810ee533d4d7f4c266b99bc1f9fabc`.
- [x] Confirm branch merge base is current `main`, `behind_by=0`.
- [x] Revalidate open PRs: #99 I9 and #100 C11 preflight.
- [x] Compare concurrent surfaces: only `.github/workflows/factory-sonar-ci.yml` overlaps; current hunks are semantically independent but the second PR merged will require normal reconciliation against updated `main`.
- [x] Confirm PR #99 currently has no review threads or submitted reviews.
- [x] Perform internal correctness/security review of materializer, registry/capability surfaces, machine state, menu/block interaction, GameTests, and CI; no Critical/Important finding identified before documentation reconciliation.
- [ ] Update PR #99 body with exact RED/GREEN evidence, final gates, non-goals, and #100 concurrency note.
- [ ] Re-run all applicable checks on the documentation-reconciled HEAD and require terminal success.
- [ ] Mark PR #99 ready for review only after fresh verification.
- [ ] Process any reviewer findings; Critical/Important findings require correction with regression evidence before merge.

Before merge require fresh evidence:

```text
main unchanged or branch reconciled with latest main
mergeable = true
no unresolved competing change on an I9-owned runtime surface
I9 workflow = success
relevant regressions = success
Sonar Quality Gate = PASS
review threads = resolved
```

PR #100 is not an I9 runtime competitor, but it currently shares `factory-sonar-ci.yml`; merge ordering must be rechecked immediately before merging #99.

Merge with the expected PR head SHA and regular merge unless repository policy observed at merge time requires otherwise.

Post-merge:

- [ ] Poll every workflow for the implementation merge SHA until terminal.
- [ ] Require zero required workflow failure/cancelled/pending/null conclusions.
- [ ] Inspect main Sonar log for `QUALITY GATE STATUS: PASSED`.
- [ ] Only then create a dedicated STATUS closeout branch/PR.
- [ ] Record `I9_STATE=PASS`, exact evidence, and `NEXT_ACTION=BEGIN_I10_MULTIBLOCK_FOUNDATION`.
- [ ] Merge STATUS closeout and again verify post-closeout workflows plus main Sonar before calling I9 formally closed.

## Acceptance boundary

I9 implementation is merge-ready only after Task 10 pre-merge gates are freshly satisfied. I9 is formally closed only after the implementation merge and the separate STATUS closeout have both been revalidated on `main`.
