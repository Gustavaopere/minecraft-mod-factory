# I9 Machine Foundation Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible NeoForge 1.21.1 Machine Foundation Golden that proves inventory, energy, vanilla-smelting recipe lookup, progress, persistence, sync, menu backend, GameTests, and dedicated-server compatibility without making I8 machine-aware.

**Architecture:** Generate a fresh canonical I3 project, then apply a deterministic I9-owned overlay for a fixed synthetic mod identity (`i9_machine`, package `dev.example.i9machine`). Shared scaffold behavior remains owned by I3; the one known GameTest run-config defect is corrected in I3 first. I9 runtime is a single-block server-authoritative machine whose two-slot `ItemStackHandler`, bounded `IEnergyStorage`, menu `ContainerData`, and vanilla `minecraft:smelting` lookup are exercised by required GameTests.

**Tech Stack:** Java 21, Minecraft 1.21.1, NeoForge 21.1.248, NeoGradle userdev 7.1.26, Gradle 8.14, Python 3 unittest tooling, GitHub Actions, SonarQube Cloud.

**Spec:** `docs/superpowers/specs/2026-09-12-i9-machine-foundation-reference-design.md`

## Global Constraints

- Physical target is exactly Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`.
- The physical modlist authority is the project-supplied snapshot with SHA-256 `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`.
- I9 is a dedicated Golden/reference capability; it is not injected into every generated mod.
- I8 remains generic and is not extended with a `machine` feature in this PR.
- No custom recipe serializer/type is introduced; use vanilla `minecraft:smelting` with `SingleRecipeInput`.
- Canonical behavior constants: capacity `10_000`, max external receive `1_000`, external extraction `0`, cost `20` energy/tick, duration `100` server ticks.
- Machine item slots are fixed: input `0`, output `1`.
- Menu sync exposes exactly progress, max progress, and current energy through `ContainerData`; items sync through slots.
- No `AbstractContainerScreen`, custom visual GUI, textures, VFX, multiblock, logistics, fluid, tiers, upgrades, side configuration, or release tooling in I9.
- Existing files are never overwritten silently; generated-project mutations use exact anchors and fail closed on drift.
- Required runtime gates are `test build`, `runGameTestServer`, and I5 dedicated-server smoke.
- `STATUS.md` is not changed until I9 is merged and post-merge workflows plus main Sonar are green.

## Planned File Structure

Shared I3 correction:

- Modify `engineering/tests/test_i3_mod_scaffolder.py` — add the run-config regression contract.
- Modify `engineering/templates/neoforge-mod/build.gradle.tmpl` — add `setForceExit false` under `gameTestServer`.
- Modify `engineering/tests/golden/i3-golden-mod/build.gradle` — keep checked-in I3 Golden byte-equivalent to scaffold output.

I9 composition authority:

- Create `engineering/tests/fixtures/i9-machine-mod-spec.json` — fixed synthetic mod spec targeting the canonical stack.
- Create `engineering/tests/fixtures/i9-machine-scaffold-config.json` — fixed package/classes for the I9 generated project.
- Create `engineering/tooling/machine-foundation/materialize_i9.py` — safe deterministic composition of I3 scaffold + I9 overlay + exact main-class wiring.
- Create `engineering/tests/test_i9_machine_foundation.py` — structural, determinism, containment, ownership, and generated-source contracts.
- Create `engineering/tests/golden/i9-machine-foundation/manifest.json` — closed list of I9-owned overlay files and the one declared generated-main wiring mutation.

I9 Java overlay:

- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/I9MachineContent.java` — registries and capability registration.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlock.java` — block entity creation, server ticker, and menu opening.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineEnergyStorage.java` — bounded external energy API plus internal consumption/load.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java` — two-slot inventory, smelting lookup, processing, persistence, and `ContainerData`.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/machine/MachineMenu.java` — backend slots, sync, validity, and shift-click.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/java/dev/example/i9machine/gametest/I9MachineGameTests.java` — seven required GameTests.
- Create `engineering/tests/golden/i9-machine-foundation/overlay/src/main/resources/data/i9_machine/structure/machine_test.nbt` — minimal deterministic GameTest structure template.

CI:

- Create `.github/workflows/factory-engineering-i9-machine-foundation.yml` — contract tests, dependency regressions, materialization, build, GameTest server, I5 dedicated server, and whitespace.
- Modify `.github/workflows/factory-sonar-ci.yml` only if the new Python materializer is not covered automatically by current Python coverage collection; any change must be justified by a failing coverage gate first.

---

### Task 1: Correct I3 GameTest Server Run Configuration

**Files:**
- Modify: `engineering/tests/test_i3_mod_scaffolder.py`
- Modify: `engineering/templates/neoforge-mod/build.gradle.tmpl`
- Modify: `engineering/tests/golden/i3-golden-mod/build.gradle`

**Interfaces:**
- Consumes: `generate_project(mod_spec_path, scaffold_config_path, output_dir) -> Path` from I3.
- Produces: every generated `build.gradle` contains `gameTestServer { ... setForceExit false ... }`.

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

Run:

```bash
python3 -m unittest engineering/tests/test_i3_mod_scaffolder.py
```

Expected: exactly the new test fails because the current template has no `setForceExit false`; all prior I3 tests remain passing.

- [ ] **Step 3: Apply the owner-correct minimal fix**

Change the canonical template block to:

```groovy
gameTestServer {
    systemProperty 'neoforge.enabledGameTestNamespaces', project.mod_id
    setForceExit false
}
```

Make the identical textual change in `engineering/tests/golden/i3-golden-mod/build.gradle` so I3 byte-equivalence remains authoritative.

- [ ] **Step 4: Run GREEN plus I3 security regression**

Run:

```bash
python3 -m unittest \
  engineering/tests/test_i3_mod_scaffolder.py \
  engineering/tests/test_i3_security_review.py
