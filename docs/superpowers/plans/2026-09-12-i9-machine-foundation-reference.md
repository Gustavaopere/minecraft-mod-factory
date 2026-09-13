# I9 Machine Foundation Reference Implementation Plan

> **Execution method:** use TDD. No production surface is added before the corresponding failing contract is observed. The current physical target is Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21 / NeoGradle userdev 7.1.26.

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
- Canonical test transform: `minecraft:raw_iron` -> `minecraft:iron_ingot`.
- Menu sync: exactly three integers — progress, max progress, energy.
- No custom recipe type, fluids, visual screen, multiblock, logistics, provider adapter, release tooling, or I14 end-to-end scope.
- I8 remains generic.
- `STATUS.md` changes only in a dedicated post-merge closeout.

## Completed target-exact prerequisite audit

- [x] Add an experimental RED requiring `setForceExit false` in the I3 Game Test Server run.
- [x] Capture RED run `34733484481`: `19 PASS / 1 FAIL`, failure exactly `'setForceExit false' not found`.
- [x] Apply the experimental I3 directive on HEAD `7e9b2bcbc44e827df13bbc5e13b3543b9d641af3`.
- [x] Capture target-exact run `34733610517`: I3/security tests `20/20 PASS`, generated project fails at Gradle evaluation because NeoGradle `7.1.26` `RunImpl` has no `setForceExit` method.
- [x] Confirm I8 generated-project build also fails from the same unsupported scaffold directive.
- [x] Inspect NeoGradle `NG_7.1` run DSL: no force-exit property/method is exposed by the physical run contract.
- [x] Reconcile the I9 design: do not retain the unsupported directive; real `runGameTestServer` execution is the authoritative gate.
- [ ] Restore I3 test/template/Golden to canonical pre-probe bytes and reverify I3/I8/Sonar before I9 composition work.

## Planned files

Create:

- `engineering/tests/fixtures/i9-machine-mod-spec.json`
- `engineering/tests/fixtures/i9-machine-scaffold-config.json`
- `engineering/tests/test_i9_machine_foundation.py`
- `engineering/tooling/machine-foundation/materialize_i9.py`
- `engineering/tests/golden/i9-machine-foundation/manifest.json`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/I9MachineContent.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlock.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineEnergyStorage.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineMenu.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/gametest/I9MachineGameTests.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/resources/data/i9_machine/structure/machine_test.nbt`
- `.github/workflows/factory-engineering-i9-machine-foundation.yml`

Modify existing shared files only when a new failing regression proves ownership. `.github/workflows/factory-sonar-ci.yml` may change only if a real Sonar run proves that `materialize_i9.py` lacks imported coverage.

---

## Task 1 — Restore and verify the canonical I3 prerequisite

- [ ] Restore `engineering/tests/test_i3_mod_scaffolder.py` to the canonical main blob, removing the experimental `setForceExit` assertion.
- [ ] Restore `engineering/templates/neoforge-mod/build.gradle.tmpl` to the canonical main blob.
- [ ] Restore `engineering/tests/golden/i3-golden-mod/build.gradle` to the same canonical buildscript bytes.
- [ ] Run the I3 workflow and require Python contract/security PASS, generated `test build` PASS, and whitespace PASS.
- [ ] Run/review I8 on the same HEAD and require generated project build + datagen PASS.
- [ ] Require Sonar workflow success and `QUALITY GATE STATUS: PASSED`.
- [ ] Record the prerequisite as `TARGET_EXACT_NO_I3_CHANGE_REQUIRED`; do not claim the experimental fix as retained work.

---

## Task 2 — RED/GREEN: I9 composition authority

**RED files only:**

- `engineering/tests/fixtures/i9-machine-mod-spec.json`
- `engineering/tests/fixtures/i9-machine-scaffold-config.json`
- `engineering/tests/test_i9_machine_foundation.py`
- initial permanent `.github/workflows/factory-engineering-i9-machine-foundation.yml` that only runs the I9 contract plus required setup.

The RED commit must not create the materializer, manifest, or overlay.

### RED fixture identity

Scaffold config:

```json
{
  "schema_version": 1,
  "project_name": "i9-machine-foundation",
  "java_package": "dev.example.i9machine",
  "mod_group_id": "dev.example",
  "mod_version": "0.1.0",
  "main_class": "I9MachineMod",
  "client_class": "I9MachineModClient",
  "license": "MIT",
  "authors": "Engineering Golden Fixture",
  "description": "Synthetic project proving the canonical I9 Machine Foundation reference."
}
```

The mod spec must preserve the current I3 schema exactly while declaring target `1.21.1 / neoforge / 21.1.248 / Java 21`, one machine block/menu backend, persistence for inventory/energy/progress, and vanilla smelting. No real distribution or provider claim is invented.

### RED contract

`engineering/tests/test_i9_machine_foundation.py` begins with:

```python
ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = ROOT / "engineering/tooling/machine-foundation/materialize_i9.py"
OVERLAY = ROOT / "engineering/tests/golden/i9-machine-foundation/overlay"
MANIFEST = ROOT / "engineering/tests/golden/i9-machine-foundation/manifest.json"

