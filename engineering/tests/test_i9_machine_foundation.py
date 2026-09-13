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
MACHINE_SOURCE_ROOT = OVERLAY / "src/main/java/dev/example/i9machine/machine"
MACHINE_SOURCES = {
    "I9MachineContent.java": ("DeferredRegister", "registerBlockEntity", "Capabilities.ItemHandler.BLOCK", "Capabilities.EnergyStorage.BLOCK"),
    "MachineBlock.java": ("BaseEntityBlock", "newBlockEntity"),
    "MachineEnergyStorage.java": ("IEnergyStorage",),
    "MachineBlockEntity.java": ("BlockEntity", "ItemStackHandler"),
    "MachineMenu.java": ("AbstractContainerMenu",),
}


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
        self.assertEqual(
            {
                "minecraft": "1.21.1",
                "loader": "neoforge",
                "neoforge": "21.1.248",
                "java": 21,
            },
            mod_spec["identity"]["target"],
        )
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


if __name__ == "__main__":
    unittest.main()
