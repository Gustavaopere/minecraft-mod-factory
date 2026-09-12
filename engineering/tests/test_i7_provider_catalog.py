import copy
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


def load_validator_module():
    spec = importlib.util.spec_from_file_location("i7_provider_catalog_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load I7 provider catalog validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    def test_validator_directly_accepts_canonical_catalog(self):
        self.require_production()
        validator = load_validator_module()
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual([], validator.validate_catalog(catalog, ROOT))

    def test_validator_accepts_a_fully_proven_provider_shape(self):
        self.require_production()
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            provider = self.make_valid_provider(workspace)
            catalog = self.make_catalog(validator, providers=[provider])
            self.assertEqual([], validator.validate_catalog(catalog, workspace))

    def test_validator_rejects_invalid_top_level_contracts(self):
        self.require_production()
        validator = load_validator_module()
        self.assertEqual(["catalog must be an object"], validator.validate_catalog([], ROOT))

        invalid = {
            "schema_version": 2,
            "target": {},
            "authority": {},
            "providers": "not-an-array",
            "state": "NOT_A_STATE",
        }
        errors = validator.validate_catalog(invalid, ROOT)
        self.assertContainsErrors(
            errors,
            "schema_version must be 1",
            "target must match Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21",
            "authority must reuse the canonical Engineering source/profile/compatibility authorities",
            "providers must be an array",
            "state is invalid",
        )

        pass_without_provider = self.make_catalog(validator, providers=[], state="PASS")
        self.assertIn("state PASS requires at least one provider", validator.validate_catalog(pass_without_provider, ROOT))

    def test_validator_rejects_duplicate_provider_ids(self):
        self.require_production()
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            provider = self.make_valid_provider(workspace)
            duplicate = copy.deepcopy(provider)
            errors = validator.validate_catalog(
                self.make_catalog(validator, providers=[provider, duplicate]),
                workspace,
            )
            self.assertIn("providers[1].mod_id duplicates sample_provider", errors)

    def test_validator_provider_fail_closed_matrix(self):
        self.require_production()
        validator = load_validator_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            valid = self.make_valid_provider(workspace)

            self.assertEqual(["providers[0] must be an object"], validator._validate_provider([], 0, workspace))
            missing = copy.deepcopy(valid)
            missing.pop("physical")
            self.assertIn("providers[0] missing fields: physical", validator._validate_provider(missing, 0, workspace))

            cases = []

            bad_identity = copy.deepcopy(valid)
            bad_identity["mod_id"] = "Bad Mod ID"
            cases.append((bad_identity, "providers[0].mod_id has invalid syntax"))

            bad_physical_type = copy.deepcopy(valid)
            bad_physical_type["physical"] = []
            cases.append((bad_physical_type, "providers[0].physical must be an object"))

            bad_physical_missing = copy.deepcopy(valid)
            bad_physical_missing["physical"] = {"version": "1.0.0"}
            cases.append((bad_physical_missing, "providers[0].physical missing fields:"))

            bad_physical_values = copy.deepcopy(valid)
            bad_physical_values["physical"] = {
                "version": "",
                "version_evidence": "INVENTED",
                "source_registry_id": "",
                "source_sha256": "ABC",
            }
            cases.extend(
                [
                    (bad_physical_values, "providers[0].physical.version must be non-empty"),
                    (bad_physical_values, "providers[0].physical.version_evidence is invalid"),
                    (bad_physical_values, "providers[0].physical.source_registry_id must be non-empty"),
                    (bad_physical_values, "providers[0].physical.source_sha256 must be lowercase SHA-256"),
                ]
            )

            bad_profile_syntax = copy.deepcopy(valid)
            bad_profile_syntax["dependency_profile"] = "../profile.json"
            cases.append((bad_profile_syntax, "providers[0].dependency_profile must use the canonical provider profile path"))

            missing_profile = copy.deepcopy(valid)
            missing_profile["dependency_profile"] = "engineering/catalog/providers/profiles/missing.json"
            cases.append((missing_profile, "providers[0].dependency_profile does not exist:"))

            bad_arrays = copy.deepcopy(valid)
            bad_arrays["docs"] = [""]
            bad_arrays["known_conflicts"] = None
            bad_arrays["integration_tests"] = [None]
            bad_arrays["jar_fingerprints"] = "not-an-array"
            cases.extend(
                [
                    (bad_arrays, "providers[0].docs must be an array of non-empty strings"),
                    (bad_arrays, "providers[0].known_conflicts must be an array of non-empty strings"),
                    (bad_arrays, "providers[0].integration_tests must be an array of non-empty strings"),
                    (bad_arrays, "providers[0].jar_fingerprints must be an array of non-empty strings"),
                ]
            )

            bad_surface_type = copy.deepcopy(valid)
            bad_surface_type["api_surface"] = "not-an-array"
            cases.append((bad_surface_type, "providers[0].api_surface must be an array"))

            bad_surface_object = copy.deepcopy(valid)
            bad_surface_object["api_surface"] = [None]
            cases.append((bad_surface_object, "providers[0].api_surface[0] must be an object"))

            missing_surface_fields = copy.deepcopy(valid)
            missing_surface_fields["api_surface"] = [{"surface_id": "api"}]
            cases.append((missing_surface_fields, "providers[0].api_surface[0] missing fields:"))

            bad_surface_values = copy.deepcopy(valid)
            bad_surface_values["api_surface"] = [
                {
                    "surface_id": "",
                    "proof_level": "P9 INVENTED",
                    "state": "NOT_A_STATE",
                    "evidence": [],
                }
            ]
            cases.extend(
                [
                    (bad_surface_values, "providers[0].api_surface[0].surface_id must be non-empty"),
                    (bad_surface_values, "providers[0].api_surface[0].proof_level is invalid"),
                    (bad_surface_values, "providers[0].api_surface[0].state is invalid"),
                    (bad_surface_values, "providers[0].api_surface[0].evidence must contain at least one item"),
                ]
            )

            bad_compatibility_type = copy.deepcopy(valid)
            bad_compatibility_type["compatibility"] = []
            cases.append((bad_compatibility_type, "providers[0].compatibility must be an object"))

            bad_compatibility_values = copy.deepcopy(valid)
            bad_compatibility_values["compatibility"] = {"state": "NOT_A_STATE", "evidence": []}
            cases.extend(
                [
                    (bad_compatibility_values, "providers[0].compatibility.state is invalid"),
                    (bad_compatibility_values, "providers[0].compatibility.evidence must contain at least one item"),
                ]
            )

            bad_scalar_values = copy.deepcopy(valid)
            bad_scalar_values["runtime_health"] = "NOT_A_STATE"
            bad_scalar_values["requirement"] = "MAYBE"
            bad_scalar_values["supported"] = "yes"
            bad_scalar_values["state"] = "NOT_A_STATE"
            cases.extend(
                [
                    (bad_scalar_values, "providers[0].runtime_health is invalid"),
                    (bad_scalar_values, "providers[0].requirement is invalid"),
                    (bad_scalar_values, "providers[0].supported must be boolean"),
                    (bad_scalar_values, "providers[0].state is invalid"),
                ]
            )

            unsupported_p0 = copy.deepcopy(valid)
            unsupported_p0["supported"] = True
            unsupported_p0["api_surface"][0]["proof_level"] = "P0 PRESENCE_ONLY"
            cases.append((unsupported_p0, "providers[0] cannot be supported with only P0 or no API proof"))

            for candidate, expected in cases:
                with self.subTest(expected=expected):
                    self.assertTrue(
                        any(expected in error for error in validator._validate_provider(candidate, 0, workspace)),
                        expected,
                    )

    def test_validator_workspace_path_and_cli_fail_closed(self):
        self.require_production()
        validator = load_validator_module()
        self.assertEqual(CATALOG.resolve(), validator._workspace_path(CATALOG.relative_to(ROOT).as_posix()))

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as external:
            external.write("{}")
            external_path = Path(external.name)
        try:
            with self.assertRaisesRegex(ValueError, "catalog must stay inside workspace"):
                validator._workspace_path(str(external_path))
        finally:
            external_path.unlink(missing_ok=True)

        with self.assertRaisesRegex(ValueError, "catalog must identify a file"):
            validator._workspace_path(".")

        with mock.patch.object(sys, "argv", [str(VALIDATOR), "--catalog", str(CATALOG)]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, validator.main())

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            dir=ROOT,
            delete=False,
        ) as malformed:
            malformed.write("{")
            malformed_path = Path(malformed.name)
        try:
            with mock.patch.object(sys, "argv", [str(VALIDATOR), "--catalog", str(malformed_path)]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(2, validator.main())
        finally:
            malformed_path.unlink(missing_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            dir=ROOT,
            delete=False,
        ) as invalid:
            invalid.write(json.dumps(self.make_catalog(validator, providers=[], state="PASS")))
            invalid_path = Path(invalid.name)
        try:
            with mock.patch.object(sys, "argv", [str(VALIDATOR), "--catalog", str(invalid_path)]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(1, validator.main())
        finally:
            invalid_path.unlink(missing_ok=True)

    def make_catalog(self, validator, providers, state="PENDING"):
        return {
            "schema_version": 1,
            "target": copy.deepcopy(validator.TARGET),
            "authority": copy.deepcopy(validator.AUTHORITY),
            "providers": providers,
            "state": state,
        }

    def make_valid_provider(self, workspace: Path):
        profile = "engineering/catalog/providers/profiles/sample_provider.json"
        profile_path = workspace / profile
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text("{}\n", encoding="utf-8")
        return {
            "mod_id": "sample_provider",
            "physical": {
                "version": "1.0.0",
                "version_evidence": "MOD_METADATA",
                "source_registry_id": "latest_physical_modlist_2026_09_09",
                "source_sha256": "0" * 64,
            },
            "dependency_profile": profile,
            "docs": ["https://example.invalid/provider-docs"],
            "api_surface": [
                {
                    "surface_id": "sample_api",
                    "proof_level": "P2 SOURCE/DOC_VERIFIED",
                    "state": "CONFIRMED",
                    "evidence": ["source audit"],
                }
            ],
            "compatibility": {
                "state": "CONFIRMED",
                "evidence": ["target audit"],
            },
            "runtime_health": "UNRESOLVED",
            "known_conflicts": ["none confirmed"],
            "requirement": "OPTIONAL",
            "integration_tests": ["contract test"],
            "jar_fingerprints": ["sha256:unresolved-test-fixture"],
            "supported": True,
            "state": "CONFIRMED",
        }

    def assertContainsErrors(self, errors, *expected):
        for message in expected:
            with self.subTest(error=message):
                self.assertIn(message, errors)


if __name__ == "__main__":
    unittest.main()