class I9MachineFoundationContractTest(unittest.TestCase):
    def test_i9_materializer_and_overlay_exist(self):
        self.assertTrue(MATERIALIZER.is_file(), "I9 RED: materializer is missing")
        self.assertTrue(OVERLAY.is_dir(), "I9 RED: overlay is missing")
        self.assertTrue(MANIFEST.is_file(), "I9 RED: manifest is missing")
```

- [ ] Commit RED fixtures/test/permanent minimal workflow.
- [ ] Capture Actions failure caused only by missing I9 materializer/overlay/manifest.

### GREEN composition

Create `engineering/tooling/machine-foundation/materialize_i9.py` with public interface:

```python
class MaterializationError(RuntimeError):
    pass

def materialize_i9(output_dir: Path | str) -> Path:
    ...
```

Required behavior:

1. output must resolve inside current workspace and must not equal workspace root;
2. generate a fresh project from the fixed I9 fixtures through canonical I3 `generate_project`;
3. manifest root keys are closed and validated;
4. overlay paths reject absolute paths, `..`, duplicates, symlinks, escapes, and existing destinations;
5. copy overlay files byte-for-byte;
6. patch only `src/main/java/dev/example/i9machine/I9MachineMod.java` through one exact constructor anchor;
7. zero/multiple anchor matches fail before writing;
8. repeat materialization in two fresh outputs is byte-identical.

Main-class result:

```java
public I9MachineMod(IEventBus modBus) {
    I9MachineContent.register(modBus);
    modBus.addListener(I9MachineContent::registerCapabilities);
}
```

- [ ] Add traversal, absolute-path, symlink, duplicate, unknown-manifest-key, overwrite, anchor-drift, and determinism tests before declaring GREEN.
- [ ] Require I3/security/I9 Python tests PASS.
- [ ] Commit composition GREEN.

---

## Task 3 — RED/GREEN: registry and capability surfaces

Before adding Java, extend I9 contract tests to require exact overlay paths and source tokens for:

- `I9MachineContent.java`
- `MachineBlock.java`
- `MachineEnergyStorage.java`
- `MachineBlockEntity.java`
- `MachineMenu.java`

Require `DeferredRegister`, `Capabilities.ItemHandler.BLOCK`, `Capabilities.EnergyStorage.BLOCK`, and block-entity capability registration. Capture RED.

GREEN requirements:

- register one `machine` block;
- register its block item;
- register one `MachineBlockEntity` type;
- register one `MachineMenu` type;
- register stable item and energy block capabilities;
- `MachineBlock` extends `BaseEntityBlock` and creates the machine BE;
- no screen class.

Materialize a fresh I9 project and run:

```bash
./gradlew test build --no-daemon
```

Any API mismatch is fixed against NeoForge `21.1.248`; compilation is authority.

---

## Task 4 — RED/GREEN: inventory and energy

Add source/runtime contracts before implementation for constants:

```java
ENERGY_CAPACITY = 10_000
MAX_RECEIVE = 1_000
ENERGY_PER_TICK = 20
MAX_PROGRESS = 100
INPUT_SLOT = 0
OUTPUT_SLOT = 1
```

GREEN:

- one stable `ItemStackHandler(2)`;
- `onContentsChanged` marks BE changed;
- output rejects insertion;
- input validates against smelting recipe when server level exists and fails closed before server attachment;
- direct `IEnergyStorage` implementation;
- receive is bounded by request, `1_000`, and remaining capacity;
- external extraction always `0`;
- `canExtract=false`, `canReceive=true`;
- explicit internal consume method;
- explicit clamped load method;
- energy mutation marks BE changed.

Rematerialize and require `test build` PASS.

---

## Task 5 — RED/GREEN: smelting, progress, persistence, sync

RED must require `SingleRecipeInput`, `RecipeType.SMELTING`, `getRecipeFor`, `assemble`, `loadAdditional`, `saveAdditional`, and `ContainerData` count `3`.

GREEN server tick:

1. return immediately when not on `ServerLevel`;
2. resolve smelting recipe for input;
3. assemble result with server registry access;
4. verify output compatibility/capacity;
5. verify `20` energy;
6. consume `20`, increment progress;
7. at `100`, consume one input, insert result, reset progress;
8. failed precondition resets progress to `0` without input/output mutation.

Persist item handler, energy, progress. Clamp energy `0..10_000` and progress `0..99` on load. Fixed constants are not persisted.

`ContainerData` exposes exactly progress, max progress, energy. Client-side menu data must not mutate server-owned energy storage.

Require fresh `test build` PASS.

---

## Task 6 — RED/GREEN: menu and block interaction

RED requires `SlotItemHandler`, `SimpleContainerData(3)`, `checkContainerDataCount(data, 3)`, `ContainerLevelAccess`, real `stillValid`, and non-stub `quickMoveStack`.

GREEN menu index contract:

```text
0 input
1 output
2..28 player inventory
29..37 hotbar
```

- machine-to-player shift-click targets `[2, 38)`;
- player-to-machine targets input `[0, 1)` only;
- output never accepts player shift-click;
- client constructor uses dummy handler/data and `ContainerLevelAccess.NULL`;
- server constructor receives real handler/data/access;
- block opens menu only on logical server;
- ticker delegates to machine server tick only for the correct BE type.

Require fresh `test build` PASS.

---

## Task 7 — RED/GREEN: seven required GameTests

Create only after RED requires:

- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/gametest/I9MachineGameTests.java`
- `engineering/tests/golden/i9-machine-foundation/overlay/src/main/resources/data/i9_machine/structure/machine_test.nbt`