```

Expected: PASS with zero failures.

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
- Consumes: canonical I3 `generate_project(...)`.
- Produces: `materialize_i9(output_dir: Path | str) -> Path` for one fixed synthetic I9 Golden identity.

- [ ] **Step 1: Create fixed I9 fixtures**

Use this scaffold config exactly:

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

Create the mod spec by preserving the I3 schema shape while setting:

```json
{
  "identity": {
    "name": "I9 Machine Foundation",
    "mod_id": "i9_machine",
    "target": {
      "minecraft": "1.21.1",
      "loader": "neoforge",
      "neoforge": "21.1.248",
      "java": 21
    }
  },
  "dependencies": {"required": ["neoforge"], "optional": [], "incompatible": [], "profiles": []},
  "systems": {"machines": ["single_block_smelting_machine"]},
  "data": {"recipes": ["minecraft:smelting"]}
}
```

All other required schema fields must remain explicit and synthetic, using the I3 fixture as the shape authority; no production repository/provider claims are added.

- [ ] **Step 2: Write the structural RED**

Start `test_i9_machine_foundation.py` with constants and tests:

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

- [ ] **Step 3: Run RED**

Run:

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

Expected: FAIL for the absent materializer/overlay/manifest.

- [ ] **Step 4: Implement the safe composition entrypoint**

`materialize_i9.py` must expose only:

```python
def materialize_i9(output_dir: Path | str) -> Path:
    ...
```

Implementation requirements:

```python
EXPECTED_TARGET = {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "neoforge": "21.1.248",
    "java": 21,
}
```

The function must:

1. resolve `output_dir` under the current workspace and reject workspace root/outside paths;
2. call I3 `generate_project(I9_MOD_SPEC, I9_SCAFFOLD_CONFIG, output_dir)`;
3. load `manifest.json` and reject unknown keys, absolute paths, `..`, symlinks, duplicates, and targets outside the generated project;
4. copy each overlay file byte-for-byte only when the destination does not already exist;
5. patch only `src/main/java/dev/example/i9machine/I9MachineMod.java` by replacing the exact constructor anchor with registration calls; reject zero or multiple anchor matches;
6. return the generated project path.

The main-class mutation is exact and closed:

```java
public I9MachineMod(IEventBus modBus) {
    I9MachineContent.register(modBus);
    modBus.addListener(I9MachineContent::registerCapabilities);
}
```

- [ ] **Step 5: Add determinism and containment tests**

Tests must generate into two temp directories and assert byte-identical file maps, then separately prove traversal/symlink/unknown-manifest mutations fail before any I9 overlay write.

Use assertions of this form:

```python
self.assertEqual(file_map(first), file_map(second))
with self.assertRaises(module.MaterializationError):
    module._validated_relative_path("../escape.java")
