#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAFFOLDER_PATH = REPO_ROOT / "engineering/tooling/scaffolder/scaffold_mod.py"
MOD_SPEC_PATH = REPO_ROOT / "engineering/tests/fixtures/i10-multiblock-mod-spec.json"
SCAFFOLD_CONFIG_PATH = REPO_ROOT / "engineering/tests/fixtures/i10-multiblock-scaffold-config.json"
GOLDEN_ROOT = REPO_ROOT / "engineering/tests/golden/i10-multiblock-foundation"
MANIFEST_PATH = GOLDEN_ROOT / "manifest.json"
HANDOFF_PATH = GOLDEN_ROOT / "asset-handoff.json"
OVERLAY_ROOT = GOLDEN_ROOT / "overlay"
MAIN_CLASS_RELATIVE = "src/main/java/dev/example/i10multiblock/I10MultiblockMod.java"
GAMETEST_STRUCTURE_RELATIVE = "src/main/resources/data/i10_multiblock/structure/multiblock_test.nbt"
GAMETEST_STRUCTURE_SHA256 = "75b23fb80317d88bbde1a2aff7121cfd903b8a1010878e0327ce26fd4d3f1c99"

CANONICAL_OVERLAY_FILES = (
    ("README.md", "I10-MULTIBLOCK-FOUNDATION.md"),
    ("src/main/java/dev/example/i10multiblock/multiblock/I10MultiblockContent.java", "src/main/java/dev/example/i10multiblock/multiblock/I10MultiblockContent.java"),
    ("src/main/java/dev/example/i10multiblock/multiblock/MultiblockPattern.java", "src/main/java/dev/example/i10multiblock/multiblock/MultiblockPattern.java"),
    ("src/main/java/dev/example/i10multiblock/multiblock/MultiblockValidationResult.java", "src/main/java/dev/example/i10multiblock/multiblock/MultiblockValidationResult.java"),
    ("src/main/java/dev/example/i10multiblock/multiblock/MultiblockRuntimeState.java", "src/main/java/dev/example/i10multiblock/multiblock/MultiblockRuntimeState.java"),
    ("src/main/java/dev/example/i10multiblock/multiblock/MultiblockInvalidation.java", "src/main/java/dev/example/i10multiblock/multiblock/MultiblockInvalidation.java"),
    ("src/main/java/dev/example/i10multiblock/multiblock/MultiblockCasingBlock.java", "src/main/java/dev/example/i10multiblock/multiblock/MultiblockCasingBlock.java"),
    ("src/main/java/dev/example/i10multiblock/multiblock/MultiblockControllerBlock.java", "src/main/java/dev/example/i10multiblock/multiblock/MultiblockControllerBlock.java"),
    ("src/main/java/dev/example/i10multiblock/multiblock/MultiblockControllerBlockEntity.java", "src/main/java/dev/example/i10multiblock/multiblock/MultiblockControllerBlockEntity.java"),
    ("src/main/java/dev/example/i10multiblock/multiblock/MultiblockPortBlock.java", "src/main/java/dev/example/i10multiblock/multiblock/MultiblockPortBlock.java"),
    ("src/main/java/dev/example/i10multiblock/multiblock/MultiblockPortBlockEntity.java", "src/main/java/dev/example/i10multiblock/multiblock/MultiblockPortBlockEntity.java"),
    ("src/main/java/dev/example/i10multiblock/gametest/I10MultiblockGameTests.java", "src/main/java/dev/example/i10multiblock/gametest/I10MultiblockGameTests.java"),
    ("src/main/java/dev/example/i10multiblock/acceptance/I10AcceptanceCommands.java", "src/main/java/dev/example/i10multiblock/acceptance/I10AcceptanceCommands.java"),
    ("src/main/resources/assets/i10_multiblock/blockstates/multiblock_controller.json", "src/main/resources/assets/i10_multiblock/blockstates/multiblock_controller.json"),
    ("src/main/resources/assets/i10_multiblock/blockstates/multiblock_io_port.json", "src/main/resources/assets/i10_multiblock/blockstates/multiblock_io_port.json"),
    ("src/main/resources/assets/i10_multiblock/blockstates/multiblock_casing.json", "src/main/resources/assets/i10_multiblock/blockstates/multiblock_casing.json"),
    (GAMETEST_STRUCTURE_RELATIVE, GAMETEST_STRUCTURE_RELATIVE),
)
CANONICAL_FILE_SHA256 = {
    GAMETEST_STRUCTURE_RELATIVE: GAMETEST_STRUCTURE_SHA256,
}
CANONICAL_ART_FILES = (
    ("art/golden-samples/i10-multiblock-visual/models/controller_unformed.json", "src/main/resources/assets/i10_multiblock/models/block/controller_unformed.json"),
    ("art/golden-samples/i10-multiblock-visual/models/controller_formed.json", "src/main/resources/assets/i10_multiblock/models/block/controller_formed.json"),
    ("art/golden-samples/i10-multiblock-visual/models/casing.json", "src/main/resources/assets/i10_multiblock/models/block/casing.json"),
    ("art/golden-samples/i10-multiblock-visual/models/io_port_unformed.json", "src/main/resources/assets/i10_multiblock/models/block/io_port_unformed.json"),
    ("art/golden-samples/i10-multiblock-visual/models/io_port_formed.json", "src/main/resources/assets/i10_multiblock/models/block/io_port_formed.json"),
)
CANONICAL_PATCH = {
    "path": MAIN_CLASS_RELATIVE,
    "anchor": "    public I10MultiblockMod(IEventBus modBus, ModContainer container) {\n    }\n",
    "replacement": (
        "    public I10MultiblockMod(IEventBus modBus, ModContainer container) {\n"
        "        dev.example.i10multiblock.multiblock.I10MultiblockContent.register(modBus);\n"
        "        modBus.addListener(dev.example.i10multiblock.multiblock.I10MultiblockContent::registerCapabilities);\n"
        "    }\n"
    ),
}


