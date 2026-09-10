import contextlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "engineering" / "tooling" / "import-physical-modlist.py"
FIXTURE = ROOT / "engineering" / "tests" / "fixtures" / "modlist-i2-sample.txt"


def load_importer():
    spec = importlib.util.spec_from_file_location("i2_security_review", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class I2SecurityAndReviewContractTest(unittest.TestCase):
    def setUp(self):
        self.module = load_importer()
        self.snapshot = self.module.parse_modlist_text(
            FIXTURE.read_text(encoding="utf-8"),
            captured_at="2026-09-09",
        )

    def test_empty_mod_id_is_rejected(self):
        snapshot = json.loads(json.dumps(self.snapshot))
        snapshot["entries"][0]["mod_id"] = ""
        errors = self.module.validate_normalized_snapshot(snapshot)
        self.assertTrue(
            any("mod_id" in error for error in errors),
            "I2 RED: empty physical mod IDs must fail closed",
        )

    def test_snapshot_writer_rejects_destination_outside_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            outside = root / "outside.json"
            with contextlib.chdir(workspace):
                with self.assertRaises(ValueError):
                    self.module.write_persisted_snapshot(self.snapshot, outside, shard_size=2)
            self.assertFalse(outside.exists())

    def test_snapshot_loader_rejects_shard_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            with contextlib.chdir(workspace):
                manifest = self.module.write_persisted_snapshot(self.snapshot, Path("snapshot.json"), shard_size=2)
                shard = workspace / manifest["entry_shards"][0]["path"]
                external = root / "external-shard.json"
                external.write_bytes(shard.read_bytes())
                shard.unlink()
                shard.symlink_to(external)
                with self.assertRaises(ValueError):
                    self.module.load_persisted_snapshot(Path("snapshot.json"))

    def test_cli_rejects_input_outside_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            outside_input = root / "modlist.txt"
            outside_input.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
            with contextlib.chdir(workspace):
                with self.assertRaises(ValueError):
                    self.module.main([
                        str(outside_input),
                        "--captured-at",
                        "2026-09-09",
                        "--output",
                        "snapshot.json",
                    ])


if __name__ == "__main__":
    unittest.main()
