#!/usr/bin/env python3
"""Derive a reviewed I10 current-source physical .248 handoff without rewriting Java.

The explicit profile conversion reuses the canonical I3 scaffolder. It does
not establish two-client multiplayer, full modpack, or missing-neighbor PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "engineering/tooling/scaffolder"))
import scaffold_mod  # noqa: E402

TARGET = "21.1.248"
SOURCE = "21.1.250"
MODLIST_SHA = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"
MODIFIED = ("gradle.lockfile", "gradle.properties", "run-i10-manual-process.py")
MANIFEST = "I10-PROFILE-RECONCILIATION.json"


class ProfileBlocked(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_source(root: Path, expected_sha: str) -> dict[str, bytes]:
    if root.is_symlink() or not root.is_dir():
        raise ProfileBlocked("source must be an existing non-symlink directory")
    files: dict[str, bytes] = {}
    for item in root.rglob("*"):
        if item.is_symlink():
            raise ProfileBlocked(f"source symlink prohibited: {item}")
        if not item.is_file():
            continue
        rel = item.relative_to(root).as_posix()
        parts = PurePosixPath(rel)
        if parts.is_absolute() or ".." in parts.parts or rel in files:
            raise ProfileBlocked(f"unsafe source path: {rel}")
        if parts.parts[0] in {"run", "build", ".gradle"}:
            raise ProfileBlocked(f"runtime/build files prohibited: {rel}")
        files[rel] = item.read_bytes()
    if len(files) != 47 or sum(p.endswith(".java") for p in files) != 15:
        raise ProfileBlocked(f"source inventory mismatch: {len(files)} files")
    if files.get("I10-SOURCE-COMMIT.txt", b"").decode("ascii").strip() != expected_sha:
        raise ProfileBlocked("source commit does not match the exact requested HEAD")
    return files


def _replace_exact(data: bytes, before: str, after: str, label: str) -> bytes:
    text = data.decode("utf-8")
    if text.count(before) != 1:
        raise ProfileBlocked(f"{label} profile anchor mismatch")
    return text.replace(before, after, 1).encode("utf-8")


def _derive_files(source: dict[str, bytes]) -> dict[str, bytes]:
    result = dict(source)
    try:
        for name, template in (
            ("gradle.properties", "gradle.properties.tmpl"),
            ("gradle.lockfile", "gradle.lockfile.tmpl"),
        ):
            original = source[name].decode("utf-8")
            rendered = scaffold_mod._render_target_exact(template, original, {"neoforge": TARGET})
            result[name] = rendered.encode("utf-8")
        result["run-i10-manual-process.py"] = _replace_exact(
            source["run-i10-manual-process.py"],
            '    "neoforge": "21.1.250",',
            '    "neoforge": "21.1.248",',
            "physical helper",
        )
    except (KeyError, ValueError, UnicodeError) as exc:
        raise ProfileBlocked(f"canonical target profile mismatch: {exc}") from exc
    if b"neo_version=21.1.248" not in result["gradle.properties"]:
        raise ProfileBlocked("target loader profile was not applied")
    lock = result["gradle.lockfile"]
    if b"net.neoforged:neoforge:21.1.248=sdk,testSdk" not in lock:
        raise ProfileBlocked("target lockfile mismatch")
    if b"21.1.250" in lock or b"4.0.44" in lock:
        raise ProfileBlocked("previous profile survived in lockfile")
    changed = tuple(sorted(k for k in source if result[k] != source[k]))
    if changed != MODIFIED:
        raise ProfileBlocked(f"unsafe source mutations: {changed}")
    return result


def derive(source: Path | str, output: Path | str, archive: Path | str, source_sha: str) -> dict:
    source, output, archive = Path(source), Path(output), Path(archive)
    if re.fullmatch(r"[0-9a-f]{40}", source_sha) is None:
        raise ProfileBlocked("source commit must be an exact lowercase 40-character SHA")
    if output.exists() or output.is_symlink() or archive.exists() or archive.is_symlink():
        raise ProfileBlocked("refusing to overwrite a prior handoff or evidence archive")
    source_root = source.resolve()
    target_root = output.resolve(strict=False)
    zip_root = archive.resolve(strict=False)
    if source_root == target_root or source_root in target_root.parents or target_root in source_root.parents:
        raise ProfileBlocked("source and target roots must be disjoint")
    if source_root == zip_root or source_root in zip_root.parents:
        raise ProfileBlocked("archive cannot be inside the source")
    files = _read_source(source, source_sha)
    updated = _derive_files(files)
    manifest = {
        "schema_version": 1,
        "source_commit": source_sha,
        "minecraft": "1.21.1",
        "source_neoforge": SOURCE,
        "target_neoforge": TARGET,
        "target_fml": scaffold_mod.SUPPORTED_NEOFORGE_TARGETS[TARGET]["fml"],
        "java": 21,
        "physical_modlist_sha256": MODLIST_SHA,
        "source_file_count": len(files),
        "java_sources_preserved": sum(k.endswith(".java") and files[k] == updated[k] for k in files),
        "modified_paths": list(MODIFIED),
        "modified_sha256": {
            path: {"before": sha(files[path]), "after": sha(updated[path])}
            for path in MODIFIED
        },
        "source_code_and_assets_preserved": all(
            files[path] == updated[path] for path in files if path not in MODIFIED
        ),
        "two_real_clients": "PENDING",
        "physical_missing_neighbor": "UNPROVEN",
        "full_modpack": "UNPROVEN",
        "p2_review_threads": "OPEN",
        "merge": "BLOCKED",
    }
    if manifest["java_sources_preserved"] != 15 or not manifest["source_code_and_assets_preserved"]:
        raise ProfileBlocked("Java source/assets must be preserved byte-identically")
    updated[MANIFEST] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".i10-physical248-stage-", dir=output.parent) as tmp:
        stage = Path(tmp)
        folder = stage / "project"
        folder.mkdir()
        for path, contents in updated.items():
            rel = PurePosixPath(path)
            dst = folder.joinpath(*rel.parts)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(contents)
        zip_path = stage / "handoff.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for path in sorted(updated):
                info = zipfile.ZipInfo(path, (2026, 10, 14, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100755 if path in {
                    "gradlew", "START-I10-SERVER.sh", "START-I10-CLIENT-A.sh",
                    "START-I10-CLIENT-B.sh", "run-i10-manual-process.py",
                } else 0o100644) << 16
                z.writestr(info, updated[path], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(zip_path) as z:
            if z.testzip() is not None or len(z.namelist()) != len(updated):
                raise ProfileBlocked("handoff ZIP CRC/inventory failed")
        folder.replace(output)
        zip_path.replace(archive)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    try:
        result = derive(args.source, args.output, args.archive, args.source_sha)
    except (ProfileBlocked, OSError) as exc:
        print(f"I10 current-source physical loader derivation BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
