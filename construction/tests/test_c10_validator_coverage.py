from __future__ import annotations

import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "construction" / "scripts" / "validate_c10.py"
PROFILE_DIR = ROOT / "construction" / "providers" / "profiles"
UPSTREAM = ROOT / "construction" / "upstream" / "registry.json"
SCHEMA_DIR = ROOT / "construction" / "schemas"
SCHEMA_NAMES = (
    "external-provider-profile.schema.json",
    "provider-handoff-request.schema.json",
    "provider-handoff-receipt.schema.json",
)


def load_validator():
    spec = importlib.util.spec_from_file_location("construction_c10_validator_coverage", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load C10 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC10ValidatorCoverageTest(unittest.TestCase):
    def copy_contract_tree(self, temp_root: Path) -> None:
        (temp_root / "construction" / "upstream").mkdir(parents=True)
        (temp_root / "construction" / "providers").mkdir(parents=True)
        (temp_root / "construction" / "schemas").mkdir(parents=True)
        shutil.copy2(UPSTREAM, temp_root / "construction" / "upstream" / "registry.json")
        shutil.copytree(PROFILE_DIR, temp_root / "construction" / "providers" / "profiles")
        for name in SCHEMA_NAMES:
            shutil.copy2(SCHEMA_DIR / name, temp_root / "construction" / "schemas" / name)

    def test_validator_accepts_canonical_repository_and_main_entrypoint(self):
        module = load_validator()
        self.assertEqual([], module.validate_repository(ROOT))

        stdout = io.StringIO()
        with mock.patch.object(Path, "cwd", return_value=ROOT), redirect_stdout(stdout):
            result = module.main()
        self.assertEqual(0, result)
        self.assertEqual("CONSTRUCTION C10: PASS\n", stdout.getvalue())

    def test_validator_cli_runs_from_repository_root(self):
        result = subprocess.run(
            [sys.executable, "construction/scripts/validate_c10.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("CONSTRUCTION C10: PASS\n", result.stdout)

    def test_validator_reports_schema_and_secret_failures_without_secret_values(self):
        module = load_validator()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            self.copy_contract_tree(temp_root)
            fixture_dir = temp_root / "construction" / "fixtures" / "c10" / "coverage"
            fixture_dir.mkdir(parents=True)

            secret_value = "do-not-print-validator-coverage-secret"
            (fixture_dir / "secret.json").write_text(
                json.dumps({"token": secret_value}),
                encoding="utf-8",
            )
            schema_path = temp_root / "construction" / "schemas" / "provider-handoff-request.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["additionalProperties"] = True
            schema_path.write_text(json.dumps(schema), encoding="utf-8")

            errors = module.validate_repository(temp_root)
            rendered = "\n".join(errors)
            self.assertIn("secret-like key $.token", rendered)
            self.assertIn("top-level additionalProperties must be false", rendered)
            self.assertNotIn(secret_value, rendered)

    def test_validator_rejects_malformed_json_fixture_deterministically(self):
        module = load_validator()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            self.copy_contract_tree(temp_root)
            fixture_dir = temp_root / "construction" / "fixtures" / "c10" / "coverage"
            fixture_dir.mkdir(parents=True)
            (fixture_dir / "broken.json").write_text("{", encoding="utf-8")

            first = module.validate_repository(temp_root)
            second = module.validate_repository(temp_root)
            self.assertEqual(first, second)
            self.assertEqual(sorted(set(first)), first)
            self.assertTrue(any("invalid JSON" in error for error in first))


if __name__ == "__main__":
    unittest.main()
