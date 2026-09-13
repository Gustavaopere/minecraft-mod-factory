from __future__ import annotations

import copy
import unittest

from construction.runtime.c12_runtime_acceptance import (
    C12Error,
    build_runtime_acceptance_report,
    validate_i5_manifest,
    validate_runtime_acceptance_report,
)

TARGET = {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "neoforge": "21.1.248",
    "java": 21,
}
BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
FINGERPRINTS = {
    "i2_physical_snapshot_sha256": None,
    "c4_registry_sha256": None,
    "c11_manifest_sha256": None,
    "c6_schematic_sha256": None,
    "c7_report_sha256": None,
    "c8_report_sha256": None,
}
STAGES = {
    "target_environment": "PASS",
    "i5_baseline": "PASS",
    "client_smoke": "DEFERRED",
    "live_placement": "DEFERRED",
    "runtime_visual_fidelity": "DEFERRED",
    "multiplayer": "DEFERRED",
    "full_modpack": "DEFERRED",
    "evidence_packaging": "PASS",
}


def _preflight_report(**overrides):
    kwargs = {
        "mode": "PREFLIGHT",
        "target": copy.deepcopy(TARGET),
        "blocker": {"status": BLOCKER, "blocks_c12_acceptance": True},
        "authority_fingerprints": copy.deepcopy(FINGERPRINTS),
        "stages": copy.deepcopy(STAGES),
    }
    kwargs.update(overrides)
    return build_runtime_acceptance_report(**kwargs)


class C12RuntimeAcceptanceTest(unittest.TestCase):
    def test_preflight_ready_is_not_acceptance(self):
        report = _preflight_report()
        self.assertEqual(report["overall_readiness"], "PREFLIGHT_READY")
        self.assertEqual(report["overall_acceptance"], "BLOCKED")
        self.assertEqual(report["blocker"], BLOCKER)
        self.assertEqual(validate_runtime_acceptance_report(report), [])

    def test_target_drift_fails_closed(self):
        bad_target = dict(TARGET, neoforge="21.1.247")
        with self.assertRaisesRegex(C12Error, "target drift"):
            _preflight_report(target=bad_target)

    def test_stage_set_is_exact(self):
        bad_stages = copy.deepcopy(STAGES)
        bad_stages.pop("multiplayer")
        with self.assertRaisesRegex(C12Error, "stage ids"):
            _preflight_report(stages=bad_stages)

    def test_unknown_stage_state_fails_closed(self):
        bad_stages = copy.deepcopy(STAGES)
        bad_stages["client_smoke"] = "READY"
        with self.assertRaisesRegex(C12Error, "stage state"):
            _preflight_report(stages=bad_stages)

    def test_preflight_physical_fingerprints_may_be_null(self):
        report = _preflight_report()
        self.assertTrue(all(value is None for value in report["authority_fingerprints"].values()))

    def test_physical_acceptance_requires_all_physical_fingerprints(self):
        stages = {key: "PASS" for key in STAGES}
        report = build_runtime_acceptance_report(
            mode="PHYSICAL_ACCEPTANCE",
            target=TARGET,
            blocker={"status": None, "blocks_c12_acceptance": False},
            authority_fingerprints=FINGERPRINTS,
            stages=stages,
        )
        self.assertEqual(report["overall_acceptance"], "BLOCKED")

    def test_c11_not_accepted_cannot_promote_c12(self):
        stages = {key: "PASS" for key in STAGES}
        fingerprints = {key: "a" * 64 for key in FINGERPRINTS}
        report = build_runtime_acceptance_report(
            mode="PHYSICAL_ACCEPTANCE",
            target=TARGET,
            blocker={"status": BLOCKER, "blocks_c12_acceptance": True},
            authority_fingerprints=fingerprints,
            stages=stages,
        )
        self.assertEqual(report["overall_acceptance"], "BLOCKED")
        self.assertEqual(report["blocker"], BLOCKER)

    def test_c8_offline_pass_does_not_replace_runtime_visual_fidelity(self):
        stages = copy.deepcopy(STAGES)
        stages["runtime_visual_fidelity"] = "DEFERRED"
        report = _preflight_report(stages=stages)
        self.assertEqual(report["stages"]["runtime_visual_fidelity"], "DEFERRED")
        self.assertEqual(report["overall_acceptance"], "BLOCKED")

    def test_dedicated_server_baseline_does_not_replace_multiplayer(self):
        report = _preflight_report()
        self.assertEqual(report["stages"]["i5_baseline"], "PASS")
        self.assertEqual(report["stages"]["multiplayer"], "DEFERRED")

    def test_standalone_baseline_does_not_replace_full_modpack(self):
        report = _preflight_report()
        self.assertEqual(report["stages"]["i5_baseline"], "PASS")
        self.assertEqual(report["stages"]["full_modpack"], "DEFERRED")

    def test_validate_i5_manifest_accepts_exact_baseline(self):
        manifest = {
            "schema_version": 1,
            "mod_id": "factoryprobe",
            "target": TARGET,
            "suites": [
                {"suite_id": "unit", "type": "unit", "state": "PASS", "command": "./gradlew --no-daemon test", "evidence": []},
                {"suite_id": "gametest", "type": "gametest", "state": "PASS", "command": "./gradlew --no-daemon runGameTestServer", "evidence": []},
                {"suite_id": "dedicated_server", "type": "dedicated_server", "state": "PASS", "command": "./gradlew --no-daemon runServer", "evidence": []},
            ],
            "overall_state": "PASS",
        }
        self.assertEqual(validate_i5_manifest(manifest), [])

    def test_validate_i5_manifest_rejects_target_drift(self):
        manifest = {
            "schema_version": 1,
            "mod_id": "factoryprobe",
            "target": dict(TARGET, minecraft="1.21.4"),
            "suites": [],
            "overall_state": "BLOCKED",
        }
        errors = validate_i5_manifest(manifest)
        self.assertTrue(any("target" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
