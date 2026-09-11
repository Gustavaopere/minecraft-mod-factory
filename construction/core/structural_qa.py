from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
from collections import deque
from pathlib import Path
from typing import Any

CHECK_ORDER = [
    "bounds",
    "runtime_state_validity",
    "head_clearance",
    "walkable_surface_graph",
    "circulation_components",
    "vertical_step_connectivity",
    "enclosure",
    "floor_continuity_semantic",
    "unsupported_placement",
]
CHECK_STATUSES = {"PASS", "FAIL", "DEFERRED", "NOT_APPLICABLE"}
SEVERITIES = {"error", "warning", "info"}
OVERALL_STATUSES = {"PASS", "FAIL", "DEFERRED"}
RESOURCE_LOCATION_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
NAMESPACE_RE = re.compile(r"^[a-z0-9_.-]+$")
PROPERTY_NAME_RE = re.compile(r"^[a-z0-9_]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FINDING_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
SAFETY_CLASSES = {
    "ordinary",
    "stateful",
    "connected_or_multipart",
    "material_bearing",
    "block_entity",
    "dynamic_renderer",
    "functional_machine",
    "unknown",
}


class StructuralQAError(ValueError):
    """Raised when C7 cannot safely validate authoritative structural QA inputs."""


def _c2_module():
    path = Path(__file__).with_name("build_ir.py")
    spec = importlib.util.spec_from_file_location("construction_c2_build_ir_for_c7", path)
    if spec is None or spec.loader is None:
        raise StructuralQAError(f"cannot load C2 Build IR authority: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StructuralQAError(f"{label} must be an object")
    return value


def _require_keys(
    value: dict[str, Any],
    *,
    allowed: set[str],
    required: set[str],
    label: str,
) -> None:
    extras = set(value) - allowed
    missing = required - set(value)
    if extras:
        raise StructuralQAError(f"{label} contains unsupported fields: {', '.join(sorted(extras))}")
    if missing:
        raise StructuralQAError(f"{label} is missing required fields: {', '.join(sorted(missing))}")


def _require_string(value: Any, label: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        qualifier = "non-empty " if nonempty else ""
        raise StructuralQAError(f"{label} must be a {qualifier}string")
    return value


def _validate_build_spec(build_spec: Any) -> dict[str, Any]:
    spec = _require_object(build_spec, "BuildSpec")
    _require_keys(
        spec,
        allowed={"schema_version", "identity", "target", "geometry", "palette", "qa", "outputs"},
        required={"schema_version", "identity", "target", "geometry", "palette", "outputs"},
        label="BuildSpec",
    )
    if spec.get("schema_version") != 1:
        raise StructuralQAError("BuildSpec schema_version must be 1")

    identity = _require_object(spec["identity"], "BuildSpec identity")
    _require_keys(
        identity,
        allowed={"name", "seed", "description"},
        required={"name", "seed"},
        label="BuildSpec identity",
    )
    _require_string(identity["name"], "BuildSpec identity.name")
    if not _is_int(identity["seed"]):
        raise StructuralQAError("BuildSpec identity.seed must be an integer")
    if "description" in identity and not isinstance(identity["description"], str):
        raise StructuralQAError("BuildSpec identity.description must be a string")

    target = _require_object(spec["target"], "BuildSpec target")
    _require_keys(
        target,
        allowed={"minecraft_version", "loader", "modpack_snapshot"},
        required={"minecraft_version", "loader"},
        label="BuildSpec target",
    )
    if target["minecraft_version"] != "1.21.1":
        raise StructuralQAError("BuildSpec target.minecraft_version must be 1.21.1")
    if target["loader"] not in {"neoforge", "none"}:
        raise StructuralQAError("BuildSpec target.loader must be neoforge or none")
    if "modpack_snapshot" in target:
        _require_string(target["modpack_snapshot"], "BuildSpec target.modpack_snapshot")

    geometry = _require_object(spec["geometry"], "BuildSpec geometry")
    _require_keys(
        geometry,
        allowed={"max_size", "terrain_policy", "architectural_brief", "required_spaces"},
        required={"max_size"},
        label="BuildSpec geometry",
    )
    max_size = _require_object(geometry["max_size"], "BuildSpec geometry.max_size")
    _require_keys(
        max_size,
        allowed={"x", "y", "z"},
        required={"x", "y", "z"},
        label="BuildSpec geometry.max_size",
    )
    for axis in ("x", "y", "z"):
        if not _is_int(max_size[axis]) or max_size[axis] < 1:
            raise StructuralQAError(f"BuildSpec geometry.max_size.{axis} must be a positive integer")
    if "terrain_policy" in geometry and geometry["terrain_policy"] not in {"flat", "preserve", "adapt", "unspecified"}:
        raise StructuralQAError("BuildSpec geometry.terrain_policy is unsupported")
    if "architectural_brief" in geometry and not isinstance(geometry["architectural_brief"], str):
        raise StructuralQAError("BuildSpec geometry.architectural_brief must be a string")
    if "required_spaces" in geometry:
        spaces = geometry["required_spaces"]
        if not isinstance(spaces, list) or any(not isinstance(item, str) or not item for item in spaces):
            raise StructuralQAError("BuildSpec geometry.required_spaces must contain non-empty strings")
        if len(spaces) != len(set(spaces)):
            raise StructuralQAError("BuildSpec geometry.required_spaces must be unique")

    palette = _require_object(spec["palette"], "BuildSpec palette")
    _require_keys(
        palette,
        allowed={"allow_modded", "allowed_namespaces", "forbidden_blocks"},
        required={"allow_modded"},
        label="BuildSpec palette",
    )
    if not isinstance(palette["allow_modded"], bool):
        raise StructuralQAError("BuildSpec palette.allow_modded must be a boolean")
    if "allowed_namespaces" in palette:
        namespaces = palette["allowed_namespaces"]
        if not isinstance(namespaces, list) or any(
            not isinstance(item, str) or NAMESPACE_RE.fullmatch(item) is None for item in namespaces
        ):
            raise StructuralQAError("BuildSpec palette.allowed_namespaces contains an invalid namespace")
        if len(namespaces) != len(set(namespaces)):
            raise StructuralQAError("BuildSpec palette.allowed_namespaces must be unique")
    if "forbidden_blocks" in palette:
        forbidden = palette["forbidden_blocks"]
        if not isinstance(forbidden, list) or any(
            not isinstance(item, str) or RESOURCE_LOCATION_RE.fullmatch(item) is None for item in forbidden
        ):
            raise StructuralQAError("BuildSpec palette.forbidden_blocks contains an invalid block id")
        if len(forbidden) != len(set(forbidden)):
            raise StructuralQAError("BuildSpec palette.forbidden_blocks must be unique")

    qa = spec.get("qa", {})
    qa = _require_object(qa, "BuildSpec qa")
    _require_keys(
        qa,
        allowed={"require_walkability", "require_complete_interior", "require_determinism"},
        required=set(),
        label="BuildSpec qa",
    )
    for field in ("require_walkability", "require_complete_interior", "require_determinism"):
        if field in qa and not isinstance(qa[field], bool):
            raise StructuralQAError(f"BuildSpec qa.{field} must be a boolean")

    outputs = _require_object(spec["outputs"], "BuildSpec outputs")
    _require_keys(outputs, allowed={"formats"}, required={"formats"}, label="BuildSpec outputs")
    formats = outputs["formats"]
    allowed_formats = {"sponge_v3", "litematic", "structure_nbt"}
    if not isinstance(formats, list) or not formats or any(item not in allowed_formats for item in formats):
        raise StructuralQAError("BuildSpec outputs.formats must contain supported output formats")
    if len(formats) != len(set(formats)):
        raise StructuralQAError("BuildSpec outputs.formats must be unique")
    return spec


def _validate_registry(registry: Any) -> dict[str, Any]:
    document = _require_object(registry, "C4 registry")
    _require_keys(
        document,
        allowed={"schema_version", "physical", "runtime", "static_index", "blocks", "content_sha256"},
        required={"schema_version", "physical", "runtime", "static_index", "blocks", "content_sha256"},
        label="C4 registry",
    )
    if document["schema_version"] != 1:
        raise StructuralQAError("C4 registry schema_version must be 1")
    for field in ("physical", "runtime", "static_index"):
        _require_object(document[field], f"C4 registry {field}")
    claimed = document["content_sha256"]
    if not isinstance(claimed, str) or SHA256_RE.fullmatch(claimed) is None:
        raise StructuralQAError("C4 registry content_sha256 is invalid")
    hash_payload = copy.deepcopy(document)
    hash_payload.pop("content_sha256", None)
    expected = hashlib.sha256(_canonical_json_bytes(hash_payload)).hexdigest()
    if claimed != expected:
        raise StructuralQAError("C4 registry content_sha256 does not match canonical content")

    blocks = document["blocks"]
    if not isinstance(blocks, list):
        raise StructuralQAError("C4 registry blocks must be an array")
    seen: set[str] = set()
    for index, raw_block in enumerate(blocks):
        block = _require_object(raw_block, f"C4 registry blocks[{index}]")
        _require_keys(
            block,
            allowed={"id", "available", "authority", "static_discovered", "states", "safety"},
            required={"id", "available", "authority", "static_discovered", "states", "safety"},
            label=f"C4 registry blocks[{index}]",
        )
        block_id = block["id"]
        if not isinstance(block_id, str) or RESOURCE_LOCATION_RE.fullmatch(block_id) is None:
            raise StructuralQAError(f"C4 registry blocks[{index}].id is invalid")
        if block_id in seen:
            raise StructuralQAError(f"C4 registry contains duplicate block id: {block_id}")
        seen.add(block_id)
        if not isinstance(block["available"], bool) or not isinstance(block["static_discovered"], bool):
            raise StructuralQAError(f"C4 registry blocks[{index}] availability fields must be booleans")
        if block["authority"] not in {"runtime_confirmed", "static_only_unconfirmed"}:
            raise StructuralQAError(f"C4 registry blocks[{index}].authority is invalid")
        if block["safety"] not in SAFETY_CLASSES:
            raise StructuralQAError(f"C4 registry blocks[{index}].safety is invalid")
        states = block["states"]
        if not isinstance(states, list):
            raise StructuralQAError(f"C4 registry blocks[{index}].states must be an array")
        seen_states: set[bytes] = set()
        for state_index, state in enumerate(states):
            if not isinstance(state, dict):
                raise StructuralQAError(f"C4 registry blocks[{index}].states[{state_index}] must be an object")
            canonical_state: dict[str, str] = {}
            for key, value in state.items():
                if not isinstance(key, str) or PROPERTY_NAME_RE.fullmatch(key) is None:
                    raise StructuralQAError(f"C4 registry blocks[{index}] contains an invalid state property name")
                if not isinstance(value, str) or not value:
                    raise StructuralQAError(f"C4 registry blocks[{index}] state values must be non-empty strings")
                canonical_state[key] = value
            state_bytes = _canonical_json_bytes(canonical_state)
            if state_bytes in seen_states:
                raise StructuralQAError(f"C4 registry blocks[{index}] contains duplicate states")
            seen_states.add(state_bytes)
    return document


def _position_key(position: tuple[int, int, int]) -> tuple[int, int, int]:
    x, y, z = position
    return (y, z, x)


def _finding(code: str, message: str, *, subject: str | None = None, position: tuple[int, int, int] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"code": code, "message": message}
    if subject is not None:
        result["subject"] = subject
    if position is not None:
        result["position"] = [position[0], position[1], position[2]]
    return result


def _check(
    check_id: str,
    *,
    required: bool,
    status: str,
    summary: str,
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    severity = "error" if status == "FAIL" else "warning" if status == "DEFERRED" else "info"
    return {
        "id": check_id,
        "required": required,
        "status": status,
        "severity": severity,
        "summary": summary,
        "findings": list(findings or []),
    }


def _derive_overall(checks: list[dict[str, Any]]) -> str:
    required = [item for item in checks if item["required"]]
    if any(item["status"] == "FAIL" for item in required):
        return "FAIL"
    if any(item["status"] == "DEFERRED" for item in required):
        return "DEFERRED"
    return "PASS"


def _occupancy(build_ir: dict[str, Any]) -> tuple[set[tuple[int, int, int]], dict[str, int]]:
    size = build_ir["bounds"]["size"]
    occupied = {(block["x"], block["y"], block["z"]) for block in build_ir["blocks"]}
    return occupied, {axis: size[axis] for axis in ("x", "y", "z")}


def _walkability(
    occupied: set[tuple[int, int, int]],
    size: dict[str, int],
) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]]]:
    supported: list[tuple[int, int, int]] = []
    clear: list[tuple[int, int, int]] = []
    for y in range(1, size["y"]):
        for z in range(size["z"]):
            for x in range(size["x"]):
                position = (x, y, z)
                if position in occupied or (x, y - 1, z) not in occupied:
                    continue
                supported.append(position)
                if y + 1 < size["y"] and (x, y + 1, z) not in occupied:
                    clear.append(position)
    supported.sort(key=_position_key)
    clear.sort(key=_position_key)
    return supported, clear


def _graph(
    nodes: list[tuple[int, int, int]],
) -> tuple[int, int, list[list[tuple[int, int, int]]], dict[tuple[int, int, int], set[tuple[int, int, int]]]]:
    node_set = set(nodes)
    adjacency: dict[tuple[int, int, int], set[tuple[int, int, int]]] = {node: set() for node in nodes}
    horizontal_edges: set[tuple[tuple[int, int, int], tuple[int, int, int]]] = set()
    vertical_edges: set[tuple[tuple[int, int, int], tuple[int, int, int]]] = set()

    def add_edge(a: tuple[int, int, int], b: tuple[int, int, int], *, vertical: bool) -> None:
        ordered = tuple(sorted((a, b), key=_position_key))
        if vertical:
            vertical_edges.add(ordered)
        else:
            horizontal_edges.add(ordered)
        adjacency[a].add(b)
        adjacency[b].add(a)

    for x, y, z in nodes:
        current = (x, y, z)
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            same = (x + dx, y, z + dz)
            if same in node_set:
                add_edge(current, same, vertical=False)
            for dy in (-1, 1):
                step = (x + dx, y + dy, z + dz)
                if step in node_set:
                    add_edge(current, step, vertical=True)

    components: list[list[tuple[int, int, int]]] = []
    remaining = set(nodes)
    while remaining:
        start = min(remaining, key=_position_key)
        queue: deque[tuple[int, int, int]] = deque([start])
        remaining.remove(start)
        component: list[tuple[int, int, int]] = []
        while queue:
            node = queue.popleft()
            component.append(node)
            for neighbor in sorted(adjacency[node], key=_position_key):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        component.sort(key=_position_key)
        components.append(component)
    components.sort(key=lambda component: (-len(component), [_position_key(item) for item in component]))
    return len(horizontal_edges), len(vertical_edges), components, adjacency


def _runtime_state_check(
    build_spec: dict[str, Any],
    build_ir: dict[str, Any],
    registry: dict[str, Any] | None,
) -> dict[str, Any]:
    target_requires = build_spec["target"]["loader"] == "neoforge" or build_spec["palette"]["allow_modded"]
    required = target_requires or registry is not None
    if registry is None:
        if required:
            return _check(
                "runtime_state_validity",
                required=True,
                status="DEFERRED",
                summary="Runtime state validity requires a C4 runtime-confirmed registry snapshot.",
                findings=[_finding("registry_missing", "No C4 registry evidence was supplied for this invocation.")],
            )
        return _check(
            "runtime_state_validity",
            required=False,
            status="NOT_APPLICABLE",
            summary="Runtime state validation is not required for this vanilla/no-loader invocation.",
        )

    by_id = {block["id"]: block for block in registry["blocks"]}
    findings: list[dict[str, Any]] = []
    for state in build_ir["palette"]:
        block_id = state["name"]
        properties = state["properties"]
        block = by_id.get(block_id)
        if block is None:
            findings.append(_finding("runtime_block_missing", "Block id is absent from the supplied C4 registry.", subject=block_id))
            continue
        if not block["available"]:
            findings.append(_finding("runtime_block_unavailable", "Block is not runtime-available in the supplied C4 registry.", subject=block_id))
        if block["authority"] != "runtime_confirmed":
            findings.append(_finding("runtime_authority_unconfirmed", "Block does not have runtime_confirmed authority.", subject=block_id))
        if properties not in block["states"]:
            findings.append(_finding("runtime_state_missing", "Exact block-state properties are absent from the supplied C4 registry.", subject=block_id))
    findings.sort(key=lambda item: (item.get("subject", ""), item["code"], item["message"]))
    if findings:
        return _check(
            "runtime_state_validity",
            required=required,
            status="FAIL",
            summary="One or more Build IR states lack exact runtime-confirmed C4 evidence.",
            findings=findings,
        )
    return _check(
        "runtime_state_validity",
        required=required,
        status="PASS",
        summary="All Build IR states have exact runtime-confirmed C4 evidence.",
    )


def validate_structural_qa_report(report: dict) -> None:
    value = _require_object(report, "C7 report")
    expected_top = {
        "schema_version",
        "build_spec_sha256",
        "build_ir_sha256",
        "registry_fingerprint",
        "overall_status",
        "checks",
        "metrics",
    }
    _require_keys(value, allowed=expected_top, required=expected_top, label="C7 report")
    if value["schema_version"] != 1:
        raise StructuralQAError("C7 report schema_version must be 1")
    for field in ("build_spec_sha256", "build_ir_sha256"):
        if not isinstance(value[field], str) or SHA256_RE.fullmatch(value[field]) is None:
            raise StructuralQAError(f"C7 report {field} is invalid")
    registry_fingerprint = value["registry_fingerprint"]
    if registry_fingerprint is not None and (
        not isinstance(registry_fingerprint, str) or SHA256_RE.fullmatch(registry_fingerprint) is None
    ):
        raise StructuralQAError("C7 report registry_fingerprint is invalid")
    if value["overall_status"] not in OVERALL_STATUSES:
        raise StructuralQAError("C7 report overall_status is invalid")

    checks = value["checks"]
    if not isinstance(checks, list) or len(checks) != len(CHECK_ORDER):
        raise StructuralQAError("C7 report checks must contain exactly the canonical check set")
    if [item.get("id") if isinstance(item, dict) else None for item in checks] != CHECK_ORDER:
        raise StructuralQAError("C7 report checks are not in canonical order")
    for index, raw_check in enumerate(checks):
        item = _require_object(raw_check, f"C7 report checks[{index}]")
        check_keys = {"id", "required", "status", "severity", "summary", "findings"}
        _require_keys(item, allowed=check_keys, required=check_keys, label=f"C7 report checks[{index}]")
        if not isinstance(item["required"], bool):
            raise StructuralQAError(f"C7 report checks[{index}].required must be boolean")
        if item["status"] not in CHECK_STATUSES:
            raise StructuralQAError(f"C7 report checks[{index}].status is invalid")
        if item["severity"] not in SEVERITIES:
            raise StructuralQAError(f"C7 report checks[{index}].severity is invalid")
        if not isinstance(item["summary"], str) or not item["summary"]:
            raise StructuralQAError(f"C7 report checks[{index}].summary must be non-empty")
        if item["required"] and item["status"] == "NOT_APPLICABLE":
            raise StructuralQAError(f"C7 report required check {item['id']} cannot be NOT_APPLICABLE")
        findings = item["findings"]
        if not isinstance(findings, list):
            raise StructuralQAError(f"C7 report checks[{index}].findings must be an array")
        for finding_index, raw_finding in enumerate(findings):
            finding = _require_object(raw_finding, f"C7 report checks[{index}].findings[{finding_index}]")
            _require_keys(
                finding,
                allowed={"code", "message", "subject", "position"},
                required={"code", "message"},
                label=f"C7 report checks[{index}].findings[{finding_index}]",
            )
            if not isinstance(finding["code"], str) or FINDING_CODE_RE.fullmatch(finding["code"]) is None:
                raise StructuralQAError("C7 report finding code is invalid")
            if not isinstance(finding["message"], str) or not finding["message"]:
                raise StructuralQAError("C7 report finding message must be non-empty")
            if "subject" in finding and (not isinstance(finding["subject"], str) or not finding["subject"]):
                raise StructuralQAError("C7 report finding subject must be non-empty")
            if "position" in finding:
                position = finding["position"]
                if not isinstance(position, list) or len(position) != 3 or any(not _is_int(axis) for axis in position):
                    raise StructuralQAError("C7 report finding position must contain three integers")

    metrics = _require_object(value["metrics"], "C7 report metrics")
    metric_keys = {
        "occupied_block_count",
        "supported_foot_cell_count",
        "clear_foot_cell_count",
        "blocked_supported_cell_count",
        "walkable_node_count",
        "horizontal_edge_count",
        "vertical_step_edge_count",
        "walkable_component_count",
        "component_sizes",
        "walkable_y_levels",
    }
    _require_keys(metrics, allowed=metric_keys, required=metric_keys, label="C7 report metrics")
    count_fields = metric_keys - {"component_sizes", "walkable_y_levels"}
    for field in count_fields:
        if not _is_int(metrics[field]) or metrics[field] < 0:
            raise StructuralQAError(f"C7 report metrics.{field} must be a non-negative integer")
    component_sizes = metrics["component_sizes"]
    if not isinstance(component_sizes, list) or any(not _is_int(item) or item < 1 for item in component_sizes):
        raise StructuralQAError("C7 report metrics.component_sizes is invalid")
    if component_sizes != sorted(component_sizes, reverse=True):
        raise StructuralQAError("C7 report metrics.component_sizes must be descending")
    levels = metrics["walkable_y_levels"]
    if not isinstance(levels, list) or any(not _is_int(item) for item in levels) or levels != sorted(set(levels)):
        raise StructuralQAError("C7 report metrics.walkable_y_levels must be sorted unique integers")
    if metrics["supported_foot_cell_count"] != metrics["clear_foot_cell_count"] + metrics["blocked_supported_cell_count"]:
        raise StructuralQAError("C7 report supported-foot metrics are inconsistent")
    if metrics["walkable_node_count"] != metrics["clear_foot_cell_count"]:
        raise StructuralQAError("C7 report walkable node count must equal clear foot-cell count")
    if metrics["walkable_component_count"] != len(component_sizes):
        raise StructuralQAError("C7 report component count is inconsistent")
    if sum(component_sizes) != metrics["walkable_node_count"]:
        raise StructuralQAError("C7 report component sizes do not cover all walkable nodes")
    expected_overall = _derive_overall(checks)
    if value["overall_status"] != expected_overall:
        raise StructuralQAError("C7 report overall_status does not match required check statuses")


def run_structural_qa(build_spec: dict, build_ir: dict, registry: dict | None = None) -> dict:
    spec = _validate_build_spec(build_spec)
    c2 = _c2_module()
    try:
        c2_errors = c2.validate_build_ir(build_ir)
    except Exception as exc:  # C2 remains authority; C7 normalizes the failure boundary.
        raise StructuralQAError(f"C2 Build IR validation failed: {exc}") from exc
    if c2_errors:
        raise StructuralQAError("invalid C2 Build IR: " + "; ".join(c2_errors))
    try:
        build_spec_sha = c2.build_spec_fingerprint(spec)
        build_ir_sha = c2.fingerprint_build_ir(build_ir)
    except Exception as exc:
        raise StructuralQAError(f"cannot fingerprint C2 authority: {exc}") from exc
    if build_ir["metadata"]["build_spec_sha256"] != build_spec_sha:
        raise StructuralQAError("Build IR does not reference the exact BuildSpec fingerprint")

    registry_doc = _validate_registry(registry) if registry is not None else None
    occupied, size = _occupancy(build_ir)
    supported, clear = _walkability(occupied, size)
    clear_set = set(clear)
    blocked = [position for position in supported if position not in clear_set]
    horizontal_edges, vertical_edges, components, _adjacency = _graph(clear)
    levels = sorted({position[1] for position in clear})

    walkability_required = bool(spec.get("qa", {}).get("require_walkability", False))
    complete_interior_required = bool(spec.get("qa", {}).get("require_complete_interior", False))

    checks: list[dict[str, Any]] = []
    checks.append(
        _check(
            "bounds",
            required=True,
            status="PASS",
            summary="Canonical C2 Build IR spatial invariants are valid.",
        )
    )
    checks.append(_runtime_state_check(spec, build_ir, registry_doc))

    head_findings = [
        _finding(
            "blocked_supported_cell",
            "Supported foot cell lacks a second in-bounds geometric air cell above it.",
            position=position,
        )
        for position in blocked
    ]
    if walkability_required:
        head_status = "PASS" if clear else "FAIL"
        head_summary = (
            "At least one conservative two-block-high walkable position exists."
            if clear
            else "No conservative two-block-high walkable position exists."
        )
    else:
        head_status = "NOT_APPLICABLE"
        head_summary = "Head-clearance metrics are informational because walkability is not required."
    checks.append(
        _check(
            "head_clearance",
            required=walkability_required,
            status=head_status,
            summary=head_summary,
            findings=head_findings,
        )
    )

    if walkability_required:
        graph_status = "PASS" if clear else "FAIL"
        graph_summary = (
            "Conservative walkable graph contains at least one node."
            if clear
            else "Conservative walkable graph contains no nodes."
        )
    else:
        graph_status = "NOT_APPLICABLE"
        graph_summary = "Walkable graph metrics are informational because walkability is not required."
    checks.append(
        _check(
            "walkable_surface_graph",
            required=walkability_required,
            status=graph_status,
            summary=graph_summary,
        )
    )

    circulation_findings: list[dict[str, Any]] = []
    if len(components) > 1:
        for index, component in enumerate(components):
            circulation_findings.append(
                _finding(
                    "walkable_component",
                    f"Conservative walkable component {index + 1} contains {len(component)} node(s).",
                    position=component[0],
                )
            )
    if not walkability_required:
        circulation_status = "NOT_APPLICABLE"
        circulation_summary = "Circulation connectivity is not gating because walkability is not required."
    elif not clear:
        circulation_status = "FAIL"
        circulation_summary = "Circulation cannot be established because the walkable graph has no nodes."
    elif len(components) == 1:
        circulation_status = "PASS"
        circulation_summary = "All conservative walkable nodes form one connected component."
    else:
        circulation_status = "DEFERRED"
        circulation_summary = "Multiple walkable components exist, but current intent data cannot prove which components require circulation."
    checks.append(
        _check(
            "circulation_components",
            required=walkability_required,
            status=circulation_status,
            summary=circulation_summary,
            findings=circulation_findings,
        )
    )

    vertical_required = walkability_required and len(levels) > 1
    if len(levels) <= 1:
        vertical_status = "NOT_APPLICABLE"
        vertical_summary = "Walkable graph occupies at most one vertical level."
    elif vertical_edges > 0:
        vertical_status = "PASS"
        vertical_summary = "Conservative one-block vertical-step connectivity is present."
    else:
        vertical_status = "DEFERRED"
        vertical_summary = "Multiple walkable levels exist without a conservative step, but authoritative traversal semantics are unavailable."
    checks.append(
        _check(
            "vertical_step_connectivity",
            required=vertical_required,
            status=vertical_status,
            summary=vertical_summary,
        )
    )

    checks.append(
        _check(
            "enclosure",
            required=complete_interior_required,
            status="DEFERRED",
            summary="Enclosure semantics require authoritative interior/opening mappings not present in BuildSpec v1.",
            findings=[_finding("semantic_authority_missing", "C7 cannot distinguish intentional openings from incomplete enclosure.")],
        )
    )
    checks.append(
        _check(
            "floor_continuity_semantic",
            required=False,
            status="DEFERRED",
            summary="Semantic floor continuity requires mapped intended floor regions not present in BuildSpec v1.",
            findings=[_finding("semantic_authority_missing", "Named spaces are not mapped to voxel floor regions.")],
        )
    )
    checks.append(
        _check(
            "unsupported_placement",
            required=False,
            status="DEFERRED",
            summary="Provider-aware support validation requires support/gravity/attachment metadata not present in C4 evidence.",
            findings=[_finding("provider_support_authority_missing", "C7 does not infer support physics from block ids or safety classes.")],
        )
    )

    metrics = {
        "occupied_block_count": len(occupied),
        "supported_foot_cell_count": len(supported),
        "clear_foot_cell_count": len(clear),
        "blocked_supported_cell_count": len(blocked),
        "walkable_node_count": len(clear),
        "horizontal_edge_count": horizontal_edges,
        "vertical_step_edge_count": vertical_edges,
        "walkable_component_count": len(components),
        "component_sizes": sorted((len(component) for component in components), reverse=True),
        "walkable_y_levels": levels,
    }
    report = {
        "schema_version": 1,
        "build_spec_sha256": build_spec_sha,
        "build_ir_sha256": build_ir_sha,
        "registry_fingerprint": registry_doc["content_sha256"] if registry_doc is not None else None,
        "overall_status": _derive_overall(checks),
        "checks": checks,
        "metrics": metrics,
    }
    validate_structural_qa_report(report)
    return report
