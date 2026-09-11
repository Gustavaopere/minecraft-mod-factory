from __future__ import annotations

import copy
import unittest

from construction.tests.test_c8_visual_qa import (
    make_build_spec,
    make_ir,
    matching_c5_resolution,
    placement,
    render,
    visual_module,
)


class C8PaletteResolutionContractTests(unittest.TestCase):
    def test_malformed_c5_resolution_fails_closed(self) -> None:
        spec = make_build_spec(size=(1, 1, 1))
        ir = make_ir(spec, [placement(0, 0, 0)])
        views = render(ir)
        base = matching_c5_resolution(spec, ir)
        module = visual_module()

        variants: list[tuple[str, dict[str, object]]] = []

        unexpected_top_level = copy.deepcopy(base)
        unexpected_top_level["unexpected"] = True
        variants.append(("unexpected top-level field", unexpected_top_level))

        malformed_registry_fingerprint = copy.deepcopy(base)
        malformed_registry_fingerprint["registry_fingerprint"] = "not-a-sha256"
        variants.append(("malformed registry fingerprint", malformed_registry_fingerprint))

        invalid_authority = copy.deepcopy(base)
        invalid_authority["roles"][0]["selected"]["authority"] = "static_index"
        variants.append(("non-runtime authority", invalid_authority))

        namespace_mismatch = copy.deepcopy(base)
        namespace_mismatch["roles"][0]["selected"]["namespace"] = "other"
        variants.append(("namespace mismatch", namespace_mismatch))

        malformed_candidates = copy.deepcopy(base)
        malformed_candidates["roles"][0]["selected"]["state_candidates"] = "not-an-array"
        variants.append(("malformed state candidates", malformed_candidates))

        impossible_selection = copy.deepcopy(base)
        selected = impossible_selection["roles"][0]["selected"]
        selected["state_candidates"] = [
            copy.deepcopy(selected["selected_state"]),
            {
                "name": selected["block"],
                "properties": {"variant": "alternate"},
            },
        ]
        variants.append(("selected state retained with ambiguous candidates", impossible_selection))

        for label, candidate in variants:
            with self.subTest(label=label):
                with self.assertRaises(module.VisualQAError):
                    module.run_visual_qa(spec, ir, views, palette_resolution=candidate)


if __name__ == "__main__":
    unittest.main()
