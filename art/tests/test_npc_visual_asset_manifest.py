import contextlib
import hashlib
import importlib.util
import io
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "art" / "tooling" / "validate_npc_visual_assets.py"
spec = importlib.util.spec_from_file_location("npc_visual_asset_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def write_png(path: Path, width: int, height: int) -> None:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, data: bytes) -> bytes:
        checksum = zlib.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    scanline = b"\x00" + (b"\x00\x00\x00" * width)
    raw = scanline * height
    path.write_bytes(
        signature
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def write_jpeg(path: Path, width: int, height: int) -> None:
    app0_payload = b"AB"
    app0 = b"\xff\xe0" + struct.pack(">H", len(app0_payload) + 2) + app0_payload
    sof_payload = b"\x08" + struct.pack(">HH", height, width)
    sof0 = b"\xff\xc0" + struct.pack(">H", len(sof_payload) + 2) + sof_payload
    path.write_bytes(b"\xff\xd8" + app0 + sof0)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(root: Path, manifest: object) -> Path:
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def make_asset(
    root: Path,
    image: Path,
    *,
    asset_kind: str = "portrait",
    status: str = "CANDIDATE",
    width: int | None = None,
    height: int | None = None,
    image_format: str = "PNG",
    native_target_resolution: bool = False,
    final_asset: bool = False,
) -> dict[str, object]:
    actual_width, actual_height, _ = validator.image_info(image)
    return {
        "asset_kind": asset_kind,
        "status": status,
        "path": image.relative_to(root).as_posix(),
        "width": actual_width if width is None else width,
        "height": actual_height if height is None else height,
        "format": image_format,
        "sha256": digest(image),
        "native_target_resolution": native_target_resolution,
        "final_asset": final_asset,
    }


def base_manifest(assets: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "asset_root": "campaign/assets/npcs",
        "policy": {
            "portrait_master": {
                "width": 128,
                "height": 128,
                "format": "PNG",
                "require_native_target_resolution": True,
            },
            "humanoid_skin": {"width": 64, "height": 64, "format": "PNG"},
        },
        "assets": assets,
    }


class NpcVisualAssetManifestTest(unittest.TestCase):
    def make_png(self, root: Path, name: str = "npc.png", width: int = 32, height: int = 32) -> Path:
        asset_root = root / "campaign" / "assets" / "npcs"
        asset_root.mkdir(parents=True, exist_ok=True)
        image = asset_root / name
        write_png(image, width, height)
        return image

    def test_candidate_uses_declared_metadata_without_forcing_master_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = self.make_png(root)
            manifest = base_manifest([make_asset(root, image)])
            self.assertEqual([], validator.validate_manifest(write_manifest(root, manifest), root))

    def test_approved_master_is_checked_against_consumer_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = self.make_png(root, width=64, height=64)
            asset = make_asset(root, image, status="APPROVED MASTER")
            errors = validator.validate_manifest(write_manifest(root, base_manifest([asset])), root)
            self.assertTrue(any("policy width 128" in error for error in errors))
            self.assertTrue(any("policy height 128" in error for error in errors))
            self.assertTrue(any("native_target_resolution=true" in error for error in errors))

    def test_final_portrait_is_checked_against_master_policy_even_when_final_flag_is_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = self.make_png(root, width=64, height=64)
            asset = make_asset(root, image, status="FINAL")
            errors = validator.validate_manifest(write_manifest(root, base_manifest([asset])), root)
            self.assertTrue(any("policy width 128" in error for error in errors))
            self.assertTrue(any("policy height 128" in error for error in errors))
            self.assertTrue(any("native_target_resolution=true" in error for error in errors))

    def test_valid_final_portrait_and_skin_pass_consumer_policies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            portrait = self.make_png(root, "portrait.png", 128, 128)
            skin = self.make_png(root, "skin.png", 64, 64)
            assets = [
                make_asset(
                    root,
                    portrait,
                    status="FINAL",
                    native_target_resolution=True,
                    final_asset=True,
                ),
                make_asset(root, skin, asset_kind="skin", status="SKIN CANDIDATE"),
            ]
            self.assertEqual(
                [],
                validator.validate_manifest(write_manifest(root, base_manifest(assets)), root),
            )

    def test_jpeg_candidate_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "campaign" / "assets" / "npcs"
            asset_root.mkdir(parents=True)
            image = asset_root / "npc.jpg"
            write_jpeg(image, 41, 29)
            asset = make_asset(root, image, image_format="JPEG")
            manifest = base_manifest([asset])
            self.assertEqual([], validator.validate_manifest(write_manifest(root, manifest), root))

    def test_image_readers_and_extension_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            png = root / "image.png"
            jpg = root / "image.jpeg"
            gif = root / "image.gif"
            write_png(png, 7, 9)
            write_jpeg(jpg, 11, 13)
            gif.write_bytes(b"GIF89a")
            self.assertEqual((7, 9, "PNG"), validator.image_info(png))
            self.assertEqual((11, 13, "JPEG"), validator.image_info(jpg))
            with self.assertRaisesRegex(ValueError, "unsupported image extension"):
                validator.image_info(gif)

    def test_invalid_png_header_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.png"
            path.write_bytes(b"not-a-png")
            with self.assertRaisesRegex(ValueError, "invalid PNG signature/IHDR"):
                validator.read_png_size(path)

    def test_jpeg_parser_fails_closed_on_malformed_segments(self):
        cases = {
            "bad-soi": (b"NO", "invalid JPEG SOI"),
            "no-sof": (b"\xff\xd8abc", "JPEG SOF marker not found"),
            "truncated-marker": (b"\xff\xd8\xff", "truncated JPEG marker"),
            "eoi-before-sof": (b"\xff\xd8\xff\xd9", "JPEG ended before SOF marker"),
            "truncated-length": (b"\xff\xd8\xff\xe0\x00", "truncated JPEG segment length"),
            "short-length": (b"\xff\xd8\xff\xe0\x00\x01", "invalid JPEG segment length"),
            "truncated-sof": (b"\xff\xd8\xff\xc0\x00\x07\x08\x00", "truncated JPEG SOF segment"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, (payload, message) in cases.items():
                with self.subTest(name=name):
                    path = root / f"{name}.jpg"
                    path.write_bytes(payload)
                    with self.assertRaisesRegex(ValueError, message):
                        validator.read_jpeg_size(path)

    def test_jpeg_parser_accepts_fill_bytes_and_no_length_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "filled.jpg"
            sof_payload = b"\x08" + struct.pack(">HH", 19, 17)
            path.write_bytes(
                b"\xff\xd8"
                + b"\xff\xff\xd0"
                + b"\xff\xc0"
                + struct.pack(">H", len(sof_payload) + 2)
                + sof_payload
            )
            self.assertEqual((17, 19, "JPEG"), validator.read_jpeg_size(path))

    def test_positive_integer_helper_rejects_bool_zero_and_non_integer(self):
        self.assertTrue(validator._positive_int(1))
        self.assertFalse(validator._positive_int(True))
        self.assertFalse(validator._positive_int(0))
        self.assertFalse(validator._positive_int("1"))

    def test_apply_policy_reports_invalid_policy_values(self):
        errors: list[str] = []
        validator._apply_policy(
            errors,
            "asset",
            {"native_target_resolution": False},
            (64, 64, "PNG"),
            {
                "width": True,
                "height": 0,
                "format": "",
                "require_native_target_resolution": True,
            },
        )
        self.assertTrue(any("policy width must be a positive integer" in error for error in errors))
        self.assertTrue(any("policy height must be a positive integer" in error for error in errors))
        self.assertTrue(any("policy format must be a non-empty string" in error for error in errors))
        self.assertTrue(any("native_target_resolution=true" in error for error in errors))

    def test_apply_policy_reports_dimension_and_format_mismatch(self):
        errors: list[str] = []
        validator._apply_policy(
            errors,
            "asset",
            {"native_target_resolution": True},
            (64, 64, "PNG"),
            {"width": 32, "height": 48, "format": "JPEG"},
        )
        self.assertTrue(any("width 64 does not satisfy policy width 32" in error for error in errors))
        self.assertTrue(any("height 64 does not satisfy policy height 48" in error for error in errors))
        self.assertTrue(any("format PNG does not satisfy policy format JPEG" in error for error in errors))

    def test_apply_policy_without_policy_is_noop(self):
        errors: list[str] = []
        validator._apply_policy(errors, "asset", {}, (1, 1, "PNG"), None)
        self.assertEqual([], errors)

    def test_invalid_json_and_non_object_root_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            malformed = root / "malformed.json"
            malformed.write_text("{", encoding="utf-8")
            errors = validator.validate_manifest(malformed, root)
            self.assertTrue(any("cannot read manifest" in error for error in errors))

            sequence = root / "sequence.json"
            sequence.write_text("[]", encoding="utf-8")
            self.assertEqual(["manifest root must be an object"], validator.validate_manifest(sequence, root))

    def test_manifest_shape_errors_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {
                "schema_version": 2,
                "asset_root": 123,
                "policy": [],
                "assets": {},
            }
            errors = validator.validate_manifest(write_manifest(root, manifest), root)
            self.assertIn("manifest schema_version must be 1", errors)
            self.assertIn("manifest asset_root must be a non-empty repository-relative path", errors)
            self.assertIn("manifest policy must be an object when present", errors)
            self.assertIn("manifest assets must be a list", errors)

    def test_asset_root_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {"schema_version": 1, "asset_root": "../outside", "assets": []}
            errors = validator.validate_manifest(write_manifest(root, manifest), root)
            self.assertTrue(any("asset_root escapes repo root" in error for error in errors))

    def test_asset_path_cannot_escape_asset_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "campaign" / "assets" / "npcs").mkdir(parents=True)
            image = root / "outside.png"
            write_png(image, 16, 16)
            manifest = base_manifest(
                [
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
                ]
            )
            errors = validator.validate_manifest(write_manifest(root, manifest), root)
            self.assertTrue(any("path must stay under asset_root" in error for error in errors))

    def test_absolute_asset_root_is_rejected_even_when_inside_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "campaign" / "assets" / "npcs"
            asset_root.mkdir(parents=True)
            manifest = {"schema_version": 1, "asset_root": str(asset_root), "assets": []}
            errors = validator.validate_manifest(write_manifest(root, manifest), root)
            self.assertTrue(any("asset_root must be repository-relative" in error for error in errors))

    def test_absolute_asset_path_is_rejected_even_when_inside_asset_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = self.make_png(root, width=16, height=16)
            asset = make_asset(root, image)
            asset["path"] = str(image)
            errors = validator.validate_manifest(write_manifest(root, base_manifest([asset])), root)
            self.assertTrue(any("path must be repository-relative" in error for error in errors))

    def test_non_object_asset_and_missing_path_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = base_manifest([])
            manifest["assets"] = [42, {}]
            errors = validator.validate_manifest(write_manifest(root, manifest), root)
            self.assertTrue(any("entry must be an object" in error for error in errors))
            self.assertTrue(any("path is required" in error for error in errors))

    def test_duplicate_path_and_missing_file_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "campaign" / "assets" / "npcs").mkdir(parents=True)
            asset = {
                "asset_kind": "portrait",
                "status": "CANDIDATE",
                "path": "campaign/assets/npcs/missing.png",
                "width": 1,
                "height": 1,
                "format": "PNG",
                "sha256": "0" * 64,
            }
            manifest = base_manifest([asset, dict(asset)])
            errors = validator.validate_manifest(write_manifest(root, manifest), root)
            self.assertTrue(any("duplicate path" in error for error in errors))
            self.assertTrue(any("missing file" in error for error in errors))

    def test_sha256_validation_rejects_bad_length_non_hex_and_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = self.make_png(root)
            cases = [
                ("short", "abc", "64-character"),
                ("nonhex", "g" * 64, "not hexadecimal"),
                ("mismatch", "0" * 64, "SHA-256 mismatch"),
            ]
            for name, value, expected in cases:
                with self.subTest(name=name):
                    asset = make_asset(root, image)
                    asset["sha256"] = value
                    errors = validator.validate_manifest(write_manifest(root, base_manifest([asset])), root)
                    self.assertTrue(any(expected in error for error in errors))

    def test_declared_metadata_invalid_status_and_final_flag_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = self.make_png(root, width=32, height=32)
            asset = make_asset(
                root,
                image,
                status="UNKNOWN",
                width=31,
                height=30,
                image_format="JPEG",
                final_asset=True,
            )
            errors = validator.validate_manifest(write_manifest(root, base_manifest([asset])), root)
            self.assertTrue(any("dimension mismatch" in error for error in errors))
            self.assertTrue(any("format mismatch" in error for error in errors))
            self.assertTrue(any("invalid status" in error for error in errors))
            self.assertTrue(any("final_asset=true requires status=FINAL" in error for error in errors))

    def test_unsupported_image_in_manifest_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset_root = root / "campaign" / "assets" / "npcs"
            asset_root.mkdir(parents=True)
            image = asset_root / "npc.gif"
            image.write_bytes(b"GIF89a")
            asset = {
                "asset_kind": "portrait",
                "status": "CANDIDATE",
                "path": image.relative_to(root).as_posix(),
                "width": 1,
                "height": 1,
                "format": "GIF",
                "sha256": digest(image),
            }
            errors = validator.validate_manifest(write_manifest(root, base_manifest([asset])), root)
            self.assertTrue(any("unsupported image extension" in error for error in errors))

    def test_required_policy_missing_for_approved_portrait_and_skin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            portrait = self.make_png(root, "portrait.png", 64, 64)
            skin = self.make_png(root, "skin.png", 64, 64)
            manifest = {
                "schema_version": 1,
                "asset_root": "campaign/assets/npcs",
                "policy": {},
                "assets": [
                    make_asset(root, portrait, status="APPROVED MASTER"),
                    make_asset(root, skin, asset_kind="skin", status="FINAL"),
                ],
            }
            errors = validator.validate_manifest(write_manifest(root, manifest), root)
            self.assertTrue(any("requires policy.portrait_master" in error for error in errors))
            self.assertTrue(any("requires policy.humanoid_skin" in error for error in errors))

    def test_policy_member_with_wrong_shape_is_treated_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            portrait = self.make_png(root, "portrait.png", 64, 64)
            manifest = {
                "schema_version": 1,
                "asset_root": "campaign/assets/npcs",
                "policy": {"portrait_master": []},
                "assets": [make_asset(root, portrait, status="FINAL")],
            }
            errors = validator.validate_manifest(write_manifest(root, manifest), root)
            self.assertTrue(any("requires policy.portrait_master" in error for error in errors))

    def test_cli_main_reports_pass_and_asset_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = self.make_png(root)
            manifest_path = write_manifest(root, base_manifest([make_asset(root, image)]))
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = validator.main(["--manifest", str(manifest_path), "--repo-root", str(root)])
            self.assertEqual(0, result)
            self.assertIn("PASS (1 assets)", stdout.getvalue())

    def test_cli_main_reports_validation_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = write_manifest(root, {"schema_version": 1, "asset_root": "assets", "assets": {}})
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                result = validator.main(["--manifest", str(manifest_path), "--repo-root", str(root)])
            self.assertEqual(1, result)
            self.assertIn("NPC visual asset manifest: FAIL", stderr.getvalue())
            self.assertIn("manifest assets must be a list", stderr.getvalue())

    def test_cli_count_read_failure_falls_back_to_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing.json"
            stdout = io.StringIO()
            with mock.patch.object(validator, "validate_manifest", return_value=[]):
                with contextlib.redirect_stdout(stdout):
                    result = validator.main(["--manifest", str(missing), "--repo-root", str(root)])
            self.assertEqual(0, result)
            self.assertIn("PASS (0 assets)", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
