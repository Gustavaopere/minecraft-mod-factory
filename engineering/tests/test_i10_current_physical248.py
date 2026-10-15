"""Prove the current-HEAD physical 21.1.248 handoff is explicitly derived."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DERIVER = ROOT / "engineering/tests/experiments/i10_current_physical248.py"
MATERIALIZER = ROOT / "engineering/tooling/multiblock-foundation/materialize_i10.py"
SHA = "b" * 40


def load(path):
    assert path.is_file(), f"I10 RED: required executable missing: {path}"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CurrentPhysical248Test(unittest.TestCase):
    def test_exact_current_head_derivation_and_byte_integrity(self):
        materializer = load(MATERIALIZER)
        deriver = load(DERIVER)
        with tempfile.TemporaryDirectory(prefix=".i10-248-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            source = materializer.materialize_i10(root / "source")
            (source / "I10-SOURCE-COMMIT.txt").write_text(SHA + "\n", encoding="utf-8")
            output, archive = root / "derived", root / "derived.zip"
            evidence = deriver.derive(source, output, archive, SHA)
            manifest = json.loads((output / "I10-PROFILE-RECONCILIATION.json").read_text())
            self.assertEqual(SHA, evidence["source_commit"])
            self.assertEqual("21.1.248", evidence["target_neoforge"])
            self.assertEqual("4.0.43", manifest["target_fml"])
            self.assertEqual("PENDING", manifest["two_real_clients"])
            self.assertEqual("UNPROVEN", manifest["physical_missing_neighbor"])
            self.assertEqual(["gradle.lockfile", "gradle.properties", "run-i10-manual-process.py"],
                             manifest["modified_paths"])
            self.assertIn("neo_version=21.1.248", (output / "gradle.properties").read_text())
            self.assertIn("net.neoforged:neoforge:21.1.248=sdk,testSdk",
                          (output / "gradle.lockfile").read_text())
            self.assertIn('"neoforge": "21.1.248"',
                          (output / "run-i10-manual-process.py").read_text())
            self.assertTrue(archive.is_file())
            self.assertEqual(15, len(list(output.rglob("*.java"))))
            for path in source.rglob("*"):
                if path.is_file():
                    rel = path.relative_to(source)
                    if rel.as_posix() not in manifest["modified_paths"]:
                        self.assertEqual(path.read_bytes(), (output / rel).read_bytes(), str(rel))

    def test_wrong_commit_and_existing_destination_fail_closed(self):
        materializer, deriver = load(MATERIALIZER), load(DERIVER)
        with tempfile.TemporaryDirectory(prefix=".i10-248-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            source = materializer.materialize_i10(root / "source")
            (source / "I10-SOURCE-COMMIT.txt").write_text(SHA + "\n", encoding="utf-8")
            with self.assertRaisesRegex(deriver.ProfileBlocked, "source commit"):
                deriver.derive(source, root / "derived", root / "derived.zip", "a" * 40)
            (root / "derived").mkdir()
            with self.assertRaisesRegex(deriver.ProfileBlocked, "overwrite"):
                deriver.derive(source, root / "derived", root / "derived.zip", SHA)

    def test_symlink_and_wrong_loader_rejected(self):
        materializer, deriver = load(MATERIALIZER), load(DERIVER)
        with tempfile.TemporaryDirectory(prefix=".i10-248-test-", dir=ROOT) as tmp:
            root = Path(tmp)
            source = materializer.materialize_i10(root / "source")
            (source / "I10-SOURCE-COMMIT.txt").write_text(SHA + "\n", encoding="utf-8")
            (source / "unsafe-link").symlink_to(source / "gradle.properties")
            with self.assertRaisesRegex(deriver.ProfileBlocked, "symlink"):
                deriver.derive(source, root / "derived", root / "derived.zip", SHA)
            (source / "unsafe-link").unlink()
            properties = source / "gradle.properties"
            properties.write_text(properties.read_text().replace(
                "neo_version=21.1.250", "neo_version=21.1.247"))
            with self.assertRaisesRegex(deriver.ProfileBlocked, "target|anchor|profile"):
                deriver.derive(source, root / "derived", root / "derived.zip", SHA)


if __name__ == "__main__":
    unittest.main()
