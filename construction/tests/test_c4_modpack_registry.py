import copy
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_MODULE = ROOT / "construction" / "core" / "modpack_registry.py"
REGISTRY_SCHEMA = ROOT / "construction" / "schemas" / "modpack-registry.schema.json"
INDEX_SCRIPT = ROOT / "construction" / "scripts" / "index_modpack_jars.py"
I2_IMPORTER = ROOT / "engineering" / "tooling" / "import-physical-modlist.py"
WORKFLOW = ROOT / ".github" / "workflows" / "factory-construction-c4-modpack-registry.yml"

PHYSICAL_SAMPLE = """Mods count: 4

jar name | notes | mod id | mod name | mod version | mixin configs | modrinth hash | curseforge hash
---------+-------+--------+----------+-------------+---------------+---------------+----------------
neoforge-21.1.248 (modloader) | | neoforge | neoforge | neoforge-21.1.248 | | |
alpha-1.0.0.jar | | alpha | Alpha | 1.0.0 | alpha.mixins.json | aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | 111
    /META-INF/jarjar/metadata-only.jar | | | | | | |
opaque-top-level.jar | | | | | | |
beta-1.1.0.jar | | beta | Beta | 1.1.0 | | bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb | 222
"""


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ConstructionC4ModpackRegistryTest(unittest.TestCase):
    def require_registry(self):
        if not REGISTRY_MODULE.is_file():
            self.skipTest("C4 registry module intentionally absent during RED")
        return load_module(REGISTRY_MODULE, "construction_c4_registry")

    def physical_snapshot(self):
        i2 = load_module(I2_IMPORTER, "engineering_i2_modlist")
        return i2.parse_modlist_text(PHYSICAL_SAMPLE, captured_at="2026-09-09")

    def runtime_snapshot(self, source_sha256):
        return {
            "schema_version": 1,
            "captured_at": "2026-09-10T00:00:00Z",
            "physical_snapshot_sha256": source_sha256,
            "target": {
                "minecraft": "1.21.1",
                "loader": "neoforge",
                "loader_version": "21.1.248",
            },
            "blocks": [
                {
                    "id": "alpha:machine",
                    "states": [{"facing": "north"}, {"facing": "south"}],
                    "safety": "block_entity",
                },
                {
                    "id": "minecraft:stone",
                    "states": [{}],
                    "safety": "ordinary",
                },
            ],
        }

    def test_required_c4_files_exist(self):
        missing = [str(path.relative_to(ROOT)) for path in (REGISTRY_MODULE, REGISTRY_SCHEMA, INDEX_SCRIPT, WORKFLOW) if not path.is_file()]
        self.assertEqual([], missing, f"C4 RED: missing required files: {missing}")

    def test_engineering_i2_accepts_physical_rows_without_mod_id(self):
        i2 = load_module(I2_IMPORTER, "engineering_i2_blank_id")
        snapshot = self.physical_snapshot()
        self.assertEqual(4, snapshot["parsed_top_level_mods"])
        self.assertEqual(1, snapshot["parsed_nested_mods"])
        blank_entries = [entry for entry in snapshot["entries"] if not entry["mod_id"]]
        self.assertEqual(2, len(blank_entries))
        self.assertEqual([], i2.validate_normalized_snapshot(snapshot))
        providers = i2.build_provider_catalog(snapshot)
        self.assertNotIn("", providers)
        self.assertEqual({"alpha", "beta", "neoforge"}, set(providers))

    def test_registry_reuses_engineering_i2_authority(self):
        registry = self.require_registry()
        snapshot = self.physical_snapshot()
        normalized = registry.normalize_physical_snapshot(snapshot)
        self.assertEqual(snapshot["source_sha256"], normalized["source_sha256"])
        self.assertEqual(4, normalized["top_level_mods"])
        self.assertEqual(1, normalized["nested_mods"])
        self.assertEqual(3, normalized["provider_count"])
        self.assertEqual(2, normalized["unidentified_entries"])

    def test_static_jar_index_discovers_assets_and_nested_jars_without_extracting(self):
        registry = self.require_registry()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested_buffer = io.BytesIO()
            with zipfile.ZipFile(nested_buffer, "w", compression=zipfile.ZIP_DEFLATED) as nested:
                nested.writestr("META-INF/neoforge.mods.toml", '[[mods]]\nmodId="nestedlib"\nversion="1.0.0"\n')
                nested.writestr("assets/nestedlib/blockstates/gear.json", "{}")
                nested.writestr("assets/nestedlib/models/block/gear.json", "{}")
            jar_path = root / "alpha-1.0.0.jar"
            with zipfile.ZipFile(jar_path, "w", compression=zipfile.ZIP_DEFLATED) as jar:
                jar.writestr("META-INF/neoforge.mods.toml", '[[mods]]\nmodId="alpha"\nversion="1.0.0"\n')
                jar.writestr("assets/alpha/blockstates/machine.json", "{}")
                jar.writestr("assets/alpha/blockstates/ghost.json", "{}")
                jar.writestr("assets/alpha/models/block/machine.json", "{}")
                jar.writestr("assets/alpha/textures/block/machine.png", b"png")
                jar.writestr("META-INF/jarjar/nestedlib.jar", nested_buffer.getvalue())
            indexed = registry.index_jar_file(jar_path)
        self.assertEqual("alpha-1.0.0.jar", indexed["jar"])
        self.assertEqual(["alpha"], indexed["mod_ids"])
        self.assertEqual(["alpha:ghost", "alpha:machine"], indexed["blockstates"])
        self.assertEqual(["alpha:block/machine"], indexed["block_models"])
        self.assertEqual(["alpha:block/machine"], indexed["block_textures"])
        self.assertEqual(1, len(indexed["nested_jars"]))
        self.assertEqual(["nestedlib:gear"], indexed["nested_jars"][0]["blockstates"])

    def test_runtime_registry_wins_for_block_and_state_existence(self):
        registry = self.require_registry()
        physical = self.physical_snapshot()
        static_indexes = [{
            "jar": "alpha-1.0.0.jar",
            "sha256": "0" * 64,
            "mod_ids": ["alpha"],
            "blockstates": ["alpha:ghost", "alpha:machine"],
            "block_models": [],
            "block_textures": [],
            "nested_jars": [],
        }]
        runtime = self.runtime_snapshot(physical["source_sha256"])
        result = registry.build_modpack_registry(physical, static_indexes, runtime)
        blocks = {block["id"]: block for block in result["blocks"]}
        self.assertTrue(blocks["alpha:machine"]["available"])
        self.assertEqual("runtime_confirmed", blocks["alpha:machine"]["authority"])
        self.assertEqual([{"facing": "north"}, {"facing": "south"}], blocks["alpha:machine"]["states"])
        self.assertFalse(blocks["alpha:ghost"]["available"])
        self.assertEqual("static_only_unconfirmed", blocks["alpha:ghost"]["authority"])
        self.assertTrue(blocks["minecraft:stone"]["available"])
        self.assertEqual("runtime_confirmed", blocks["minecraft:stone"]["authority"])

    def test_runtime_snapshot_is_bound_to_exact_physical_snapshot_and_target(self):
        registry = self.require_registry()
        physical = self.physical_snapshot()
        runtime = self.runtime_snapshot("f" * 64)
        with self.assertRaisesRegex(ValueError, "physical snapshot"):
            registry.build_modpack_registry(physical, [], runtime)
        runtime = self.runtime_snapshot(physical["source_sha256"])
        runtime["target"]["loader_version"] = "21.1.247"
        with self.assertRaisesRegex(ValueError, "loader version"):
            registry.build_modpack_registry(physical, [], runtime)

    def test_registry_is_deterministic_and_fingerprinted(self):
        registry = self.require_registry()
        physical = self.physical_snapshot()
        runtime = self.runtime_snapshot(physical["source_sha256"])
        static_a = {
            "jar": "z.jar",
            "sha256": "1" * 64,
            "mod_ids": ["alpha"],
            "blockstates": ["alpha:machine", "alpha:ghost"],
            "block_models": [],
            "block_textures": [],
            "nested_jars": [],
        }
        static_b = {
            "jar": "a.jar",
            "sha256": "2" * 64,
            "mod_ids": ["beta"],
            "blockstates": ["beta:decor"],
            "block_models": [],
            "block_textures": [],
            "nested_jars": [],
        }
        first = registry.build_modpack_registry(physical, [static_a, static_b], runtime)
        second = registry.build_modpack_registry(physical, [static_b, static_a], runtime)
        self.assertEqual(first, second)
        self.assertRegex(first["content_sha256"], r"^[0-9a-f]{64}$")
        without_hash = dict(first)
        digest = without_hash.pop("content_sha256")
        expected = hashlib.sha256(registry.canonical_json_bytes(without_hash)).hexdigest()
        self.assertEqual(expected, digest)

    def canonical_composed_registry(self):
        registry = self.require_registry()
        physical = self.physical_snapshot()
        static_indexes = [{
            "jar": "alpha-1.0.0.jar",
            "sha256": "0" * 64,
            "mod_ids": ["alpha"],
            "blockstates": ["alpha:ghost", "alpha:machine"],
            "block_models": [],
            "block_textures": [],
            "nested_jars": [],
        }]
        runtime = self.runtime_snapshot(physical["source_sha256"])
        return registry, registry.build_modpack_registry(physical, static_indexes, runtime)

    def rehash_composed_registry(self, registry, document):
        payload = copy.deepcopy(document)
        payload.pop("content_sha256", None)
        document["content_sha256"] = hashlib.sha256(registry.canonical_json_bytes(payload)).hexdigest()

    def test_public_validator_accepts_canonical_composed_registry(self):
        registry, document = self.canonical_composed_registry()
        self.assertEqual([], registry.validate_modpack_registry(document))

    def test_public_validator_rejects_composed_contract_mutations(self):
        registry, canonical = self.canonical_composed_registry()

        def extra_top_level(document):
            document["unexpected"] = True

        def malformed_physical_sha(document):
            document["physical"]["source_sha256"] = "bad"
            document["runtime"]["physical_snapshot_sha256"] = "bad"

        def runtime_link_mismatch(document):
            document["runtime"]["physical_snapshot_sha256"] = "f" * 64

        def runtime_target_mismatch(document):
            document["runtime"]["target"]["minecraft"] = "1.21"

        def runtime_loader_version_mismatch(document):
            document["runtime"]["target"]["loader_version"] = "21.1.999"

        def negative_static_counter(document):
            document["static_index"]["jar_count"] = -1

        def noncanonical_block_order(document):
            document["blocks"] = list(reversed(document["blocks"]))

        def duplicate_block_id(document):
            document["blocks"].append(copy.deepcopy(document["blocks"][0]))

        def invalid_block_id(document):
            document["blocks"][0]["id"] = "INVALID"

        def invalid_authority(document):
            document["blocks"][1]["authority"] = "invented"

        def runtime_confirmed_unavailable(document):
            block = next(item for item in document["blocks"] if item["authority"] == "runtime_confirmed")
            block["available"] = False

        def static_only_available(document):
            block = next(item for item in document["blocks"] if item["authority"] == "static_only_unconfirmed")
            block["available"] = True

        def static_only_has_states(document):
            block = next(item for item in document["blocks"] if item["authority"] == "static_only_unconfirmed")
            block["states"] = [{}]

        def invalid_safety(document):
            document["blocks"][0]["safety"] = "invented"

        def empty_state_value(document):
            block = next(item for item in document["blocks"] if len(item["states"]) > 1)
            block["states"][0]["facing"] = ""

        def duplicate_state(document):
            block = next(item for item in document["blocks"] if len(item["states"]) > 1)
            block["states"].append(copy.deepcopy(block["states"][0]))

        def noncanonical_state_order(document):
            block = next(item for item in document["blocks"] if len(item["states"]) > 1)
            block["states"] = list(reversed(block["states"]))

        mutations = {
            "extra top-level field": extra_top_level,
            "malformed physical SHA": malformed_physical_sha,
            "runtime physical linkage": runtime_link_mismatch,
            "runtime Minecraft target": runtime_target_mismatch,
            "runtime loader version linkage": runtime_loader_version_mismatch,
            "negative static counter": negative_static_counter,
            "canonical block order": noncanonical_block_order,
            "duplicate block id": duplicate_block_id,
            "invalid block id": invalid_block_id,
            "invalid authority": invalid_authority,
            "runtime-confirmed availability": runtime_confirmed_unavailable,
            "static-only availability": static_only_available,
            "static-only states": static_only_has_states,
            "invalid safety": invalid_safety,
            "empty state value": empty_state_value,
            "duplicate state": duplicate_state,
            "canonical state order": noncanonical_state_order,
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                document = copy.deepcopy(canonical)
                mutate(document)
                self.rehash_composed_registry(registry, document)
                errors = registry.validate_modpack_registry(document)
                self.assertTrue(errors, f"mutation should fail closed: {label}")

    def test_public_validator_rejects_content_hash_tampering(self):
        registry, document = self.canonical_composed_registry()
        document["content_sha256"] = "f" * 64
        self.assertTrue(registry.validate_modpack_registry(document))

    def test_schema_and_workflow_encode_c4_boundary(self):
        self.require_registry()
        schema = json.loads(REGISTRY_SCHEMA.read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertTrue({"schema_version", "physical", "runtime", "blocks", "content_sha256"}.issubset(required))
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("feat/construction-c4-modpack-registry", workflow)
        self.assertIn("main", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("test_c4_modpack_registry.py", workflow)
        self.assertIn("test_i2_modlist_catalog.py", workflow)
        self.assertNotIn("write-all", workflow)


if __name__ == "__main__":
    unittest.main()
