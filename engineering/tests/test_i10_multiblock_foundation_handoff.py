import contextlib
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART_ROOT = ROOT / "art/golden-samples/i10-multiblock-visual"
MODELS_ROOT = ART_ROOT / "models"
HANDOFF = ROOT / "engineering/tests/golden/i10-multiblock-foundation/asset-handoff.json"
OVERLAY = ROOT / "engineering/tests/golden/i10-multiblock-foundation/overlay"
MATERIALIZER = ROOT / "engineering/tooling/multiblock-foundation/materialize_i10.py"
I6_VALIDATOR = ROOT / "engineering/tooling/asset-handoff/validate_asset_handoff.py"
I6_SCHEMA = ROOT / "engineering/schemas/asset-handoff.schema.json"

EXPECTED_ARTIFACTS = {
    "controller_unformed": (
        "art/golden-samples/i10-multiblock-visual/models/controller_unformed.json",
        "src/main/resources/assets/i10_multiblock/models/block/controller_unformed.json",
    ),
    "controller_formed": (
        "art/golden-samples/i10-multiblock-visual/models/controller_formed.json",
        "src/main/resources/assets/i10_multiblock/models/block/controller_formed.json",
    ),
    "casing": (
        "art/golden-samples/i10-multiblock-visual/models/casing.json",
        "src/main/resources/assets/i10_multiblock/models/block/casing.json",
    ),
    "io_port_unformed": (
        "art/golden-samples/i10-multiblock-visual/models/io_port_unformed.json",
        "src/main/resources/assets/i10_multiblock/models/block/io_port_unformed.json",
    ),
    "io_port_formed": (
        "art/golden-samples/i10-multiblock-visual/models/io_port_formed.json",
        "src/main/resources/assets/i10_multiblock/models/block/io_port_formed.json",
    ),
}

EXPECTED_VISUAL_INPUTS = {
    "formed": {
        "type": "bool",
        "runtime_binding": (
            "dev.example.i10multiblock.multiblock.MultiblockControllerBlock.FORMED;"
            "dev.example.i10multiblock.multiblock.MultiblockPortBlock.FORMED"
        ),
    },
    "facing": {
        "type": "string",
        "runtime_binding": (
            "dev.example.i10multiblock.multiblock.MultiblockControllerBlock.FACING;"
            "dev.example.i10multiblock.multiblock.MultiblockPortBlock.FACING"
        ),
    },
}

BLOCKSTATES = {
    "multiblock_controller.json": ("controller_unformed", "controller_formed"),
    "multiblock_io_port.json": ("io_port_unformed", "io_port_formed"),
}


