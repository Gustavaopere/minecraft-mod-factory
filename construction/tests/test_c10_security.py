from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from construction.providers.common import canonical_json_bytes, sha256_hex
from construction.providers.errors import C10Error
from construction.providers.handoff import build_handoff_receipt, build_handoff_request
from construction.providers.profiles import load_profile_catalog, profile_fingerprint

ROOT = Path(__file__).resolve().parents[2]
STAGING_MODULE = ROOT / "construction" / "providers" / "staging.py"
VALIDATOR_SCRIPT = ROOT / "construction" / "scripts" / "validate_c10.py"
PROFILE_DIR = ROOT / "construction" / "providers" / "profiles"
UPSTREAM = ROOT / "construction" / "upstream" / "registry.json"
SCHEMAS = ROOT / "construction" / "schemas"
FIXTURE_PREFIX = "construction/fixtures/c10/"
PHYSICAL_SHA = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"
STAGING_FUNCTIONS = (
    "safe_repo_fixture_path",
    "artifact_descriptor_from_bytes",
    "artifact_descriptor_from_file",
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC10SecurityTest(unittest.TestCase):
    def require_security(self):
        if not STAGING_MODULE.is_file() or not VALIDATOR_SCRIPT.is_file():
            self.skipTest("C10 security implementation intentionally absent during RED")
        module = load_module(STAGING_MODULE, "construction_c10_staging")
        missing = [name for name in STAGING_FUNCTIONS if not hasattr(module, name)]
        if missing:
            self.skipTest(f"C10 security helpers intentionally absent during RED: {missing}")
        return module

    @staticmethod
    def manual_step() -> dict[str, object]:
        return {
            "required": True,
            "step_id": "submit-input",
            "instruction": "Upload the Factory-owned mesh fixture to the provider editor.",
            "expected_result": "The provider shows a generated block preview.",
        }

    def upstream_registry(self):
        return json.loads(UPSTREAM.read_text(encoding="utf-8"))

    def operational_profile(self) -> dict[str, object]:
        profile = copy.deepcopy(
            load_profile_catalog(PROFILE_DIR, self.upstream_registry())["objtoschematic"]
        )
        profile["proof_level"] = "EP1_HANDOFF_VERIFIED"
        profile["integration_mode"] = "MANUAL_FILE_HANDOFF"
        profile["capabilities"] = ["MESH_TO_STRUCTURE"]
        profile["handoff"] = {
            "accepted_input_kinds": ["MESH"],
            "output_artifact_kinds": ["SCHEMATIC_FILE"],
            "manual_action_required": True,
            "determinism": "UNKNOWN",
        }
        profile["limits"] = {
            "max_input_bytes": 1024,
            "max_output_bytes": 1024,
            "timeout_seconds": None,
        }
        profile["profile_sha256"] = profile_fingerprint(profile)
        return profile

    def test_required_task5_contract_exists(self):
        missing = []
        if not STAGING_MODULE.is_file():
            missing.append(str(STAGING_MODULE.relative_to(ROOT)))
        if not VALIDATOR_SCRIPT.is_file():
            missing.append(str(VALIDATOR_SCRIPT.relative_to(ROOT)))
        if STAGING_MODULE.is_file():
            module = load_module(STAGING_MODULE, "construction_c10_staging_red")
            missing.extend(name for name in STAGING_FUNCTIONS if not hasattr(module, name))
        self.assertEqual([], missing, f"C10 Task 5 RED: missing security contract: {missing}")

    def test_staging_helpers_have_exact_capability_limited_signatures_and_exports(self):
        module = self.require_security()
        self.assertEqual(
            ["root", "repo_relpath", "must_exist"],
            list(inspect.signature(module.safe_repo_fixture_path).parameters),
        )
        self.assertEqual(
            ["data", "kind", "media_type", "repo_relpath", "max_bytes"],
            list(inspect.signature(module.artifact_descriptor_from_bytes).parameters),
        )
        self.assertEqual(
            ["root", "repo_relpath", "kind", "media_type", "max_bytes"],
            list(inspect.signature(module.artifact_descriptor_from_file).parameters),
        )
        import construction.providers as providers

        for name in STAGING_FUNCTIONS:
            self.assertTrue(hasattr(providers, name), f"construction.providers must export {name}")
        for signature in (
            inspect.signature(module.artifact_descriptor_from_bytes),
            inspect.signature(module.artifact_descriptor_from_file),
        ):
            self.assertNotIn("filename", signature.parameters)
            self.assertNotIn("provider_filename", signature.parameters)

    def test_safe_repo_fixture_path_rejects_absolute_traversal_and_outside_prefixes(self):
        module = self.require_security()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            allowed = root / "construction" / "fixtures" / "c10" / "safe" / "artifact.bin"
            allowed.parent.mkdir(parents=True)
            allowed.write_bytes(b"safe")
            resolved = module.safe_repo_fixture_path(
                root,
                "construction/fixtures/c10/safe/artifact.bin",
                must_exist=True,
            )
            self.assertEqual(allowed.resolve(), resolved)

            invalid = (
                "/tmp/provider.bin",
                "../provider.bin",
                "construction/fixtures/c10/../escape.bin",
                "construction/fixtures/c10/./artifact.bin",
                "construction/fixtures/c10\\artifact.bin",
                "construction/fixtures/c9/artifact.bin",
                "README.md",
            )
            for value in invalid:
                with self.subTest(value=value), self.assertRaises(C10Error):
                    module.safe_repo_fixture_path(root, value, must_exist=False)

    def test_safe_repo_fixture_path_rejects_symlink_escape_directories_and_special_files(self):
        module = self.require_security()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixtures = root / "construction" / "fixtures" / "c10" / "security"
            fixtures.mkdir(parents=True)

            directory = fixtures / "directory"
            directory.mkdir()
            with self.assertRaises(C10Error):
                module.safe_repo_fixture_path(
                    root,
                    "construction/fixtures/c10/security/directory",
                    must_exist=True,
                )

            outside = root / "outside.bin"
            outside.write_bytes(b"outside")
            link = fixtures / "escaped.bin"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable on this platform")
            with self.assertRaises(C10Error):
                module.safe_repo_fixture_path(
                    root,
                    "construction/fixtures/c10/security/escaped.bin",
                    must_exist=True,
                )

            if hasattr(os, "mkfifo"):
                fifo = fixtures / "pipe"
                os.mkfifo(fifo)
                with self.assertRaises(C10Error):
                    module.safe_repo_fixture_path(
                        root,
                        "construction/fixtures/c10/security/pipe",
                        must_exist=True,
                    )

    def test_artifact_descriptor_from_bytes_is_factory_owned_and_size_limited(self):
        module = self.require_security()
        descriptor = module.artifact_descriptor_from_bytes(
            b"abcd",
            kind="MESH",
            media_type="application/octet-stream",
            repo_relpath="construction/fixtures/c10/security/input.obj",
            max_bytes=4,
        )
        self.assertEqual(
            {
                "kind": "MESH",
                "sha256": sha256_hex(b"abcd"),
                "byte_length": 4,
                "media_type": "application/octet-stream",
                "repo_relpath": "construction/fixtures/c10/security/input.obj",
            },
            descriptor,
        )
        with self.assertRaises(C10Error) as raised:
            module.artifact_descriptor_from_bytes(
                b"abcde",
                kind="MESH",
                media_type="application/octet-stream",
                repo_relpath=None,
                max_bytes=4,
            )
        self.assertEqual("ARTIFACT_LIMIT_EXCEEDED", raised.exception.code)

    def test_artifact_descriptor_from_file_enforces_limit_before_reading_and_rejects_non_files(self):
        module = self.require_security()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixtures = root / "construction" / "fixtures" / "c10" / "security"
            fixtures.mkdir(parents=True)
            artifact = fixtures / "output.schem"
            artifact.write_bytes(b"12345")

            with self.assertRaises(C10Error) as raised:
                module.artifact_descriptor_from_file(
                    root,
                    "construction/fixtures/c10/security/output.schem",
                    kind="SCHEMATIC_FILE",
                    media_type="application/octet-stream",
                    max_bytes=4,
                )
            self.assertEqual("ARTIFACT_LIMIT_EXCEEDED", raised.exception.code)

            descriptor = module.artifact_descriptor_from_file(
                root,
                "construction/fixtures/c10/security/output.schem",
                kind="SCHEMATIC_FILE",
                media_type="application/octet-stream",
                max_bytes=5,
            )
            self.assertEqual(sha256_hex(b"12345"), descriptor["sha256"])
            self.assertEqual(5, descriptor["byte_length"])

            with self.assertRaises(C10Error):
                module.artifact_descriptor_from_file(
                    root,
                    "construction/fixtures/c10/security",
                    kind="SCHEMATIC_FILE",
                    media_type="application/octet-stream",
                    max_bytes=100,
                )

    def _copy_contract_tree(self, temp_root: Path) -> None:
        (temp_root / "construction" / "upstream").mkdir(parents=True)
        (temp_root / "construction" / "providers").mkdir(parents=True)
        (temp_root / "construction" / "schemas").mkdir(parents=True)
        shutil.copy2(UPSTREAM, temp_root / "construction" / "upstream" / "registry.json")
        shutil.copytree(PROFILE_DIR, temp_root / "construction" / "providers" / "profiles")
        for name in (
            "external-provider-profile.schema.json",
            "provider-handoff-request.schema.json",
            "provider-handoff-receipt.schema.json",
        ):
            shutil.copy2(SCHEMAS / name, temp_root / "construction" / "schemas" / name)

    def _write_operational_fixture_set(self, module, temp_root: Path):
        self._copy_contract_tree(temp_root)
        profile = self.operational_profile()
        profile_path = temp_root / "construction" / "providers" / "profiles" / "objtoschematic.json"
        profile_path.write_bytes(canonical_json_bytes(profile))

        fixture_dir = temp_root / "construction" / "fixtures" / "c10" / "security-probe"
        fixture_dir.mkdir(parents=True)
        input_path = fixture_dir / "input.obj"
        output_path = fixture_dir / "output.schem"
        input_path.write_bytes(b"mesh")
        output_path.write_bytes(b"schem")

        input_descriptor = module.artifact_descriptor_from_file(
            temp_root,
            "construction/fixtures/c10/security-probe/input.obj",
            kind="MESH",
            media_type="application/octet-stream",
            max_bytes=1024,
        )
        output_descriptor = module.artifact_descriptor_from_file(
            temp_root,
            "construction/fixtures/c10/security-probe/output.schem",
            kind="SCHEMATIC_FILE",
            media_type="application/octet-stream",
            max_bytes=1024,
        )
        request = build_handoff_request(
            profile,
            operation="MESH_TO_STRUCTURE",
            text_input=None,
            input_artifacts=[input_descriptor],
            expected_output_kinds=["SCHEMATIC_FILE"],
            physical_modlist_sha256=PHYSICAL_SHA,
            manual_step=self.manual_step(),
        )
        receipt = build_handoff_receipt(
            request,
            profile,
            received_artifacts=[output_descriptor],
        )
        (fixture_dir / "request.json").write_bytes(canonical_json_bytes(request))
        (fixture_dir / "receipt.json").write_bytes(canonical_json_bytes(receipt))
        return fixture_dir, output_path, receipt

    def _run_validator(self, temp_root: Path) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT)
        return subprocess.run(
            [sys.executable, str(VALIDATOR_SCRIPT)],
            cwd=temp_root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_repository_validator_rejects_artifact_hash_and_byte_length_mismatch(self):
        module = self.require_security()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            fixture_dir, output_path, receipt = self._write_operational_fixture_set(module, temp_root)
            clean = self._run_validator(temp_root)
            self.assertEqual(0, clean.returncode, clean.stdout)

            output_path.write_bytes(b"other")
            mismatch = self._run_validator(temp_root)
            self.assertNotEqual(0, mismatch.returncode, mismatch.stdout)
            self.assertIn("ARTIFACT_HASH_MISMATCH", mismatch.stdout)
            output_path.write_bytes(b"schem")

            bad_length = copy.deepcopy(receipt)
            bad_length["received_artifacts"][0]["byte_length"] += 1
            payload = copy.deepcopy(bad_length)
            payload.pop("receipt_sha256", None)
            bad_length["receipt_sha256"] = sha256_hex(canonical_json_bytes(payload))
            (fixture_dir / "receipt.json").write_bytes(canonical_json_bytes(bad_length))
            mismatch = self._run_validator(temp_root)
            self.assertNotEqual(0, mismatch.returncode, mismatch.stdout)
            self.assertIn("byte length", mismatch.stdout.lower())

    def test_repository_validator_rejects_secret_patterns_without_printing_values(self):
        module = self.require_security()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            fixture_dir, _, _ = self._write_operational_fixture_set(module, temp_root)
            secret_value = "never-print-this-secret-value"
            secret_fixture = fixture_dir / "secret-probe.json"
            secret_fixture.write_text(
                json.dumps(
                    {
                        "api_key": secret_value,
                        "token": secret_value,
                        "password": secret_value,
                        "cookie": secret_value,
                        "session": secret_value,
                    }
                ),
                encoding="utf-8",
            )
            result = self._run_validator(temp_root)
            self.assertNotEqual(0, result.returncode, result.stdout)
            self.assertNotIn(secret_value, result.stdout)
            self.assertTrue(
                any(marker in result.stdout.lower() for marker in ("api_key", "token", "password", "cookie", "session")),
                result.stdout,
            )

    def test_repository_validator_errors_are_deterministic_and_sorted(self):
        module = self.require_security()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            fixture_dir, output_path, _ = self._write_operational_fixture_set(module, temp_root)
            output_path.write_bytes(b"other")
            (fixture_dir / "z-secret.txt").write_text("password=never-print-this-secret-value\n", encoding="utf-8")
            first = self._run_validator(temp_root)
            second = self._run_validator(temp_root)
            self.assertNotEqual(0, first.returncode)
            self.assertEqual(first.stdout, second.stdout)
            error_lines = [line for line in first.stdout.splitlines() if line.startswith("ERROR ")]
            self.assertEqual(sorted(error_lines), error_lines)


if __name__ == "__main__":
    unittest.main()
