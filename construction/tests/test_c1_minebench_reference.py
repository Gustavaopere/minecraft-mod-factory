from __future__ import annotations

import configparser
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PATH = "construction/upstream/references/minebench"
SUBMODULE_SECTION = f'submodule "{REFERENCE_PATH}"'
UPSTREAM_REPOSITORY = "Ammaar-Alam/minebench"
UPSTREAM_URL = "https://github.com/Ammaar-Alam/minebench.git"
PINNED_COMMIT = "c96abbd4c4098aa9c264490c80a1c6544a64ba85"
WORKFLOW = ROOT / ".github/workflows/factory-construction-c1-minebench-reference.yml"
CHECKOUT_ACTION = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
SETUP_NODE_ACTION = "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38"
PNPM_ACTION = "pnpm/action-setup@0977fd99725f1db4007ccb2928dbb4e90d06cc86"


class ConstructionC1MineBenchReferenceTest(unittest.TestCase):
    def test_registry_matches_minebench_reference_contract(self) -> None:
        registry = json.loads(
            (ROOT / "construction/upstream/registry.json").read_text(encoding="utf-8")
        )
        minebench = next(
            source for source in registry["sources"] if source["id"] == "minebench"
        )
        self.assertEqual(minebench["repository"], UPSTREAM_REPOSITORY)
        self.assertEqual(minebench["pinned_commit"], PINNED_COMMIT)
        self.assertEqual(minebench["integration_policy"], "ENGINE_REFERENCE")
        self.assertEqual(minebench["license"], "MIT")

    def test_gitmodules_declares_exact_minebench_reference(self) -> None:
        path = ROOT / ".gitmodules"
        self.assertTrue(path.is_file(), ".gitmodules is required for C1B")
        parser = configparser.ConfigParser()
        parser.read(path, encoding="utf-8")
        self.assertIn(SUBMODULE_SECTION, parser)
        section = parser[SUBMODULE_SECTION]
        self.assertEqual(section.get("path"), REFERENCE_PATH)
        self.assertEqual(section.get("url"), UPSTREAM_URL)

    def test_workflow_pins_actions_and_reference_integrity(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(CHECKOUT_ACTION, workflow)
        self.assertIn(SETUP_NODE_ACTION, workflow)
        self.assertIn(PNPM_ACTION, workflow)
        self.assertIn("node-version: '24'", workflow)
        self.assertIn("version: '10.26.1'", workflow)
        self.assertIn("pnpm install --frozen-lockfile", workflow)
        self.assertIn(f"160000 {PINNED_COMMIT} 0", workflow)
        self.assertIn(f"git ls-files --stage -- {REFERENCE_PATH}", workflow)
        self.assertNotIn("OPENAI_API_KEY", workflow)
        self.assertNotIn("ANTHROPIC_API_KEY", workflow)
        self.assertNotIn("OPENROUTER_API_KEY", workflow)

    def test_workflow_has_no_literal_postgres_password(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("POSTGRES_PASSWORD: minebench", workflow)
        self.assertNotIn("postgresql://minebench:minebench@", workflow)

    def test_workflow_revalidates_c1b_on_main_push(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "push:\n    branches:\n      - main\n      - feat/construction-c1-minebench-reference",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
