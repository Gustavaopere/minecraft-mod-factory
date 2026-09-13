from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from skills.scripts.capability_router import (
    FINAL_BLOCKER,
    TARGET,
    load_capability_index,
    resolve_intent,
    validate_capability_index,
)

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "skills/capabilities/capability-index.json"
BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
REFERENCE_ONLY_ROOT = "migration/provenance/historical-skills/library"


class C13SkillRouterIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = load_capability_index(INDEX)

    def assertInvalid(self, index: dict[str, object], token: str) -> None:
        errors = validate_capability_index(index, repo_root=ROOT)
        self.assertTrue(errors, "mutated C13 index unexpectedly validated")
        self.assertTrue(
            any(token in error for error in errors),
            f"expected token {token!r} in validation errors: {errors}",
        )

    def capability(self, intent: str) -> dict[str, object]:
        for capability in self.index["capabilities"]:
            if capability["intent"] == intent:
                return capability
        self.fail(f"missing canonical capability intent: {intent}")

    def test_canonical_index_is_valid_and_target_is_exact(self) -> None:
        self.assertEqual(TARGET, {
            "minecraft": "1.21.1",
            "loader": "neoforge",
            "neoforge": "21.1.248",
            "java": 21,
        })
        self.assertEqual(self.index["target"], TARGET)
        self.assertEqual(validate_capability_index(self.index, repo_root=ROOT), [])

    def test_c11_and_c12_are_preflight_ready_but_blocked(self) -> None:
        self.assertEqual(FINAL_BLOCKER, BLOCKER)
        c11 = resolve_intent(self.index, "construction.complex_modded_golden")
        c12 = resolve_intent(self.index, "construction.runtime_acceptance")
        self.assertEqual(
            (c11["readiness"], c11["acceptance"], c11["blocker"]),
            ("PREFLIGHT_READY", "BLOCKED", BLOCKER),
        )
        self.assertEqual(
            (c12["readiness"], c12["acceptance"], c12["blocker"]),
            ("PREFLIGHT_READY", "BLOCKED", BLOCKER),
        )
        self.assertEqual(
            c12["entrypoint"],
            "construction/runtime/c12_runtime_acceptance.py",
        )

    def test_proven_offline_routes_remain_available_and_accepted(self) -> None:
        expected = {
            "construction.registry_search": ("C4", "construction/mcp/server.py#registry_search"),
            "construction.palette_resolve": ("C5", "construction/mcp/server.py#palette_resolve"),
            "construction.build_canonicalize": ("C2", "construction/mcp/server.py#build_canonicalize"),
            "construction.structural_qa": ("C7", "construction/mcp/server.py#qa_structural"),
            "construction.offline_visual_qa": ("C8", "construction/mcp/server.py#qa_visual"),
            "construction.sponge_v3_export": ("C6", "construction/mcp/server.py#export_sponge_v3"),
        }
        for intent, (authority, entrypoint) in expected.items():
            with self.subTest(intent=intent):
                route = resolve_intent(self.index, intent)
                self.assertEqual(route["authority"], authority)
                self.assertEqual(route["entrypoint"], entrypoint)
                self.assertEqual(route["readiness"], "AVAILABLE")
                self.assertEqual(route["acceptance"], "ACCEPTED")
                self.assertIsNone(route["blocker"])

    def test_cross_domain_routes_preserve_runtime_and_art_authorities(self) -> None:
        engineering = resolve_intent(self.index, "engineering.runtime_modification")
        art = resolve_intent(self.index, "art.visual_authoring")
        self.assertEqual(
            (engineering["authority"], engineering["acceptance"]),
            ("ENGINEERING", "NOT_APPLICABLE"),
        )
        self.assertEqual(
            (art["authority"], art["acceptance"]),
            ("ART", "NOT_APPLICABLE"),
        )

    def test_external_provider_handoff_selects_c10_and_user_guided_protocol(self) -> None:
        route = resolve_intent(self.index, "construction.external_provider_handoff")
        self.assertEqual(route["authority"], "C10")
        self.assertEqual(route["entrypoint"], "construction/providers")
        self.assertIn("USER_GUIDED_WORKFLOW", route["required_evidence"])
        self.assertIn(
            "NO_PROVIDER_PRESENCE_TO_API_SUPPORT",
            route["forbidden_promotions"],
        )

    def test_unknown_intent_fails_closed_without_guessing_fallback(self) -> None:
        route = resolve_intent(self.index, "provider.unproven.magic_api")
        self.assertIsNone(route["capability_id"])
        self.assertEqual(route["readiness"], "UNAVAILABLE")
        self.assertEqual(route["acceptance"], "BLOCKED")
        self.assertEqual(route["blocker"], "NO_DECLARED_CAPABILITY_ROUTE")
        self.assertEqual(route["fallback_policy"], "NONE")

    def test_duplicate_capability_id_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.index)
        mutated["capabilities"][1]["capability_id"] = mutated["capabilities"][0]["capability_id"]
        self.assertInvalid(mutated, "duplicate capability_id")

    def test_duplicate_intent_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.index)
        mutated["capabilities"][1]["intent"] = mutated["capabilities"][0]["intent"]
        self.assertInvalid(mutated, "duplicate intent")

    def test_unknown_authority_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.index)
        mutated["capabilities"][0]["authority"] = "INVENTED_AUTHORITY"
        self.assertInvalid(mutated, "unknown authority")

    def test_target_drift_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.index)
        mutated["target"]["neoforge"] = "21.1.999"
        self.assertInvalid(mutated, "target")

    def test_missing_entrypoint_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.index)
        mutated["capabilities"][0]["entrypoint"] = "construction/does-not-exist.py"
        self.assertInvalid(mutated, "entrypoint")

    def test_entrypoint_parent_escape_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.index)
        mutated["capabilities"][0]["entrypoint"] = "../outside.py"
        self.assertInvalid(mutated, "entrypoint")

    def test_reference_only_path_cannot_become_active_authority(self) -> None:
        mutated = copy.deepcopy(self.index)
        mutated["capabilities"][0]["entrypoint"] = (
            REFERENCE_ONLY_ROOT + "/minecraft-mod-dev/SKILL.md"
        )
        self.assertInvalid(mutated, "REFERENCE_ONLY")

    def test_accepted_route_cannot_keep_a_blocker(self) -> None:
        mutated = copy.deepcopy(self.index)
        mutated["capabilities"][0]["blocker"] = BLOCKER
        self.assertInvalid(mutated, "ACCEPTED")

    def test_unavailable_route_cannot_be_accepted(self) -> None:
        mutated = copy.deepcopy(self.index)
        mutated["capabilities"][0]["readiness"] = "UNAVAILABLE"
        self.assertInvalid(mutated, "UNAVAILABLE")

    def test_provider_specific_api_route_requires_exact_api_proof(self) -> None:
        mutated = copy.deepcopy(self.index)
        provider_route = copy.deepcopy(mutated["capabilities"][0])
        provider_route.update(
            {
                "capability_id": "provider.example.api",
                "intent": "provider.example.api",
                "authority": "C10",
                "entrypoint": "construction/providers",
                "readiness": "AVAILABLE",
                "acceptance": "NOT_APPLICABLE",
                "blocker": None,
                "version_proof": "NOT_REQUIRED",
                "forbidden_promotions": [],
            }
        )
        mutated["capabilities"].append(provider_route)
        self.assertInvalid(mutated, "REQUIRED_EXACT_API")
        self.assertInvalid(mutated, "NO_PROVIDER_PRESENCE_TO_API_SUPPORT")

    def test_path_symbol_must_exist_in_source(self) -> None:
        mutated = copy.deepcopy(self.index)
        route = mutated["capabilities"][0]
        route["entrypoint"] = "construction/mcp/server.py#definitely_not_a_symbol"
        self.assertInvalid(mutated, "symbol")

    def test_index_load_is_deterministic_and_returns_detached_data(self) -> None:
        first = load_capability_index(INDEX)
        second = load_capability_index(INDEX)
        self.assertEqual(first, second)
        first["capabilities"][0]["readiness"] = "UNAVAILABLE"
        self.assertNotEqual(first, second)

        with tempfile.TemporaryDirectory() as tmp:
            copy_path = Path(tmp) / "index.json"
            copy_path.write_text(
                json.dumps(second, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(load_capability_index(copy_path), second)


if __name__ == "__main__":
    unittest.main()
