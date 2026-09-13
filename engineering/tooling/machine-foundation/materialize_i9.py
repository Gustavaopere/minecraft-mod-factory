#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAFFOLDER_PATH = REPO_ROOT / "engineering/tooling/scaffolder/scaffold_mod.py"
MOD_SPEC_PATH = REPO_ROOT / "engineering/tests/fixtures/i9-machine-mod-spec.json"
SCAFFOLD_CONFIG_PATH = REPO_ROOT / "engineering/tests/fixtures/i9-machine-scaffold-config.json"
GOLDEN_ROOT = REPO_ROOT / "engineering/tests/golden/i9-machine-foundation"
MANIFEST_PATH = GOLDEN_ROOT / "manifest.json"
OVERLAY_ROOT = GOLDEN_ROOT / "overlay"
MAIN_CLASS_RELATIVE = "src/main/java/dev/example/i9machine/I9MachineMod.java"
CANONICAL_OVERLAY_FILES = (
    ("README.md", "I9-MACHINE-FOUNDATION.md"),
    (
        "src/main/java/dev/example/i9machine/machine/I9MachineContent.java",
        "src/main/java/dev/example/i9machine/machine/I9MachineContent.java",
    ),
    (
        "src/main/java/dev/example/i9machine/machine/MachineBlock.java",
        "src/main/java/dev/example/i9machine/machine/MachineBlock.java",
    ),
    (
        "src/main/java/dev/example/i9machine/machine/MachineEnergyStorage.java",
        "src/main/java/dev/example/i9machine/machine/MachineEnergyStorage.java",
    ),
    (
        "src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java",
        "src/main/java/dev/example/i9machine/machine/MachineBlockEntity.java",
    ),
    (
        "src/main/java/dev/example/i9machine/machine/MachineMenu.java",
        "src/main/java/dev/example/i9machine/machine/MachineMenu.java",
    ),
)
CANONICAL_PATCH = {
    "path": MAIN_CLASS_RELATIVE,
    "anchor": "    public I9MachineMod(IEventBus modBus, ModContainer container) {\n    }\n",
    "replacement": (
        "    public I9MachineMod(IEventBus modBus, ModContainer container) {\n"
        "        dev.example.i9machine.machine.I9MachineContent.register(modBus);\n"
        "        modBus.addListener(dev.example.i9machine.machine.I9MachineContent::registerCapabilities);\n"
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
        raise MaterializationError(f"I9 output must stay inside workspace and cannot equal its root: {workspace}")
    if candidate.exists():
        raise MaterializationError(f"I9 output already exists; refusing overwrite: {candidate}")
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
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise MaterializationError(f"{label} contains unsafe path segments")
    path = PurePosixPath(value)
    if path.is_absolute():
        raise MaterializationError(f"{label} must be relative")
    return path


def _validate_manifest() -> tuple[list[tuple[PurePosixPath, PurePosixPath]], dict[str, str]]:
    manifest = _load_json_object(MANIFEST_PATH, label="I9 manifest")
    _closed_keys(manifest, {"schema_version", "files", "main_class_patch"}, label="I9 manifest")
    if manifest["schema_version"] != 1:
        raise MaterializationError("I9 manifest schema_version must be 1")

    files = manifest["files"]
    if not isinstance(files, list) or not files:
        raise MaterializationError("I9 manifest files must be a non-empty list")

    declared_files: list[tuple[str, str]] = []
    seen_sources: set[str] = set()
    seen_destinations: set[str] = set()
    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise MaterializationError(f"I9 manifest files[{index}] must be an object")
        _closed_keys(entry, {"source", "destination"}, label=f"I9 manifest files[{index}]")
        source = _safe_relative(entry["source"], label=f"I9 manifest files[{index}].source")
        destination = _safe_relative(
            entry["destination"], label=f"I9 manifest files[{index}].destination"
        )
        source_key = source.as_posix()
        destination_key = destination.as_posix()
        if source_key in seen_sources or destination_key in seen_destinations:
            raise MaterializationError("I9 manifest overlay paths must be unique")
        seen_sources.add(source_key)
        seen_destinations.add(destination_key)
        declared_files.append((source_key, destination_key))

    if tuple(declared_files) != CANONICAL_OVERLAY_FILES:
        raise MaterializationError("I9 manifest cannot delegate overlay write authority")

    patch = manifest["main_class_patch"]
    if not isinstance(patch, dict):
        raise MaterializationError("I9 manifest main_class_patch must be an object")
    _closed_keys(patch, {"path", "anchor", "replacement"}, label="I9 main_class_patch")
    patch_path = _safe_relative(patch["path"], label="I9 main_class_patch.path")
    declared_patch = {
        "path": patch_path.as_posix(),
        "anchor": patch.get("anchor"),
        "replacement": patch.get("replacement"),
    }
    if declared_patch != CANONICAL_PATCH:
        raise MaterializationError("I9 manifest cannot delegate main-class patch authority")

    operational_files = [
        (PurePosixPath(source), PurePosixPath(destination))
        for source, destination in CANONICAL_OVERLAY_FILES
    ]
    return operational_files, dict(CANONICAL_PATCH)


def _validate_overlay_source(relative: PurePosixPath) -> Path:
    if not OVERLAY_ROOT.is_dir():
        raise MaterializationError(f"I9 overlay root is missing: {OVERLAY_ROOT}")
    current = OVERLAY_ROOT
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise MaterializationError(f"I9 overlay source cannot contain symlinks: {relative.as_posix()}")
    if not current.is_file():
        raise MaterializationError(f"I9 overlay source is missing: {relative.as_posix()}")
    overlay_root = OVERLAY_ROOT.resolve(strict=True)
    resolved = current.resolve(strict=True)
    if not _is_within(resolved, overlay_root):
        raise MaterializationError(f"I9 overlay source escapes overlay root: {relative.as_posix()}")
    return resolved


def _load_scaffolder():
    spec = importlib.util.spec_from_file_location("factory_i3_scaffolder_for_i9", SCAFFOLDER_PATH)
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


def materialize_i9(output_dir: Path | str) -> Path:
    workspace, output = _workspace_output_path(output_dir)
    files, patch = _validate_manifest()
    overlay_sources = [(source, destination, _validate_overlay_source(source)) for source, destination in files]

    stage = Path(tempfile.mkdtemp(prefix=".i9-stage-", dir=workspace)).resolve()
    try:
        scaffolder = _load_scaffolder()
        try:
            scaffolder.generate_project(MOD_SPEC_PATH, SCAFFOLD_CONFIG_PATH, stage)
        except Exception as exc:
            raise MaterializationError(f"canonical I3 scaffold generation failed: {exc}") from exc

        destinations: list[tuple[Path, Path]] = []
        for _source_relative, destination_relative, source_path in overlay_sources:
            destination = _stage_destination(stage, destination_relative, label="I9 overlay destination")
            if destination.exists() or destination.is_symlink():
                raise MaterializationError(
                    f"I9 overlay destination already exists in canonical scaffold: {destination_relative.as_posix()}"
                )
            destinations.append((source_path, destination))

        patch_relative = _safe_relative(patch["path"], label="I9 main class path")
        patch_target = _stage_destination(stage, patch_relative, label="I9 main class patch")
        if not patch_target.is_file() or patch_target.is_symlink():
            raise MaterializationError("I9 canonical main class target is missing or unsafe")
        text = patch_target.read_text(encoding="utf-8")
        matches = text.count(patch["anchor"])
        if matches != 1:
            raise MaterializationError(f"I9 main class constructor anchor must match exactly once; got {matches}")

        for source, destination in destinations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        patched = text.replace(patch["anchor"], patch["replacement"], 1)
        patch_target.write_text(patched, encoding="utf-8", newline="\n")

        output.parent.mkdir(parents=True, exist_ok=True)
        stage.replace(output)
        return output
    finally:
        if stage.exists():
            shutil.rmtree(stage)
