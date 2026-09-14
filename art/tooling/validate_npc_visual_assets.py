#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

VALID_STATUSES = {"LOOK-DEV", "CANDIDATE", "APPROVED MASTER", "SKIN CANDIDATE", "FINAL"}
SOF_MARKERS = {
    0xC0, 0xC1, 0xC2, 0xC3,
    0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB,
    0xCD, 0xCE, 0xCF,
}
NO_LENGTH_MARKERS = {0x01, *range(0xD0, 0xD9)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_png_size(path: Path) -> tuple[int, int, str]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature/IHDR")
    width, height = struct.unpack(">II", header[16:24])
    return width, height, "PNG"


def read_jpeg_size(path: Path) -> tuple[int, int, str]:
    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            raise ValueError("invalid JPEG SOI")
        while True:
            byte = handle.read(1)
            if not byte:
                raise ValueError("JPEG SOF marker not found")
            if byte != b"\xff":
                continue
            while byte == b"\xff":
                byte = handle.read(1)
                if not byte:
                    raise ValueError("truncated JPEG marker")
            marker = byte[0]
            if marker == 0xD9:
                raise ValueError("JPEG ended before SOF marker")
            if marker in NO_LENGTH_MARKERS:
                continue
            length_bytes = handle.read(2)
            if len(length_bytes) != 2:
                raise ValueError("truncated JPEG segment length")
            segment_length = struct.unpack(">H", length_bytes)[0]
            if segment_length < 2:
                raise ValueError("invalid JPEG segment length")
            if marker in SOF_MARKERS:
                payload = handle.read(5)
                if len(payload) != 5:
                    raise ValueError("truncated JPEG SOF segment")
                height, width = struct.unpack(">HH", payload[1:5])
                return width, height, "JPEG"
            handle.seek(segment_length - 2, 1)


def image_info(path: Path) -> tuple[int, int, str]:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return read_png_size(path)
    if suffix in {".jpg", ".jpeg"}:
        return read_jpeg_size(path)
    raise ValueError(f"unsupported image extension: {suffix}")


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _apply_policy(
    errors: list[str],
    prefix: str,
    asset: dict[str, Any],
    actual: tuple[int, int, str],
    policy: dict[str, Any] | None,
) -> None:
    if not policy:
        return

    width, height, actual_format = actual
    expected_width = policy.get("width")
    expected_height = policy.get("height")
    expected_format = policy.get("format")

    if expected_width is not None and not _positive_int(expected_width):
        errors.append(f"{prefix}: policy width must be a positive integer")
    elif expected_width is not None and width != expected_width:
        errors.append(f"{prefix}: width {width} does not satisfy policy width {expected_width}")

    if expected_height is not None and not _positive_int(expected_height):
        errors.append(f"{prefix}: policy height must be a positive integer")
    elif expected_height is not None and height != expected_height:
        errors.append(f"{prefix}: height {height} does not satisfy policy height {expected_height}")

    if expected_format is not None:
        if not isinstance(expected_format, str) or not expected_format:
            errors.append(f"{prefix}: policy format must be a non-empty string")
        elif actual_format.upper() != expected_format.upper():
            errors.append(f"{prefix}: format {actual_format} does not satisfy policy format {expected_format}")

    if policy.get("require_native_target_resolution") is True and asset.get("native_target_resolution") is not True:
        errors.append(f"{prefix}: policy requires native_target_resolution=true")


def validate_manifest(manifest_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = manifest_path.resolve()
    repo_root = repo_root.resolve()

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"cannot read manifest {manifest_path}: {exc}"]

    if not isinstance(manifest, dict):
        return ["manifest root must be an object"]
    if manifest.get("schema_version") != 1:
        errors.append("manifest schema_version must be 1")

    asset_root_raw = manifest.get("asset_root")
    if not isinstance(asset_root_raw, str) or not asset_root_raw:
        errors.append("manifest asset_root must be a non-empty repository-relative path")
        asset_root_raw = "."

    asset_root_literal = Path(asset_root_raw)
    if asset_root_literal.is_absolute():
        errors.append(f"manifest asset_root must be repository-relative: {asset_root_raw}")
        asset_root = repo_root
    else:
        asset_root = (repo_root / asset_root_literal).resolve()
        try:
            asset_root.relative_to(repo_root)
        except ValueError:
            errors.append(f"asset_root escapes repo root: {asset_root_raw}")
            asset_root = repo_root

    policy = manifest.get("policy", {})
    if not isinstance(policy, dict):
        errors.append("manifest policy must be an object when present")
        policy = {}

    assets = manifest.get("assets")
    if not isinstance(assets, list):
        errors.append("manifest assets must be a list")
        return errors

    seen_paths: set[str] = set()
    for index, asset in enumerate(assets):
        prefix = f"assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{prefix}: entry must be an object")
            continue

        rel_path = asset.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            errors.append(f"{prefix}: path is required")
            continue
        if rel_path in seen_paths:
            errors.append(f"{prefix}: duplicate path {rel_path}")
        seen_paths.add(rel_path)

        path_literal = Path(rel_path)
        if path_literal.is_absolute():
            errors.append(f"{prefix}: path must be repository-relative: {rel_path}")
            continue

        path = (repo_root / path_literal).resolve()
        try:
            path.relative_to(asset_root)
        except ValueError:
            errors.append(f"{prefix}: path must stay under asset_root {asset_root_raw}: {rel_path}")
            continue

        if not path.is_file():
            errors.append(f"{prefix}: missing file {rel_path}")
            continue

        expected_hash = asset.get("sha256")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            errors.append(f"{prefix}: sha256 must be a 64-character hex string")
        else:
            try:
                int(expected_hash, 16)
            except ValueError:
                errors.append(f"{prefix}: sha256 is not hexadecimal")
            else:
                actual_hash = sha256(path)
                if actual_hash.lower() != expected_hash.lower():
                    errors.append(
                        f"{prefix}: SHA-256 mismatch for {rel_path}: manifest={expected_hash} actual={actual_hash}"
                    )

        try:
            width, height, actual_format = image_info(path)
        except ValueError as exc:
            errors.append(f"{prefix}: {rel_path}: {exc}")
            continue

        if asset.get("width") != width or asset.get("height") != height:
            errors.append(
                f"{prefix}: dimension mismatch for {rel_path}: "
                f"manifest={asset.get('width')}x{asset.get('height')} actual={width}x{height}"
            )
        declared_format = asset.get("format")
        if not isinstance(declared_format, str) or declared_format.upper() != actual_format:
            errors.append(
                f"{prefix}: format mismatch for {rel_path}: manifest={declared_format} actual={actual_format}"
            )

        status = asset.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{prefix}: invalid status {status!r}")

        kind = asset.get("asset_kind")
        is_final = asset.get("final_asset") is True
        if is_final and status != "FINAL":
            errors.append(f"{prefix}: final_asset=true requires status=FINAL")

        if kind == "portrait" and status in {"APPROVED MASTER", "FINAL"}:
            portrait_policy = policy.get("portrait_master")
            if not isinstance(portrait_policy, dict):
                errors.append(f"{prefix}: approved/final portrait requires policy.portrait_master")
            else:
                _apply_policy(errors, prefix, asset, (width, height, actual_format), portrait_policy)

        if kind == "skin" and status in {"SKIN CANDIDATE", "FINAL"}:
            skin_policy = policy.get("humanoid_skin")
            if not isinstance(skin_policy, dict):
                errors.append(f"{prefix}: skin candidate/final requires policy.humanoid_skin")
            else:
                _apply_policy(errors, prefix, asset, (width, height, actual_format), skin_policy)

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a consumer NPC visual asset manifest.")
    parser.add_argument("--manifest", required=True, type=Path, help="Path to the consumer manifest JSON")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Consumer repository root (default: cwd)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = validate_manifest(args.manifest, args.repo_root)
    if errors:
        print("NPC visual asset manifest: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    try:
        count = len(json.loads(args.manifest.read_text(encoding="utf-8")).get("assets", []))
    except Exception:
        count = 0
    print(f"NPC visual asset manifest: PASS ({count} assets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
