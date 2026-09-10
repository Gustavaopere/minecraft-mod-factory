import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENG = ROOT / "engineering"
SCHEMA_PATH = ENG / "schemas" / "asset-handoff.schema.json"
EXAMPLE_PATH = ENG / "examples" / "asset-handoff.example.json"
SCRIPT = ENG / "tooling" / "asset-handoff" / "validate_asset_handoff.py"
SCRIPT_EXISTS = SCRIPT.is_file()
FACTORY_REPOSITORY = "Gustavaopere/minecraft-mod-factory"


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_validator():
    spec = importlib.util.spec_from_file_location("i6_asset_handoff", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _run_cli(workspace: Path, manifest: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(manifest), *extra],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=10,
        check=False,
    )


class I6AssetHandoffContractTest(unittest.TestCase):
    def test_production_validator_exists(self):
        self.assertTrue(SCRIPT.is_file(), f"missing production validator: {SCRIPT}")

    def test_schema_exposes_i6_contract_fields(self):
        schema = _load_json(SCHEMA_PATH)
        self.assertEqual(2, schema["properties"]["schema_version"]["const"])
        required = set(schema["required"])
        for field in ("source_repository", "source_revision", "provider_bindings", "visual_inputs"):
            self.assertIn(field, required)
        artifact_required = set(schema["properties"]["artifacts"]["items"]["required"])
        for field in (
            "provider_profile",
            "source_sha256",
            "delivery_sha256",
            "required_bones",
            "required_anchors",
            "required_clips",
            "textures",
            "qa",
        ):
            self.assertIn(field, artifact_required)

    def test_canonical_example_uses_factory_art_authority_but_stays_fail_closed_until_f4(self):
        example = _load_json(EXAMPLE_PATH)
        self.assertEqual("Repo Textura", example.get("source_authority"))
        self.assertEqual(FACTORY_REPOSITORY, example.get("source_repository"))
        self.assertEqual("UNRESOLVED", example.get("source_revision"))
        self.assertEqual("UNRESOLVED", example.get("runtime_authority"))
        self.assertNotEqual("PASS", example["state"])

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_fully_resolved_fixture_passes_schema_semantics_hashes_and_revision(self):
        validator = _load_validator()
        with tempfile.TemporaryDirectory() as td:
            source_root, runtime_root, digest = self._materialize_artifact_pair(Path(td))
            manifest = self._resolved_fixture(digest)
            errors = validator.validate_manifest_data(
                manifest,
                schema=_load_json(SCHEMA_PATH),
                source_root=source_root,
                runtime_root=runtime_root,
                actual_source_revision="a" * 40,
            )
            self.assertEqual([], errors)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_pass_rejects_source_revision_drift(self):
        validator = _load_validator()
        manifest = self._resolved_fixture("0" * 64)
        errors = validator.validate_manifest_data(
            manifest,
            schema=_load_json(SCHEMA_PATH),
            actual_source_revision="b" * 40,
        )
        self.assertTrue(any("source_revision" in error and "actual" in error for error in errors), errors)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_pass_rejects_provider_binding_drift(self):
        validator = _load_validator()
        manifest = self._resolved_fixture("0" * 64)
        manifest["artifacts"][0]["provider_profile"] = "undeclared_provider"
        errors = validator.validate_manifest_data(manifest, schema=_load_json(SCHEMA_PATH))
        self.assertTrue(any("provider_profile" in error for error in errors), errors)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_pass_rejects_unresolved_visual_input_binding(self):
        validator = _load_validator()
        manifest = self._resolved_fixture("0" * 64)
        manifest["visual_inputs"][0]["runtime_binding"] = "UNRESOLVED"
        errors = validator.validate_manifest_data(manifest, schema=_load_json(SCHEMA_PATH))
        self.assertTrue(any("visual_inputs" in error and "runtime_binding" in error for error in errors), errors)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_pass_rejects_missing_required_clip_qa_proof(self):
        validator = _load_validator()
        manifest = self._resolved_fixture("0" * 64)
        manifest["artifacts"][0]["required_clips"] = ["spin"]
        errors = validator.validate_manifest_data(manifest, schema=_load_json(SCHEMA_PATH))
        self.assertTrue(any("required_clips" in error and "spin" in error for error in errors), errors)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_paths_are_bounded_and_delivery_namespace_matches_mod_id(self):
        validator = _load_validator()
        manifest = self._resolved_fixture("0" * 64)
        manifest["artifacts"][0]["source_path"] = "../private.png"
        manifest["artifacts"][0]["delivery_path"] = "src/main/resources/assets/other_mod/textures/block/machine.png"
        errors = validator.validate_manifest_data(manifest, schema=_load_json(SCHEMA_PATH))
        self.assertTrue(any("source_path" in error and "bounded" in error for error in errors), errors)
        self.assertTrue(any("delivery_path" in error and "namespace" in error for error in errors), errors)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_hash_mismatch_is_fail_closed_when_roots_are_available(self):
        validator = _load_validator()
        with tempfile.TemporaryDirectory() as td:
            source_root, runtime_root, _ = self._materialize_artifact_pair(
                Path(td),
                source_payload=b"source",
                runtime_payload=b"runtime",
            )
            manifest = self._resolved_fixture("0" * 64)
            errors = validator.validate_manifest_data(
                manifest,
                schema=_load_json(SCHEMA_PATH),
                source_root=source_root,
                runtime_root=runtime_root,
            )
            self.assertTrue(any("source_sha256" in error for error in errors), errors)
            self.assertTrue(any("delivery_sha256" in error for error in errors), errors)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_pass_rejects_unresolved_artifact_resolution_fields(self):
        validator = _load_validator()
        manifest = self._resolved_fixture("0" * 64)
        manifest["provider_profiles"] = ["UNRESOLVED"]
        manifest["provider_bindings"] = [
            {
                "provider_profile": "UNRESOLVED",
                "runtime_adapter": "fixture_native_adapter",
                "evidence": ["synthetic unresolved provider fixture"],
            }
        ]
        artifact = manifest["artifacts"][0]
        for field in (
            "provider_profile",
            "source_path",
            "source_format",
            "delivery_path",
            "delivery_format",
        ):
            artifact[field] = "UNRESOLVED"
        artifact["conversion"].update(
            {
                "performed": False,
                "from_format": "UNRESOLVED",
                "to_format": "UNRESOLVED",
            }
        )

        errors = validator.validate_manifest_data(manifest, schema=_load_json(SCHEMA_PATH))

        for field in (
            "provider_profiles",
            "provider_profile",
            "source_path",
            "source_format",
            "delivery_path",
            "delivery_format",
        ):
            self.assertTrue(
                any(field in error and "UNRESOLVED" in error for error in errors),
                (field, errors),
            )

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_asset_formats_must_match_source_and_delivery_path_suffixes(self):
        validator = _load_validator()
        with tempfile.TemporaryDirectory() as td:
            source_root, runtime_root, digest = self._materialize_artifact_pair(Path(td))
            manifest = self._resolved_fixture(digest)
            artifact = manifest["artifacts"][0]
            artifact["source_format"] = ".bbmodel"
            artifact["delivery_format"] = ".bbmodel"
            artifact["conversion"].update(
                {
                    "performed": False,
                    "from_format": ".bbmodel",
                    "to_format": ".bbmodel",
                }
            )

            errors = validator.validate_manifest_data(
                manifest,
                schema=_load_json(SCHEMA_PATH),
                source_root=source_root,
                runtime_root=runtime_root,
            )

            self.assertTrue(any("source_format" in error and "suffix" in error for error in errors), errors)
            self.assertTrue(any("delivery_format" in error and "suffix" in error for error in errors), errors)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_schema_invalid_provider_profiles_returns_errors_without_exception(self):
        validator = _load_validator()
        manifest = self._resolved_fixture("0" * 64)
        manifest["provider_profiles"] = 42

        errors = validator.validate_manifest_data(manifest, schema=_load_json(SCHEMA_PATH))

        self.assertTrue(any("provider_profiles" in error for error in errors), errors)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_cli_rejects_manifest_outside_current_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            workspace = root / "workspace"
            workspace.mkdir()
            outside_manifest = root / "outside-manifest.json"
            outside_manifest.write_text(EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")

            result = _run_cli(workspace, outside_manifest)

            self._assert_workspace_rejected(result)

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_cli_rejects_source_root_outside_current_workspace(self):
        self._assert_outside_root_rejected(
            option="--source-root",
            outside_name="outside-source",
            relative_file=Path("textures/machine.png"),
        )

    @unittest.skipUnless(SCRIPT_EXISTS, "I6 production validator not implemented yet")
    def test_cli_rejects_runtime_root_outside_current_workspace(self):
        self._assert_outside_root_rejected(
            option="--runtime-root",
            outside_name="outside-runtime",
            relative_file=Path("src/main/resources/assets/example_mod/textures/block/machine.png"),
        )

    def _materialize_artifact_pair(
        self,
        root: Path,
        *,
        source_payload: bytes = b"fixture-texture-bytes",
        runtime_payload: bytes | None = None,
    ) -> tuple[Path, Path, str]:
        source_root = root / "source"
        runtime_root = root / "runtime"
        source_file = source_root / "textures" / "machine.png"
        runtime_file = runtime_root / "src" / "main" / "resources" / "assets" / "example_mod" / "textures" / "block" / "machine.png"
        source_file.parent.mkdir(parents=True)
        runtime_file.parent.mkdir(parents=True)
        source_file.write_bytes(source_payload)
        runtime_file.write_bytes(source_payload if runtime_payload is None else runtime_payload)
        return source_root, runtime_root, hashlib.sha256(source_payload).hexdigest()

    def _assert_outside_root_rejected(self, *, option: str, outside_name: str, relative_file: Path) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            workspace = root / "workspace"
            workspace.mkdir()
            outside_root = root / outside_name
            payload_file = outside_root / relative_file
            payload_file.parent.mkdir(parents=True)
            payload = b"fixture-texture-bytes"
            payload_file.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            manifest_path = workspace / "manifest.json"
            manifest_path.write_text(
                json.dumps(self._resolved_fixture(digest), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result = _run_cli(
                workspace,
                manifest_path,
                option,
                str(outside_root),
                "--source-revision",
                "a" * 40,
            )
            self._assert_workspace_rejected(result)

    def _assert_workspace_rejected(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertNotEqual(0, result.returncode, result.stdout)
        self.assertIn("workspace", result.stdout.lower())

    def _resolved_fixture(self, digest):
        manifest = copy.deepcopy(_load_json(EXAMPLE_PATH))
        manifest.update(
            {
                "schema_version": 2,
                "source_repository": FACTORY_REPOSITORY,
                "source_revision": "a" * 40,
                "runtime_authority": "FIXTURE_RUNTIME_REPOSITORY",
                "provider_profiles": ["fixture_native"],
                "provider_bindings": [
                    {
                        "provider_profile": "fixture_native",
                        "runtime_adapter": "fixture_native_adapter",
                        "evidence": ["synthetic I6 test fixture"],
                    }
                ],
                "visual_inputs": [
                    {
                        "name": "active",
                        "type": "bool",
                        "runtime_binding": "MachineBlockEntity#isActive()",
                        "evidence": ["synthetic I6 test fixture"],
                    }
                ],
                "state": "PASS",
                "evidence": ["synthetic I6 test fixture"],
            }
        )
        delivery_path = "src/main/resources/assets/example_mod/textures/block/machine.png"
        manifest["artifacts"] = [
            {
                "asset_id": "machine_texture",
                "provider_profile": "fixture_native",
                "source_path": "textures/machine.png",
                "source_format": ".png",
                "source_sha256": digest,
                "delivery_path": delivery_path,
                "delivery_format": ".png",
                "delivery_sha256": digest,
                "required_bones": [],
                "required_anchors": [],
                "required_clips": [],
                "textures": [delivery_path],
                "conversion": {
                    "performed": False,
                    "from_format": ".png",
                    "to_format": ".png",
                    "state": "PASS",
                    "evidence": ["no format conversion in synthetic fixture"],
                },
                "qa": {
                    "verified_bones": [],
                    "verified_anchors": [],
                    "verified_clips": [],
                    "verified_textures": [delivery_path],
                    "namespace_verified": True,
                    "output_destination_verified": True,
                    "state": "PASS",
                    "evidence": ["synthetic I6 QA fixture"],
                },
                "state": "PASS",
            }
        ]
        return manifest


if __name__ == "__main__":
    unittest.main()