```

- [ ] **Step 6: Run GREEN**

```bash
python3 -m unittest \
  engineering/tests/test_i3_mod_scaffolder.py \
  engineering/tests/test_i3_security_review.py \
  engineering/tests/test_i9_machine_foundation.py
```

Expected: PASS.

- [ ] **Step 7: Commit composition foundation**

```bash
git add engineering/tests/fixtures/i9-machine-*.json \
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
- `I9MachineContent.register(IEventBus)` registers block/item/BE/menu.
- `I9MachineContent.registerCapabilities(RegisterCapabilitiesEvent)` exposes item and energy block capabilities.
- `MachineBlockEntity#getItemHandler() -> IItemHandler` and `getEnergyStorage() -> IEnergyStorage` are stable-lifetime capability instances.

- [ ] **Step 1: Extend structural tests before adding Java sources**

Assert the exact required relative paths and required source tokens, including:

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

Source-token assertions must require `DeferredRegister`, `Capabilities.ItemHandler.BLOCK`, `Capabilities.EnergyStorage.BLOCK`, and `registerBlockEntity`.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

Expected: FAIL because Java overlay files do not exist.

- [ ] **Step 3: Implement registry/capability authority**

`I9MachineContent` owns four deferred registrations and the capability event:

```java
public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(I9MachineMod.MOD_ID);
public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(I9MachineMod.MOD_ID);
public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES = DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, I9MachineMod.MOD_ID);
public static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(Registries.MENU, I9MachineMod.MOD_ID);
```

Register `machine`, `machine` block item, `machine` BlockEntity type, and `machine` menu type. Capability registration is:

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

`MachineBlock` extends `BaseEntityBlock`; `newBlockEntity` returns `new MachineBlockEntity(pos, state)`. `MachineBlockEntity` extends `BlockEntity` and exposes stable handler fields. `MachineMenu` extends `AbstractContainerMenu` and initially only satisfies constructor/stillValid/quickMoveStack compile contracts.

- [ ] **Step 5: Materialize and run target-exact compile GREEN**

```bash
rm -rf .factory-ci/i9/generated
mkdir -p .factory-ci/i9
python3 engineering/tooling/machine-foundation/materialize_i9.py --output .factory-ci/i9/generated
chmod +x .factory-ci/i9/generated/gradlew
cd .factory-ci/i9/generated
GRADLE_USER_HOME="$OLDPWD/.factory-ci/i9/gradle-home" ./gradlew test build --no-daemon
```

Expected: BUILD SUCCESSFUL. Any API mismatch is fixed against NeoForge 21.1.248, not guessed around.

- [ ] **Step 6: Commit registry/runtime surfaces**

```bash
git add engineering/tests/golden/i9-machine-foundation \
  engineering/tests/test_i9_machine_foundation.py
git commit -m "feat(engineering): add I9 machine runtime surfaces"
```

---

### Task 4: Implement Inventory and Energy Contracts

**Files:**
- Modify: `.../MachineEnergyStorage.java`
- Modify: `.../MachineBlockEntity.java`
- Modify: `.../MachineMenu.java`
- Modify: `engineering/tests/test_i9_machine_foundation.py`

**Interfaces:**
- `MachineEnergyStorage`: `receiveEnergy`, `extractEnergy`, `getEnergyStored`, `getMaxEnergyStored`, `canExtract`, `canReceive`, `consumeInternal(int)`, `setStoredEnergy(int)`.
- `MachineBlockEntity`: slot constants `INPUT_SLOT = 0`, `OUTPUT_SLOT = 1`; `getItemHandler()`; `getEnergyStorage()`.

- [ ] **Step 1: Add source-contract REDs for fixed constants and policies**

Require exact constants in `MachineBlockEntity`:

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

Use a direct `IEnergyStorage` implementation so external and internal mutation paths are explicit:

```java
public final class MachineEnergyStorage implements IEnergyStorage {
    private final int capacity;
    private final int maxReceive;
    private final Runnable onChanged;
    private int energy;

    public boolean consumeInternal(int amount) {
        if (amount <= 0 || this.energy < amount) return false;
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

    @Override
    public int extractEnergy(int maxExtract, boolean simulate) {
        return 0;
    }
}
```

