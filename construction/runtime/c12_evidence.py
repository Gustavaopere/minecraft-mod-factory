from __future__ import annotations

import hashlib
from pathlib import Path


class C12EvidenceError(RuntimeError):
    """Raised when C12 evidence cannot be safely packaged."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _lexical_candidate(workspace: Path, candidate: Path) -> tuple[Path, Path]:
    raw = candidate if candidate.is_absolute() else workspace / candidate
    try:
        relative = raw.relative_to(workspace)
    except ValueError as exc:
        raise C12EvidenceError(f"evidence path escapes workspace: {candidate}") from exc
    if not relative.parts or any(part in {"..", "."} for part in relative.parts):
        raise C12EvidenceError(f"evidence path is not canonical inside workspace: {candidate}")
    return raw, relative


def _reject_symlink_components(workspace: Path, relative: Path) -> None:
    current = workspace
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise C12EvidenceError(
                f"evidence path contains symlink component: {relative.as_posix()}"
            )


def package_evidence(workspace: Path, paths: list[Path]) -> list[dict[str, str]]:
    """Hash regular evidence files contained by one non-symlink workspace."""
    workspace = Path(workspace).expanduser()
    if workspace.is_symlink():
        raise C12EvidenceError("evidence workspace must not be a symlink")
    if not workspace.is_dir():
        raise C12EvidenceError("evidence workspace must be an existing directory")
    workspace_resolved = workspace.resolve()

    if not isinstance(paths, list):
        raise C12EvidenceError("evidence paths must be a list")

    packaged: list[dict[str, str]] = []
    seen_resolved: set[Path] = set()
    for raw_candidate in paths:
        if not isinstance(raw_candidate, Path):
            raise C12EvidenceError("every evidence path must be a pathlib.Path")

        candidate, relative = _lexical_candidate(workspace, raw_candidate)
        _reject_symlink_components(workspace, relative)

        if not candidate.exists():
            raise C12EvidenceError(f"evidence file does not exist: {relative.as_posix()}")
        if not candidate.is_file():
            raise C12EvidenceError(f"evidence path must be a regular file: {relative.as_posix()}")

        resolved = candidate.resolve()
        if not resolved.is_relative_to(workspace_resolved):
            raise C12EvidenceError(f"evidence path escapes workspace: {relative.as_posix()}")
        if resolved in seen_resolved:
            raise C12EvidenceError(f"duplicate evidence path: {relative.as_posix()}")
        seen_resolved.add(resolved)

        canonical_relative = resolved.relative_to(workspace_resolved).as_posix()
        packaged.append({"path": canonical_relative, "sha256": _sha256(resolved)})

    packaged.sort(key=lambda item: item["path"])
    return packaged
