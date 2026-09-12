import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "engineering" / "schemas" / "provider-catalog.schema.json"
CATALOG = ROOT / "engineering" / "catalog" / "providers" / "PROVIDER-CATALOG.json"
VALIDATOR = ROOT / "engineering" / "tooling" / "provider-catalog" / "validate_provider_catalog.py"
DEPENDENCY_SCHEMA = ROOT / "engineering" / "schemas" / "dependency-profile.schema.json"
COMPATIBILITY_SCHEMA = ROOT / "engineering" / "schemas" / "compatibility-matrix.schema.json"
SOURCE_REGISTRY = ROOT / "engineering" / "catalog" / "sources" / "SOURCE-REGISTRY.json"

CANONICAL_PROOF_LEVELS = [
    "P0 PRESENCE_ONLY",
    "P1 METADATA_VERIFIED",
    "P2 SOURCE/DOC_VERIFIED",
    "P3 COMPILE_PROVEN",
    "P4 RUNTIME_SMOKE",
    "P5 INTEGRATION_TESTED",
    "P6 MULTIPLAYER/PERF_PROVEN",
]


class I7ProviderCatalogContractTest(unittest.TestCase):
    def production_paths(self):
        return (SCHEMA, CATALOG, VALIDATOR)

    def require_production(self):
        missing = [path.relative_to(ROOT).as_posix() for path in self.production_paths() if not path.is_file()]
        if missing:
            self.skipTest("I7 production artifacts intentionally absent during RED: " + ", ".join(missing))

    def test_i7_production_artifacts_exist(self):
        for path in self.production_paths():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertTrue(
                    path.is_file(),
                    f"I7 RED: production artifact {path.relative_to(ROOT).as_posix()} is missing",
                )

    def test_existing_authority_inputs_remain_available(self):
        for path in (DEPENDENCY_SCHEMA, COMPATIBILITY_SCHEMA, SOURCE_REGISTRY):
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertTrue(path.is_file())

    def test_schema_exposes_exact_canonical_proof_levels(self):
        self.require_production()
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        proof_levels = schema.get("$defs", {}).get("proof_level", {}).get("enum")
        self.assertEqual(CANONICAL_PROOF_LEVELS, proof_levels)

    def test_catalog_reuses_existing_engineering_authorities(self):
        self.require_production()
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        authority = catalog.get("authority", {})
        self.assertEqual(
            "engineering/catalog/sources/SOURCE-REGISTRY.json",
            authority.get("source_registry"),
        )
        self.assertEqual(
            "engineering/tooling/import-physical-modlist.py",
            authority.get("physical_catalog_builder"),
        )
        self.assertEqual(
            "engineering/schemas/dependency-profile.schema.json",
            authority.get("dependency_profile_schema"),
        )
        self.assertEqual(
            "engineering/schemas/compatibility-matrix.schema.json",
            authority.get("compatibility_matrix_schema"),
        )

    def test_catalog_target_is_exact_factory_target(self):
        self.require_production()
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "minecraft": "1.21.1",
                "loader": "neoforge",
                "neoforge": "21.1.248",
                "java": 21,
            },
            catalog.get("target"),
        )

    def test_validator_accepts_canonical_catalog(self):
        self.require_production()
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR), "--catalog", str(CATALOG)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
