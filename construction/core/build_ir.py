from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

BLOCK_ID_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
PROPERTY_NAME_RE = re.compile(r"^[a-z0-9_]+$")
PROPERTY_VALUE_RE = re.compile(r"^[a-z0-9_.-]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
AIR_STATES = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}
COORDINATE_SYSTEM = {
    "axes": ["x", "y", "z"],
    "up": "y",
    "origin": "min_corner",
    "unit": "block",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "identity",
    "target",
    "bounds",
    "coordinate_system",
    "palette",
    "blocks",
    "metadata",
}


class BuildIRError(ValueError):
    """Raised when engine output cannot be represented losslessly in canonical C2 IR."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise BuildIRError(f"{label} must be a non-empty string")
    return value


def _normalize_block_state(block_state: Any) -> dict[str, Any]:
    if not isinstance(block_state, dict):
        raise BuildIRError("block_state must be an object")
    if set(block_state) - {"name", "properties"}:
        raise BuildIRError("block_state contains unsupported fields")

    name = block_state.get("name")
    if not isinstance(name, str) or not BLOCK_ID_RE.fullmatch(name):
        raise BuildIRError("block state name must be a namespaced block id")
    if name in AIR_STATES:
        raise BuildIRError("explicit air blocks are not allowed in sparse Build IR")

    raw_properties = block_state.get("properties", {})
    if not isinstance(raw_properties, dict):
        raise BuildIRError("block state properties must be an object")

    properties: dict[str, str] = {}
    for key, value in raw_properties.items():
        if not isinstance(key, str) or not PROPERTY_NAME_RE.fullmatch(key):
            raise BuildIRError(f"invalid block state property name: {key!r}")
        if not isinstance(value, str) or not PROPERTY_VALUE_RE.fullmatch(value):
            raise BuildIRError(f"invalid block state property value for {key}")
        properties[key] = value

    return {"name": name, "properties": dict(sorted(properties.items()))}


def canonical_block_state_string(block_state: dict[str, Any]) -> str:
    normalized = _normalize_block_state(block_state)
    properties = normalized["properties"]
    if not properties:
        return normalized["name"]
    encoded = ",".join(f"{key}={value}" for key, value in properties.items())
    return f"{normalized['name']}[{encoded}]"


def _build_spec_core(build_spec: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
    if not isinstance(build_spec, dict):
        raise BuildIRError("BuildSpec must be an object")
    if build_spec.get("schema_version") != 1:
        raise BuildIRError("BuildSpec schema_version must be 1")

    identity = build_spec.get("identity")
    if not isinstance(identity, dict):
        raise BuildIRError("BuildSpec identity must be an object")
    name = _require_nonempty_string(identity.get("name"), "BuildSpec identity.name")
    seed = identity.get("seed")
    if not _is_int(seed):
        raise BuildIRError("BuildSpec identity.seed must be an integer")
    normalized_identity: dict[str, Any] = {"name": name, "seed": seed}
    if "description" in identity:
        if not isinstance(identity["description"], str):
            raise BuildIRError("BuildSpec identity.description must be a string")
        normalized_identity["description"] = identity["description"]

    target = build_spec.get("target")
    if not isinstance(target, dict):
        raise BuildIRError("BuildSpec target must be an object")
    if target.get("minecraft_version") != "1.21.1":
        raise BuildIRError("BuildSpec target.minecraft_version must be 1.21.1")
    loader = target.get("loader")
    if loader not in {"neoforge", "none"}:
        raise BuildIRError("BuildSpec target.loader must be neoforge or none")
    normalized_target: dict[str, Any] = {
        "minecraft_version": "1.21.1",
        "loader": loader,
    }
    if "modpack_snapshot" in target:
        normalized_target["modpack_snapshot"] = _require_nonempty_string(
            target["modpack_snapshot"], "BuildSpec target.modpack_snapshot"
        )

    geometry = build_spec.get("geometry")
    if not isinstance(geometry, dict) or not isinstance(geometry.get("max_size"), dict):
        raise BuildIRError("BuildSpec geometry.max_size must be an object")
    size: dict[str, int] = {}
    for axis in ("x", "y", "z"):
        value = geometry["max_size"].get(axis)
        if not _is_int(value) or value < 1:
            raise BuildIRError(f"BuildSpec geometry.max_size.{axis} must be a positive integer")
        size[axis] = value

    return normalized_identity, normalized_target, size


def build_spec_fingerprint(build_spec: Any) -> str:
    if not isinstance(build_spec, dict):
        raise BuildIRError("BuildSpec must be an object")
    return _sha256_json(build_spec)


def _hash_payload(build_ir: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(build_ir)
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        metadata.pop("content_sha256", None)
    return payload


def fingerprint_build_ir(build_ir: dict[str, Any]) -> str:
    if not isinstance(build_ir, dict):
        raise BuildIRError("Build IR must be an object")
    return _sha256_json(_hash_payload(build_ir))


def canonicalize_build_ir(
    build_spec: dict[str, Any],
    placements: list[dict[str, Any]],
    *,
    producer: str,
    producer_version: str,
) -> dict[str, Any]:
    identity, target, size = _build_spec_core(build_spec)
    producer = _require_nonempty_string(producer, "producer")
    producer_version = _require_nonempty_string(producer_version, "producer_version")
    if not isinstance(placements, list):
        raise BuildIRError("placements must be a list")

    seen_coordinates: set[tuple[int, int, int]] = set()
    normalized_placements: list[tuple[int, int, int, dict[str, Any]]] = []
    state_by_key: dict[str, dict[str, Any]] = {}

    for index, placement in enumerate(placements):
        if not isinstance(placement, dict):
            raise BuildIRError(f"placement {index} must be an object")
        if set(placement) != {"x", "y", "z", "block_state"}:
            raise BuildIRError(f"placement {index} must contain only x, y, z and block_state")

        coordinates: list[int] = []
        for axis in ("x", "y", "z"):
            value = placement[axis]
            if not _is_int(value):
                raise BuildIRError(f"placement {index} coordinate {axis} must be an integer")
            if value < 0 or value >= size[axis]:
                raise BuildIRError(
                    f"placement {index} coordinate {axis}={value} is out of bounds for size {size[axis]}"
                )
            coordinates.append(value)

        coordinate = (coordinates[0], coordinates[1], coordinates[2])
        if coordinate in seen_coordinates:
            raise BuildIRError(f"duplicate coordinate {coordinate}")
        seen_coordinates.add(coordinate)

        state = _normalize_block_state(placement["block_state"])
        state_key = canonical_block_state_string(state)
        state_by_key[state_key] = state
        normalized_placements.append((coordinate[0], coordinate[1], coordinate[2], state))

    palette_keys = sorted(state_by_key)
    palette = [state_by_key[key] for key in palette_keys]
    palette_index = {key: index for index, key in enumerate(palette_keys)}

    blocks = [
        {
            "x": x,
            "y": y,
            "z": z,
            "palette_index": palette_index[canonical_block_state_string(state)],
        }
        for x, y, z, state in sorted(normalized_placements, key=lambda item: item[:3])
    ]

    build_ir: dict[str, Any] = {
        "schema_version": 1,
        "identity": identity,
        "target": target,
        "bounds": {"size": dict(size)},
        "coordinate_system": deepcopy(COORDINATE_SYSTEM),
        "palette": palette,
        "blocks": blocks,
        "metadata": {
            "build_spec_sha256": build_spec_fingerprint(build_spec),
            "producer": producer,
            "producer_version": producer_version,
        },
    }
    build_ir["metadata"]["content_sha256"] = fingerprint_build_ir(build_ir)
    return build_ir


def validate_build_ir(build_ir: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(build_ir, dict):
        return ["Build IR must be an object"]

    if set(build_ir) != TOP_LEVEL_KEYS:
        errors.append("Build IR top-level fields do not match the C2 contract")
    if build_ir.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    identity = build_ir.get("identity")
    if not isinstance(identity, dict):
        errors.append("identity must be an object")
    else:
        if not isinstance(identity.get("name"), str) or not identity.get("name"):
            errors.append("identity.name must be a non-empty string")
        if not _is_int(identity.get("seed")):
            errors.append("identity.seed must be an integer")

    target = build_ir.get("target")
    if not isinstance(target, dict):
        errors.append("target must be an object")
    else:
        if target.get("minecraft_version") != "1.21.1":
            errors.append("target.minecraft_version must be 1.21.1")
        if target.get("loader") not in {"neoforge", "none"}:
            errors.append("target.loader must be neoforge or none")

    bounds = build_ir.get("bounds")
    size: dict[str, int] | None = None
    if not isinstance(bounds, dict) or not isinstance(bounds.get("size"), dict):
        errors.append("bounds.size must be an object")
    else:
        candidate = bounds["size"]
        if all(_is_int(candidate.get(axis)) and candidate[axis] >= 1 for axis in ("x", "y", "z")):
            size = {axis: candidate[axis] for axis in ("x", "y", "z")}
        else:
            errors.append("bounds.size axes must be positive integers")

    if build_ir.get("coordinate_system") != COORDINATE_SYSTEM:
        errors.append("coordinate_system must be canonical x/y/z with y up and min_corner origin")

    palette = build_ir.get("palette")
    palette_keys: list[str] = []
    if not isinstance(palette, list):
        errors.append("palette must be a list")
    else:
        for index, state in enumerate(palette):
            try:
                palette_keys.append(canonical_block_state_string(state))
            except BuildIRError as exc:
                errors.append(f"palette[{index}]: {exc}")
        if len(palette_keys) != len(set(palette_keys)):
            errors.append("palette contains duplicate block states")
        if palette_keys != sorted(palette_keys):
            errors.append("palette is not in canonical order")

    blocks = build_ir.get("blocks")
    coordinates: list[tuple[int, int, int]] = []
    if not isinstance(blocks, list):
        errors.append("blocks must be a list")
    else:
        for index, block in enumerate(blocks):
            if not isinstance(block, dict) or set(block) != {"x", "y", "z", "palette_index"}:
                errors.append(f"blocks[{index}] has invalid fields")
                continue
            if not all(_is_int(block.get(axis)) for axis in ("x", "y", "z")):
                errors.append(f"blocks[{index}] coordinates must be integers")
                continue
            coordinate = (block["x"], block["y"], block["z"])
            coordinates.append(coordinate)
            if size is not None and any(coordinate[i] < 0 or coordinate[i] >= size[axis] for i, axis in enumerate(("x", "y", "z"))):
                errors.append(f"blocks[{index}] is out of bounds")
            palette_value = block.get("palette_index")
            if not _is_int(palette_value) or palette_value < 0 or not isinstance(palette, list) or palette_value >= len(palette):
                errors.append(f"blocks[{index}].palette_index is invalid")
        if len(coordinates) != len(set(coordinates)):
            errors.append("blocks contain duplicate coordinates")
        if coordinates != sorted(coordinates):
            errors.append("blocks are not in canonical coordinate order")

    metadata = build_ir.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("metadata must be an object")
    else:
        if set(metadata) != {"build_spec_sha256", "content_sha256", "producer", "producer_version"}:
            errors.append("metadata fields do not match the C2 contract")
        build_spec_sha = metadata.get("build_spec_sha256")
        if not isinstance(build_spec_sha, str) or not SHA256_RE.fullmatch(build_spec_sha):
            errors.append("metadata.build_spec_sha256 is invalid")
        content_sha = metadata.get("content_sha256")
        if not isinstance(content_sha, str) or not SHA256_RE.fullmatch(content_sha):
            errors.append("metadata.content_sha256 is invalid")
        else:
            try:
                expected = fingerprint_build_ir(build_ir)
            except BuildIRError as exc:
                errors.append(str(exc))
            else:
                if content_sha != expected:
                    errors.append("metadata.content_sha256 does not match canonical content")
        if not isinstance(metadata.get("producer"), str) or not metadata.get("producer"):
            errors.append("metadata.producer must be a non-empty string")
        if not isinstance(metadata.get("producer_version"), str) or not metadata.get("producer_version"):
            errors.append("metadata.producer_version must be a non-empty string")

    return errors
