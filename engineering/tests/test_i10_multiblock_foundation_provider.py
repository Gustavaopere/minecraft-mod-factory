from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
MOD_SPEC = REPO / "engineering/tests/fixtures/i10-multiblock-mod-spec.json"


class I10ProviderNeutralFixtureContract(unittest.TestCase):
    def test_visual_provider_profiles_are_physical_and_provider_neutral(self) -> None:
        mod_spec = json.loads(MOD_SPEC.read_text(encoding="utf-8"))
        profiles = mod_spec["visual"]["provider_profiles"]
        self.assertEqual([], profiles, "I10 baseline visual fixture must remain provider-neutral")
        self.assertNotIn("java_block_item", json.dumps(mod_spec, sort_keys=True).lower())


if __name__ == "__main__":
    unittest.main()
