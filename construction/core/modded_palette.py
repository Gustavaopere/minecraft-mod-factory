from __future__ import annotations

import hashlib
import json
import re
from typing import Any

BLOCK_ID_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
NAMESPACE_RE = re.compile(r"^[a-z0-9_.-]+$")
ROLE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
TERM_RE = re.compile(r"^[a-z0-9_./-]+$")
PROPERTY_RE = re.compile(r"^[a-z0-9_]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SELECTABLE_SAFETY = ("ordinary", "block_entity")


class PaletteResolutionError(ValueError):
    """Raised when C5 cannot resolve a role without violating its contract."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PaletteResolutionError(f"{label} must be an object")
    return value


def _require_string(value: object, label: str, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise PaletteResolutionError(f"{label} must be a non-empty string")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise PaletteResolutionError(f"{label} has invalid format")
    return value


def _string_list(
    value: object,
    label: str,
    pattern: re.Pattern[str],
    *,
    allow_empty: bool = True,
) -> list[str]:
    if not isinstance(value, list):
        raise PaletteResolutionError(f"{label} must be an array")
    if not allow_empty and not value:
        raise PaletteResolutionError(f"{label} must not be empty")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_require_string(item, f"{label}[{index}]", pattern))
    if len(result) != len(set(result)):
        raise PaletteResolutionError(f"{label} must contain unique values")
    return result


def _build_spec_policy(build_spec: object) -> tuple[bool, set[str] | None, set[str]]:
    spec = _require_object(build_spec, "build_spec")
    if spec.get("schema_version") != 1:
        raise PaletteResolutionError("build_spec.schema_version must be 1")
    palette = _require_object(spec.get("palette"), "build_spec.palette")
    allow_modded = palette.get("allow_modded")
    if not isinstance(allow_modded, bool):
        raise PaletteResolutionError("build_spec.palette.allow_modded must be boolean")

    allowed_namespaces: set[str] | None = None
    if "allowed_namespaces" in palette:
        allowed_namespaces = set(
            _string_list(
                palette["allowed_namespaces"],
                "build_spec.palette.allowed_namespaces",
                NAMESPACE_RE,
            )
        )

    forbidden_blocks: set[str] = set()
    if "forbidden_blocks" in palette:
        forbidden_blocks = set(
            _string_list(
                palette["forbidden_blocks"],
                "build_spec.palette.forbidden_blocks",
                BLOCK_ID_RE,
            )
        )
    return allow_modded, allowed_namespaces, forbidden_blocks


def _validate_registry(registry: object) -> tuple[dict[str, Any], str]:
    value = _require_object(registry, "registry")
    if value.get("schema_version") != 1:
        raise PaletteResolutionError("registry.schema_version must be 1")
    fingerprint = _require_string(value.get("content_sha256"), "registry.content_sha256", SHA256_RE)
    blocks = value.get("blocks")
    if not isinstance(blocks, list):
        raise PaletteResolutionError("registry.blocks must be an array")
    return value, fingerprint


def _validate_request(request: object) -> list[dict[str, Any]]:
    value = _require_object(request, "request")
    if value.get("schema_version") != 1:
        raise PaletteResolutionError("request.schema_version must be 1")
    roles = value.get("roles")
    if not isinstance(roles, list) or not roles:
        raise PaletteResolutionError("request.roles must be a non-empty array")

    normalized: list[dict[str, Any]] = []
    seen_roles: set[str] = set()
    for index, raw_role in enumerate(roles):
        role = _require_object(raw_role, f"request.roles[{index}]")
        allowed_keys = {
            "role",
            "required_terms",
            "excluded_terms",
            "preferred_block_ids",
            "preferred_namespaces",
            "allowed_safety",
            "required_state_properties",
        }
        unknown = sorted(set(role) - allowed_keys)
        if unknown:
            raise PaletteResolutionError(
                f"request.roles[{index}] contains unsupported fields: {', '.join(unknown)}"
            )

        role_name = _require_string(role.get("role"), f"request.roles[{index}].role", ROLE_RE)
        if role_name in seen_roles:
            raise PaletteResolutionError(f"duplicate role: {role_name}")
        seen_roles.add(role_name)

        required_terms = _string_list(
            role.get("required_terms", []),
            f"request.roles[{index}].required_terms",
            TERM_RE,
        )
        excluded_terms = _string_list(
            role.get("excluded_terms", []),
            f"request.roles[{index}].excluded_terms",
            TERM_RE,
        )
        preferred_block_ids = _string_list(
            role.get("preferred_block_ids", []),
            f"request.roles[{index}].preferred_block_ids",
            BLOCK_ID_RE,
        )
        preferred_namespaces = _string_list(
            role.get("preferred_namespaces", []),
            f"request.roles[{index}].preferred_namespaces",
            NAMESPACE_RE,
        )
        allowed_safety = _string_list(
            role.get("allowed_safety", ["ordinary"]),
            f"request.roles[{index}].allowed_safety",
            re.compile(r"^[a-z0-9_]+$"),
            allow_empty=False,
        )
        invalid_safety = [item for item in allowed_safety if item not in SELECTABLE_SAFETY]
        if invalid_safety:
            raise PaletteResolutionError(
                f"request.roles[{index}].allowed_safety contains non-selectable safety class"
            )
        if not required_terms and not preferred_block_ids:
            raise PaletteResolutionError(
                f"request.roles[{index}] requires required_terms or preferred_block_ids"
            )

        raw_properties = role.get("required_state_properties", {})
        properties = _require_object(
            raw_properties,
            f"request.roles[{index}].required_state_properties",
        )
        normalized_properties: dict[str, str] = {}
        for key, raw_value in properties.items():
            property_name = _require_string(
                key,
                f"request.roles[{index}].required_state_properties key",
                PROPERTY_RE,
            )
            property_value = _require_string(
                raw_value,
                f"request.roles[{index}].required_state_properties.{property_name}",
            )
            normalized_properties[property_name] = property_value

        normalized.append(
            {
                "role": role_name,
                "required_terms": required_terms,
                "excluded_terms": excluded_terms,
                "preferred_block_ids": preferred_block_ids,
                "preferred_namespaces": preferred_namespaces,
                "allowed_safety": allowed_safety,
                "required_state_properties": normalized_properties,
            }
        )
    return normalized


def _runtime_states(
    block: dict[str, Any],
    block_id: str,
    required_properties: dict[str, str],
) -> list[dict[str, object]]:
    raw_states = block.get("states")
    if not isinstance(raw_states, list):
        raise PaletteResolutionError(f"registry block {block_id} has invalid states")

    by_canonical: dict[str, dict[str, object]] = {}
    for index, raw_state in enumerate(raw_states):
        state = _require_object(raw_state, f"registry block {block_id} state[{index}]")
        if state.get("block") != block_id:
            raise PaletteResolutionError(f"registry block {block_id} contains foreign state")
        properties = _require_object(
            state.get("properties"),
            f"registry block {block_id} state[{index}].properties",
        )
        normalized_properties: dict[str, str] = {}
        for key, value in properties.items():
            property_name = _require_string(key, f"registry block {block_id} property", PROPERTY_RE)
            property_value = _require_string(
                value,
                f"registry block {block_id} property {property_name}",
            )
            normalized_properties[property_name] = property_value

        if any(
            normalized_properties.get(key) != value
            for key, value in required_properties.items()
        ):
            continue

        normalized_state: dict[str, object] = {
            "block": block_id,
            "properties": dict(sorted(normalized_properties.items())),
        }
        by_canonical[_canonical_json(normalized_state)] = normalized_state

    return [by_canonical[key] for key in sorted(by_canonical)]


def _candidate(
    raw_block: object,
    *,
    allow_modded: bool,
    allowed_namespaces: set[str] | None,
    forbidden_blocks: set[str],
    role: dict[str, Any],
) -> dict[str, object] | None:
    block = _require_object(raw_block, "registry block")
    if block.get("available") is not True or block.get("authority") != "runtime_registry":
        return None

    block_id = _require_string(block.get("id"), "registry block id", BLOCK_ID_RE)
    namespace, path = block_id.split(":", 1)
    declared_namespace = _require_string(
        block.get("namespace"),
        f"registry block {block_id} namespace",
        NAMESPACE_RE,
    )
    if declared_namespace != namespace:
        raise PaletteResolutionError(f"registry block {block_id} namespace mismatch")

    if not allow_modded and namespace != "minecraft":
        return None
    if allowed_namespaces is not None and namespace not in allowed_namespaces:
        return None
    if block_id in forbidden_blocks:
        return None

    safety = _require_string(block.get("safety"), f"registry block {block_id} safety")
    if safety not in role["allowed_safety"]:
        return None
    if safety not in SELECTABLE_SAFETY:
        return None

    if any(term not in path for term in role["required_terms"]):
        return None
    if any(term in path for term in role["excluded_terms"]):
        return None

    states = _runtime_states(block, block_id, role["required_state_properties"])
    if not states:
        return None

    source_mod = _require_string(block.get("source_mod"), f"registry block {block_id} source_mod")
    return {
        "block": block_id,
        "namespace": namespace,
        "source_mod": source_mod,
        "safety": safety,
        "state_candidates": states,
        "selected_state": states[0] if len(states) == 1 else None,
    }


def _rank(candidate: dict[str, object], role: dict[str, Any]) -> tuple[object, ...]:
    block_id = str(candidate["block"])
    namespace = str(candidate["namespace"])
    preferred_ids: list[str] = role["preferred_block_ids"]
    preferred_namespaces: list[str] = role["preferred_namespaces"]

    if block_id in preferred_ids:
        block_preference = (0, preferred_ids.index(block_id))
    else:
        block_preference = (1, len(preferred_ids))

    if namespace in preferred_namespaces:
        namespace_preference = (0, preferred_namespaces.index(namespace))
    else:
        namespace_preference = (1, len(preferred_namespaces))

    return (*block_preference, *namespace_preference, block_id)


def resolve_palette(
    build_spec: object,
    registry: object,
    request: object,
) -> dict[str, object]:
    """Resolve explicit planner roles against the runtime-backed C4 block registry."""

    allow_modded, allowed_namespaces, forbidden_blocks = _build_spec_policy(build_spec)
    registry_value, fingerprint = _validate_registry(registry)
    roles = _validate_request(request)

    resolved_roles: list[dict[str, object]] = []
    for role in roles:
        candidates: list[dict[str, object]] = []
        for raw_block in registry_value["blocks"]:
            candidate = _candidate(
                raw_block,
                allow_modded=allow_modded,
                allowed_namespaces=allowed_namespaces,
                forbidden_blocks=forbidden_blocks,
                role=role,
            )
            if candidate is not None:
                candidates.append(candidate)

        candidates.sort(key=lambda item: _rank(item, role))
        if not candidates:
            raise PaletteResolutionError(f"no eligible C5 candidate for role {role['role']}")

        selected = candidates[0]
        resolved_roles.append(
            {
                "role": role["role"],
                "selected": selected,
                "alternatives": candidates[1:],
            }
        )

    return {
        "schema_version": 1,
        "registry_fingerprint": fingerprint,
        "build_spec_sha256": _sha256(build_spec),
        "request_sha256": _sha256(request),
        "roles": resolved_roles,
    }