Required test methods:

- `inventoryCapability`
- `energyCapability`
- `successfulProcessing`
- `insufficientEnergy`
- `blockedOutput`
- `persistence`
- `progressReset`

Use `@GameTestHolder(I9MachineMod.MOD_ID)` and an explicit template contract so the resource name is deterministic. The structure NBT is checked in as source authority; its actual SHA-256 is computed and stored in the I9 manifest, and the Python contract recomputes it.

Capability tests query the server level for NeoForge block capabilities. Successful processing uses raw iron, at least `2_000` energy, and verifies one iron ingot after the 100-tick contract. Persistence must exercise actual BlockEntity serialization/load, including numeric bounds.

Authoritative runtime gate:

```bash
./gradlew runGameTestServer --no-daemon
```

Require exit code `0` and all seven required tests passing. Do not add unsupported `setForceExit` configuration.

---

## Task 8 — I5 dedicated-server proof

For the generated fixture only:

```bash
mkdir -p run/server
printf 'eula=true\n' > run/server/eula.txt
```

Then run:

```bash
python3 engineering/tooling/test-harness/run_test_harness.py --project .factory-ci/i9/generated
```

Require manifest `overall_state=PASS` with unit, gametest, and dedicated_server PASS. Do not weaken I5 target identity, EULA validation, timeout, or readiness detection. If a generic I5 defect appears, add an I5 RED before changing I5.

---

## Task 9 — expand permanent I9 CI and Sonar gates

The permanent workflow `.github/workflows/factory-engineering-i9-machine-foundation.yml` is created during Task 2 RED and expanded here only after a workflow-contract RED.

Final workflow must:

- use repository-pinned action SHAs;
- use Java 21;
- run I9 + relevant I3/I4/I5/I8 regressions;
- materialize a fresh I9 project;
- run `test build`;
- run `runGameTestServer`;
- create EULA only in generated fixture;
- run I5 harness;
- run `git diff --check`.

Run the complete Python set:

```bash
python3 -m unittest \
  engineering/tests/test_i3_mod_scaffolder.py \
  engineering/tests/test_i3_security_review.py \
  engineering/tests/test_i4_engineering_validators.py \
  engineering/tests/test_i5_test_harness.py \
  engineering/tests/test_i8_feature_generator.py \
  engineering/tests/test_i8_feature_generator_neoforge.py \
  engineering/tests/test_i9_machine_foundation.py
```

Sonar policy: if branch Sonar proves `materialize_i9.py` lacks imported coverage, add the I9 test to the existing Python coverage run. Do not hide production Python through exclusions.

---

## Task 10 — PR, review, merge, post-merge, STATUS closeout

Before making PR #99 ready for review:

- revalidate current `main` and concurrent PRs;
- ensure branch is based/reconciled with current main;
- update PR body with exact RED/GREEN run IDs, test counts, `test build`, `runGameTestServer`, I5 manifest, Sonar result, and non-goals;
- require all relevant checks terminal successful;
- fix correctness/security review findings through new REDs before resolving threads.

Before merge require:

```text
mergeable = true
no competing PR affecting I9 surfaces
I9 workflow = success
relevant regressions = success
Sonar Quality Gate = PASS
review threads = resolved
```

Merge with expected head SHA and regular merge unless repository policy observed at merge time requires otherwise.

Post-merge:

- poll every workflow for the implementation merge SHA until terminal;
- require zero failure/cancelled/pending/null conclusions among required workflows;
- inspect main Sonar log for `QUALITY GATE STATUS: PASSED`;
- only then create a dedicated STATUS closeout branch/PR;
- record `I9_STATE=PASS`, exact evidence, and `NEXT_ACTION=BEGIN_I10_MULTIBLOCK_FOUNDATION`;
- merge STATUS closeout and again verify all post-closeout workflows plus main Sonar before calling I9 formally closed.
