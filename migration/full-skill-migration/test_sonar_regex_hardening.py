#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ANNOTATED_SLOW_REGEXES = {
    "skills/scripts/validate_skill_repository.py": (
        r're.search(r"^name:\s*([^\n]+)$"',
    ),
    "art/tooling/blockbench/asset-toolkit/build_toolkit_bundle.js": (
        r".replace(/\s+$/, '')",
    ),
    "art/golden-samples/validate_reference_evidence.js": (
        r".replace(/!?\[([^\]]+)\]\([^)]+\)/g, '$1')",
        r".replace(/!?\[([^\]]+)\]\[[^\]]*\]/g, '$1')",
        r"/^:?-{3,}:?$/",
    ),
    "art/tooling/validators/validate_golden_reference_rendered_edges.js": (
        r".replace(/!?\[([^\]]+)\]\([^)]+\)/g, '$1')",
        r".replace(/!?\[([^\]]+)\]\[[^\]]*\]/g, '$1')",
        r"/^ {0,3}(`{3,}|~{3,})(.*)$/",
        r"/^\s*(?:(?:[-+*]|\d+[.)])\s+)*\[[^\]]{1,999}\]:/m",
    ),
}


class SonarRegexHardeningTest(unittest.TestCase):
    def test_pr8_annotated_slow_regexes_are_removed_from_canonical_code(self) -> None:
        failures: list[str] = []
        for relative, patterns in ANNOTATED_SLOW_REGEXES.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            for pattern in patterns:
                if pattern in source:
                    failures.append(f"{relative}: {pattern}")
        self.assertEqual(
            failures,
            [],
            "PR #8 Sonar slow-regex findings must be removed from canonical analyzed code; remaining="
            + repr(failures),
        )


if __name__ == "__main__":
    unittest.main()
