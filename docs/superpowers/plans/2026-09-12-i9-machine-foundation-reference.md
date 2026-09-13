# I9 Machine Foundation Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible NeoForge 1.21.1 Machine Foundation Golden that proves inventory, energy, vanilla-smelting recipe lookup, progress, persistence, sync, menu backend, GameTests, and dedicated-server compatibility without making I8 machine-aware.

**Architecture:** Generate a fresh canonical I3 project, then apply a deterministic I9-owned overlay for a fixed synthetic mod identity (`i9_machine`, package `dev.example.i9machine`). Shared scaffold behavior remains owned by I3; the known GameTest run-config defect is corrected in I3 first. I9 runtime is a single-block server-authoritative machine whose two-slot `ItemStackHandler`, bounded `IEnergyStorage`, menu `ContainerData`, and vanilla `minecraft:smelting` lookup are exercised by required GameTests.

**Tech Stack:** Java 21, Minecraft 1.21.1, NeoForge 21.1.248, NeoGradle userdev 7.1.26, Gradle 8.14, Python 3 unittest tooling, GitHub Actions, SonarQube Cloud.

**Spec:** `docs/superpowers/specs/2026-09-12-i9-machine-foundation-reference-design.md`

## Global Constraints

- Physical target is exactly Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`.
- Physical modlist authority is the project-supplied snapshot with SHA-256 `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`.
- I9 is a dedicated Golden/reference capability; it is not injected into every generated mod.
- I8 remains generic and is not extended with a `machine` feature in this PR.
- No custom recipe serializer/type is introduced; use vanilla `minecraft:smelting` with `SingleRecipeInput`.
- Canonical constants are capacity `10_000`, max external receive `1_000`, external extraction `0`, cost `20` energy/tick, duration `100` server ticks.
- Machine item slots are input `0`, output `1`.
- Menu sync exposes exactly progress, max progress, and current energy through `ContainerData`; item stacks sync through slots.
- No `AbstractContainerScreen`, custom visual GUI, textures, VFX, multiblock, logistics, fluid, tiers, upgrades, side configuration, or release tooling in I9.
- Existing files are never overwritten silently; generated-project mutations use exact anchors and fail closed on drift.
- Required runtime gates are `test build`, `runGameTestServer`, and I5 dedicated-server smoke.
- `STATUS.md` is not changed until I9 is merged and post-merge workflows plus main Sonar are green.

## Planned File Structure

Shared I3 correction:

- Modify `engineering/tests/test_i3_mod_scaffolder.py`.
- Modify `engineering/templates/neoforge-mod/build.gradle.tmpl`.
- Modify `engineering/tests/golden/i3-golden-mod/build.gradle`.

I9 composition authority:

- Create `engineering/tests/fixtures/i9-machine-mod-spec.json`.
- Create `engineering/tests/fixtures/i9-machine-scaffold-config.json`.
- Create `engineering/tooling/machine-foundation/materialize_i9.py`.
- Create `engineering/tests/test_i9_machine_foundation.py`.
- Create `engineering/tests/golden/i9-machine-foundation/manifest.json`.

I9 Java overlay:

- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/I9MachineContent.java`.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlock.java`.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineEnergyStorage.java`.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java`.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineMenu.java`.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/gametest/I9MachineGameTests.java`.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/resources/data/i9_machine/structure/machine_test.nbt`.

CI:

- Create `.github/workflows/factory-engineering-i9-machine-foundation.yml`.
- Modify `.github/workflows/factory-sonar-ci.yml` only if a failing branch Sonar run proves the new Python materializer is missing coverage ingestion.

---

### Task 1: Correct I3 GameTest Server Run Configuration

**Files:**
- Modify: `engineering/tests/test_i3_mod_scaffolder.py`
- Modify: `engineering/templates/neoforge-mod/build.gradle.tmpl`
- Modify: `engineering/tests/golden/i3-golden-mod/build.gradle`

**Interfaces:**
- Consumes: `generate_project(mod_spec_path: Path | str, scaffold_config_path: Path | str, output_dir: Path | str) -> Path`.
- Produces this exact generated run block:

```groovy
gameTestServer {
    systemProperty 'neoforge.enabledGameTestNamespaces', project.mod_id
    setForceExit false
}
```

- [ ] **Step 1: Write the failing I3 regression test**

Add this method to `I3ModScaffolderContractTest`:

