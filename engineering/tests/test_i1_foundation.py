import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "engineering" / "tooling" / "validate-i1-foundation.py"
spec = importlib.util.spec_from_file_location("i1_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class I1FoundationContractTest(unittest.TestCase):
    def _load(self, relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_repository_foundation_is_complete(self):
        self.assertEqual([], validator.run_validation(ROOT))

    def test_json_schema_search_semantics_reject_invalid_mod_id(self):
        schema = self._load("engineering/schemas/mod-spec.schema.json")
        example = self._load("engineering/examples/mod-spec.example.json")
        example["identity"]["mod_id"] = "Invalid-Mod"
        errors = validator.validate_instance(schema, example)
        self.assertTrue(any("mod_id" in e and "pattern" in e for e in errors), errors)

    def test_all_declared_patterns_are_explicitly_anchored(self):
        schemas_dir = ROOT / "engineering" / "schemas"
        failures = []
        for schema_path in sorted(schemas_dir.glob("*.schema.json")):
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            for pattern_path, pattern in validator.iter_declared_patterns(schema):
                if not (pattern.startswith("^") and pattern.endswith("$")):
                    failures.append(f"{schema_path.name}:{pattern_path}:{pattern}")
        self.assertEqual([], failures)

    def test_asset_handoff_rejects_false_no_conversion_for_different_formats(self):
        handoff = copy.deepcopy(self._load("engineering/examples/asset-handoff.example.json"))
        artifact = handoff["artifacts"][0]
        artifact["delivery_format"] = ".json"
        artifact["conversion"]["to_format"] = ".json"
        artifact["conversion"]["performed"] = False
        errors = validator.validate_asset_handoff_semantics(handoff)
        self.assertTrue(any("conversion.performed" in e for e in errors), errors)

    def test_asset_handoff_rejects_conversion_format_drift(self):
        handoff = copy.deepcopy(self._load("engineering/examples/asset-handoff.example.json"))
        handoff["artifacts"][0]["conversion"]["from_format"] = ".json"
        errors = validator.validate_asset_handoff_semantics(handoff)
        self.assertTrue(any("conversion.from_format" in e for e in errors), errors)

    def test_source_registry_rejects_authority_order_drift(self):
        registry = copy.deepcopy(self._load("engineering/catalog/sources/SOURCE-REGISTRY.json"))
        registry["authority_order"][0], registry["authority_order"][1] = (
            registry["authority_order"][1],
            registry["authority_order"][0],
        )
        errors = validator.validate_source_registry_data(registry)
        self.assertTrue(any("authority_order" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
