#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PIN_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[^/]+/[^/]+$")
SOURCE_POLICIES = {
    "IMMUTABLE_SNAPSHOT",
    "ENGINE_REFERENCE",
    "LIBRARY_SNAPSHOT",
    "REFERENCE_ONLY",
}
SOURCE_STATES = {"AUDITED_NOT_VENDORED", "DO_NOT_VENDOR"}
EXTERNAL_API_STATES = {"UNVERIFIED_API", "VERIFIED_API", "MANUAL_HANDOFF"}
MATERIALIZABLE_SNAPSHOT_POLICIES = {"IMMUTABLE_SNAPSHOT", "LIBRARY_SNAPSHOT"}

REQUIRED_PATHS = (
    "construction/README.md",
    "construction/STATUS.md",
    "construction/docs/ARCHITECTURE.md",
    "construction/upstream/registry.json",
    "construction/schemas/build-spec.schema.json",
    "construction/schemas/upstream-source.schema.json",
    "construction/tests/test_c0_foundation.py",
    "construction/scripts/validate_c0.py",
    ".github/workflows/factory-construction-c0-foundation.yml",
)


def load_json(path: Path) -> tuple[Any | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [f"missing JSON file: {path}"]
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON {path}: {exc}"]


def validate_registry(registry: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(registry, dict):
        return ["upstream registry must be an object"]
    if registry.get("schema_version") != 1:
        errors.append("upstream registry schema_version must be 1")

    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("upstream registry sources must be a non-empty array")
        sources = []

    seen: set[str] = set()
    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif source_id in seen:
            errors.append(f"duplicate source id: {source_id}")
        else:
            seen.add(source_id)

        repository = source.get("repository")
        if not isinstance(repository, str) or not REPOSITORY_RE.fullmatch(repository):
            errors.append(f"{prefix}.repository must use owner/repo form")

        pinned = source.get("pinned_commit")
        if not isinstance(pinned, str) or not PIN_RE.fullmatch(pinned):
            errors.append(f"{prefix}.pinned_commit must be an exact 40-character lowercase Git commit")

        license_name = source.get("license")
        if not isinstance(license_name, str) or not license_name:
            errors.append(f"{prefix}.license must be explicit")

        policy = source.get("integration_policy")
        state = source.get("c0_state")
        if policy not in SOURCE_POLICIES:
            errors.append(f"{prefix}.integration_policy is unsupported: {policy!r}")
        if state not in SOURCE_STATES:
            errors.append(f"{prefix}.c0_state is unsupported: {state!r}")
        if policy == "REFERENCE_ONLY" and state != "DO_NOT_VENDOR":
            errors.append(f"{prefix} REFERENCE_ONLY sources must be DO_NOT_VENDOR")
        if state == "DO_NOT_VENDOR" and policy != "REFERENCE_ONLY":
            errors.append(f"{prefix} DO_NOT_VENDOR sources must be REFERENCE_ONLY")

    providers = registry.get("external_providers")
    if not isinstance(providers, list):
        errors.append("external_providers must be an array")
        providers = []

    provider_ids: set[str] = set()
    for index, provider in enumerate(providers):
        prefix = f"external_providers[{index}]"
        if not isinstance(provider, dict):
            errors.append(f"{prefix} must be an object")
            continue
        provider_id = provider.get("id")
        if not isinstance(provider_id, str) or not provider_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif provider_id in provider_ids:
            errors.append(f"duplicate external provider id: {provider_id}")
        else:
            provider_ids.add(provider_id)
        if provider.get("integration_policy") != "EXTERNAL_PROVIDER":
            errors.append(f"{prefix}.integration_policy must be EXTERNAL_PROVIDER")
        if provider.get("api_state") not in EXTERNAL_API_STATES:
            errors.append(f"{prefix}.api_state is unsupported: {provider.get('api_state')!r}")

    return errors


def validate_build_spec_schema(schema: Any) -> list[str]:
    errors: list[str] = []
    try:
        properties = schema["properties"]
        target = properties["target"]["properties"]
        formats = properties["outputs"]["properties"]["formats"]["items"]["enum"]
    except (KeyError, TypeError):
        return ["build-spec schema is missing required C0 contract structure"]

    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("build-spec schema must declare JSON Schema draft 2020-12")
    if target.get("minecraft_version", {}).get("const") != "1.21.1":
        errors.append("build-spec target.minecraft_version must be fixed to 1.21.1 in C0")
    loaders = target.get("loader", {}).get("enum", [])
    if "neoforge" not in loaders:
        errors.append("build-spec target.loader must allow neoforge")
    if "sponge_v3" not in formats:
        errors.append("build-spec outputs must include sponge_v3")
    return errors


def validate_upstream_schema(schema: Any) -> list[str]:
    if not isinstance(schema, dict):
        return ["upstream-source schema must be an object"]
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("upstream-source schema must declare JSON Schema draft 2020-12")
    required = set(schema.get("required", []))
    expected = {"schema_version", "audited_at", "sources", "external_providers"}
    if not expected.issubset(required):
        errors.append("upstream-source schema must require schema_version, audited_at, sources and external_providers")
    return errors


def _is_initialized_git_submodule(path: Path) -> bool:
    marker = path / ".git"
    if not marker.is_file():
        return False
    try:
        marker_text = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return marker_text.startswith("gitdir: ")


def validate_snapshot_boundary(root: Path, registry: Any) -> list[str]:
    snapshots = root / "construction/upstream/snapshots"
    if not snapshots.exists():
        return []

    materializable_ids: set[str] = set()
    if isinstance(registry, dict):
        sources = registry.get("sources", [])
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict):
                    continue
                source_id = source.get("id")
                policy = source.get("integration_policy")
                if isinstance(source_id, str) and policy in MATERIALIZABLE_SNAPSHOT_POLICIES:
                    materializable_ids.add(source_id)

    errors: list[str] = []
    for entry in sorted(snapshots.iterdir(), key=lambda item: item.name):
        relative = entry.relative_to(root).as_posix()
        if entry.is_symlink():
            errors.append(f"snapshot boundary forbids symlinks: {relative}")
            continue
        if entry.is_dir() and entry.name in materializable_ids and _is_initialized_git_submodule(entry):
            continue

        payloads: list[str] = []
        if entry.is_file():
            payloads.append(relative)
        elif entry.is_dir():
            payloads.extend(
                path.relative_to(root).as_posix()
                for path in entry.rglob("*")
                if path.is_file()
            )
        if payloads:
            errors.append(
                "snapshot payload must be an initialized materializable Git submodule: "
                + ", ".join(sorted(payloads))
            )
    return errors


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []

    for relative in REQUIRED_PATHS:
        if not (root / relative).is_file():
            errors.append(f"missing required C0 path: {relative}")

    registry, registry_load_errors = load_json(root / "construction/upstream/registry.json")
    errors.extend(registry_load_errors)
    if registry is not None:
        errors.extend(validate_registry(registry))
    errors.extend(validate_snapshot_boundary(root, registry))

    build_schema, build_schema_errors = load_json(root / "construction/schemas/build-spec.schema.json")
    errors.extend(build_schema_errors)
    if build_schema is not None:
        errors.extend(validate_build_spec_schema(build_schema))

    upstream_schema, upstream_schema_errors = load_json(root / "construction/schemas/upstream-source.schema.json")
    errors.extend(upstream_schema_errors)
    if upstream_schema is not None:
        errors.extend(validate_upstream_schema(upstream_schema))

    readme = root / "construction/README.md"
    if readme.is_file():
        readme_text = readme.read_text(encoding="utf-8")
        for marker in ("Sponge Schematic v3", "immutable", "C0"):
            if marker not in readme_text:
                errors.append(f"construction README missing authority marker: {marker}")

    architecture = root / "construction/docs/ARCHITECTURE.md"
    if architecture.is_file():
        architecture_text = architecture.read_text(encoding="utf-8")
        for marker in ("BuildSpec", "runtime NeoForge registry", "Sponge Schematic v3", "MCP"):
            if marker not in architecture_text:
                errors.append(f"construction architecture missing marker: {marker}")

    workflow = root / ".github/workflows/factory-construction-c0-foundation.yml"
    if workflow.is_file():
        workflow_text = workflow.read_text(encoding="utf-8")
        commands = (
            "python3 -m unittest discover -s construction/tests",
            "python3 construction/scripts/validate_c0.py",
            "git diff --check HEAD^ -- construction",
        )
        for command in commands:
            if command not in workflow_text:
                errors.append(f"construction C0 workflow missing gate: {command}")
        if "submodules: recursive" not in workflow_text:
            errors.append("construction C0 workflow must validate initialized upstream snapshots")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    errors = validate(root)
    if errors:
        print("CONSTRUCTION C0: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CONSTRUCTION C0: PASS")
    print(f"- required paths: {len(REQUIRED_PATHS)}")
    print("- upstream pins: validated")
    print("- schemas: validated")
    print("- snapshot boundary: validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
