#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "migration/full-skill-migration/check_whitespace.py"
SONAR_WORKFLOW = ROOT / ".github/workflows/factory-sonar-ci.yml"


def load_checker():
    spec = importlib.util.spec_from_file_location("full_skill_whitespace_markdown", CHECKER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CHECKER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MarkdownWhitespacePolicyTest(unittest.TestCase):
    def test_markdown_two_space_hard_break_is_not_reported(self):
        checker = load_checker()
        output = (
            "plans/textura/README.md:3: trailing whitespace.\n"
            "+**Data:** 2026-09-13  \n"
            "plans/textura/README.md:4: trailing whitespace.\n"
            "+bad   \n"
            "engineering/tooling/example.py:7: trailing whitespace.\n"
            "+bad  \n"
        )
        filtered = checker.filter_whitespace_diagnostics(output, set())
        self.assertNotIn("plans/textura/README.md:3", filtered)
        self.assertNotIn("+**Data:** 2026-09-13  ", filtered)
        self.assertIn("plans/textura/README.md:4", filtered)
        self.assertIn("+bad   ", filtered)
        self.assertIn("engineering/tooling/example.py:7", filtered)
        self.assertIn("+bad  ", filtered)

    def test_sonar_ci_covers_changed_whitespace_checker(self):
        workflow = SONAR_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("--include=migration/full-skill-migration/check_whitespace.py", workflow)
        self.assertIn("migration/full-skill-migration/test_markdown_whitespace_policy.py", workflow)


if __name__ == "__main__":
    unittest.main()