```python
def test_game_test_server_disables_neogradle_force_exit(self):
    with tempfile.TemporaryDirectory() as tmp:
        generated = self.generate(Path(tmp) / "generated")
        build_gradle = (generated / "build.gradle").read_text(encoding="utf-8")
        block = build_gradle.split("gameTestServer {", 1)[1].split("}", 1)[0]
        self.assertIn(
            "setForceExit false",
            block,
            "I9 prerequisite RED: NeoForge 1.21.1 Game Test Server must disable NeoGradle force exit",
        )
```

- [ ] **Step 2: Run RED and record evidence**

```bash
python3 -m unittest engineering/tests/test_i3_mod_scaffolder.py
```

Expected: the new test fails because the current canonical template does not contain `setForceExit false`; all earlier I3 tests pass.

- [ ] **Step 3: Apply the owner-correct minimal fix**

Insert `setForceExit false` into the `gameTestServer` block in both `engineering/templates/neoforge-mod/build.gradle.tmpl` and `engineering/tests/golden/i3-golden-mod/build.gradle`.

- [ ] **Step 4: Run GREEN plus I3 security regression**

```bash
python3 -m unittest \
  engineering/tests/test_i3_mod_scaffolder.py \
  engineering/tests/test_i3_security_review.py
```

Expected: zero failures/errors.

- [ ] **Step 5: Commit the I3 prerequisite**

```bash
git add engineering/tests/test_i3_mod_scaffolder.py \
  engineering/templates/neoforge-mod/build.gradle.tmpl \
  engineering/tests/golden/i3-golden-mod/build.gradle
git commit -m "fix(engineering): make I3 GameTest server exit cleanly"
```

---

### Task 2: Establish the I9 Golden Composition Contract

**Files:**
- Create: `engineering/tests/fixtures/i9-machine-mod-spec.json`
- Create: `engineering/tests/fixtures/i9-machine-scaffold-config.json`
- Create: `engineering/tests/test_i9_machine_foundation.py`
- Create: `engineering/tests/golden/i9-machine-foundation/manifest.json`
- Create: `engineering/tooling/machine-foundation/materialize_i9.py`

**Interfaces:**
- Consumes I3 `generate_project(mod_spec_path: Path | str, scaffold_config_path: Path | str, output_dir: Path | str) -> Path`.
- Produces `materialize_i9(output_dir: Path | str) -> Path` for the fixed I9 identity.

- [ ] **Step 1: Create the fixed I9 fixtures**

`engineering/tests/fixtures/i9-machine-scaffold-config.json`:

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

`engineering/tests/fixtures/i9-machine-mod-spec.json`:

```json
{
  "schema_version": 1,
  "identity": {
    "name": "I9 Machine Foundation",
    "mod_id": "i9_machine",
    "repository": "UNRESOLVED",
    "target": {
      "minecraft": "1.21.1",
      "loader": "neoforge",
      "neoforge": "21.1.248",
      "java": 21
    }
  },
  "purpose": {
    "fantasy": "Synthetic Golden Project used only to verify the canonical I9 Machine Foundation reference.",
    "player_problem": "Prove deterministic single-block machine composition on the canonical NeoForge target.",
    "core_loop": ["Insert raw iron", "Supply energy", "Process", "Collect iron ingot"],
    "non_goals": ["Production gameplay", "Custom visual GUI", "Multiblocks", "Logistics networks"]
  },
  "dependencies": {
    "required": ["neoforge"],
    "optional": [],
    "incompatible": [],
    "profiles": []
  },
  "systems": {
    "blocks": ["machine"],
    "items": ["machine_block_item"],
    "machines": ["single_block_smelting_machine"],
    "entities": [],
    "worldgen": [],
    "ui": ["machine_menu_backend"],
    "networking": [],
    "progression": [],
    "integrations": []
  },
  "visual": {
    "repo_textura_package": "UNRESOLVED",
    "provider_profiles": [],
    "required_assets": [],
    "handoff_manifest": "UNRESOLVED"
  },
  "data": {
    "persistence": ["machine_inventory", "machine_energy", "machine_progress"],
    "recipes": ["minecraft:smelting"],
    "tags": [],
    "data_maps": [],
    "configs": []
  },
  "testing": {
    "unit": "REQUIRED",
    "gametest": "REQUIRED",
    "client": "NOT_REQUIRED_FOR_I9",
    "dedicated_server": "REQUIRED",
    "multiplayer": "NOT_REQUIRED_FOR_I9",
    "performance": "NOT_REQUIRED_FOR_I9",
    "manifest": "build/i5-test-harness/test-manifest.json"
  },
  "release": {
    "versioning": "0.1.0",
    "distribution": ["UNRESOLVED"],
    "license": "MIT",
    "state": "REFERENCE_ONLY"
  },
  "evidence": {
    "state": "PENDING_I9_GATES",
    "sources": ["synthetic I9 Golden fixture"],
    "open_questions": []
  }
}
```

