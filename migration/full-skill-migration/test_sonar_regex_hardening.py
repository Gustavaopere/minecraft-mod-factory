#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Historical evidence: PR #8 Sonar check 102867451898 annotated these live patterns.
# Formal RED: Full Skill run 34533379697 failed only this contract, with 9/9 subtests failing.
FLAGGED_PATTERNS = {
    "art/golden-samples/validate_reference_evidence.js": (
        ".replace(/!?\\[([^\\]]+)\\]\\([^)]+\\)/g, '$1')",
        ".replace(/!?\\[([^\\]]+)\\]\\[[^\\]]*\\]/g, '$1')",
        ".match(/^ {0,3}(`{3,}|~{3,})(.*)$/)",
    ),
    "art/tooling/validators/validate_golden_reference_rendered_edges.js": (
        ".replace(/!?\\[([^\\]]+)\\]\\([^)]+\\)/g, '$1')",
        ".replace(/!?\\[([^\\]]+)\\]\\[[^\\]]*\\]/g, '$1')",
        ".match(/^ {0,3}(`{3,}|~{3,})(.*)$/)",
        "const referenceDefinition = /^\\s*(?:(?:[-+*]|\\d+[.)])\\s+)*\\[[^\\]]{1,999}\\]:/m;",
    ),
    "art/tooling/blockbench/asset-toolkit/build_toolkit_bundle.js": (
        ".replace(/\\s+$/, '')",
    ),
    "skills/scripts/validate_skill_repository.py": (
        're.search(r"^name:\\s*([^\\n]+)$", path.read_text(encoding="utf-8"), re.MULTILINE)',
    ),
}


class SonarRegexHardeningContractTest(unittest.TestCase):
    def test_historical_sonar_superlinear_regex_patterns_are_removed(self) -> None:
        """Every regex explicitly annotated by Sonar on PR #8 must leave live Factory code."""
        for relative, patterns in FLAGGED_PATTERNS.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            for pattern in patterns:
                with self.subTest(path=relative, pattern=pattern):
                    self.assertNotIn(pattern, source)


if __name__ == "__main__":
    unittest.main()
