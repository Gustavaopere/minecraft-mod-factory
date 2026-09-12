from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
C0_WORKFLOW = ROOT / ".github" / "workflows" / "factory-construction-c0-foundation.yml"


class C9C0AggregateContractTests(unittest.TestCase):
    def test_c0_aggregate_installs_c9_hash_pinned_additions(self) -> None:
        workflow = C0_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "python3 -m pip install --require-hashes --no-deps -r "
            "construction/upstream/harness/schematica-test-lock.txt",
            workflow,
        )
        self.assertIn(
            "python3 -m pip install --require-hashes --no-deps -r "
            "construction/upstream/harness/c9-mcp-lock.txt",
            workflow,
        )
        self.assertIn("python3 -m pip check", workflow)
        self.assertIn(
            'python3 -c \'from importlib.metadata import version; '
            'assert version("mcp") == "2.2.0"\'',
            workflow,
        )
        self.assertNotIn("pip install mcp", workflow)
        self.assertNotIn("pip install -U", workflow)
        self.assertNotIn("pip install --upgrade", workflow)


if __name__ == "__main__":
    unittest.main()