- [ ] **Step 2: Write the structural RED**

Create `engineering/tests/test_i9_machine_foundation.py` with:

```python
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

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

- [ ] **Step 3: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

Expected: FAIL because the materializer, overlay directory, and manifest are absent.

- [ ] **Step 4: Implement the safe composition entrypoint**

`engineering/tooling/machine-foundation/materialize_i9.py` must define:

```python
EXPECTED_TARGET = {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "neoforge": "21.1.248",
    "java": 21,
}

class MaterializationError(RuntimeError):
    pass

def materialize_i9(output_dir: Path | str) -> Path:
    output = _validated_workspace_output(output_dir)
    project = _generate_i3_project(output)
    manifest = _load_manifest()
    _copy_overlay(project, manifest)
    _wire_main_class(project)
    return project
```

Implement `_validated_workspace_output`, `_generate_i3_project`, `_load_manifest`, `_copy_overlay`, `_validated_relative_path`, and `_wire_main_class` with these closed rules:

- output must be inside the current workspace and not equal to workspace root;
- I3 fixtures are the only scaffold inputs;
- manifest root keys are exactly `schema_version`, `overlay_files`, and `main_class_patch`;
- every overlay path is relative, contains no `..`, is unique, resolves inside overlay root, is not a symlink, and targets a path that does not already exist in the generated project;
- the main class patch targets only `src/main/java/dev/example/i9machine/I9MachineMod.java`;
- the exact empty constructor generated by I3 is replaced once with imports plus:

```java
public I9MachineMod(IEventBus modBus) {
    I9MachineContent.register(modBus);
    modBus.addListener(I9MachineContent::registerCapabilities);
}
```

- zero or multiple exact-anchor matches raise `MaterializationError` before writing the main class.

- [ ] **Step 5: Add determinism and containment tests**

Add helpers that load the module and compare generated file bytes. Required assertions:

```python
self.assertEqual(file_map(first), file_map(second))
with self.assertRaises(module.MaterializationError):
    module._validated_relative_path("../escape.java")
with self.assertRaises(module.MaterializationError):
    module._validated_relative_path("/absolute/escape.java")
```

Also mutate a copied manifest with an unknown root key and require fail-closed behavior before an overlay write.

- [ ] **Step 6: Run GREEN**

```bash
python3 -m unittest \
  engineering/tests/test_i3_mod_scaffolder.py \
  engineering/tests/test_i3_security_review.py \
  engineering/tests/test_i9_machine_foundation.py
```

Expected: zero failures/errors.

- [ ] **Step 7: Commit composition foundation**

```bash
git add engineering/tests/fixtures/i9-machine-mod-spec.json \
  engineering/tests/fixtures/i9-machine-scaffold-config.json \
  engineering/tests/test_i9_machine_foundation.py \
  engineering/tests/golden/i9-machine-foundation/manifest.json \
  engineering/tooling/machine-foundation/materialize_i9.py
git commit -m "test(engineering): establish I9 machine Golden contract"
```

---

### Task 3: Add Registry, Block, BlockEntity, Menu, and Capability Surfaces

**Files:**
- Create: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/I9MachineContent.java`
- Create: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlock.java`
- Create: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineEnergyStorage.java`
- Create: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java`
- Create: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineMenu.java`
- Modify: `engineering/tests/golden/i9-machine-foundation/manifest.json`
- Modify: `engineering/tests/test_i9_machine_foundation.py`

**Interfaces:**
- `I9MachineContent.register(IEventBus modBus)`.
- `I9MachineContent.registerCapabilities(RegisterCapabilitiesEvent event)`.
- `MachineBlockEntity.getItemHandler() -> IItemHandler`.
- `MachineBlockEntity.getEnergyStorage() -> IEnergyStorage`.

- [ ] **Step 1: Extend structural tests before adding Java sources**

Require these exact manifest paths:

```python
required = {
    "src/main/java/dev/example/i9machine/machine/I9MachineContent.java",
    "src/main/java/dev/example/i9machine/machine/MachineBlock.java",
    "src/main/java/dev/example/i9machine/machine/MachineEnergyStorage.java",
    "src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java",
    "src/main/java/dev/example/i9machine/machine/MachineMenu.java",
}
self.assertTrue(required.issubset(set(manifest["overlay_files"])))
```

