from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "construction" / "fixtures" / "complex-modded-golden"
REGISTRY_PATH = FIXTURE / "registry.json"
CAPTURE_PATH = FIXTURE / "capture_registry.py"
C4_PATH = ROOT / "construction" / "core" / "modpack_registry.py"
PHYSICAL_MODLIST_SHA256 = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"

CAPTURE_SAMPLE = """Mods count: 2

jar name | notes | mod id | mod name | mod version | mixin configs | modrinth hash | curseforge hash
---------+-------+--------+----------+-------------+---------------+---------------+----------------
neoforge-21.1.248 (modloader) | | neoforge | NeoForge | neoforge-21.1.248 | | |
alpha-1.0.0.jar | | alpha | Alpha | 1.0.0 | | |
"""


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC11ComplexModdedGoldenTest(unittest.TestCase):
    def test_real_c4_registry_fixture_exists_and_is_canonical(self) -> None:
        self.assertTrue(
            REGISTRY_PATH.is_file(),
            "C11 requires captured real C4 registry evidence",
        )
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        c4 = load_path(C4_PATH, "construction_c4_for_c11")
        self.assertEqual([], c4.validate_modpack_registry(registry))
        self.assertEqual(
            PHYSICAL_MODLIST_SHA256,
            registry["physical"]["source_sha256"],
        )
        self.assertEqual(
            PHYSICAL_MODLIST_SHA256,
            registry["runtime"]["physical_snapshot_sha256"],
        )
        self.assertEqual(
            {
                "minecraft": "1.21.1",
                "loader": "neoforge",
                "loader_version": "21.1.248",
            },
            registry["runtime"]["target"],
        )

    def test_capture_helper_requires_every_physical_top_level_jar(self) -> None:
        self.assertTrue(CAPTURE_PATH.is_file(), "C11 registry capture helper is required")
        capture = load_path(CAPTURE_PATH, "construction_c11_capture_registry")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            modlist = root / "modlist.txt"
            mods_dir = root / "mods"
            runtime_snapshot = root / "runtime.json"
            modlist.write_text(CAPTURE_SAMPLE, encoding="utf-8")
            mods_dir.mkdir()
            with self.assertRaisesRegex(
                ValueError,
                r"^missing physical top-level JARs: alpha-1\.0\.0\.jar$",
            ):
                capture.compose_registry(
                    modlist,
                    mods_dir,
                    runtime_snapshot,
                    captured_at="2026-09-09",
                )


if __name__ == "__main__":
    unittest.main()
