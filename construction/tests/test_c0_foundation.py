from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION = ROOT / "construction"
VALIDATOR = CONSTRUCTION / "scripts" / "validate_c0.py"


def load_validator():
    if not VALIDATOR.is_file():
        raise AssertionError(f"C0 validator is required at {VALIDATOR.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location("construction_c0_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load C0 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC0FoundationTest(unittest.TestCase):
    def test_required_foundation_files_exist(self) -> None:
        required = [
            "construction/README.md",
            "construction/STATUS.md",
            "construction/docs/ARCHITECTURE.md",
            "construction/upstream/registry.json",
            "construction/schemas/build-spec.schema.json",
            "construction/schemas/upstream-source.schema.json",
            ".github/workflows/factory-construction-c0-foundation.yml",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_registry_is_pinned_and_reference_only_source_is_not_vendorable(self) -> None:
        registry = json.loads((CONSTRUCTION / "upstream" / "registry.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["schema_version"], 1)
        sources = {source["id"]: source for source in registry["sources"]}
        self.assertEqual(set(sources), {"schematica", "minebench", "minecraft-builder-mcp", "mcschematic", "promptcraft"})
        for source in sources.values():
            self.assertRegex(source["pinned_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(sources["promptcraft"]["integration_policy"], "REFERENCE_ONLY")
        self.assertEqual(sources["promptcraft"]["c0_state"], "DO_NOT_VENDOR")

    def test_external_providers_do_not_claim_unverified_apis(self) -> None:
        registry = json.loads((CONSTRUCTION / "upstream" / "registry.json").read_text(encoding="utf-8"))
        providers = {provider["id"]: provider for provider in registry["external_providers"]}
        self.assertEqual(set(providers), {"objtoschematic", "structmatic", "schematic-helper", "blockgpt"})
        for provider in providers.values():
            self.assertEqual(provider["integration_policy"], "EXTERNAL_PROVIDER")
            self.assertEqual(provider["api_state"], "UNVERIFIED_API")

    def test_build_spec_targets_1_21_1_and_sponge_v3(self) -> None:
        schema = json.loads((CONSTRUCTION / "schemas" / "build-spec.schema.json").read_text(encoding="utf-8"))
        target = schema["properties"]["target"]["properties"]
        outputs = schema["properties"]["outputs"]["properties"]["formats"]["items"]["enum"]
        self.assertEqual(target["minecraft_version"]["const"], "1.21.1")
        self.assertIn("neoforge", target["loader"]["enum"])
        self.assertIn("sponge_v3", outputs)

    def test_c0_validator_accepts_repository(self) -> None:
        module = load_validator()
        errors = module.validate(ROOT)
        self.assertEqual(errors, [], "\n".join(errors))

    def test_validator_rejects_unpinned_source(self) -> None:
        module = load_validator()
        invalid = {
            "schema_version": 1,
            "audited_at": "2026-09-10",
            "sources": [
                {
                    "id": "bad",
                    "kind": "engine",
                    "repository": "owner/repo",
                    "pinned_commit": "main",
                    "license": "MIT",
                    "integration_policy": "IMMUTABLE_SNAPSHOT",
                    "c0_state": "AUDITED_NOT_VENDORED",
                }
            ],
            "external_providers": [],
        }
        errors = module.validate_registry(invalid)
        self.assertTrue(any("pinned_commit" in error for error in errors))

    def test_no_snapshot_payload_is_vendored_during_c0(self) -> None:
        snapshots = CONSTRUCTION / "upstream" / "snapshots"
        if snapshots.exists():
            payloads = [path for path in snapshots.rglob("*") if path.is_file()]
            self.assertEqual(payloads, [], "C0 must not vendor upstream payloads; that starts in C1")


if __name__ == "__main__":
    unittest.main()
