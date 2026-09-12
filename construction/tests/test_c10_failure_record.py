from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "construction" / "scripts" / "validate_c10.py"
PROFILE_DIR = ROOT / "construction" / "providers" / "profiles"
UPSTREAM = ROOT / "construction" / "upstream" / "registry.json"
SCHEMA_DIR = ROOT / "construction" / "schemas"
FIXTURE_DIR = ROOT / "construction" / "fixtures" / "c10"
FAILURE_RELPATH = Path("objtoschematic-smoke/failure.json")
SCHEMA_NAMES = (
    "external-provider-profile.schema.json",
    "provider-handoff-request.schema.json",
    "provider-handoff-receipt.schema.json",
)


def load_validator():
    spec = importlib.util.spec_from_file_location("construction_c10_failure_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load C10 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC10FailureRecordTest(unittest.TestCase):
    def copy_contract_tree(self, temp_root: Path) -> Path:
        (temp_root / "construction" / "upstream").mkdir(parents=True)
        (temp_root / "construction" / "providers").mkdir(parents=True)
        (temp_root / "construction" / "schemas").mkdir(parents=True)
        shutil.copy2(UPSTREAM, temp_root / "construction" / "upstream" / "registry.json")
        shutil.copytree(PROFILE_DIR, temp_root / "construction" / "providers" / "profiles")
        for name in SCHEMA_NAMES:
            shutil.copy2(SCHEMA_DIR / name, temp_root / "construction" / "schemas" / name)
        target = temp_root / "construction" / "fixtures" / "c10"
        shutil.copytree(FIXTURE_DIR, target)
        return target / FAILURE_RELPATH

    def test_canonical_failure_record_is_bound_to_historical_request(self):
        module = load_validator()
        self.assertEqual([], module.validate_repository(ROOT))

    def test_failure_record_mutations_fail_closed(self):
        module = load_validator()
        mutations = {
            "unknown_field": lambda value: value.__setitem__("unexpected", True),
            "request_id": lambda value: value.__setitem__("request_id", "0" * 64),
            "provider_id": lambda value: value.__setitem__("provider_id", "blockgpt"),
            "input_sha256": lambda value: value.__setitem__("input_sha256", "0" * 64),
            "stage": lambda value: value.__setitem__("stage", "EXPORT"),
            "outcome": lambda value: value.__setitem__("outcome", "PASS"),
            "observation": lambda value: value.__setitem__("observation", ""),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                temp_root = Path(temp)
                failure_path = self.copy_contract_tree(temp_root)
                document = json.loads(failure_path.read_text(encoding="utf-8"))
                mutate(document)
                failure_path.write_text(json.dumps(document), encoding="utf-8")
                errors = module.validate_repository(temp_root)
                self.assertEqual(sorted(set(errors)), errors)
                self.assertTrue(
                    any(str(FAILURE_RELPATH).replace("\\", "/") in error for error in errors),
                    errors,
                )

    def test_unknown_c10_json_fixture_shape_fails_closed(self):
        module = load_validator()
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            self.copy_contract_tree(temp_root)
            unknown = temp_root / "construction" / "fixtures" / "c10" / "unknown.json"
            unknown.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            errors = module.validate_repository(temp_root)
            self.assertTrue(any("unrecognized C10 fixture document" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
