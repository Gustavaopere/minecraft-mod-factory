#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

ENG = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = ENG / "schemas" / "asset-handoff.schema.json"
I1_SCRIPT = ENG / "tooling" / "validate-i1-foundation.py"
UNRESOLVED = "UNRESOLVED"
PASS = "PASS"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _load_i1_validator():
    spec = importlib.util.spec_from_file_location("i1_foundation_validator", I1_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load I1 validator from {I1_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


I1 = _load_i1_validator()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _workspace_path(value: Path | str, *, label: str, require_directory: bool = False) -> Path:
    workspace = Path.cwd().resolve()
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = workspace / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(workspace):
        raise ValueError(f"{label}: path must remain within current workspace")
    if require_directory and not candidate.is_dir():
        raise ValueError(f"{label}: directory does not exist within current workspace")
    if not require_directory and not candidate.is_file():
        raise ValueError(f"{label}: file does not exist within current workspace")
    return candidate


def _is_bounded_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or value == UNRESOLVED:
        return value == UNRESOLVED
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        return False
    parts = PurePosixPath(normalized).parts
    return bool(parts) and all(part not in {"..", ""} for part in parts)


def _bounded_file(root: Path, relative: str) -> Path | None:
    if not _is_bounded_relative_path(relative) or relative == UNRESOLVED:
        return None
    root_resolved = root.resolve()
    candidate = (root_resolved / PurePosixPath(relative.replace("\\", "/"))).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None
    return candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_file_hash(
    *,
    root: Path | None,
    relative: Any,
    expected: Any,
    path_label: str,
    hash_label: str,
) -> list[str]:
    errors: list[str] = []
    if root is None or relative == UNRESOLVED:
        return errors
    candidate = _bounded_file(root, relative) if isinstance(relative, str) else None
    if candidate is None:
        return [f"{path_label}: must be bounded beneath the supplied root"]
    if not candidate.is_file():
        return [f"{path_label}: file does not exist beneath the supplied root: {relative!r}"]
    if expected == UNRESOLVED:
        errors.append(f"{hash_label}: cannot be UNRESOLVED when the artifact file is available")
        return errors
    if isinstance(expected, str):
        actual = _sha256(candidate)
        if actual != expected:
            errors.append(f"{hash_label}: expected {expected}, actual {actual}")
    return errors


def _validate_delivery_namespace(value: Any, mod_id: Any, label: str) -> list[str]:
    if value == UNRESOLVED:
        return []
    if not isinstance(value, str) or not _is_bounded_relative_path(value):
        return [f"{label}: must be a bounded relative path"]
    parts = PurePosixPath(value.replace("\\", "/")).parts
    expected_prefix = ("src", "main", "resources", "assets")
    if len(parts) < 6 or tuple(parts[:4]) != expected_prefix:
        return [
            f"{label}: output destination must start with src/main/resources/assets/<mod_id>/"
        ]
    if isinstance(mod_id, str) and parts[4] != mod_id:
        return [f"{label}: namespace {parts[4]!r} must match mod_id {mod_id!r}"]
    return []


def _missing_proofs(required: Any, verified: Any) -> list[str]:
    if not isinstance(required, list) or not isinstance(verified, list):
        return []
    verified_set = {value for value in verified if isinstance(value, str)}
    return [value for value in required if isinstance(value, str) and value not in verified_set]


def validate_manifest_data(
    manifest: Any,
    *,
    schema: Any | None = None,
    source_root: Path | str | None = None,
    runtime_root: Path | str | None = None,
    actual_source_revision: str | None = None,
) -> list[str]:
    """Validate one I6 asset handoff manifest without resolving external remotes.

    The function is deliberately offline and fail-closed. File hashes are checked only
    when the corresponding repository root is explicitly supplied by the caller.
    """
    if schema is None:
        schema = load_json(DEFAULT_SCHEMA)

    errors = list(I1.validate_instance(schema, manifest))
    errors.extend(I1.validate_asset_handoff_semantics(manifest))
    if not isinstance(manifest, dict):
        return errors

    state = manifest.get("state")
    mod_id = manifest.get("mod_id")
    source_repository = manifest.get("source_repository")
    source_revision = manifest.get("source_revision")
    runtime_authority = manifest.get("runtime_authority")
    provider_profiles = manifest.get("provider_profiles")
    provider_bindings = manifest.get("provider_bindings")
    visual_inputs = manifest.get("visual_inputs")
    artifacts = manifest.get("artifacts")

    if state == PASS:
        for field_name, value in (
            ("source_repository", source_repository),
            ("source_revision", source_revision),
            ("runtime_authority", runtime_authority),
        ):
            if value == UNRESOLVED:
                errors.append(f"$.{field_name}: PASS cannot use UNRESOLVED")
        if not isinstance(source_revision, str) or HEX40.fullmatch(source_revision) is None:
            errors.append("$.source_revision: PASS requires an exact 40-character lowercase Git revision")
        if not isinstance(provider_profiles, list) or not provider_profiles:
            errors.append("$.provider_profiles: PASS requires at least one declared provider profile")

    if actual_source_revision is not None and state == PASS and source_revision != actual_source_revision:
        errors.append(
            f"$.source_revision: manifest {source_revision!r} does not match actual source revision {actual_source_revision!r}"
        )

    declared_profiles = {
        value for value in provider_profiles or [] if isinstance(value, str) and value != UNRESOLVED
    }
    binding_profiles: set[str] = set()
    if isinstance(provider_bindings, list):
        for index, binding in enumerate(provider_bindings):
            if not isinstance(binding, dict):
                continue
            profile = binding.get("provider_profile")
            adapter = binding.get("runtime_adapter")
            label = f"$.provider_bindings[{index}]"
            if isinstance(profile, str):
                if profile in binding_profiles:
                    errors.append(f"{label}.provider_profile: duplicate provider binding {profile!r}")
                binding_profiles.add(profile)
                if profile != UNRESOLVED and profile not in declared_profiles:
                    errors.append(f"{label}.provider_profile: {profile!r} is not declared in provider_profiles")
            if state == PASS and adapter == UNRESOLVED:
                errors.append(f"{label}.runtime_adapter: PASS cannot use UNRESOLVED")
    if state == PASS:
        for profile in sorted(declared_profiles.difference(binding_profiles)):
            errors.append(f"$.provider_bindings: missing binding for provider_profile {profile!r}")

    visual_names: set[str] = set()
    if isinstance(visual_inputs, list):
        for index, visual_input in enumerate(visual_inputs):
            if not isinstance(visual_input, dict):
                continue
            label = f"$.visual_inputs[{index}]"
            name = visual_input.get("name")
            if isinstance(name, str):
                if name in visual_names:
                    errors.append(f"{label}.name: duplicate visual input {name!r}")
                visual_names.add(name)
            if state == PASS and visual_input.get("runtime_binding") == UNRESOLVED:
                errors.append(f"{label}.runtime_binding: PASS cannot use UNRESOLVED")

    source_root_path = Path(source_root) if source_root is not None else None
    runtime_root_path = Path(runtime_root) if runtime_root is not None else None

    asset_ids: set[str] = set()
    if isinstance(artifacts, list):
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                continue
            label = f"$.artifacts[{index}]"
            asset_id = artifact.get("asset_id")
            if isinstance(asset_id, str):
                if asset_id in asset_ids:
                    errors.append(f"{label}.asset_id: duplicate asset_id {asset_id!r}")
                asset_ids.add(asset_id)

            source_path = artifact.get("source_path")
            delivery_path = artifact.get("delivery_path")
            provider_profile = artifact.get("provider_profile")
            qa = artifact.get("qa")

            if source_path != UNRESOLVED and not _is_bounded_relative_path(source_path):
                errors.append(f"{label}.source_path: must be bounded beneath the source repository root")
            errors.extend(_validate_delivery_namespace(delivery_path, mod_id, f"{label}.delivery_path"))

            if provider_profile != UNRESOLVED:
                if provider_profile not in declared_profiles:
                    errors.append(
                        f"{label}.provider_profile: {provider_profile!r} is not declared in provider_profiles"
                    )
                elif provider_profile not in binding_profiles:
                    errors.append(
                        f"{label}.provider_profile: {provider_profile!r} has no provider binding"
                    )

            if isinstance(artifact.get("textures"), list):
                for texture_index, texture in enumerate(artifact["textures"]):
                    errors.extend(
                        _validate_delivery_namespace(
                            texture,
                            mod_id,
                            f"{label}.textures[{texture_index}]",
                        )
                    )

            if isinstance(qa, dict):
                proof_pairs = (
                    ("required_bones", "verified_bones"),
                    ("required_anchors", "verified_anchors"),
                    ("required_clips", "verified_clips"),
                    ("textures", "verified_textures"),
                )
                for required_key, verified_key in proof_pairs:
                    missing = _missing_proofs(artifact.get(required_key), qa.get(verified_key))
                    for value in missing:
                        errors.append(
                            f"{label}.{required_key}: {value!r} lacks QA proof in qa.{verified_key}"
                        )
                if state == PASS:
                    if qa.get("state") != PASS:
                        errors.append(f"{label}.qa.state: top-level PASS requires artifact QA PASS")
                    if qa.get("namespace_verified") is not True:
                        errors.append(f"{label}.qa.namespace_verified: top-level PASS requires true")
                    if qa.get("output_destination_verified") is not True:
                        errors.append(f"{label}.qa.output_destination_verified: top-level PASS requires true")

            if state == PASS:
                if artifact.get("state") != PASS:
                    errors.append(f"{label}.state: top-level PASS requires artifact PASS")
                conversion = artifact.get("conversion")
                if isinstance(conversion, dict) and conversion.get("state") != PASS:
                    errors.append(f"{label}.conversion.state: top-level PASS requires conversion PASS")
                for hash_key in ("source_sha256", "delivery_sha256"):
                    if artifact.get(hash_key) == UNRESOLVED:
                        errors.append(f"{label}.{hash_key}: PASS cannot use UNRESOLVED")

            errors.extend(
                _verify_file_hash(
                    root=source_root_path,
                    relative=source_path,
                    expected=artifact.get("source_sha256"),
                    path_label=f"{label}.source_path",
                    hash_label=f"{label}.source_sha256",
                )
            )
            errors.extend(
                _verify_file_hash(
                    root=runtime_root_path,
                    relative=delivery_path,
                    expected=artifact.get("delivery_sha256"),
                    path_label=f"{label}.delivery_path",
                    hash_label=f"{label}.delivery_sha256",
                )
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an I6 asset handoff manifest without external side effects.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--source-revision")
    args = parser.parse_args(argv)

    try:
        manifest_path = _workspace_path(args.manifest, label="manifest")
        source_root = (
            _workspace_path(args.source_root, label="source root", require_directory=True)
            if args.source_root is not None
            else None
        )
        runtime_root = (
            _workspace_path(args.runtime_root, label="runtime root", require_directory=True)
            if args.runtime_root is not None
            else None
        )
        manifest = load_json(manifest_path)
        schema = load_json(DEFAULT_SCHEMA)
    except Exception as exc:
        print(f"I6 ASSET HANDOFF VALIDATION: FAIL\n- parse/load error: {exc}")
        return 1

    errors = validate_manifest_data(
        manifest,
        schema=schema,
        source_root=source_root,
        runtime_root=runtime_root,
        actual_source_revision=args.source_revision,
    )
    if errors:
        print("I6 ASSET HANDOFF VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("I6 ASSET HANDOFF VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
