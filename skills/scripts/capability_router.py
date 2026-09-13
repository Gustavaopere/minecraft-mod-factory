#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

TARGET = {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "neoforge": "21.1.248",
    "java": 21,
}
READINESS = frozenset({"AVAILABLE", "PREFLIGHT_READY", "UNAVAILABLE"})
ACCEPTANCE = frozenset({"ACCEPTED", "BLOCKED", "NOT_APPLICABLE"})
VERSION_PROOF = frozenset({"NOT_REQUIRED", "REQUIRED_PHYSICAL", "REQUIRED_EXACT_API"})
FALLBACK = frozenset({"NONE", "EXPLICIT_EQUIVALENT_ONLY"})
AUTHORITIES = frozenset({"C2", "C4", "C5", "C6", "C7", "C8", "C10", "C11", "C12", "C13", "ENGINEERING", "ART"})
FORBIDDEN_PROMOTIONS = frozenset({
    "NO_PREFLIGHT_TO_FINAL_ACCEPTANCE",
    "NO_STATIC_TO_RUNTIME_CONFIRMED",
    "NO_OFFLINE_VISUAL_TO_RUNTIME_FIDELITY",
    "NO_PROVIDER_PRESENCE_TO_API_SUPPORT",
    "NO_REFERENCE_ONLY_TO_ACTIVE_AUTHORITY",
})
FINAL_BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
REFERENCE_ONLY_PREFIX = PurePosixPath("migration/provenance/historical-skills/library")

_REQUIRED_TOP_LEVEL = frozenset({"schema_version", "target", "capabilities"})
_REQUIRED_CAPABILITY_FIELDS = frozenset({
    "capability_id",
    "intent",
    "authority",
    "entrypoint",
    "required_evidence",
    "readiness",
    "acceptance",
    "blocker",
    "version_proof",
    "fallback_policy",
    "forbidden_promotions",
})


class CapabilityIndexError(ValueError):
    """Raised when the C13 capability index cannot be loaded or resolved safely."""


def load_capability_index(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CapabilityIndexError(f"cannot load capability index: {source}") from exc
    if not isinstance(payload, dict):
        raise CapabilityIndexError("capability index root must be an object")
    return payload


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item for item in value)


def _entrypoint_errors(entrypoint: object, repo_root: Path) -> list[str]:
    if not isinstance(entrypoint, str) or not entrypoint:
        return ["entrypoint must be a non-empty repository-relative path"]

    path_text, separator, symbol = entrypoint.partition("#")
    pure = PurePosixPath(path_text)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        return [f"entrypoint escapes repository: {entrypoint}"]
    if separator and not symbol:
        return [f"entrypoint symbol is empty: {entrypoint}"]

    reference_parts = REFERENCE_ONLY_PREFIX.parts
    if pure.parts[: len(reference_parts)] == reference_parts:
        return [f"REFERENCE_ONLY entrypoint cannot be active: {entrypoint}"]

    root = repo_root.resolve()
    resolved = (root / Path(*pure.parts)).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return [f"entrypoint escapes repository: {entrypoint}"]

    if not resolved.exists():
        return [f"entrypoint does not exist: {entrypoint}"]

    if separator:
        if not resolved.is_file():
            return [f"entrypoint symbol requires a file: {entrypoint}"]
        try:
            source = resolved.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return [f"entrypoint source cannot be read: {entrypoint}"]
        pattern = rf"^\s*(?:async\s+)?def\s+{re.escape(symbol)}\s*\("
        if re.search(pattern, source, flags=re.MULTILINE) is None:
            return [f"entrypoint symbol does not exist: {entrypoint}"]

    return []


