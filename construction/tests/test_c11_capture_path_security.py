from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
CAPTURE_PATH = ROOT / "construction" / "fixtures" / "complex-modded-golden" / "capture_registry.py"

CAPTURE_SAMPLE = """Mods count: 2

jar name | notes | mod id | mod name | mod version | mixin configs | modrinth hash | curseforge hash
---------+-------+--------+----------+-------------+---------------+---------------+----------------
neoforge-21.1.248 (modloader) | | neoforge | NeoForge | neoforge-21.1.248 | | |
alpha-1.0.0.jar | | alpha | Alpha | 1.0.0 | | |
"""


def load_capture(name: str):
    spec = importlib.util.spec_from_file_location(name, CAPTURE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {CAPTURE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_runtime_snapshot() -> dict:
    return {
        "schema_version": 1,
        "captured_at": "2026-09-13T00:00:00Z",
        "physical_snapshot_sha256": hashlib.sha256(CAPTURE_SAMPLE.encode("utf-8")).hexdigest(),
        "target": {
            "minecraft": "1.21.1",
            "loader": "neoforge",
            "loader_version": "21.1.248",
        },
        "blocks": [
            {
                "id": "minecraft:stone",
                "safety": "ordinary",
                "states": [{}],
            }
        ],
    }


class ConstructionC11CapturePathSecurityTest(unittest.TestCase):
    def _prepare(self, root: Path) -> tuple[Path, Path, Path, Path]:
        workspace = root / "workspace"
        outside = root / "outside"
        mods_dir = root / "mods"
        workspace.mkdir()
        outside.mkdir()
        mods_dir.mkdir()
        with zipfile.ZipFile(mods_dir / "alpha-1.0.0.jar", "w"):
            pass
        return workspace, outside, mods_dir, root

    def _run_main(self, capture, workspace: Path, argv: list[str]) -> int:
        previous = Path.cwd()
        try:
            os.chdir(workspace)
            with mock.patch.object(sys, "argv", argv):
                return capture.main()
        finally:
            os.chdir(previous)

    def test_cli_rejects_physical_modlist_parent_traversal(self) -> None:
        capture = load_capture("construction_c11_capture_path_physical")
        with tempfile.TemporaryDirectory() as tmp:
            workspace, outside, mods_dir, _ = self._prepare(Path(tmp))
            (outside / "modlist.txt").write_text(CAPTURE_SAMPLE, encoding="utf-8")
            (workspace / "runtime.json").write_text(
                json.dumps(valid_runtime_snapshot()),
                encoding="utf-8",
            )
            argv = [
                str(CAPTURE_PATH),
                "--physical-modlist",
                "../outside/modlist.txt",
                "--mods-dir",
                str(mods_dir),
                "--runtime-snapshot",
                "runtime.json",
                "--captured-at",
                "2026-09-13",
                "--output",
                "out/registry.json",
            ]
            with self.assertRaisesRegex(
                ValueError,
                r"^physical modlist must stay inside workspace: ",
            ):
                self._run_main(capture, workspace, argv)

    def test_cli_rejects_runtime_snapshot_parent_traversal(self) -> None:
        capture = load_capture("construction_c11_capture_path_runtime")
        with tempfile.TemporaryDirectory() as tmp:
            workspace, outside, mods_dir, _ = self._prepare(Path(tmp))
            (workspace / "modlist.txt").write_text(CAPTURE_SAMPLE, encoding="utf-8")
            (outside / "runtime.json").write_text(
                json.dumps(valid_runtime_snapshot()),
                encoding="utf-8",
            )
            argv = [
                str(CAPTURE_PATH),
                "--physical-modlist",
                "modlist.txt",
                "--mods-dir",
                str(mods_dir),
                "--runtime-snapshot",
                "../outside/runtime.json",
                "--captured-at",
                "2026-09-13",
                "--output",
                "out/registry.json",
            ]
            with self.assertRaisesRegex(
                ValueError,
                r"^runtime snapshot must stay inside workspace: ",
            ):
                self._run_main(capture, workspace, argv)


if __name__ == "__main__":
    unittest.main()