class MaterializationError(RuntimeError):
    pass


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _workspace_output_path(value: Path | str) -> tuple[Path, Path]:
    workspace = Path.cwd().resolve()
    raw = Path(value)
    candidate = raw.resolve(strict=False) if raw.is_absolute() else (workspace / raw).resolve(strict=False)
    if candidate == workspace or not _is_within(candidate, workspace):
        raise MaterializationError(
            f"I10 output must stay inside workspace and cannot equal its root: {workspace}"
        )
    if candidate.exists() or candidate.is_symlink():
        raise MaterializationError(f"I10 output already exists; refusing overwrite: {candidate}")
    return workspace, candidate


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MaterializationError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise MaterializationError(f"{label} root must be an object")
    return value


def _closed_keys(mapping: dict[str, Any], expected: set[str], *, label: str) -> None:
    actual = set(mapping)
    if actual != expected:
        raise MaterializationError(
            f"{label} keys must be exactly {sorted(expected)}; got {sorted(actual)}"
        )


def _safe_relative(value: Any, *, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise MaterializationError(f"{label} must be a non-empty relative path")
    if "\\" in value or ":" in value:
        raise MaterializationError(f"{label} must use safe workspace-relative POSIX syntax")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise MaterializationError(f"{label} contains unsafe path segments")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise MaterializationError(f"{label} must be relative")
    return path


def _validate_manifest() -> tuple[list[tuple[PurePosixPath, PurePosixPath]], dict[str, str]]:
    manifest = _load_json_object(MANIFEST_PATH, label="I10 manifest")
    _closed_keys(manifest, {"schema_version", "files", "main_class_patch"}, label="I10 manifest")
    if manifest["schema_version"] != 1:
        raise MaterializationError("I10 manifest schema_version must be 1")

    files = manifest["files"]
    if not isinstance(files, list) or not files:
        raise MaterializationError("I10 manifest files must be a non-empty list")

    declared: list[tuple[str, str]] = []
    seen_sources: set[str] = set()
    seen_destinations: set[str] = set()
    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise MaterializationError(f"I10 manifest files[{index}] must be an object")
        source_hint = entry.get("source")
        expected_sha256 = CANONICAL_FILE_SHA256.get(source_hint) if isinstance(source_hint, str) else None
        expected_keys = {"source", "destination"}
        if expected_sha256 is not None:
            expected_keys.add("sha256")
        _closed_keys(entry, expected_keys, label=f"I10 manifest files[{index}]")
        source = _safe_relative(entry["source"], label=f"I10 manifest files[{index}].source")
        destination = _safe_relative(entry["destination"], label=f"I10 manifest files[{index}].destination")
        source_key = source.as_posix()
        destination_key = destination.as_posix()
        if source_key in seen_sources or destination_key in seen_destinations:
            raise MaterializationError("I10 manifest overlay paths must be unique")
        if expected_sha256 is not None and entry.get("sha256") != expected_sha256:
            raise MaterializationError(f"I10 manifest SHA-256 mismatch for canonical source: {source_key}")
        seen_sources.add(source_key)
        seen_destinations.add(destination_key)
        declared.append((source_key, destination_key))

    if tuple(declared) != CANONICAL_OVERLAY_FILES:
        raise MaterializationError("I10 manifest cannot delegate overlay write authority")

    patch = manifest["main_class_patch"]
    if not isinstance(patch, dict):
        raise MaterializationError("I10 manifest main_class_patch must be an object")
    _closed_keys(patch, {"path", "anchor", "replacement"}, label="I10 main_class_patch")
    patch_path = _safe_relative(patch["path"], label="I10 main_class_patch.path")
    declared_patch = {
        "path": patch_path.as_posix(),
        "anchor": patch.get("anchor"),
        "replacement": patch.get("replacement"),
    }
    if declared_patch != CANONICAL_PATCH:
        raise MaterializationError("I10 manifest cannot delegate main-class patch authority")

    return (
        [(PurePosixPath(source), PurePosixPath(destination)) for source, destination in CANONICAL_OVERLAY_FILES],
        dict(CANONICAL_PATCH),
    )


def _validate_handoff_art_files() -> list[tuple[PurePosixPath, PurePosixPath]]:
    handoff = _load_json_object(HANDOFF_PATH, label="I10 asset handoff")
    artifacts = handoff.get("artifacts")
    if not isinstance(artifacts, list):
        raise MaterializationError("I10 asset handoff artifacts must be an array")
    declared: list[tuple[str, str]] = []
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise MaterializationError(f"I10 asset handoff artifacts[{index}] must be an object")
        source = _safe_relative(
            artifact.get("source_path"),
            label=f"I10 asset handoff artifacts[{index}].source_path",
        )
        destination = _safe_relative(
            artifact.get("delivery_path"),
            label=f"I10 asset handoff artifacts[{index}].delivery_path",
        )
        declared.append((source.as_posix(), destination.as_posix()))
    if tuple(declared) != CANONICAL_ART_FILES:
        raise MaterializationError("I10 asset handoff cannot delegate art delivery authority")
    return [
        (PurePosixPath(source), PurePosixPath(destination))
        for source, destination in CANONICAL_ART_FILES
    ]


def _validate_overlay_source(relative: PurePosixPath) -> Path:
    if not OVERLAY_ROOT.is_dir():
        raise MaterializationError(f"I10 overlay root is missing: {OVERLAY_ROOT}")
    current = OVERLAY_ROOT
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise MaterializationError(f"I10 overlay source cannot contain symlinks: {relative.as_posix()}")
    if not current.is_file():
        raise MaterializationError(f"I10 overlay source is missing: {relative.as_posix()}")
    overlay_root = OVERLAY_ROOT.resolve(strict=True)
    resolved = current.resolve(strict=True)
    if not _is_within(resolved, overlay_root):
        raise MaterializationError(f"I10 overlay source escapes overlay root: {relative.as_posix()}")
    expected_sha256 = CANONICAL_FILE_SHA256.get(relative.as_posix())
    if expected_sha256 is not None:
        actual_sha256 = hashlib.sha256(resolved.read_bytes()).hexdigest()
        if actual_sha256 != expected_sha256:
            raise MaterializationError(f"I10 overlay source SHA-256 mismatch: {relative.as_posix()}")
    return resolved


def _validate_repo_source(relative: PurePosixPath) -> Path:
    current = REPO_ROOT
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise MaterializationError(f"I10 Repo Textura source cannot contain symlinks: {relative.as_posix()}")
    if not current.is_file():
        raise MaterializationError(f"I10 Repo Textura source is missing: {relative.as_posix()}")
    repo_root = REPO_ROOT.resolve(strict=True)
    resolved = current.resolve(strict=True)
    if not _is_within(resolved, repo_root):
        raise MaterializationError(f"I10 Repo Textura source escapes repository root: {relative.as_posix()}")
    return resolved


def _load_scaffolder():
    spec = importlib.util.spec_from_file_location("factory_i3_scaffolder_for_i10", SCAFFOLDER_PATH)
    if spec is None or spec.loader is None:
        raise MaterializationError("cannot load canonical I3 scaffolder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stage_destination(stage: Path, relative: PurePosixPath, *, label: str) -> Path:
    candidate = (stage / Path(*relative.parts)).resolve(strict=False)
    if candidate == stage or not _is_within(candidate, stage):
        raise MaterializationError(f"{label} escapes staged project")
    return candidate


def materialize_i10(output_dir: Path | str) -> Path:
    workspace, output = _workspace_output_path(output_dir)
    files, patch = _validate_manifest()
    art_files = _validate_handoff_art_files()
    overlay_sources = [
        (source, destination, _validate_overlay_source(source))
        for source, destination in files
    ]
    art_sources = [
        (source, destination, _validate_repo_source(source))
        for source, destination in art_files
    ]

    stage = Path(tempfile.mkdtemp(prefix=".i10-stage-", dir=workspace)).resolve()
    try:
        scaffolder = _load_scaffolder()
        try:
            scaffolder.generate_project(MOD_SPEC_PATH, SCAFFOLD_CONFIG_PATH, stage)
        except Exception as exc:
            raise MaterializationError(f"canonical I3 scaffold generation failed: {exc}") from exc

        destinations: list[tuple[Path, Path]] = []
        destination_keys: set[PurePosixPath] = set()
        for _source_relative, destination_relative, source_path in overlay_sources + art_sources:
            if destination_relative in destination_keys:
                raise MaterializationError(
                    "I10 canonical delivery destinations must be unique: "
                    + destination_relative.as_posix()
                )
            destination_keys.add(destination_relative)
            destination = _stage_destination(stage, destination_relative, label="I10 delivery destination")
            if destination.exists() or destination.is_symlink():
                raise MaterializationError(
                    "I10 delivery destination already exists in canonical scaffold: "
                    + destination_relative.as_posix()
                )
            destinations.append((source_path, destination))

        patch_relative = _safe_relative(patch["path"], label="I10 main class path")
        patch_target = _stage_destination(stage, patch_relative, label="I10 main class patch")
        if not patch_target.is_file() or patch_target.is_symlink():
            raise MaterializationError("I10 canonical main class target is missing or unsafe")
        text = patch_target.read_text(encoding="utf-8")
        matches = text.count(patch["anchor"])
        if matches != 1:
            raise MaterializationError(
                f"I10 main class constructor anchor must match exactly once; got {matches}"
            )

        for source, destination in destinations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        patch_target.write_text(
            text.replace(patch["anchor"], patch["replacement"], 1),
            encoding="utf-8",
            newline="\n",
        )

        output.parent.mkdir(parents=True, exist_ok=True)
        stage.replace(output)
        return output
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: materialize_i10.py OUTPUT_DIR", file=sys.stderr)
        return 2
    try:
        materialize_i10(args[0])
    except MaterializationError as exc:
        print(f"I10 materialization failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