`receiveEnergy` clamps to both `maxReceive` and remaining capacity and invokes `onChanged` only on real mutation.

- [ ] **Step 4: Implement two-slot item policy**

Back with one stable `ItemStackHandler(2)` whose `onContentsChanged` calls `setChanged()`. Output slot `1` returns `false` from `isItemValid`. Input validity delegates to `MachineBlockEntity#canSmelt(ItemStack)` when a server level is available; before level attachment it fails closed for automation insertion.

- [ ] **Step 5: Build GREEN**

Run structural tests and then:

```bash
cd .factory-ci/i9/generated
GRADLE_USER_HOME="$OLDPWD/.factory-ci/i9/gradle-home" ./gradlew clean test build --no-daemon
```

Rematerialize first if overlay files changed.

- [ ] **Step 6: Commit inventory/energy foundation**

```bash
git add engineering/tests/golden/i9-machine-foundation \
  engineering/tests/test_i9_machine_foundation.py
git commit -m "feat(engineering): implement I9 inventory and energy"
```

---

### Task 5: Implement Smelting Processing, Persistence, and Menu Sync

**Files:**
- Modify: `.../MachineBlockEntity.java`
- Modify: `.../MachineMenu.java`
- Modify: `engineering/tests/test_i9_machine_foundation.py`

**Interfaces:**
- `MachineBlockEntity.serverTick(Level, BlockPos, BlockState, MachineBlockEntity)` performs all machine mutation server-side.
- `ContainerData` indices: `0=progress`, `1=maxProgress`, `2=energy`.

- [ ] **Step 1: Add RED source contracts for recipe/persistence/sync**

Tests must require `SingleRecipeInput`, `RecipeType.SMELTING`, `getRecipeFor`, `assemble`, `loadAdditional`, `saveAdditional`, `ContainerData`, and exactly three data values.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

- [ ] **Step 3: Implement server-side recipe lookup**

Use target 1.21.1 API shape:

```java
private Optional<RecipeHolder<? extends AbstractCookingRecipe>> findRecipe(ServerLevel level) {
    ItemStack inputStack = this.items.getStackInSlot(INPUT_SLOT);
    if (inputStack.isEmpty()) return Optional.empty();
    return level.getRecipeManager().getRecipeFor(
        RecipeType.SMELTING,
        new SingleRecipeInput(inputStack),
        level
    );
}
```

Assemble with server registry access:

```java
ItemStack result = holder.value().assemble(new SingleRecipeInput(inputStack), level.registryAccess());
```

If NeoForge 21.1.248 compilation resolves the generic cooking recipe type differently, change only the concrete generic declaration while preserving `RecipeType.SMELTING`, `SingleRecipeInput`, `getRecipeFor`, and server-only lookup.

- [ ] **Step 4: Implement deterministic processing state machine**

`serverTick` must:

```java
if (!(level instanceof ServerLevel serverLevel)) return;
```

Then resolve recipe/result, verify output capacity, verify `ENERGY_PER_TICK`, consume exactly `20`, increment progress, complete at `100`, consume one input, insert one assembled result stack, reset to `0`, and reset progress to `0` whenever any precondition fails.

No input is consumed and no output is created before the completion tick.

- [ ] **Step 5: Implement persistence with bounds**

```java
@Override
protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
    super.saveAdditional(tag, registries);
    tag.put("Items", this.items.serializeNBT(registries));
    tag.putInt("Energy", this.energy.getEnergyStored());
    tag.putInt("Progress", this.progress);
}

@Override
protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
    super.loadAdditional(tag, registries);
    this.items.deserializeNBT(registries, tag.getCompound("Items"));
    this.energy.setStoredEnergy(Mth.clamp(tag.getInt("Energy"), 0, ENERGY_CAPACITY));
    this.progress = Mth.clamp(tag.getInt("Progress"), 0, MAX_PROGRESS - 1);
}
```

If the exact `ItemStackHandler` 21.1.248 serialization signature differs, compilation is the authority; keep HolderLookup-aware serialization and the same bounds contract.

- [ ] **Step 6: Implement three-value `ContainerData`**

