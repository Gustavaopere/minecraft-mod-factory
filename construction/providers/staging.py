from __future__ import annotations

import os
import stat
from pathlib import Path, PurePosixPath

from construction.providers.common import ARTIFACT_KINDS, sha256_hex
from construction.providers.errors import C10Error

_FIXTURE_PREFIX = "construction/fixtures/c10/"


def _require_positive_limit(max_bytes: int) -> None:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise C10Error("ARTIFACT_LIMIT_EXCEEDED", "artifact limit must be a positive integer")


def _normalized_repo_relpath(repo_relpath: str) -> str:
    if (
        not isinstance(repo_relpath, str)
        or not repo_relpath
        or "\\" in repo_relpath
        or repo_relpath.startswith("/")
    ):
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path is not a normalized C10 fixture path")
    parts = repo_relpath.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path is not a normalized C10 fixture path")
    try:
        normalized = PurePosixPath(repo_relpath).as_posix()
    except (TypeError, ValueError):
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path is not a normalized C10 fixture path") from None
    if normalized != repo_relpath or not normalized.startswith(_FIXTURE_PREFIX):
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path is outside construction/fixtures/c10")
    return normalized


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def safe_repo_fixture_path(root: Path, repo_relpath: str, *, must_exist: bool) -> Path:
    normalized = _normalized_repo_relpath(repo_relpath)
    root_path = Path(root).resolve()
    fixture_root = (root_path / "construction" / "fixtures" / "c10").resolve(strict=False)
    candidate = root_path.joinpath(*PurePosixPath(normalized).parts)

    if candidate.is_symlink():
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path may not be a symlink")

    try:
        resolved = candidate.resolve(strict=must_exist)
    except (FileNotFoundError, OSError):
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path does not resolve to a regular file") from None

    if not _within(resolved, fixture_root):
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path escapes construction/fixtures/c10")

    if must_exist:
        try:
            mode = candidate.stat().st_mode
        except OSError:
            raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path does not resolve to a regular file") from None
        if not stat.S_ISREG(mode):
            raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path must resolve to a regular file")

    return resolved


def _validate_kind_and_media_type(kind: str, media_type: str) -> None:
    if kind not in ARTIFACT_KINDS:
        raise C10Error("ARTIFACT_KIND_UNSUPPORTED", "artifact kind is unsupported")
    if (
        not isinstance(media_type, str)
        or not media_type.strip()
        or "\n" in media_type
        or "\r" in media_type
    ):
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact media type must be non-empty text")


def artifact_descriptor_from_bytes(
    data: bytes,
    *,
    kind: str,
    media_type: str,
    repo_relpath: str | None,
    max_bytes: int,
) -> dict[str, object]:
    _require_positive_limit(max_bytes)
    _validate_kind_and_media_type(kind, media_type)
    if not isinstance(data, bytes):
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact data must be bytes")
    if not data:
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact data must not be empty")
    if len(data) > max_bytes:
        raise C10Error("ARTIFACT_LIMIT_EXCEEDED", "artifact byte length exceeds the configured Factory limit")

    normalized_relpath = None
    if repo_relpath is not None:
        normalized_relpath = _normalized_repo_relpath(repo_relpath)

    return {
        "kind": kind,
        "sha256": sha256_hex(data),
        "byte_length": len(data),
        "media_type": media_type,
        "repo_relpath": normalized_relpath,
    }


def artifact_descriptor_from_file(
    root: Path,
    repo_relpath: str,
    *,
    kind: str,
    media_type: str,
    max_bytes: int,
) -> dict[str, object]:
    _require_positive_limit(max_bytes)
    _validate_kind_and_media_type(kind, media_type)
    normalized = _normalized_repo_relpath(repo_relpath)
    path = safe_repo_fixture_path(root, normalized, must_exist=True)

    try:
        with path.open("rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise C10Error("INVALID_HANDOFF_REQUEST", "artifact repository path must resolve to a regular file")
            if before.st_size <= 0:
                raise C10Error("INVALID_HANDOFF_REQUEST", "artifact file must not be empty")
            if before.st_size > max_bytes:
                raise C10Error("ARTIFACT_LIMIT_EXCEEDED", "artifact byte length exceeds the configured Factory limit")
            data = handle.read(max_bytes + 1)
            after = os.fstat(handle.fileno())
    except C10Error:
        raise
    except OSError:
        raise C10Error("INVALID_HANDOFF_REQUEST", "artifact file could not be read safely") from None

    if len(data) > max_bytes:
        raise C10Error("ARTIFACT_LIMIT_EXCEEDED", "artifact byte length exceeds the configured Factory limit")
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or len(data) != before.st_size
    ):
        raise C10Error("ARTIFACT_HASH_MISMATCH", "artifact changed while Factory-owned bytes were being read")

    return artifact_descriptor_from_bytes(
        data,
        kind=kind,
        media_type=media_type,
        repo_relpath=normalized,
        max_bytes=max_bytes,
    )
