import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET_BASELINE = ROOT / "engineering" / "contracts" / "target-baseline.json"
LOCKFILES = (
    ROOT / "engineering" / "templates" / "neoforge-mod" / "gradle.lockfile.tmpl",
    ROOT / "engineering" / "tests" / "golden" / "i3-golden-mod" / "gradle.lockfile",
)


class I3FancyModLoaderLockContractTest(unittest.TestCase):
    def test_neoforge_21_1_250_uses_fml_4_0_44_lock_entries(self):
        baseline = json.loads(TARGET_BASELINE.read_text(encoding="utf-8"))
        self.assertEqual("21.1.250", baseline["target"]["neoforge"])

        required = (
            "net.neoforged.fancymodloader:earlydisplay:4.0.44=",
            "net.neoforged.fancymodloader:loader:4.0.44=",
        )
        stale = (
            "net.neoforged.fancymodloader:earlydisplay:4.0.43=",
            "net.neoforged.fancymodloader:loader:4.0.43=",
        )

        for lockfile in LOCKFILES:
            text = lockfile.read_text(encoding="utf-8")
            for entry in required:
                self.assertIn(entry, text, f"{lockfile} is not aligned with FancyModLoader 4.0.44")
            for entry in stale:
                self.assertNotIn(entry, text, f"{lockfile} still pins stale FancyModLoader 4.0.43")


if __name__ == "__main__":
    unittest.main()