`get(0)` returns progress, `get(1)` returns `MAX_PROGRESS`, `get(2)` returns current energy; `getCount()` returns `3`. Setter accepts synchronized client values without mutating server-authoritative energy storage outside the client menu instance.

- [ ] **Step 7: Build GREEN**

Rematerialize, then run:

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
- Modify: `.../MachineBlock.java`
- Modify: `.../MachineBlockEntity.java`
- Modify: `.../MachineMenu.java`
- Modify: `engineering/tests/test_i9_machine_foundation.py`

**Interfaces:**
- Client menu constructor: `MachineMenu(int containerId, Inventory playerInventory)`.
- Server menu constructor: `MachineMenu(int containerId, Inventory playerInventory, IItemHandler machineItems, ContainerData data, ContainerLevelAccess access)`.

- [ ] **Step 1: Add RED contracts for menu invariants**

Require `SlotItemHandler`, `SimpleContainerData(3)`, `checkContainerDataCount(data, 3)`, `ContainerLevelAccess.NULL`, `AbstractContainerMenu.stillValid`, and non-stub `quickMoveStack`.

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

Server constructor adds machine slots first (`0` input, `1` output), then 27 player inventory slots, then 9 hotbar slots, and finally `addDataSlots(data)`.

Output menu slot must override `mayPlace(ItemStack)` to return `false` even though the underlying handler already rejects insertion.

- [ ] **Step 4: Implement `stillValid` and `quickMoveStack`**

Use:

```java
@Override
public boolean stillValid(Player player) {
    return AbstractContainerMenu.stillValid(this.access, player, I9MachineContent.MACHINE_BLOCK.get());
}
```

Index contract is exactly:

```text
0 input
1 output
2..28 player inventory
29..37 hotbar
```

Shift-click from machine slots moves to `[2, 38)`; player inventory/hotbar moves only to input `[0, 1)`, never to output. If input rejects the stack, fall back between player inventory and hotbar without touching output.

- [ ] **Step 5: Implement menu opening and server ticker**

`MachineBlock#getTicker` returns the machine server ticker for the registered BE type. `getMenuProvider` creates a `SimpleMenuProvider` whose server menu receives the BE item handler, BE container data, and `ContainerLevelAccess.create(level, pos)`. `useWithoutItem` opens the menu only on the logical server and returns sided success.

- [ ] **Step 6: Target-exact build GREEN**

Rematerialize and run:

```bash
./gradlew clean test build --no-daemon
```

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
- `@GameTestHolder(I9MachineMod.MOD_ID)` owns all required tests.
- All seven tests are required and use the same `machine_test` structure template.

- [ ] **Step 1: Add GameTest surface RED**

Structural test requires seven method names:

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

Also require `@GameTestHolder(I9MachineMod.MOD_ID)` and the exact NBT resource path in the manifest.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

- [ ] **Step 3: Add deterministic minimal structure template**

Create a valid Minecraft structure NBT named `machine_test.nbt` under `data/i9_machine/structure`. The scene needs enough empty space for a single machine block placed by the test. The binary blob itself is the checked-in source authority; tests record its SHA-256 in `manifest.json` and fail on drift.

Manifest entry shape:

```json
{
  "path": "src/main/resources/data/i9_machine/structure/machine_test.nbt",
  "sha256": "COMPUTE_FROM_COMMITTED_BINARY_DURING_IMPLEMENTATION"
}
```

The implementation step must compute the real SHA-256 and replace `COMPUTE_FROM_COMMITTED_BINARY_DURING_IMPLEMENTATION` before the manifest is committed. This token is an explicit procedure marker in the plan, not allowed in production files.

- [ ] **Step 4: Implement capability GameTests**

Inventory test queries:

```java
IItemHandler items = helper.getLevel().getCapability(Capabilities.ItemHandler.BLOCK, absolutePos, null);
helper.assertTrue(items != null, "machine item capability missing");
```

Energy test queries `Capabilities.EnergyStorage.BLOCK`, verifies one receive call accepts at most `1_000`, total storage caps at `10_000`, and `extractEnergy(..., false)` returns `0`.

- [ ] **Step 5: Implement processing GameTests**

Use `Items.RAW_IRON` input and assert `Items.IRON_INGOT` output. Supply at least `2_000` energy. Successful processing must succeed only after the 100-tick contract has elapsed. Other tests assert insufficient energy, blocked output, and input invalidation do not consume/create items and reset progress to `0`.