Require source tokens `DeferredRegister`, `Capabilities.ItemHandler.BLOCK`, `Capabilities.EnergyStorage.BLOCK`, and `registerBlockEntity`.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

Expected: FAIL because the Java overlay files are absent.

- [ ] **Step 3: Implement registry/capability authority**

`I9MachineContent` owns deferred registers for blocks, items, block entity types, and menus. Use the target registry APIs and register exactly one `machine` block, one block item, one `MachineBlockEntity` type, and one `MachineMenu` type.

Capability registration is exactly:

```java
public static void registerCapabilities(RegisterCapabilitiesEvent event) {
    event.registerBlockEntity(
        Capabilities.ItemHandler.BLOCK,
        MACHINE_BLOCK_ENTITY.get(),
        (blockEntity, side) -> blockEntity.getItemHandler()
    );
    event.registerBlockEntity(
        Capabilities.EnergyStorage.BLOCK,
        MACHINE_BLOCK_ENTITY.get(),
        (blockEntity, side) -> blockEntity.getEnergyStorage()
    );
}
```

- [ ] **Step 4: Implement minimal compiling block/menu/BE shells**

`MachineBlock` extends `BaseEntityBlock` and returns `new MachineBlockEntity(pos, state)` from `newBlockEntity`. `MachineBlockEntity` extends `BlockEntity` with stable handler fields. `MachineMenu` extends `AbstractContainerMenu` with real constructor signatures, `stillValid`, and `quickMoveStack` implementations that compile without screen code.

- [ ] **Step 5: Materialize and run target-exact compile GREEN**

```bash
rm -rf .factory-ci/i9/generated
mkdir -p .factory-ci/i9
python3 engineering/tooling/machine-foundation/materialize_i9.py --output .factory-ci/i9/generated
chmod +x .factory-ci/i9/generated/gradlew
cd .factory-ci/i9/generated
GRADLE_USER_HOME="$GITHUB_WORKSPACE/.factory-ci/i9/gradle-home" ./gradlew test build --no-daemon
```

Expected: BUILD SUCCESSFUL. Fix any compile mismatch against NeoForge `21.1.248`; do not invent substitute APIs.

- [ ] **Step 6: Commit registry/runtime surfaces**

```bash
git add engineering/tests/golden/i9-machine-foundation \
  engineering/tests/test_i9_machine_foundation.py
git commit -m "feat(engineering): add I9 machine runtime surfaces"
```

---

### Task 4: Implement Inventory and Energy Contracts

**Files:**
- Modify: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineEnergyStorage.java`
- Modify: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java`
- Modify: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineMenu.java`
- Modify: `engineering/tests/test_i9_machine_foundation.py`

**Interfaces:**
- `MachineEnergyStorage.receiveEnergy(int maxReceive, boolean simulate)`.
- `MachineEnergyStorage.extractEnergy(int maxExtract, boolean simulate)` always exposes zero external extraction.
- `MachineEnergyStorage.consumeInternal(int amount)` performs machine-owned energy consumption.
- `MachineEnergyStorage.setStoredEnergy(int value)` clamps to valid range.
- `MachineBlockEntity.INPUT_SLOT = 0`, `OUTPUT_SLOT = 1`.

- [ ] **Step 1: Add RED contracts for fixed constants and policies**

Require these exact constants in `MachineBlockEntity`:

```java
public static final int ENERGY_CAPACITY = 10_000;
public static final int MAX_RECEIVE = 1_000;
public static final int ENERGY_PER_TICK = 20;
public static final int MAX_PROGRESS = 100;
public static final int INPUT_SLOT = 0;
public static final int OUTPUT_SLOT = 1;
```

Require output insertion rejection and external energy extraction rejection.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

- [ ] **Step 3: Implement `MachineEnergyStorage`**

Use a direct `IEnergyStorage` implementation with fields `capacity`, `maxReceive`, `onChanged`, and `energy`. `receiveEnergy` returns `0` for non-positive requests; otherwise it accepts at most `min(maxReceive, capacity - energy)`. Real receives update state and call `onChanged`. `extractEnergy` returns `0`. `canExtract` returns `false`; `canReceive` returns `true`; `getMaxEnergyStored` returns `capacity`.

Internal mutation code:

```java
public boolean consumeInternal(int amount) {
    if (amount <= 0 || this.energy < amount) {
        return false;
    }
    this.energy -= amount;
    this.onChanged.run();
    return true;
}

