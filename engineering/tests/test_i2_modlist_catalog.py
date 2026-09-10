import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "engineering" / "tooling" / "import-physical-modlist.py"
FIXTURE = ROOT / "engineering" / "tests" / "fixtures" / "modlist-i2-sample.txt"


def load_importer():
    spec = importlib.util.spec_from_file_location("i2_modlist", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class I2PhysicalModlistCatalogTest(unittest.TestCase):
    def require_importer(self):
        if not SCRIPT.is_file():
            self.skipTest("production importer is intentionally absent during I2 RED")
        return load_importer()

    def parse_fixture(self, captured_at="2026-09-09"):
        module = self.require_importer()
        return module.parse_modlist_text(FIXTURE.read_text(encoding="utf-8"), captured_at=captured_at)

    def test_importer_production_entrypoint_exists(self):
        self.assertTrue(
            SCRIPT.is_file(),
            "I2 RED: production importer engineering/tooling/import-physical-modlist.py is missing",
        )

    def test_parser_preserves_top_level_and_nested_hierarchy(self):
        snapshot = self.parse_fixture()
        self.assertEqual(3, snapshot["declared_top_level_mods"])
        self.assertEqual(3, snapshot["parsed_top_level_mods"])
        self.assertEqual(2, snapshot["parsed_nested_mods"])
        by_mod_id = {entry["mod_id"]: entry for entry in snapshot["entries"]}
        self.assertTrue(by_mod_id["alpha"]["top_level"])
        self.assertEqual(0, by_mod_id["alpha"]["nesting_depth"])
        self.assertFalse(by_mod_id["shared"]["top_level"])
        self.assertEqual(1, by_mod_id["shared"]["nesting_depth"])
        self.assertEqual("alpha-1.0.0.jar", by_mod_id["shared"]["parent_jar"])
        self.assertEqual(1, by_mod_id["shared"]["parent_ordinal"])
        self.assertEqual(["alpha-1.0.0.jar"], by_mod_id["shared"]["container_path"])
        self.assertEqual(2, by_mod_id["deep"]["nesting_depth"])
        self.assertEqual("/META-INF/jarjar/shared-2.0.0.jar", by_mod_id["deep"]["parent_jar"])
        self.assertEqual(2, by_mod_id["deep"]["parent_ordinal"])
        self.assertEqual(
            ["alpha-1.0.0.jar", "/META-INF/jarjar/shared-2.0.0.jar"],
            by_mod_id["deep"]["container_path"],
        )

    def test_parser_preserves_provider_metadata_and_hashes(self):
        snapshot = self.parse_fixture()
        beta = next(entry for entry in snapshot["entries"] if entry["mod_id"] == "beta")
        self.assertEqual("MCreator mod", beta["notes"])
        self.assertEqual("1.1.0", beta["version"])
        self.assertEqual("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", beta["modrinth_hash"])
        self.assertEqual("222", beta["curseforge_hash"])
        self.assertEqual([], beta["mixin_configs"])

    def test_persisted_snapshot_keeps_physical_evidence_columns(self):
        module = self.require_importer()
        persisted = module.build_persisted_snapshot(self.parse_fixture())
        beta = next(entry for entry in persisted["entries"] if entry["mod_id"] == "beta")
        self.assertEqual("MCreator mod", beta["notes"])
        self.assertEqual("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", beta["modrinth_hash"])
        self.assertEqual("222", beta["curseforge_hash"])
        self.assertEqual([], beta["mixin_configs"])
        self.assertIn("parent_ordinal", beta)
        self.assertIn("container_path", beta)

    def test_parser_fails_closed_on_declared_count_mismatch(self):
        module = self.require_importer()
        text = FIXTURE.read_text(encoding="utf-8").replace("Mods count: 3", "Mods count: 4", 1)
        with self.assertRaisesRegex(ValueError, "declared top-level mod count"):
            module.parse_modlist_text(text, captured_at="2026-09-09")

    def test_provider_catalog_does_not_collapse_nested_occurrences(self):
        module = self.require_importer()
        providers = module.build_provider_catalog(self.parse_fixture())
        shared = providers["shared"]
        self.assertEqual(["2.0.0"], shared["versions"])
        self.assertEqual(0, shared["top_level_occurrences"])
        self.assertEqual(1, shared["nested_occurrences"])
        occurrence = shared["occurrences"][0]
        self.assertEqual(1, occurrence["parent_ordinal"])
        self.assertEqual(["alpha-1.0.0.jar"], occurrence["container_path"])

    def test_version_drift_reports_added_removed_version_and_topology_changes(self):
        module = self.require_importer()
        before = self.parse_fixture("2026-09-08")
        after = json.loads(json.dumps(before))
        after["captured_at"] = "2026-09-09"
        for entry in after["entries"]:
            if entry["mod_id"] == "alpha":
                entry["version"] = "1.1.0"
            if entry["mod_id"] == "shared":
                entry["parent_jar"] = "beta-1.1.0.jar"
                entry["parent_ordinal"] = 4
                entry["container_path"] = ["beta-1.1.0.jar"]
        after["entries"] = [entry for entry in after["entries"] if entry["mod_id"] != "deep"]
        after["entries"].append({
            "ordinal": len(after["entries"]),
            "jar": "/META-INF/jarjar/gamma-1.0.0.jar",
            "notes": "",
            "mod_id": "gamma",
            "mod_name": "Gamma",
            "version": "1.0.0",
            "mixin_configs": [],
            "modrinth_hash": "",
            "curseforge_hash": "",
            "top_level": False,
            "nesting_depth": 1,
            "parent_jar": "beta-1.1.0.jar",
            "parent_ordinal": 4,
            "container_path": ["beta-1.1.0.jar"],
        })
        drift = module.compare_snapshots(before, after)
        self.assertIn("gamma", drift["added_mod_ids"])
        self.assertIn("deep", drift["removed_mod_ids"])
        self.assertIn("alpha", drift["version_changed_mod_ids"])
        self.assertIn("shared", drift["topology_changed_mod_ids"])

    def test_fixture_round_trips_through_sharded_snapshot_and_provider_catalog(self):
        module = self.require_importer()
        snapshot = self.parse_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_path = root / "snapshot.json"
            provider_path = root / "providers.json"
            manifest = module.write_persisted_snapshot(snapshot, snapshot_path, shard_size=2)
            self.assertEqual(len(snapshot["entries"]), manifest["entry_count"])
            self.assertGreater(len(manifest["entry_shards"]), 1)
            loaded = module.load_persisted_snapshot(snapshot_path)
            self.assertEqual(snapshot, loaded)
            providers = module.build_persisted_provider_catalog(loaded)
            provider_path.write_text(json.dumps(providers), encoding="utf-8")
            self.assertEqual([], module.validate_persisted_provider_catalog(loaded, providers))
            self.assertEqual(len(module.build_provider_catalog(loaded)), providers["provider_count"])


if __name__ == "__main__":
    unittest.main()
