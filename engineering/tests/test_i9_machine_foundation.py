import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = ROOT / "engineering" / "tooling" / "machine-foundation" / "materialize_i9.py"
OVERLAY = ROOT / "engineering" / "tests" / "golden" / "i9-machine-foundation" / "overlay"
MANIFEST = ROOT / "engineering" / "tests" / "golden" / "i9-machine-foundation" / "manifest.json"
MOD_SPEC = ROOT / "engineering" / "tests" / "fixtures" / "i9-machine-mod-spec.json"
SCAFFOLD_CONFIG = ROOT / "engineering" / "tests" / "fixtures" / "i9-machine-scaffold-config.json"
I1_VALIDATOR = ROOT / "engineering" / "tooling" / "validate-i1-foundation.py"
SCHEMA = ROOT / "engineering" / "schemas" / "mod-spec.schema.json"
I9_WORKFLOW = ROOT / ".github" / "workflows" / "factory-engineering-i9-machine-foundation.yml"
TARGET_BASELINE = ROOT / "engineering" / "contracts" / "target-baseline.json"
MACHINE_SOURCE_ROOT = OVERLAY / "src/main/java/dev/example/i9machine/machine"
MACHINE_SOURCES = {
    "I9MachineContent.java": ("DeferredRegister", "registerBlockEntity", "Capabilities.ItemHandler.BLOCK", "Capabilities.EnergyStorage.BLOCK"),
    "MachineBlock.java": ("BaseEntityBlock", "newBlockEntity"),
    "MachineEnergyStorage.java": ("IEnergyStorage",),
    "MachineBlockEntity.java": ("BlockEntity", "ItemStackHandler"),
    "MachineMenu.java": ("AbstractContainerMenu",),
}
GAMETEST_JAVA_RELATIVE = "src/main/java/dev/example/i9machine/gametest/I9MachineGameTests.java"
GAMETEST_STRUCTURE_RELATIVE = "src/main/resources/data/i9_machine/structure/machine_test.nbt"
GAMETEST_SOURCE = OVERLAY / GAMETEST_JAVA_RELATIVE
GAMETEST_STRUCTURE = OVERLAY / GAMETEST_STRUCTURE_RELATIVE
GAMETEST_METHODS = (
    "inventoryCapability",
    "energyCapability",
    "successfulProcessing",
    "insufficientEnergy",
    "blockedOutput",
    "persistence",
    "progressReset",
)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class I9MachineFoundationContractTest(unittest.TestCase):
    def test_i9_fixtures_target_exact_canonical_stack(self):
        mod_spec = json.loads(MOD_SPEC.read_text(encoding="utf-8"))
        config = json.loads(SCAFFOLD_CONFIG.read_text(encoding="utf-8"))
        baseline = json.loads(TARGET_BASELINE.read_text(encoding="utf-8"))["target"]
        expected_target = {key: value for key, value in baseline.items() if key != "neoforge_line"}
        self.assertEqual(expected_target, mod_spec["identity"]["target"])
        self.assertEqual("i9_machine", mod_spec["identity"]["mod_id"])
        self.assertEqual("dev.example.i9machine", config["java_package"])
        self.assertEqual("I9MachineMod", config["main_class"])
        self.assertEqual("I9MachineModClient", config["client_class"])

    def test_i9_mod_spec_is_valid_i1_contract(self):
        validator = load_module(I1_VALIDATOR, "i1_validator_for_i9")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        instance = json.loads(MOD_SPEC.read_text(encoding="utf-8"))
        self.assertEqual([], validator.validate_instance(schema, instance))

    def test_i9_materializer_overlay_and_manifest_exist(self):
        missing = [
            path.relative_to(ROOT).as_posix()
            for path in (MATERIALIZER, OVERLAY, MANIFEST)
            if not path.exists()
        ]
        self.assertEqual(
            [],
            missing,
            "I9 RED: composition authority is intentionally absent before GREEN",
        )

    def test_i9_registry_and_capability_sources_exist_with_required_contract_tokens(self):
        missing = []
        missing_tokens = []
        for filename, tokens in MACHINE_SOURCES.items():
            source = MACHINE_SOURCE_ROOT / filename
            if not source.is_file():
                missing.append(source.relative_to(ROOT).as_posix())
                continue
            text = source.read_text(encoding="utf-8")
            for token in tokens:
                if token not in text:
                    missing_tokens.append(f"{filename}:{token}")
        self.assertEqual([], missing, "I9 RED: registry/capability Java sources are missing")
        self.assertEqual([], missing_tokens, "I9 RED: registry/capability contract tokens are missing")

    def test_i9_inventory_and_energy_contract_tokens(self):
        block_entity = (MACHINE_SOURCE_ROOT / "MachineBlockEntity.java").read_text(encoding="utf-8")
        energy = (MACHINE_SOURCE_ROOT / "MachineEnergyStorage.java").read_text(encoding="utf-8")

        block_entity_tokens = (
            "public static final int INPUT_SLOT = 0;",
            "public static final int OUTPUT_SLOT = 1;",
            "public static final int ENERGY_PER_TICK = 20;",
            "public static final int MAX_PROGRESS = 100;",
            "new ItemStackHandler(2)",
            "onContentsChanged",
            "isItemValid",
            "RecipeType.SMELTING",
            "SingleRecipeInput",
            "getRecipeFor",
            "this::setChanged",
        )
        energy_tokens = (
            "public static final int ENERGY_CAPACITY = 10_000;",
            "public static final int MAX_RECEIVE = 1_000;",
            "private int energy;",
            "consumeInternal",
            "loadClamped",
            "onChanged.run()",
        )

        missing = [
            f"MachineBlockEntity.java:{token}"
            for token in block_entity_tokens
            if token not in block_entity
        ]
        missing.extend(
            f"MachineEnergyStorage.java:{token}"
            for token in energy_tokens
            if token not in energy
        )
        self.assertEqual([], missing, "I9 RED: inventory/energy contract is incomplete")

    def test_i9_processing_persistence_and_sync_contract_tokens(self):
        block_entity = (MACHINE_SOURCE_ROOT / "MachineBlockEntity.java").read_text(encoding="utf-8")
        required = (
            "private int progress;",
            "serverTick",
            "SingleRecipeInput",
            "RecipeType.SMELTING",
            "getRecipeFor",
            "assemble",
            "consumeInternal(ENERGY_PER_TICK)",
            "resetProgress",
            "loadAdditional",
            "saveAdditional",
            "serializeNBT",
            "deserializeNBT",
            "energyStorage.loadClamped",
            "ContainerData",
            "return 3;",
        )
        missing = [token for token in required if token not in block_entity]
        self.assertEqual([], missing, "I9 RED: processing/persistence/sync contract is incomplete")

    def test_i9_menu_and_block_interaction_contract_tokens(self):
        menu = (MACHINE_SOURCE_ROOT / "MachineMenu.java").read_text(encoding="utf-8")
        block = (MACHINE_SOURCE_ROOT / "MachineBlock.java").read_text(encoding="utf-8")

        menu_tokens = (
            "SlotItemHandler",
            "SimpleContainerData(3)",
            "checkContainerDataCount(data, 3)",
            "ContainerLevelAccess",
            "ContainerLevelAccess.NULL",
            "moveItemStackTo",
            "addDataSlots(data)",
            "MachineBlockEntity.INPUT_SLOT",
            "MachineBlockEntity.OUTPUT_SLOT",
            "I9MachineContent.MACHINE.get()",
        )
        block_tokens = (
            "openMenu",
            "getTicker",
            "createTickerHelper",
            "MachineBlockEntity::serverTick",
        )

        missing = [f"MachineMenu.java:{token}" for token in menu_tokens if token not in menu]
        missing.extend(f"MachineBlock.java:{token}" for token in block_tokens if token not in block)
        self.assertEqual([], missing, "I9 RED: menu/block interaction contract is incomplete")

    def test_i9_seven_required_gametests_and_structure_are_declared(self):
        missing_paths = [
            relative
            for relative, path in (
                (GAMETEST_JAVA_RELATIVE, GAMETEST_SOURCE),
                (GAMETEST_STRUCTURE_RELATIVE, GAMETEST_STRUCTURE),
            )
            if not path.is_file()
        ]
        self.assertEqual([], missing_paths, "I9 RED: required GameTest source authority is missing")

        source = GAMETEST_SOURCE.read_text(encoding="utf-8")
        required_tokens = (
            "@GameTestHolder(I9MachineMod.MOD_ID)",
            "@PrefixGameTestTemplate(false)",
            "@GameTest(",
            'template = "machine_test"',
            *tuple(f"void {method}(" for method in GAMETEST_METHODS),
        )
        missing_tokens = [token for token in required_tokens if token not in source]
        self.assertEqual([], missing_tokens, "I9 RED: seven required GameTests are incomplete")

        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        declared = {
            entry.get("source"): entry
            for entry in manifest["files"]
            if isinstance(entry, dict) and isinstance(entry.get("source"), str)
        }
        missing_manifest = [
            relative
            for relative in (GAMETEST_JAVA_RELATIVE, GAMETEST_STRUCTURE_RELATIVE)
            if relative not in declared
        ]
        self.assertEqual([], missing_manifest, "I9 RED: GameTest files are not composition-authorized")

        structure_entry = declared[GAMETEST_STRUCTURE_RELATIVE]
        actual_sha256 = hashlib.sha256(GAMETEST_STRUCTURE.read_bytes()).hexdigest()
        self.assertEqual(
            actual_sha256,
            structure_entry.get("sha256"),
            "I9 RED: structure source SHA-256 is not pinned in the manifest",
        )

    def test_i9_workflow_runs_authoritative_gametest_server_gate(self):
        workflow = I9_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "./gradlew runGameTestServer --no-daemon",
            workflow,
            "I9 RED: permanent workflow must execute the target-exact GameTest server",
        )
        self.assertNotIn(
            "setForceExit",
            workflow,
            "I9 workflow must not reintroduce the unsupported NeoGradle setForceExit directive",
        )

    def test_i9_workflow_runs_final_regressions_and_i5_harness(self):
        workflow = I9_WORKFLOW.read_text(encoding="utf-8")
        required = (
            "engineering/tests/test_i3_mod_scaffolder.py",
            "engineering/tests/test_i3_security_review.py",
            "engineering/tests/test_i4_engineering_validators.py",
            "engineering/tests/test_i5_test_harness.py",
            "engineering/tests/test_i8_feature_generator.py",
            "engineering/tests/test_i8_feature_generator_neoforge.py",
            "engineering/tests/test_i9_machine_foundation.py",
            "engineering/tests/test_i9_machine_foundation_composition.py",
            "mkdir -p .factory-ci/i9/generated/run/server",
            "printf 'eula=true\\n' > .factory-ci/i9/generated/run/server/eula.txt",
            "python3 engineering/tooling/test-harness/run_test_harness.py",
            "--project .factory-ci/i9/generated",
            ".factory-ci/i9/generated/build/i5-test-harness/test-manifest.json",
            "manifest['overall_state'] == 'PASS'",
            "'unit': 'PASS'",
            "'gametest': 'PASS'",
            "'dedicated_server': 'PASS'",
        )
        missing = [token for token in required if token not in workflow]
        self.assertEqual(
            [],
            missing,
            "I9 RED: permanent workflow lacks final regressions or canonical I5 harness proof",
        )


if __name__ == "__main__":
    unittest.main()