public void setStoredEnergy(int value) {
    int clamped = Mth.clamp(value, 0, this.capacity);
    if (clamped != this.energy) {
        this.energy = clamped;
        this.onChanged.run();
    }
}
```

- [ ] **Step 4: Implement two-slot item policy**

Back the machine with one stable `ItemStackHandler(2)` whose `onContentsChanged` calls `setChanged()`. Output slot `1` returns `false` from `isItemValid`. Input slot validity calls `MachineBlockEntity.canSmelt(ItemStack)` when a `ServerLevel` exists; before server-level attachment it rejects automation insertion.

- [ ] **Step 5: Build GREEN**

Rematerialize and run:

```bash
cd .factory-ci/i9/generated
GRADLE_USER_HOME="$GITHUB_WORKSPACE/.factory-ci/i9/gradle-home" ./gradlew clean test build --no-daemon
```

Expected: BUILD SUCCESSFUL.

- [ ] **Step 6: Commit inventory/energy foundation**

```bash
git add engineering/tests/golden/i9-machine-foundation \
  engineering/tests/test_i9_machine_foundation.py
git commit -m "feat(engineering): implement I9 inventory and energy"
```

---

### Task 5: Implement Smelting Processing, Persistence, and Menu Sync

**Files:**
- Modify: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java`
- Modify: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineMenu.java`
- Modify: `engineering/tests/test_i9_machine_foundation.py`

**Interfaces:**
- `MachineBlockEntity.serverTick(Level level, BlockPos pos, BlockState state, MachineBlockEntity blockEntity)` is the only tick mutation path.
- `ContainerData` indices are `0=progress`, `1=maxProgress`, `2=energy`.

- [ ] **Step 1: Add RED source contracts**

Require `SingleRecipeInput`, `RecipeType.SMELTING`, `getRecipeFor`, `assemble`, `loadAdditional`, `saveAdditional`, `ContainerData`, and `getCount() == 3` behavior.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

- [ ] **Step 3: Implement server-side recipe lookup**

Use this target shape:

```java
private Optional<RecipeHolder<? extends AbstractCookingRecipe>> findRecipe(ServerLevel level) {
    ItemStack inputStack = this.items.getStackInSlot(INPUT_SLOT);
    if (inputStack.isEmpty()) {
        return Optional.empty();
    }
    return level.getRecipeManager().getRecipeFor(
        RecipeType.SMELTING,
        new SingleRecipeInput(inputStack),
        level
    );
}
```

Assemble with:

```java
SingleRecipeInput recipeInput = new SingleRecipeInput(inputStack);
ItemStack result = holder.value().assemble(recipeInput, level.registryAccess());
```

If target compilation changes only the concrete generic type returned by `RecipeType.SMELTING`, use the compiler-resolved vanilla cooking recipe class while preserving server-only `RecipeManager`, `SingleRecipeInput`, `RecipeType.SMELTING`, and `assemble` semantics.

- [ ] **Step 4: Implement the processing state machine**

Start with:

```java
if (!(level instanceof ServerLevel serverLevel)) {
    return;
}
```

Each valid server tick resolves recipe and result, verifies output compatibility, verifies `20` stored energy, consumes exactly `20`, increments progress by `1`, and completes at `100`. Completion consumes one input, inserts the assembled result, and resets progress to `0`. Any invalid precondition resets progress to `0` without consuming input or creating output.

- [ ] **Step 5: Implement persistence bounds**

Use `saveAdditional(CompoundTag, HolderLookup.Provider)` and `loadAdditional(CompoundTag, HolderLookup.Provider)`. Persist item handler contents, energy, and progress. On load clamp energy to `0..10_000` and progress to `0..99`. Call superclass methods. Use the actual HolderLookup-aware `ItemStackHandler` serialization methods exposed by NeoForge 21.1.248.

- [ ] **Step 6: Implement three-value `ContainerData`**

Server data returns progress at index `0`, `MAX_PROGRESS` at index `1`, energy at index `2`, and count `3`. The menu client constructor uses `new SimpleContainerData(3)` so network-applied values do not mutate server-owned storage.

- [ ] **Step 7: Build GREEN**

Rematerialize and run:

```bash
./gradlew test build --no-daemon
```

Expected: BUILD SUCCESSFUL.

- [ ] **Step 8: Commit processing/persistence/sync**

```bash
git add engineering/tests/golden/i9-machine-foundation \
  engineering/tests/test_i9_machine_foundation.py
git commit -m "feat(engineering): add I9 processing persistence and sync"
```

---

### Task 6: Complete Menu Backend and Block Interaction

**Files:**
- Modify: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlock.java`
- Modify: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java`
- Modify: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineMenu.java`
- Modify: `engineering/tests/test_i9_machine_foundation.py`

