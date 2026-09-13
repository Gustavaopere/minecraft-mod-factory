#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
POLICY = ROOT / "engineering" / "tooling" / "ci" / "queue-control-policy.json"

CANONICAL_GROUP = "${{ github.workflow }}-${{ github.ref }}-${{ github.ref == 'refs/heads/main' && github.run_id || 'dedupe' }}"
CANONICAL_CANCEL = "${{ github.ref != 'refs/heads/main' }}"


def load_policy() -> dict[str, object]:
    return json.loads(POLICY.read_text(encoding="utf-8"))


def factory_workflow_paths() -> list[Path]:
    return sorted(WORKFLOWS.glob("factory-*.yml"))


def trigger_block(text: str, trigger: str) -> str:
    marker = f"  {trigger}:"
    start = text.find(marker)
    if start < 0:
        return ""
    lines = text[start:].splitlines()
    captured = [lines[0]]
    for line in lines[1:]:
        if line and not line.startswith("    "):
            break
        captured.append(line)
    return "\n".join(captured)


class QueueControlPolicyTest(unittest.TestCase):
    def test_policy_is_closed_over_factory_workflows(self) -> None:
        policy = load_policy()
        actual = {
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in factory_workflow_paths()
        }
        declared = set(policy["workflows"])
        self.assertEqual(declared, actual)
        self.assertEqual(len(actual), 41)

    def test_global_and_mutating_classifications_are_exact(self) -> None:
        policy = load_policy()["workflows"]
        self.assertEqual(
            policy[".github/workflows/factory-e1-s1-governance.yml"]["class"],
            "GLOBAL_READ_ONLY",
        )
        self.assertEqual(
            policy[".github/workflows/factory-sonar-ci.yml"]["class"],
            "GLOBAL_READ_ONLY",
        )
        self.assertEqual(
            policy[".github/workflows/factory-full-skill-materialize.yml"]["class"],
            "MUTATING_EXEMPT",
        )

    def test_i9_main_push_is_path_scoped(self) -> None:
        text = (WORKFLOWS / "factory-engineering-i9-machine-foundation.yml").read_text(
            encoding="utf-8"
        )
        push = trigger_block(text, "push")
        self.assertIn("\n    paths:", push, "I9 main push must be path-scoped")

    def test_sonar_has_safe_read_only_concurrency(self) -> None:
        text = (WORKFLOWS / "factory-sonar-ci.yml").read_text(encoding="utf-8")
        self.assertIn("concurrency:", text)
        self.assertIn(f"group: {CANONICAL_GROUP}", text)
        self.assertIn(f"cancel-in-progress: {CANONICAL_CANCEL}", text)

    def test_mutating_materializer_has_no_cancel_in_progress(self) -> None:
        text = (WORKFLOWS / "factory-full-skill-materialize.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("cancel-in-progress:", text)


if __name__ == "__main__":
    unittest.main()
