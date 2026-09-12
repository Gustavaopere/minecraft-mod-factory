from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from construction.providers.errors import C10Error
from construction.providers.handoff import validate_handoff_receipt, validate_handoff_request
from construction.providers.profiles import load_profile_catalog
from construction.providers.staging import artifact_descriptor_from_file

_SCHEMA_NAMES = (
    "external-provider-profile.schema.json",
    "provider-handoff-request.schema.json",
    "provider-handoff-receipt.schema.json",
)
_SECRET_KEYS = {
    "api_key",
    "apikey",
    "cookie",
    "password",
    "session",
    "session_id",
    "sessionid",
    "token",
}
_TEXT_SECRET_RE = re.compile(
    r"(?i)(?P<key>api[_-]?key|token|password|cookie|session(?:[_-]?id)?)\s*[:=]"
)


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError:
        return "construction/c10-external-path"


def _load_json_object(path: Path, *, label: str, errors: list[str]) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append(f"{label}: invalid JSON")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label}: JSON document must be an object")
        return None
    return value


def _secret_keys_in_json(value: object, prefix: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for raw_key in sorted(value, key=lambda item: str(item)):
            key = str(raw_key)
            normalized = key.lower().replace("-", "_")
            child = f"{prefix}.{key}"
            if normalized in _SECRET_KEYS:
                found.append(child)
            found.extend(_secret_keys_in_json(value[raw_key], child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_secret_keys_in_json(item, f"{prefix}[{index}]"))
    return found


def _scan_secret_file(root: Path, path: Path, errors: list[str]) -> None:
    label = _rel(root, path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        errors.append(f"{label}: unreadable text fixture")
        return

    if path.suffix.lower() == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            errors.append(f"{label}: invalid JSON fixture")
            return
        for key_path in _secret_keys_in_json(value):
            errors.append(f"{label}: secret-like key {key_path}")
        return

    seen: set[str] = set()
    for match in _TEXT_SECRET_RE.finditer(text):
        key = match.group("key").lower().replace("-", "_")
        if key not in seen:
            seen.add(key)
            errors.append(f"{label}: secret-like key {key}")


def _scan_secrets(root: Path, profile_dir: Path, fixture_dir: Path, errors: list[str]) -> None:
    paths: list[Path] = []
    if profile_dir.is_dir():
        paths.extend(profile_dir.glob("*.json"))
    if fixture_dir.is_dir():
        paths.extend(
            path
            for path in fixture_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".json", ".txt"}
        )
    for path in sorted(set(paths), key=lambda item: _rel(root, item)):
        _scan_secret_file(root, path, errors)


def _validate_schemas(root: Path, errors: list[str]) -> None:
    schema_dir = root / "construction" / "schemas"
    for name in _SCHEMA_NAMES:
        path = schema_dir / name
        label = f"construction/schemas/{name}"
        document = _load_json_object(path, label=label, errors=errors)
        if document is not None and document.get("additionalProperties") is not False:
            errors.append(f"{label}: top-level additionalProperties must be false")


def _positive_limit(profile: dict[str, object], field: str) -> int | None:
    limits = profile.get("limits")
    value = limits.get(field) if isinstance(limits, dict) else None
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return None


def _bind_artifact(
    root: Path,
    artifact: object,
    *,
    max_bytes: int | None,
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(artifact, dict):
        return
    repo_relpath = artifact.get("repo_relpath")
    if repo_relpath is None:
        return
    if max_bytes is None:
        errors.append(f"{label}: ARTIFACT_LIMIT_EXCEEDED: Factory size limit is not configured")
        return

    kind = artifact.get("kind")
    media_type = artifact.get("media_type")
    if not isinstance(repo_relpath, str) or not isinstance(kind, str) or not isinstance(media_type, str):
        return
    try:
        actual = artifact_descriptor_from_file(
            root,
            repo_relpath,
            kind=kind,
            media_type=media_type,
            max_bytes=max_bytes,
        )
    except C10Error as exc:
        errors.append(f"{label}: {exc.code}: artifact bytes rejected")
        return

    expected_length = artifact.get("byte_length")
    if expected_length != actual["byte_length"]:
        errors.append(f"{label}: INVALID_HANDOFF_RECEIPT: byte length does not match Factory-owned artifact bytes")
    if artifact.get("sha256") != actual["sha256"]:
        errors.append(f"{label}: ARTIFACT_HASH_MISMATCH: SHA-256 does not match Factory-owned artifact bytes")


def _fixture_documents(
    root: Path,
    fixture_dir: Path,
    errors: list[str],
) -> list[tuple[Path, dict[str, object]]]:
    documents: list[tuple[Path, dict[str, object]]] = []
    if not fixture_dir.is_dir():
        return documents
    for path in sorted(fixture_dir.rglob("*.json"), key=lambda item: _rel(root, item)):
        document = _load_json_object(path, label=_rel(root, path), errors=errors)
        if document is not None:
            documents.append((path, document))
    return documents


def _validate_fixtures(
    root: Path,
    profiles: dict[str, dict[str, object]],
    fixture_dir: Path,
    errors: list[str],
) -> None:
    documents = _fixture_documents(root, fixture_dir, errors)
    requests: dict[str, tuple[Path, dict[str, object]]] = {}

    for path, document in documents:
        if "request_id" in document and "receipt_sha256" not in document:
            request_id = document.get("request_id")
            if isinstance(request_id, str):
                if request_id in requests:
                    errors.append(f"{_rel(root, path)}: duplicate request_id")
                else:
                    requests[request_id] = (path, document)

    for path, document in documents:
        label = _rel(root, path)
        provider_id = document.get("provider_id")
        profile = profiles.get(provider_id) if isinstance(provider_id, str) else None

        if "request_id" in document and "receipt_sha256" not in document:
            if profile is None:
                errors.append(f"{label}: UNKNOWN_PROVIDER: request provider is not in the C10 profile catalog")
                continue
            for error in validate_handoff_request(document, profile):
                errors.append(f"{label}: {error}")
            max_input = _positive_limit(profile, "max_input_bytes")
            raw_artifacts = document.get("input_artifacts")
            if isinstance(raw_artifacts, list):
                for index, artifact in enumerate(raw_artifacts):
                    _bind_artifact(
                        root,
                        artifact,
                        max_bytes=max_input,
                        label=f"{label}: input_artifacts[{index}]",
                        errors=errors,
                    )

        elif "receipt_sha256" in document:
            if profile is None:
                errors.append(f"{label}: UNKNOWN_PROVIDER: receipt provider is not in the C10 profile catalog")
                continue
            request_id = document.get("request_id")
            request_entry = requests.get(request_id) if isinstance(request_id, str) else None
            if request_entry is None:
                errors.append(f"{label}: INVALID_HANDOFF_RECEIPT: matching request fixture is missing")
                continue
            _, request = request_entry
            for error in validate_handoff_receipt(document, request, profile):
                errors.append(f"{label}: {error}")
            max_output = _positive_limit(profile, "max_output_bytes")
            raw_artifacts = document.get("received_artifacts")
            if isinstance(raw_artifacts, list):
                for index, artifact in enumerate(raw_artifacts):
                    _bind_artifact(
                        root,
                        artifact,
                        max_bytes=max_output,
                        label=f"{label}: received_artifacts[{index}]",
                        errors=errors,
                    )


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []
    root = Path(root).resolve()
    registry_path = root / "construction" / "upstream" / "registry.json"
    profile_dir = root / "construction" / "providers" / "profiles"
    fixture_dir = root / "construction" / "fixtures" / "c10"

    registry = _load_json_object(
        registry_path,
        label="construction/upstream/registry.json",
        errors=errors,
    )
    profiles: dict[str, dict[str, object]] = {}
    if registry is not None:
        try:
            profiles = load_profile_catalog(profile_dir, registry)
        except (C10Error, OSError, ValueError, json.JSONDecodeError):
            errors.append("construction/providers/profiles: profile catalog rejected")

    _validate_schemas(root, errors)
    _scan_secrets(root, profile_dir, fixture_dir, errors)
    if profiles:
        _validate_fixtures(root, profiles, fixture_dir, errors)
    return sorted(set(errors))


def main() -> int:
    errors = validate_repository(Path.cwd())
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print("CONSTRUCTION C10: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