**Interfaces:**
- Client constructor: `MachineMenu(int containerId, Inventory playerInventory)`.
- Server constructor: `MachineMenu(int containerId, Inventory playerInventory, IItemHandler machineItems, ContainerData data, ContainerLevelAccess access)`.

- [ ] **Step 1: Add RED contracts for menu invariants**

Require `SlotItemHandler`, `new SimpleContainerData(3)`, `checkContainerDataCount(data, 3)`, `ContainerLevelAccess.NULL`, `AbstractContainerMenu.stillValid`, and a non-stub `quickMoveStack`.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

- [ ] **Step 3: Implement constructors and slot order**

Client constructor:

```java
public MachineMenu(int containerId, Inventory playerInventory) {
    this(
        containerId,
        playerInventory,
        new ItemStackHandler(2),
        new SimpleContainerData(3),
        ContainerLevelAccess.NULL
    );
}
```

Server constructor adds machine input slot `0`, machine output slot `1`, 27 player inventory slots, 9 hotbar slots, then `addDataSlots(data)`. The output `SlotItemHandler` overrides `mayPlace(ItemStack)` to return `false`.

- [ ] **Step 4: Implement `stillValid` and `quickMoveStack`**

```java
@Override
public boolean stillValid(Player player) {
    return AbstractContainerMenu.stillValid(this.access, player, I9MachineContent.MACHINE_BLOCK.get());
}
```

Slot indexes are exactly `0` input, `1` output, `2..28` player inventory, `29..37` hotbar. Machine-to-player shift-click targets `[2, 38)`. Player-to-machine shift-click targets input `[0, 1)` only. Player inventory and hotbar can fall back between their own ranges but never target output slot `1`.

- [ ] **Step 5: Implement block interaction and ticker**

`MachineBlock.getTicker` returns `MachineBlockEntity::serverTick` only for the registered machine BE type. `getMenuProvider` returns a `SimpleMenuProvider` whose server menu receives BE item handler, BE `ContainerData`, and `ContainerLevelAccess.create(level, pos)`. `useWithoutItem` opens the menu only on the logical server through `ServerPlayer.openMenu` and returns sided success.

- [ ] **Step 6: Run target-exact build GREEN**

```bash
./gradlew clean test build --no-daemon
```

Expected: BUILD SUCCESSFUL.

- [ ] **Step 7: Commit menu backend**

```bash
git add engineering/tests/golden/i9-machine-foundation \
  engineering/tests/test_i9_machine_foundation.py
git commit -m "feat(engineering): complete I9 machine menu backend"
```

---

### Task 7: Add Required GameTests and Structure Template

**Files:**
- Create: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/gametest/I9MachineGameTests.java`
- Create: `engineering/tests/golden/i9-machine-foundation/overlay/src/main/resources/data/i9_machine/structure/machine_test.nbt`
- Modify: `engineering/tests/golden/i9-machine-foundation/manifest.json`
- Modify: `engineering/tests/test_i9_machine_foundation.py`

**Interfaces:**
- `@GameTestHolder(I9MachineMod.MOD_ID)` owns the I9 GameTests.
- Seven required tests use one `machine_test` structure template.

- [ ] **Step 1: Add GameTest surface RED**

Require all method names:

```python
for name in (
    "inventoryCapability",
    "energyCapability",
    "successfulProcessing",
    "insufficientEnergy",
    "blockedOutput",
    "persistence",
    "progressReset",
):
    self.assertIn(f"void {name}(GameTestHelper helper)", source)
