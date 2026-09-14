import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "art" / "tooling" / "validate_npc_visual_assets.py"
spec = importlib.util.spec_from_file_location("npc_visual_asset_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def write_png(path: Path, width: int, height: int) -> None:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    scanline = b"\x00" + (b"\x00\x00\x00" * width)
    raw = scanline * height
    path.write_bytes(signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NpcVisualAssetManifestTest(unittest.TestCase):
    def test_candidate_uses_declared_metadata_without_forcing_master_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "campaign" / "assets" / "npcs"
            asset_root.mkdir(parents=True)
            image = asset_root / "npc.png"
            write_png(image, 32, 32)
            manifest = {
                "schema_version": 1,
                "asset_root": "campaign/assets/npcs",
                "policy": {
                    "portrait_master": {"width": 2048, "height": 2048, "format": "PNG", "require_native_target_resolution": True},
                    "humanoid_skin": {"width": 64, "height": 64, "format": "PNG"},
                },
                "assets": [
                    {
                        "asset_kind": "portrait",
                        "status": "CANDIDATE",
                        "path": "campaign/assets/npcs/npc.png",
                        "width": 32,
                        "height": 32,
                        "format": "PNG",
                        "sha256": digest(image),
                        "native_target_resolution": False,
                        "final_asset": False,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual([], validator.validate_manifest(manifest_path, root))

    def test_approved_master_is_checked_against_consumer_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "campaign" / "assets" / "npcs"
            asset_root.mkdir(parents=True)
            image = asset_root / "npc.png"
            write_png(image, 64, 64)
            manifest = {
                "schema_version": 1,
                "asset_root": "campaign/assets/npcs",
                "policy": {
                    "portrait_master": {"width": 128, "height": 128, "format": "PNG", "require_native_target_resolution": True}
                },
                "assets": [
                    {
                        "asset_kind": "portrait",
                        "status": "APPROVED MASTER",
                        "path": "campaign/assets/npcs/npc.png",
                        "width": 64,
                        "height": 64,
                        "format": "PNG",
                        "sha256": digest(image),
                        "native_target_resolution": False,
                        "final_asset": False,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validator.validate_manifest(manifest_path, root)
            self.assertTrue(any("policy width 128" in error for error in errors))
            self.assertTrue(any("policy height 128" in error for error in errors))
            self.assertTrue(any("native_target_resolution=true" in error for error in errors))

    def test_final_portrait_is_checked_against_master_policy_even_when_final_flag_is_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "campaign" / "assets" / "npcs"
            asset_root.mkdir(parents=True)
            image = asset_root / "npc.png"
            write_png(image, 64, 64)
            manifest = {
                "schema_version": 1,
                "asset_root": "campaign/assets/npcs",
                "policy": {
                    "portrait_master": {"width": 128, "height": 128, "format": "PNG", "require_native_target_resolution": True}
                },
                "assets": [
                    {
                        "asset_kind": "portrait",
                        "status": "FINAL",
                        "path": "campaign/assets/npcs/npc.png",
                        "width": 64,
                        "height": 64,
                        "format": "PNG",
                        "sha256": digest(image),
                        "native_target_resolution": False,
                        "final_asset": False,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validator.validate_manifest(manifest_path, root)
            self.assertTrue(any("policy width 128" in error for error in errors))
            self.assertTrue(any("policy height 128" in error for error in errors))
            self.assertTrue(any("native_target_resolution=true" in error for error in errors))

    def test_asset_path_cannot_escape_asset_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "campaign" / "assets" / "npcs").mkdir(parents=True)
            image = root / "outside.png"
            write_png(image, 16, 16)
            manifest = {
                "schema_version": 1,
                "asset_root": "campaign/assets/npcs",
                "assets": [
                    {
                        "asset_kind": "portrait",
                        "status": "CANDIDATE",
                        "path": "outside.png",
                        "width": 16,
                        "height": 16,
                        "format": "PNG",
                        "sha256": digest(image),
                        "native_target_resolution": False,
                        "final_asset": False,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validator.validate_manifest(manifest_path, root)
            self.assertTrue(any("path must stay under asset_root" in error for error in errors))

    def test_absolute_asset_root_is_rejected_even_when_inside_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "campaign" / "assets" / "npcs"
            asset_root.mkdir(parents=True)
            manifest = {
                "schema_version": 1,
                "asset_root": str(asset_root),
                "assets": [],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validator.validate_manifest(manifest_path, root)
            self.assertTrue(any("asset_root must be repository-relative" in error for error in errors))

    def test_absolute_asset_path_is_rejected_even_when_inside_asset_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "campaign" / "assets" / "npcs"
            asset_root.mkdir(parents=True)
            image = asset_root / "npc.png"
            write_png(image, 16, 16)
            manifest = {
                "schema_version": 1,
                "asset_root": "campaign/assets/npcs",
                "assets": [
                    {
                        "asset_kind": "portrait",
                        "status": "CANDIDATE",
                        "path": str(image),
                        "width": 16,
                        "height": 16,
                        "format": "PNG",
                        "sha256": digest(image),
                        "native_target_resolution": False,
                        "final_asset": False,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validator.validate_manifest(manifest_path, root)
            self.assertTrue(any("path must be repository-relative" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