- [ ] **Step 6: Implement persistence GameTest**

Exercise BlockEntity serialization/load using the target registry provider and assert inventory, energy, and progress are restored with bounds. Do not substitute a pure Java field-copy test.

- [ ] **Step 7: Run real GameTest Server GREEN**

From a freshly materialized project:

```bash
GRADLE_USER_HOME="$GITHUB_WORKSPACE/.factory-ci/i9/gradle-home" ./gradlew runGameTestServer --no-daemon
```

Expected: Gradle exits `0`; all seven required I9 tests pass. The GameTest server must not be counted as PASS if Gradle exits nonzero.

- [ ] **Step 8: Commit GameTests**

```bash
git add engineering/tests/golden/i9-machine-foundation \
  engineering/tests/test_i9_machine_foundation.py
git commit -m "test(engineering): prove I9 machine behavior with GameTests"
```

---

### Task 8: Prove I5 Dedicated-Server Compatibility

**Files:**
- Modify: `engineering/tests/test_i9_machine_foundation.py` only if a materialization assertion is needed.
- No change to `engineering/tooling/test-harness/run_test_harness.py` unless a reproducible I5 defect is found.

**Interfaces:**
- Consumes: I5 `run_harness(project_root)` with suites `test`, `runGameTestServer`, `runServer`.
- Produces: I5 manifest with `overall_state == "PASS"` for the materialized I9 project.

- [ ] **Step 1: Prepare only the controlled fixture EULA**

```bash
mkdir -p .factory-ci/i9/generated/run/server
printf 'eula=true\n' > .factory-ci/i9/generated/run/server/eula.txt
```

This is CI-fixture setup only; do not add a repository-wide EULA file.

- [ ] **Step 2: Run I5 harness**

```bash
python3 engineering/tooling/test-harness/run_test_harness.py \
  --project .factory-ci/i9/generated
```

Expected: `I5 test harness: PASS` and `build/i5-test-harness/test-manifest.json` records PASS for unit, gametest, and dedicated_server.

- [ ] **Step 3: If blocked, fix only the demonstrated owner**

A machine runtime defect is fixed in I9. A generic harness defect requires a separate I5 RED in `engineering/tests/test_i5_test_harness.py` before changing I5. Do not weaken timeouts, EULA checks, target identity, or server-ready detection to force PASS.

- [ ] **Step 4: Re-run I5 regression tests**

```bash
python3 -m unittest engineering/tests/test_i5_test_harness.py
```

Expected: PASS.

- [ ] **Step 5: Commit only if Task 8 required source changes**

```bash
git add engineering/tests/test_i9_machine_foundation.py engineering/tests/test_i5_test_harness.py engineering/tooling/test-harness/run_test_harness.py
git commit -m "fix(engineering): reconcile I9 with canonical test harness"
```

Skip this commit when Task 8 required no source change.

---

### Task 9: Add I9 CI and Complete Pre-Merge Gates

**Files:**
- Create: `.github/workflows/factory-engineering-i9-machine-foundation.yml`
- Modify: `.github/workflows/factory-sonar-ci.yml` only after a failing coverage gate proves it necessary.

**Interfaces:**
- Produces: branch/PR workflow named `Factory Engineering I9 Machine Foundation`.

- [ ] **Step 1: Write workflow contract before workflow implementation**

Add test assertions in `test_i9_machine_foundation.py` that the workflow exists, watches I9 plus consumed I3/I5 surfaces, uses Java 21, runs I9/I3/I5 regressions, materializes the Golden, executes `test build`, executes `runGameTestServer`, prepares only fixture EULA, runs I5 harness, and runs `git diff --check`.

- [ ] **Step 2: Run workflow-contract RED**

```bash
python3 -m unittest engineering/tests/test_i9_machine_foundation.py
```

Expected: FAIL because the workflow is absent.

- [ ] **Step 3: Implement workflow**

Required job sequence:

```yaml
name: Factory Engineering I9 Machine Foundation
permissions:
  contents: read
```

Steps must include:

```bash
python3 -m unittest \
  engineering/tests/test_i9_machine_foundation.py \
  engineering/tests/test_i3_mod_scaffolder.py \
  engineering/tests/test_i3_security_review.py \
  engineering/tests/test_i5_test_harness.py \
  engineering/tests/test_i8_feature_generator.py \
  engineering/tests/test_i8_feature_generator_neoforge.py
```