```

Also require `@GameTestHolder(I9MachineMod.MOD_ID)` and `src/main/resources/data/i9_machine/structure/machine_test.nbt` in the manifest.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

Expected: FAIL because GameTest Java and structure files are absent.

- [ ] **Step 3: Add deterministic minimal structure binary**

Create a valid Minecraft structure NBT with empty space sufficient for one machine block placed by test setup. Save it at `engineering/tests/golden/i9-machine-foundation/overlay/src/main/resources/data/i9_machine/structure/machine_test.nbt`. Compute its SHA-256 with:

```bash
sha256sum engineering/tests/golden/i9-machine-foundation/overlay/src/main/resources/data/i9_machine/structure/machine_test.nbt
```

Insert the returned 64-hex digest into the manifest entry for that exact path. `test_i9_machine_foundation.py` recomputes the digest and fails on drift.

- [ ] **Step 4: Implement capability GameTests**

Place the machine block at a fixed relative position, get its absolute position through `GameTestHelper.absolutePos`, then query block capabilities from the server level. Inventory test proves input accepts raw iron, output rejects insertion, and output allows extraction. Energy test proves one receive call accepts no more than `1_000`, total energy caps at `10_000`, and external extraction returns `0`.

- [ ] **Step 5: Implement processing GameTests**

Use `Items.RAW_IRON` input and assert `Items.IRON_INGOT` output. Supply at least `2_000` energy. Successful processing must only succeed after the 100-tick contract. Insufficient-energy, blocked-output, and progress-reset tests prove no premature input consumption/output creation and progress reset to `0`.

- [ ] **Step 6: Implement persistence GameTest**

Exercise real BlockEntity save/load serialization with the server registry provider and assert inventory, energy, and progress restore correctly. Also feed out-of-range numeric values through the serialization path and prove energy/progress bounds.

- [ ] **Step 7: Run real GameTest Server GREEN**

```bash
GRADLE_USER_HOME="$GITHUB_WORKSPACE/.factory-ci/i9/gradle-home" ./gradlew runGameTestServer --no-daemon
```

Expected: Gradle exit code `0` and seven required I9 GameTests pass.

- [ ] **Step 8: Commit GameTests**

```bash
git add engineering/tests/golden/i9-machine-foundation \
  engineering/tests/test_i9_machine_foundation.py
git commit -m "test(engineering): prove I9 machine behavior with GameTests"
```

---

### Task 8: Prove I5 Dedicated-Server Compatibility

**Files:**
- Modify `engineering/tests/test_i9_machine_foundation.py` only if a new materialization assertion is needed.
- Do not modify `engineering/tooling/test-harness/run_test_harness.py` unless a reproducible I5 defect is demonstrated by a new failing I5 regression.

**Interfaces:**
- Consumes I5 `run_harness(project_root)` with unit, gametest, and dedicated-server suites.
- Produces `build/i5-test-harness/test-manifest.json` with `overall_state` equal to `PASS`.

- [ ] **Step 1: Prepare only the controlled fixture EULA**

```bash
mkdir -p .factory-ci/i9/generated/run/server
printf 'eula=true\n' > .factory-ci/i9/generated/run/server/eula.txt
```

Do not add a repository-wide EULA file.

- [ ] **Step 2: Run I5 harness**

```bash
python3 engineering/tooling/test-harness/run_test_harness.py \
  --project .factory-ci/i9/generated
```

Expected: terminal output `I5 test harness: PASS` and the manifest records PASS for unit, gametest, and dedicated_server.

- [ ] **Step 3: Fix only demonstrated ownership defects**

If machine runtime fails, fix I9 through a new I9 RED. If generic harness behavior fails, first add a failing regression in `engineering/tests/test_i5_test_harness.py`; do not weaken EULA, target identity, timeouts, or server-ready detection.

- [ ] **Step 4: Run I5 regression suite**

```bash
python3 -m unittest engineering/tests/test_i5_test_harness.py
```

Expected: zero failures/errors.

- [ ] **Step 5: Commit only when Task 8 changes source**

Stage only files actually changed and commit with:

```bash
git commit -m "fix(engineering): reconcile I9 with canonical test harness"
```

No empty commit is created when no source change is required.

---

### Task 9: Add I9 CI and Complete Pre-Merge Gates

**Files:**
- Create: `.github/workflows/factory-engineering-i9-machine-foundation.yml`
- Modify: `.github/workflows/factory-sonar-ci.yml` only after a failing coverage gate proves it necessary.
- Modify: `engineering/tests/test_i9_machine_foundation.py`

**Interfaces:**
- Produces workflow `Factory Engineering I9 Machine Foundation`.

- [ ] **Step 1: Write workflow-contract RED**

Add assertions that `.github/workflows/factory-engineering-i9-machine-foundation.yml` exists, watches I9 and consumed I3/I5 surfaces, uses Java 21, runs I9/I3/I5 regressions, materializes I9, runs `test build`, runs `runGameTestServer`, creates only fixture EULA, runs I5 harness, and runs `git diff --check`.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

Expected: FAIL because the workflow file is absent.

- [ ] **Step 3: Implement workflow**

Workflow header:

```yaml
name: Factory Engineering I9 Machine Foundation
permissions:
  contents: read
```

Regression command:

```bash
python3 -m unittest \
  engineering/tests/test_i9_machine_foundation.py \
  engineering/tests/test_i3_mod_scaffolder.py \
  engineering/tests/test_i3_security_review.py \
  engineering/tests/test_i5_test_harness.py \
  engineering/tests/test_i8_feature_generator.py \
  engineering/tests/test_i8_feature_generator_neoforge.py
