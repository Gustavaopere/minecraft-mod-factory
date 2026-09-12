import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "engineering" / "catalog" / "providers" / "PROVIDER-CATALOG.json"
VALIDATOR = ROOT / "engineering" / "tooling" / "provider-catalog" / "validate_provider_catalog.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("i7_provider_catalog_supported_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load I7 provider catalog validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class I7ProviderCatalogSupportedSemanticsRedTest(unittest.TestCase):
    def geckolib_provider(self):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        return next(provider for provider in catalog["providers"] if provider["mod_id"] == "geckolib")

    def test_source_and_license_are_validator_required_fields(self):
        validator = load_validator_module()
        provider = copy.deepcopy(self.geckolib_provider())
        provider.pop("source")
        provider.pop("license")
        errors = validator._validate_provider(provider, 0, ROOT)
        expected = {
            "providers[0] missing fields: license, source",
        }
        self.assertTrue(expected.issubset(set(errors)), f"missing fail-closed errors: {expected.difference(errors)}")

    def test_supported_provider_requires_confirmed_source_and_license(self):
        validator = load_validator_module()
        provider = copy.deepcopy(self.geckolib_provider())
        provider["supported"] = True
        provider["source"] = {
            "state": "UNRESOLVED",
            "evidence": ["source provenance intentionally unresolved test fixture"],
        }
        provider["license"] = {
            "state": "UNRESOLVED",
            "evidence": ["license provenance intentionally unresolved test fixture"],
        }
        errors = validator._validate_provider(provider, 0, ROOT)
        expected = {
            "providers[0] cannot be supported without CONFIRMED source metadata",
            "providers[0] cannot be supported without CONFIRMED license metadata",
        }
        self.assertTrue(expected.issubset(set(errors)), f"missing fail-closed errors: {expected.difference(errors)}")


if __name__ == "__main__":
    unittest.main()
