#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TARGET = {"minecraft": "1.21.1", "loader": "neoforge", "neoforge": "21.1.248", "java": 21}
AUTHORITY = {
    "source_registry": "engineering/catalog/sources/SOURCE-REGISTRY.json",
    "physical_catalog_builder": "engineering/tooling/import-physical-modlist.py",
    "dependency_profile_schema": "engineering/schemas/dependency-profile.schema.json",
    "compatibility_matrix_schema": "engineering/schemas/compatibility-matrix.schema.json",
}
PROOF_LEVELS = [
    "P0 PRESENCE_ONLY",
    "P1 METADATA_VERIFIED",
    "P2 SOURCE/DOC_VERIFIED",
    "P3 COMPILE_PROVEN",
    "P4 RUNTIME_SMOKE",
    "P5 INTEGRATION_TESTED",
    "P6 MULTIPLAYER/PERF_PROVEN",
]
STATES = {
    "CONFIRMED",
    "IMPLEMENTED",
    "MERGED",
    "PASS",
    "PENDING",
    "UNRESOLVED",
    "UNAVAILABLE",
    "DEFERRED",
    "REFERENCE_ONLY",
    "INCOMPATIBLE",
    "BLOCKED",
    "SUPERSEDED",
}
PROVENANCE_STATES = {"CONFIRMED", "UNRESOLVED", "REFERENCE_ONLY"}
MOD_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PROFILE_RE = re.compile(r"^engineering/catalog/providers/profiles/[a-z0-9_.-]+\.json$")


def _workspace_path(value: str) -> Path:
    workspace = Path.cwd().resolve()
    raw = Path(value)
    candidate = raw.resolve(strict=True) if raw.is_absolute() else (workspace / raw).resolve(strict=True)
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"catalog must stay inside workspace: {workspace}") from exc
    if candidate == workspace:
        raise ValueError("catalog must identify a file, not the workspace root")
    return candidate


def _nonempty_strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item for item in value)


def _validate_source(source, prefix: str) -> tuple[list[str], bool]:
    errors: list[str] = []
    if not isinstance(source, dict):
        return [f"{prefix}.source must be an object"], False

    state = source.get("state")
    evidence = source.get("evidence")
    if state not in PROVENANCE_STATES:
        errors.append(f"{prefix}.source.state is invalid")
    if not _nonempty_strings(evidence) or not evidence:
        errors.append(f"{prefix}.source.evidence must contain at least one item")

    if state in {"CONFIRMED", "REFERENCE_ONLY"}:
        locators = ("repository", "commit", "documentation", "artifact")
        if not any(isinstance(source.get(field), str) and source.get(field) for field in locators):
            errors.append(f"{prefix}.source must include a provenance locator")

    confirmed = (
        state == "CONFIRMED"
        and isinstance(source.get("repository"), str)
        and bool(source.get("repository"))
        and isinstance(source.get("commit"), str)
        and bool(source.get("commit"))
        and _nonempty_strings(evidence)
        and bool(evidence)
    )
    return errors, confirmed


def _validate_license(license_info, prefix: str) -> tuple[list[str], bool]:
    errors: list[str] = []
    if not isinstance(license_info, dict):
        return [f"{prefix}.license must be an object"], False

    state = license_info.get("state")
    evidence = license_info.get("evidence")
    if state not in PROVENANCE_STATES:
        errors.append(f"{prefix}.license.state is invalid")
    if not _nonempty_strings(evidence) or not evidence:
        errors.append(f"{prefix}.license.evidence must contain at least one item")
    if state in {"CONFIRMED", "REFERENCE_ONLY"} and (
        not isinstance(license_info.get("name"), str) or not license_info.get("name")
    ):
        errors.append(f"{prefix}.license.name must be non-empty when license state is resolved")

    confirmed = (
        state == "CONFIRMED"
        and isinstance(license_info.get("name"), str)
        and bool(license_info.get("name"))
        and _nonempty_strings(evidence)
        and bool(evidence)
    )
    return errors, confirmed