```

Then materialize `.factory-ci/i9/generated`, run `./gradlew test build --no-daemon`, run `./gradlew runGameTestServer --no-daemon`, create `.factory-ci/i9/generated/run/server/eula.txt` with `eula=true`, run the I5 harness, and finish with `git diff --check`.

- [ ] **Step 4: Run complete Python regression set**

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

Expected: zero failures/errors.

- [ ] **Step 5: Run fresh target-exact runtime gates**

```bash
rm -rf .factory-ci/i9/generated
python3 engineering/tooling/machine-foundation/materialize_i9.py --output .factory-ci/i9/generated
chmod +x .factory-ci/i9/generated/gradlew
cd .factory-ci/i9/generated
GRADLE_USER_HOME="$GITHUB_WORKSPACE/.factory-ci/i9/gradle-home" ./gradlew clean test build --no-daemon
GRADLE_USER_HOME="$GITHUB_WORKSPACE/.factory-ci/i9/gradle-home" ./gradlew runGameTestServer --no-daemon
mkdir -p run/server
printf 'eula=true\n' > run/server/eula.txt
cd "$GITHUB_WORKSPACE"
python3 engineering/tooling/test-harness/run_test_harness.py --project .factory-ci/i9/generated
git diff --check
```

Record exact Python test counts, Gradle results, GameTest result, and I5 manifest state.

- [ ] **Step 6: Verify Sonar coverage registration**

Run branch Sonar. If Quality Gate fails specifically because `engineering/tooling/machine-foundation/materialize_i9.py` lacks imported coverage, update `.github/workflows/factory-sonar-ci.yml` to execute `engineering/tests/test_i9_machine_foundation.py` under the existing coverage process, then rerun. Do not hide I9 production Python with exclusions.

- [ ] **Step 7: Commit CI**

```bash
git add .github/workflows/factory-engineering-i9-machine-foundation.yml \
  engineering/tests/test_i9_machine_foundation.py
```

If `.github/workflows/factory-sonar-ci.yml` changed for proven coverage reasons, add it explicitly. Commit:

```bash
git commit -m "ci(engineering): gate I9 machine foundation"
```

---

### Task 10: Review, PR, Merge, and Post-Merge Closure

**Files:**
- No implementation files unless a review finding first produces a failing regression.
- Modify `STATUS.md` only in a separate closeout PR after implementation merge SHA gates are complete.

**Interfaces:**
- Pre-merge: all required branch/PR workflows terminal successful, Sonar Quality Gate PASS, review threads resolved.
- Post-merge: all workflows for the merge SHA terminal successful and main Sonar Quality Gate PASS.

- [ ] **Step 1: Revalidate concurrency immediately before PR**

Confirm current `main`, open PRs, and branch base. If main moved, compare the new commits against I3/I5/I8/I9 surfaces before rebasing or merging main.

- [ ] **Step 2: Open implementation PR**

Title:

```text
feat(engineering): implement I9 machine foundation reference
```

Body includes RED evidence, final test counts, `test build`, `runGameTestServer`, I5 manifest, Sonar metrics, exact target, and explicit I10/I11/I12/I13/I14 non-goals.

- [ ] **Step 3: Resolve review findings through TDD**

For each correctness/security finding: add or tighten a regression first, record RED, implement minimal fix, rerun affected gates, then resolve the thread.

- [ ] **Step 4: Final pre-merge verification**

Require all of these simultaneously:

```text
mergeable = true
no competing PR affects I9 surfaces
all required workflows terminal success
I9 workflow success
Sonar Quality Gate PASS
all review threads resolved
```

- [ ] **Step 5: Merge with expected head SHA**

Use regular merge unless repository policy observed at merge time requires another strategy.

- [ ] **Step 6: Verify implementation merge SHA**

Poll until every workflow for the merge SHA is terminal. Require zero queued, zero in-progress, zero failure, zero cancelled, zero null conclusion. Inspect main Sonar job log for `QUALITY GATE STATUS: PASSED`.

- [ ] **Step 7: Create STATUS closeout branch and PR**

Update only the current frontier/evidence fields needed to record `I9_STATE=PASS`, implementation PR/head/merge SHA, RED runs, final branch/PR gates, post-merge workflow counts, post-merge Sonar result, and `NEXT_ACTION=BEGIN_I10_MULTIBLOCK_FOUNDATION`.

- [ ] **Step 8: Merge STATUS closeout and verify its merge SHA**

Again require every post-closeout workflow terminal successful plus main Sonar PASS before calling I9 formally closed.