def validate_capability_index(index: object, *, repo_root: str | Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(index, dict):
        return ["capability index root must be an object"]

    keys = set(index)
    if keys != _REQUIRED_TOP_LEVEL:
        missing = sorted(_REQUIRED_TOP_LEVEL - keys)
        extra = sorted(keys - _REQUIRED_TOP_LEVEL)
        errors.append(f"top-level fields mismatch: missing={missing} extra={extra}")

    if index.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if index.get("target") != TARGET:
        errors.append(f"target must exactly match {TARGET}")

    capabilities = index.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("capabilities must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    seen_intents: set[str] = set()
    root = Path(repo_root)

    for position, capability in enumerate(capabilities):
        label = f"capabilities[{position}]"
        if not isinstance(capability, dict):
            errors.append(f"{label} must be an object")
            continue

        fields = set(capability)
        if fields != _REQUIRED_CAPABILITY_FIELDS:
            missing = sorted(_REQUIRED_CAPABILITY_FIELDS - fields)
            extra = sorted(fields - _REQUIRED_CAPABILITY_FIELDS)
            errors.append(f"{label} fields mismatch: missing={missing} extra={extra}")

        capability_id = capability.get("capability_id")
        intent = capability.get("intent")
        authority = capability.get("authority")
        readiness = capability.get("readiness")
        acceptance = capability.get("acceptance")
        blocker = capability.get("blocker")
        version_proof = capability.get("version_proof")
        fallback_policy = capability.get("fallback_policy")
        required_evidence = capability.get("required_evidence")
        forbidden = capability.get("forbidden_promotions")

        if not isinstance(capability_id, str) or not capability_id:
            errors.append(f"{label} capability_id must be a non-empty string")
        elif capability_id in seen_ids:
            errors.append(f"duplicate capability_id: {capability_id}")
        else:
            seen_ids.add(capability_id)

        if not isinstance(intent, str) or not intent:
            errors.append(f"{label} intent must be a non-empty string")
        elif intent in seen_intents:
            errors.append(f"duplicate intent: {intent}")
        else:
            seen_intents.add(intent)

        if authority not in AUTHORITIES:
            errors.append(f"unknown authority: {authority!r}")
        if readiness not in READINESS:
            errors.append(f"{label} invalid readiness: {readiness!r}")
        if acceptance not in ACCEPTANCE:
            errors.append(f"{label} invalid acceptance: {acceptance!r}")
        if version_proof not in VERSION_PROOF:
            errors.append(f"{label} invalid version_proof: {version_proof!r}")
        if fallback_policy not in FALLBACK:
            errors.append(f"{label} invalid fallback_policy: {fallback_policy!r}")

        if not _is_string_list(required_evidence):
            errors.append(f"{label} required_evidence must be a string list")
        elif len(required_evidence) != len(set(required_evidence)):
            errors.append(f"{label} required_evidence contains duplicates")

        if not _is_string_list(forbidden):
            errors.append(f"{label} forbidden_promotions must be a string list")
        else:
            unknown_forbidden = sorted(set(forbidden) - FORBIDDEN_PROMOTIONS)
            if unknown_forbidden:
                errors.append(f"{label} unknown forbidden promotion tokens: {unknown_forbidden}")
            if len(forbidden) != len(set(forbidden)):
                errors.append(f"{label} forbidden_promotions contains duplicates")

        if blocker is not None and (not isinstance(blocker, str) or not blocker):
            errors.append(f"{label} blocker must be null or a non-empty string")

        if acceptance == "ACCEPTED":
            if readiness != "AVAILABLE":
                errors.append(f"{label} ACCEPTED requires AVAILABLE readiness")
            if blocker is not None:
                errors.append(f"{label} ACCEPTED capability cannot retain a blocker")
        elif acceptance == "NOT_APPLICABLE":
            if readiness != "AVAILABLE":
                errors.append(f"{label} NOT_APPLICABLE requires AVAILABLE readiness")
            if blocker is not None:
                errors.append(f"{label} NOT_APPLICABLE capability cannot retain a blocker")
        elif acceptance == "BLOCKED" and not blocker:
            errors.append(f"{label} BLOCKED capability requires a blocker")

        if readiness == "UNAVAILABLE" and acceptance != "BLOCKED":
            errors.append(f"{label} UNAVAILABLE capability must be BLOCKED")
        if readiness == "PREFLIGHT_READY" and acceptance != "BLOCKED":
            errors.append(f"{label} PREFLIGHT_READY capability must be BLOCKED")

        errors.extend(_entrypoint_errors(capability.get("entrypoint"), root))

        if isinstance(intent, str) and intent.startswith("provider."):
            if version_proof != "REQUIRED_EXACT_API":
                errors.append(f"{label} provider-specific route requires REQUIRED_EXACT_API")
            if not isinstance(forbidden, list) or "NO_PROVIDER_PRESENCE_TO_API_SUPPORT" not in forbidden:
                errors.append(
                    f"{label} provider-specific route requires NO_PROVIDER_PRESENCE_TO_API_SUPPORT"
                )

    return errors


def resolve_intent(index: object, intent: str) -> dict[str, Any]:
    if not isinstance(index, dict) or not isinstance(index.get("capabilities"), list):
        raise CapabilityIndexError("cannot resolve intent from malformed capability index")
    if not isinstance(intent, str) or not intent:
        raise CapabilityIndexError("intent must be a non-empty string")

    matches = [
        capability
        for capability in index["capabilities"]
        if isinstance(capability, dict) and capability.get("intent") == intent
    ]
    if len(matches) > 1:
        raise CapabilityIndexError(f"ambiguous capability route for intent: {intent}")
    if len(matches) == 1:
        return copy.deepcopy(matches[0])

    return {
        "capability_id": None,
        "intent": intent,
        "authority": None,
        "entrypoint": None,
        "required_evidence": [],
        "readiness": "UNAVAILABLE",
        "acceptance": "BLOCKED",
        "blocker": "NO_DECLARED_CAPABILITY_ROUTE",
        "version_proof": "NOT_REQUIRED",
        "fallback_policy": "NONE",
        "forbidden_promotions": [],
    }