def _validate_provider(provider, index: int, workspace: Path) -> list[str]:
    prefix = f"providers[{index}]"
    errors: list[str] = []
    if not isinstance(provider, dict):
        return [f"{prefix} must be an object"]

    required = {
        "mod_id",
        "physical",
        "source",
        "license",
        "dependency_profile",
        "docs",
        "api_surface",
        "compatibility",
        "runtime_health",
        "known_conflicts",
        "requirement",
        "integration_tests",
        "jar_fingerprints",
        "supported",
        "state",
    }
    missing = sorted(required.difference(provider))
    if missing:
        errors.append(f"{prefix} missing fields: {', '.join(missing)}")
        return errors

    mod_id = provider["mod_id"]
    if not isinstance(mod_id, str) or MOD_ID_RE.fullmatch(mod_id) is None:
        errors.append(f"{prefix}.mod_id has invalid syntax")

    physical = provider["physical"]
    if not isinstance(physical, dict):
        errors.append(f"{prefix}.physical must be an object")
    else:
        physical_required = {"version", "version_evidence", "source_registry_id", "source_sha256"}
        physical_missing = sorted(physical_required.difference(physical))
        if physical_missing:
            errors.append(f"{prefix}.physical missing fields: {', '.join(physical_missing)}")
        else:
            if not isinstance(physical["version"], str) or not physical["version"]:
                errors.append(f"{prefix}.physical.version must be non-empty")
            if physical["version_evidence"] not in {"MOD_METADATA", "JAR_FILENAME", "UNRESOLVED"}:
                errors.append(f"{prefix}.physical.version_evidence is invalid")
            if not isinstance(physical["source_registry_id"], str) or not physical["source_registry_id"]:
                errors.append(f"{prefix}.physical.source_registry_id must be non-empty")
            if not isinstance(physical["source_sha256"], str) or SHA256_RE.fullmatch(physical["source_sha256"]) is None:
                errors.append(f"{prefix}.physical.source_sha256 must be lowercase SHA-256")

    source_errors, source_confirmed = _validate_source(provider["source"], prefix)
    license_errors, license_confirmed = _validate_license(provider["license"], prefix)
    errors.extend(source_errors)
    errors.extend(license_errors)

    profile = provider["dependency_profile"]
    if not isinstance(profile, str) or PROFILE_RE.fullmatch(profile) is None:
        errors.append(f"{prefix}.dependency_profile must use the canonical provider profile path")
    else:
        profile_path = (workspace / profile).resolve(strict=False)
        try:
            profile_path.relative_to(workspace)
        except ValueError:
            errors.append(f"{prefix}.dependency_profile escapes workspace")
        if not profile_path.is_file():
            errors.append(f"{prefix}.dependency_profile does not exist: {profile}")

    for field in ("docs", "known_conflicts", "integration_tests", "jar_fingerprints"):
        if not _nonempty_strings(provider[field]):
            errors.append(f"{prefix}.{field} must be an array of non-empty strings")

    surfaces = provider["api_surface"]
    if not isinstance(surfaces, list):
        errors.append(f"{prefix}.api_surface must be an array")
        surfaces = []
    for surface_index, surface in enumerate(surfaces):
        surface_prefix = f"{prefix}.api_surface[{surface_index}]"
        if not isinstance(surface, dict):
            errors.append(f"{surface_prefix} must be an object")
            continue
        surface_required = {"surface_id", "proof_level", "state", "evidence"}
        surface_missing = sorted(surface_required.difference(surface))
        if surface_missing:
            errors.append(f"{surface_prefix} missing fields: {', '.join(surface_missing)}")
            continue
        if not isinstance(surface["surface_id"], str) or not surface["surface_id"]:
            errors.append(f"{surface_prefix}.surface_id must be non-empty")
        if surface["proof_level"] not in PROOF_LEVELS:
            errors.append(f"{surface_prefix}.proof_level is invalid")
        if surface["state"] not in STATES:
            errors.append(f"{surface_prefix}.state is invalid")
        if not _nonempty_strings(surface["evidence"]) or not surface["evidence"]:
            errors.append(f"{surface_prefix}.evidence must contain at least one item")

    compatibility = provider["compatibility"]
    if not isinstance(compatibility, dict):
        errors.append(f"{prefix}.compatibility must be an object")
    else:
        if compatibility.get("state") not in STATES:
            errors.append(f"{prefix}.compatibility.state is invalid")
        evidence = compatibility.get("evidence")
        if not _nonempty_strings(evidence) or not evidence:
            errors.append(f"{prefix}.compatibility.evidence must contain at least one item")

    if provider["runtime_health"] not in STATES:
        errors.append(f"{prefix}.runtime_health is invalid")
    if provider["requirement"] not in {"OPTIONAL", "REQUIRED"}:
        errors.append(f"{prefix}.requirement is invalid")
    if not isinstance(provider["supported"], bool):
        errors.append(f"{prefix}.supported must be boolean")
    if provider["state"] not in STATES:
        errors.append(f"{prefix}.state is invalid")

    proven_surfaces = [
        surface
        for surface in surfaces
        if isinstance(surface, dict) and surface.get("proof_level") in PROOF_LEVELS[1:]
    ]
    if provider.get("supported") is True:
        if not proven_surfaces:
            errors.append(f"{prefix} cannot be supported with only P0 or no API proof")
        if not source_confirmed:
            errors.append(f"{prefix} cannot be supported without CONFIRMED source metadata")
        if not license_confirmed:
            errors.append(f"{prefix} cannot be supported without CONFIRMED license metadata")

    return errors


def validate_catalog(catalog: object, workspace: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(catalog, dict):
        return ["catalog must be an object"]
    if catalog.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if catalog.get("target") != TARGET:
        errors.append("target must match Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21")
    if catalog.get("authority") != AUTHORITY:
        errors.append("authority must reuse the canonical Engineering source/profile/compatibility authorities")
    providers = catalog.get("providers")
    if not isinstance(providers, list):
        errors.append("providers must be an array")
        providers = []
    seen: set[str] = set()
    for index, provider in enumerate(providers):
        errors.extend(_validate_provider(provider, index, workspace))
        if isinstance(provider, dict) and isinstance(provider.get("mod_id"), str):
            mod_id = provider["mod_id"]
            if mod_id in seen:
                errors.append(f"providers[{index}].mod_id duplicates {mod_id}")
            seen.add(mod_id)
    if catalog.get("state") not in STATES:
        errors.append("state is invalid")
    if catalog.get("state") == "PASS" and not providers:
        errors.append("state PASS requires at least one provider")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Factory I7 Engineering provider catalog.")
    parser.add_argument("--catalog", default="engineering/catalog/providers/PROVIDER-CATALOG.json")
    args = parser.parse_args()
    try:
        catalog_path = _workspace_path(args.catalog)
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"I7 provider catalog validation failed: {exc}")
        return 2

    errors = validate_catalog(catalog, Path.cwd().resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("I7 provider catalog validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