def load_module(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"I10 RED: required module is missing: {path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_handoff():
    if not HANDOFF.is_file():
        raise AssertionError("I10 RED: asset-handoff.json is missing")
    return json.loads(HANDOFF.read_text(encoding="utf-8"))


class I10AssetHandoffContract(unittest.TestCase):
    def test_repo_textura_source_surface_exists(self):
        self.assertTrue((ART_ROOT / "README.md").is_file(), "I10 RED: Repo Textura I10 README is missing")
        for asset_id, (source_path, _delivery_path) in EXPECTED_ARTIFACTS.items():
            with self.subTest(asset_id=asset_id):
                source = ROOT / source_path
                self.assertTrue(source.is_file(), f"I10 RED: source-native model missing: {source_path}")
                value = json.loads(source.read_text(encoding="utf-8"))
                self.assertIsInstance(value, dict)
                self.assertIn("parent", value, f"I10 RED: {source_path} must be a native Java block model")

    def test_handoff_is_provider_neutral_and_pending(self):
        handoff = load_handoff()
        self.assertEqual(2, handoff.get("schema_version"))
        self.assertEqual("i10_multiblock", handoff.get("mod_id"))
        self.assertEqual("Repo Textura", handoff.get("source_authority"))
        self.assertEqual("https://github.com/Gustavaopere/minecraft-mod-factory", handoff.get("source_repository"))
        self.assertEqual("I10 multiblock foundation Golden", handoff.get("runtime_authority"))
        self.assertEqual([], handoff.get("provider_profiles"))
        self.assertEqual([], handoff.get("provider_bindings"))
        self.assertEqual("PENDING", handoff.get("state"))
        serialized = json.dumps(handoff, sort_keys=True).lower()
        self.assertNotIn("java_block_item", serialized)
        self.assertNotIn("geckolib", serialized)
        self.assertNotIn("azurelib", serialized)

    def test_handoff_visual_inputs_bind_real_runtime_properties(self):
        handoff = load_handoff()
        actual = {
            item["name"]: {
                "type": item["type"],
                "runtime_binding": item["runtime_binding"],
            }
            for item in handoff.get("visual_inputs", [])
        }
        self.assertEqual(EXPECTED_VISUAL_INPUTS, actual)
        for item in handoff["visual_inputs"]:
            self.assertTrue(item.get("evidence"), f"I10 RED: visual input {item['name']} lacks evidence")

    def test_handoff_artifacts_preserve_source_bytes_and_pending_visual_qa(self):
        handoff = load_handoff()
        artifacts = {item["asset_id"]: item for item in handoff.get("artifacts", [])}
        self.assertEqual(set(EXPECTED_ARTIFACTS), set(artifacts))
        for asset_id, (source_path, delivery_path) in EXPECTED_ARTIFACTS.items():
            with self.subTest(asset_id=asset_id):
                artifact = artifacts[asset_id]
                self.assertEqual("UNRESOLVED", artifact.get("provider_profile"))
                self.assertEqual(source_path, artifact.get("source_path"))
                self.assertEqual(delivery_path, artifact.get("delivery_path"))
                self.assertEqual(".json", artifact.get("source_format"))
                self.assertEqual(".json", artifact.get("delivery_format"))
                source = ROOT / source_path
                self.assertTrue(source.is_file(), f"I10 RED: source missing: {source_path}")
                expected_hash = sha256(source)
                self.assertEqual(expected_hash, artifact.get("source_sha256"))
                self.assertEqual(expected_hash, artifact.get("delivery_sha256"))
                conversion = artifact.get("conversion", {})
                self.assertFalse(conversion.get("performed"))
                self.assertEqual(".json", conversion.get("from_format"))
                self.assertEqual(".json", conversion.get("to_format"))
                self.assertIn(conversion.get("state"), {"CONFIRMED", "PASS"})
                self.assertEqual("PENDING", artifact.get("qa", {}).get("state"))
                self.assertEqual("IMPLEMENTED", artifact.get("state"))

    def test_engineering_blockstates_bind_formed_and_facing_without_reauthoring_models(self):
        blockstate_root = OVERLAY / "src/main/resources/assets/i10_multiblock/blockstates"
        expected_facings = {"north", "east", "south", "west"}
        for filename, models in BLOCKSTATES.items():
            with self.subTest(filename=filename):
                path = blockstate_root / filename
                self.assertTrue(path.is_file(), f"I10 RED: runtime blockstate wiring missing: {filename}")
                variants = json.loads(path.read_text(encoding="utf-8")).get("variants", {})
                expected_keys = {
                    f"facing={facing},formed={str(formed).lower()}"
                    for facing in expected_facings
                    for formed in (False, True)
                }
                self.assertEqual(expected_keys, set(variants))
                referenced = {entry["model"].split(":block/", 1)[-1] for entry in variants.values()}
                self.assertEqual(set(models), referenced)
        casing = blockstate_root / "multiblock_casing.json"
        self.assertTrue(casing.is_file(), "I10 RED: casing blockstate wiring missing")
        self.assertEqual(
            {"": {"model": "i10_multiblock:block/casing"}},
            json.loads(casing.read_text(encoding="utf-8")).get("variants"),
        )

    def test_fresh_materialization_passes_canonical_i6_validation_and_byte_exact_delivery(self):
        materializer = load_module(MATERIALIZER, "i10_task6_materializer")
        validator = load_module(I6_VALIDATOR, "i10_task6_i6_validator")
        schema = json.loads(I6_SCHEMA.read_text(encoding="utf-8"))
        handoff = load_handoff()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with contextlib.chdir(workspace):
                generated = materializer.materialize_i10("generated")
            errors = validator.validate_manifest_data(
                handoff,
                schema=schema,
                source_root=ROOT,
                runtime_root=generated,
            )
            self.assertEqual([], errors, "I10 RED: canonical I6 validation must pass")
            for artifact in handoff["artifacts"]:
                source = ROOT / artifact["source_path"]
                delivery = generated / artifact["delivery_path"]
                self.assertTrue(delivery.is_file(), f"I10 RED: delivery missing: {artifact['delivery_path']}")
                self.assertEqual(source.read_bytes(), delivery.read_bytes())


if __name__ == "__main__":
    unittest.main()
