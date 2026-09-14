from __future__ import annotations

import json
import unittest
from pathlib import Path

from skills.scripts.capability_router import TARGET

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "engineering/contracts/target-baseline.json"
INDEX = ROOT / "skills/capabilities/capability-index.json"
SCHEMA = ROOT / "skills/capabilities/capability-index.schema.json"
WORKFLOW = ROOT / ".github/workflows/factory-construction-c13-skill-router.yml"


def _campaign_target() -> dict[str, object]:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    target = baseline["target"]
    return {
        key: target[key]
        for key in ("minecraft", "loader", "neoforge", "java")
    }


class C13CampaignTargetTest(unittest.TestCase):
    def test_router_target_matches_campaign_authority(self) -> None:
        self.assertEqual(TARGET, _campaign_target())

    def test_capability_index_target_matches_campaign_authority(self) -> None:
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertEqual(index["target"], _campaign_target())

    def test_capability_schema_target_matches_campaign_authority(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        properties = schema["properties"]["target"]["properties"]
        schema_target = {
            key: properties[key]["const"]
            for key in ("minecraft", "loader", "neoforge", "java")
        }
        self.assertEqual(schema_target, _campaign_target())

    def test_workflow_runs_when_campaign_target_changes(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        token = "'engineering/contracts/target-baseline.json'"
        self.assertGreaterEqual(text.count(token), 2)


if __name__ == "__main__":
    unittest.main()
