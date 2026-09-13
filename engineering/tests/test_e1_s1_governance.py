import hashlib
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

ENGINEERING_PLAN = "plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md"
ART_PLAN = "plans/textura/PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md"

EXPECTED_FILES = [
    "engineering/README.md",
    "engineering/REPO-ROUTING.md",
    "engineering/AGENT-WORKFLOW.md",
    "engineering/DIAGNOSTICS.md",
    "engineering/TESTING.md",
    "engineering/catalog/sources/SOURCE-REGISTRY.json",
    "engineering/tooling/validate-e1-s1-governance.py",
    "skills/README.md",
    "skills/ROUTER.md",
    "skills/VERSION-AUTHORITY.md",
    "skills/USER-GUIDED-WORKFLOW.md",
    ENGINEERING_PLAN,
    ART_PLAN,
]


class GovernanceMigrationTests(unittest.TestCase):
    def test_expected_governance_files_exist(self):
        missing = [path for path in EXPECTED_FILES if not (ROOT / path).is_file()]
        self.assertEqual([], missing, f"missing E1/S1 files: {missing}")

    def test_source_registry_binds_both_factory_authorities(self):
        registry_path = ROOT / "engineering/catalog/sources/SOURCE-REGISTRY.json"
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        by_id = {entry["source_id"]: entry for entry in data["sources"]}

        control = by_id["integration_control_plane"]
        self.assertEqual("CONFIRMED", control["state"])
        self.assertEqual(
            "Gustavaopere/minecraft-mod-factory",
            control["locator"]["repository_full_name"],
        )
        self.assertEqual("engineering/", control["locator"]["authority_root"])

        art = by_id["repo_textura"]
        self.assertEqual("CONFIRMED", art["state"])
        self.assertEqual(
            "Gustavaopere/minecraft-mod-factory",
            art["locator"]["repository_full_name"],
        )
        self.assertEqual("art/", art["locator"]["authority_root"])

    def test_source_registry_binds_canonical_plans(self):
        registry_path = ROOT / "engineering/catalog/sources/SOURCE-REGISTRY.json"
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        by_id = {entry["source_id"]: entry for entry in data["sources"]}

        expected = {
            "mod_engineering_plan_v1_1": ENGINEERING_PLAN,
            "repo_textura_plan_v5_1": ART_PLAN,
        }
        for source_id, rel in expected.items():
            source = by_id[source_id]
            self.assertEqual("CONFIRMED", source["state"])
            self.assertEqual(rel, source["locator"]["path"])
            actual_hash = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            self.assertEqual(actual_hash, source["locator"]["sha256"])

    def test_version_authority_matches_physical_baseline(self):
        text = (ROOT / "skills/VERSION-AUTHORITY.md").read_text(encoding="utf-8")
        self.assertIn("Minecraft: **1.21.1**", text)
        self.assertIn("NeoForge: **21.1.248**", text)
        self.assertIn("Java: **21**", text)
        self.assertIn("modlist física", text)

    def test_routing_keeps_runtime_outside_factory(self):
        text = (ROOT / "engineering/REPO-ROUTING.md").read_text(encoding="utf-8")
        self.assertIn("Gustavaopere/minecraft-mod-factory", text)
        self.assertIn("runtime authority", text)
        self.assertIn("art/", text)
        self.assertNotIn(
            "Gustavaopere/neoforge-rpg-skilltree` is the canonical integration/control-plane repository",
            text,
        )

    def test_validator_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "engineering/tooling/validate-e1-s1-governance.py")],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("E1/S1 governance validation: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