Then materialize into `.factory-ci/i9/generated`, run `./gradlew test build --no-daemon`, run `./gradlew runGameTestServer --no-daemon`, create only `.factory-ci/i9/generated/run/server/eula.txt`, execute I5 harness, and finish with `git diff --check`.

- [ ] **Step 4: Run complete local/static regression set**

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
./gradlew clean test build --no-daemon
./gradlew runGameTestServer --no-daemon
mkdir -p run/server
printf 'eula=true\n' > run/server/eula.txt
cd "$GITHUB_WORKSPACE"
python3 engineering/tooling/test-harness/run_test_harness.py --project .factory-ci/i9/generated
git diff --check
```

Record exact test counts, Gradle outcomes, GameTest result, and I5 manifest state in the PR body.

- [ ] **Step 6: Verify Sonar coverage registration**

Run the branch Sonar workflow. If Quality Gate fails because `materialize_i9.py` has no imported coverage, first add direct unit coverage from `test_i9_machine_foundation.py` to `.github/workflows/factory-sonar-ci.yml`, rerun, and require Quality Gate PASS. Do not change Sonar exclusions merely to hide new I9 production Python.

- [ ] **Step 7: Commit CI**

```bash
git add .github/workflows/factory-engineering-i9-machine-foundation.yml \
  .github/workflows/factory-sonar-ci.yml \
  engineering/tests/test_i9_machine_foundation.py
git commit -m "ci(engineering): gate I9 machine foundation"
```

Only stage `.github/workflows/factory-sonar-ci.yml` if it actually changed.

---

### Task 10: Review, PR, Merge, and Post-Merge Closure

**Files:**
- No implementation files unless review findings produce a new RED.
- `STATUS.md` is modified only after implementation PR post-merge evidence is complete, in a dedicated closeout PR.

**Interfaces:**
- Pre-merge evidence: all required branch/PR workflows terminal successful, Sonar Quality Gate PASS, review threads resolved.
- Post-merge evidence: all workflows for the merge SHA terminal successful and main Sonar Quality Gate PASS.

- [ ] **Step 1: Revalidate concurrency immediately before PR**

Confirm current `main`, open PRs, and branch base. If main moved, compare/rebase only after checking whether the new commits intersect I3/I5/I8/I9 surfaces.

- [ ] **Step 2: Open the implementation PR**

Title:

```text
feat(engineering): implement I9 machine foundation reference
```

Body must include RED evidence, final test counts, `test build`, `runGameTestServer`, I5 dedicated-server manifest, Sonar metrics, exact target, and explicit I10/I11/I12/I13/I14 non-goals.

- [ ] **Step 3: Resolve review findings through TDD**

For every correctness/security finding, add or tighten a regression first, record RED, implement minimal fix, rerun affected runtime gates, then resolve the thread. Do not resolve findings based only on code inspection.

- [ ] **Step 4: Final pre-merge verification**

Require:

```text
mergeable = true
open competing PRs = none affecting I9 surfaces
required workflows = terminal success
I9 workflow = success
Sonar Quality Gate = PASS
review threads = resolved
```

- [ ] **Step 5: Merge with expected head SHA**

Use regular merge unless repository policy observed at merge time requires another strategy. Preserve implementation history.

- [ ] **Step 6: Poll the merge SHA until every workflow is terminal**

Do not infer success from a subset. Require zero queued, zero in-progress, zero failure, zero cancelled, zero null conclusion, and inspect the main Sonar job log for `QUALITY GATE STATUS: PASSED`.

- [ ] **Step 7: Create dedicated STATUS closeout branch/PR**

Update only the current frontier/evidence fields needed to record:

```text
I9_STATE=PASS
NEXT_ACTION=BEGIN_I10_MULTIBLOCK_FOUNDATION
```

Also record implementation PR/head/merge SHA, RED runs, final branch/PR runtime gates, post-merge workflow count, and post-merge Sonar result truthfully.

- [ ] **Step 8: Merge STATUS closeout and verify its merge SHA**

Again require every post-closeout workflow terminal successful plus main Sonar PASS before calling I9 formally closed.
