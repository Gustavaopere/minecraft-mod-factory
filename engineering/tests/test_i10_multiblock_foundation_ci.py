from __future__ import annotations

import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github/workflows/factory-engineering-i10-multiblock-foundation.yml"
SONAR_WORKFLOW = REPO / ".github/workflows/factory-sonar-ci.yml"
PROTOCOL = REPO / "engineering/tests/i10-multiplayer-acceptance.md"


class I10PermanentCIContract(unittest.TestCase):
    def test_workflow_is_permanent_on_main_and_tracks_shared_dependencies(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        push_section = text.split("  push:", 1)[1].split("  pull_request:", 1)[0]
        self.assertIn("- main", push_section, "I10 permanent workflow must run on main pushes")
        self.assertIn("- engineering/i10-multiblock-foundation-reference", push_section)

        for token in (
            "'engineering/tests/test_i10_multiblock_foundation*.py'",
            "'engineering/templates/neoforge-mod/**'",
            "'engineering/tooling/scaffolder/**'",
            "'engineering/tooling/test-harness/**'",
            "'engineering/tooling/asset-handoff/**'",
            "'engineering/schemas/asset-handoff.schema.json'",
            "'engineering/tooling/feature-generator/**'",
            "'engineering/tooling/machine-foundation/**'",
        ):
            self.assertIn(token, text, f"I10 workflow must track shared dependency path: {token}")
        self.assertNotIn("test_i10_multiblock-foundation*.py", text)

    def test_relevant_engineering_regressions_are_explicit(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        for token in (
            "engineering/tests/test_i3_mod_scaffolder.py",
            "engineering/tests/test_i3_security_review.py",
            "engineering/tests/test_i4_engineering_validators.py",
            "engineering/tests/test_i5_test_harness.py",
            "engineering/tests/test_i6_asset_handoff.py",
            "engineering/tests/test_i8_feature_generator.py",
            "engineering/tests/test_i8_feature_generator_neoforge.py",
            "engineering/tests/test_i9_machine_foundation.py",
            "engineering/tests/test_i9_machine_foundation_composition.py",
            "engineering/tests/test_i10_multiblock_foundation.py",
            "engineering/tests/test_i10_multiblock_foundation_task5.py",
            "engineering/tests/test_i10_multiblock_foundation_handoff.py",
            "engineering/tests/test_i10_multiblock_foundation_gametest.py",
            "engineering/tests/test_i10_multiblock_foundation_provider.py",
            "engineering/tests/test_i10_chunk_acceptance.py",
            "engineering/tests/test_i10_multiplayer_acceptance.py",
            "engineering/tests/test_i10_multiblock_foundation_composition.py",
            "engineering/tests/test_i10_multiblock_foundation_ci.py",
        ):
            self.assertIn(token, text, f"I10 permanent CI is missing regression: {token}")

    def test_i5_dedicated_server_harness_is_a_required_gate(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        for token in (
            "Accept EULA in generated fixture only",
            "engineering/tooling/test-harness/run_test_harness.py",
            "--project .factory-ci/i10/generated",
            "Verify I5 manifest",
            "build/i5-test-harness/test-manifest.json",
            "'unit': 'PASS'",
            "'gametest': 'PASS'",
            "'dedicated_server': 'PASS'",
        ):
            self.assertIn(token, text, f"I10 permanent CI is missing I5 gate token: {token}")

    def test_sonar_fail_closed_coverage_includes_i10_tooling(self) -> None:
        text = SONAR_WORKFLOW.read_text(encoding="utf-8")
        for token in (
            "--source=engineering/tooling/multiblock-foundation",
            "engineering/tests/test_i10_multiblock_foundation.py",
            "engineering/tests/test_i10_multiblock_foundation_composition.py",
            "engineering/tests/test_i10_chunk_acceptance.py",
            "--include='engineering/tooling/multiblock-foundation/*'",
            "--fail-under=80",
        ):
            self.assertIn(token, text, f"Sonar CI must measure I10 tooling coverage: {token}")

    def test_multiplayer_remains_fail_closed_until_real_evidence(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        protocol = PROTOCOL.read_text(encoding="utf-8")
        self.assertIn(
            "I10_MULTIPLAYER_ACCEPTANCE_STATE=PENDING_MANUAL_MULTIPLAYER_ACCEPTANCE",
            protocol,
        )
        self.assertNotIn("I10_MULTIPLAYER_ACCEPTANCE_STATE=PASS", protocol)
        self.assertNotIn("I10_MULTIPLAYER_ACCEPTANCE_STATE=PASS", workflow)
        self.assertNotIn("fake player", workflow.lower())


if __name__ == "__main__":
    unittest.main()
