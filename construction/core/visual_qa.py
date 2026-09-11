from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

RENDERER_VERSION = "c8-svg-v1"
VIEW_IDS = ("front", "back", "left", "right", "top", "isometric", "layers")
ORTHO_IDS = ("front", "back", "left", "right", "top")
FACADE_IDS = ("front", "back", "left", "right")
SUBJECTIVE_CHECKS = (
    "silhouette_readability",
    "proportion",
    "material_hierarchy",
    "repetition",
    "facade_readability",
    "interior_density",
)
CHECK_ORDER = (
    "canonical_preview_integrity",
    *SUBJECTIVE_CHECKS,
    "runtime_visual_fidelity",
)
ALLOWED_EVIDENCE_VIEWS = {
    "silhouette_readability": ("front", "back", "left", "right", "top", "isometric"),
    "proportion": ("front", "back", "left", "right", "top", "isometric"),
    "material_hierarchy": VIEW_IDS,
    "repetition": ("front", "back", "left", "right", "top", "isometric"),
    "facade_readability": ("front", "back", "left", "right", "isometric"),
    "interior_density": ("top", "isometric", "layers"),
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ROLE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
FINDING_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
REPORT_KEYS = {
    "schema_version",
    "build_spec_sha256",
    "build_ir_sha256",
    "structural_report_sha256",
    "palette_resolution_sha256",
    "review_evidence_sha256",
    "renderer_version",
    "views",
    "metrics",
    "checks",
    "overall_status",
    "content_sha256",
}


class VisualQAError(ValueError):
    """Raised when C8 inputs or evidence violate the Visual QA contract."""


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise VisualQAError(f"cannot load authority module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _c2_module():
    return _load_module(Path(__file__).resolve().parent / "build_ir.py", "construction_c2_for_c8")


def _c7_module():
    return _load_module(Path(__file__).resolve().parent / "structural_qa.py", "construction_c7_for_c8")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VisualQAError(f"{label} must be an object")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise VisualQAError(f"{label} fields do not match the C8 contract")


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise VisualQAError(f"{label} must be a non-empty string")
    return value


def _require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise VisualQAError(f"{label} must be a lowercase SHA-256 string")
    return value


def _fraction(numerator: int, denominator: int) -> dict[str, int]:
    if denominator <= 0:
        raise VisualQAError("fraction denominator must be positive")
    if numerator == 0:
        return {"numerator": 0, "denominator": 1}
    divisor = math.gcd(abs(numerator), abs(denominator))
    return {"numerator": numerator // divisor, "denominator": denominator // divisor}


def _validate_build_inputs(build_spec: object, build_ir: object):
    spec = _require_object(build_spec, "build_spec")
    if spec.get("schema_version") != 1:
        raise VisualQAError("build_spec schema_version must be 1")
    geometry = _require_object(spec.get("geometry"), "build_spec.geometry")
    max_size = _require_object(geometry.get("max_size"), "build_spec.geometry.max_size")
    for axis in ("x", "y", "z"):
        if not _is_int(max_size.get(axis)) or max_size[axis] < 1:
            raise VisualQAError(f"build_spec.geometry.max_size.{axis} must be a positive integer")
    if "architectural_brief" in geometry and not isinstance(geometry["architectural_brief"], str):
        raise VisualQAError("build_spec.geometry.architectural_brief must be a string")
    if "required_spaces" in geometry:
        spaces = geometry["required_spaces"]
        if not isinstance(spaces, list) or any(not isinstance(item, str) or not item for item in spaces):
            raise VisualQAError("build_spec.geometry.required_spaces must contain non-empty strings")
    qa = spec.get("qa", {})
    if not isinstance(qa, dict):
        raise VisualQAError("build_spec.qa must be an object")
    if "require_determinism" in qa and not isinstance(qa["require_determinism"], bool):
        raise VisualQAError("build_spec.qa.require_determinism must be boolean")

    c2 = _c2_module()
    try:
        errors = c2.validate_build_ir(build_ir)
    except Exception as exc:
        raise VisualQAError(f"C2 Build IR validation failed: {exc}") from exc
    if errors:
        raise VisualQAError("invalid C2 Build IR: " + "; ".join(errors))
    assert isinstance(build_ir, dict)
    try:
        build_spec_sha = c2.build_spec_fingerprint(spec)
        build_ir_sha = c2.fingerprint_build_ir(build_ir)
    except Exception as exc:
        raise VisualQAError(f"cannot fingerprint C2 authority: {exc}") from exc
    if build_ir["metadata"]["build_spec_sha256"] != build_spec_sha:
        raise VisualQAError("Build IR does not reference the exact BuildSpec fingerprint")
    ir_size = build_ir["bounds"]["size"]
    if any(ir_size[axis] != max_size[axis] for axis in ("x", "y", "z")):
        raise VisualQAError("Build IR bounds do not match BuildSpec max_size")
    return spec, build_ir, c2, build_spec_sha, build_ir_sha


def _validate_structural_report(
    structural_report: object | None,
    *,
    build_spec_sha: str,
    build_ir_sha: str,
) -> str | None:
    if structural_report is None:
        return None
    report = _require_object(structural_report, "structural_report")
    c7 = _c7_module()
    try:
        c7.validate_structural_qa_report(report)
    except Exception as exc:
        raise VisualQAError(f"invalid C7 structural report: {exc}") from exc
    if report.get("build_spec_sha256") != build_spec_sha:
        raise VisualQAError("C7 structural report BuildSpec fingerprint does not match")
    if report.get("build_ir_sha256") != build_ir_sha:
        raise VisualQAError("C7 structural report Build IR fingerprint does not match")
    return _sha256_json(report)


def _validate_palette_resolution(
    palette_resolution: object | None,
    *,
    build_spec_sha: str,
    c2,
) -> tuple[str | None, dict[str, list[str]]]:
    if palette_resolution is None:
        return None, {}
    value = _require_object(palette_resolution, "palette_resolution")
    if value.get("schema_version") != 1:
        raise VisualQAError("palette_resolution schema_version must be 1")
    if value.get("build_spec_sha256") != build_spec_sha:
        raise VisualQAError("C5 palette resolution BuildSpec fingerprint does not match")
    roles = value.get("roles")
    if not isinstance(roles, list):
        raise VisualQAError("palette_resolution.roles must be an array")

    labels: dict[str, list[str]] = {}
    seen_roles: set[str] = set()
    for index, raw_role in enumerate(roles):
        role = _require_object(raw_role, f"palette_resolution.roles[{index}]")
        role_name = _require_string(role.get("role"), f"palette_resolution.roles[{index}].role")
        if ROLE_RE.fullmatch(role_name) is None:
            raise VisualQAError(f"palette_resolution.roles[{index}].role has invalid format")
        if role_name in seen_roles:
            raise VisualQAError(f"duplicate C5 role: {role_name}")
        seen_roles.add(role_name)
        selected = _require_object(role.get("selected"), f"palette_resolution.roles[{index}].selected")
        block_id = _require_string(selected.get("block"), f"palette_resolution.roles[{index}].selected.block")
        selected_state = selected.get("selected_state")
        if selected_state is None:
            continue
        try:
            state_key = c2.canonical_block_state_string(selected_state)
        except Exception as exc:
            raise VisualQAError(f"invalid selected state for C5 role {role_name}: {exc}") from exc
        if selected_state.get("name") != block_id:
            raise VisualQAError(f"C5 role {role_name} selected block does not match selected state")
        labels.setdefault(state_key, []).append(role_name)

    for state_key in labels:
        labels[state_key] = sorted(labels[state_key])
    return _sha256_json(value), labels


def _local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def _validate_svg(
    view_id: str,
    data: object,
    *,
    build_ir_sha: str,
) -> dict[str, object]:
    if not isinstance(data, bytes) or not data:
        raise VisualQAError(f"view {view_id} must be non-empty SVG bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VisualQAError(f"view {view_id} must be UTF-8") from exc
    if not text.endswith("\n"):
        raise VisualQAError(f"view {view_id} must end with one canonical newline")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise VisualQAError(f"view {view_id} is malformed SVG") from exc
    if root.tag != f"{{{SVG_NAMESPACE}}}svg":
        raise VisualQAError(f"view {view_id} must use the canonical SVG namespace")
    allowed_elements = {"svg", "g", "rect", "polygon"}
    for element in root.iter():
        if not isinstance(element.tag, str) or not element.tag.startswith(f"{{{SVG_NAMESPACE}}}"):
            raise VisualQAError(f"view {view_id} contains a non-SVG namespace element")
        if _local_name(element.tag) not in allowed_elements:
            raise VisualQAError(f"view {view_id} contains unsupported SVG element")
        for raw_name, raw_value in element.attrib.items():
            name = _local_name(raw_name).lower()
            value = str(raw_value).lower()
            if raw_name.startswith("{") and not raw_name.startswith(f"{{{SVG_NAMESPACE}}}"):
                raise VisualQAError(f"view {view_id} contains external attribute namespace")
            if name.startswith("on") or name in {"href", "style"}:
                raise VisualQAError(f"view {view_id} contains unsafe SVG attribute")
            if "url(" in value or value.startswith("http://") or value.startswith("https://"):
                raise VisualQAError(f"view {view_id} contains external SVG resource reference")
    if root.attrib.get("data-renderer-version") != RENDERER_VERSION:
        raise VisualQAError(f"view {view_id} renderer version does not match C8")
    if root.attrib.get("data-build-ir-sha256") != build_ir_sha:
        raise VisualQAError(f"view {view_id} Build IR fingerprint does not match")
    if root.attrib.get("data-view-id") != view_id:
        raise VisualQAError(f"view {view_id} embedded view id does not match")
    try:
        width = int(root.attrib["width"])
        height = int(root.attrib["height"])
    except (KeyError, ValueError) as exc:
        raise VisualQAError(f"view {view_id} canvas dimensions are invalid") from exc
    if width < 1 or height < 1:
        raise VisualQAError(f"view {view_id} canvas dimensions must be positive")
    if root.attrib.get("viewBox") != f"0 0 {width} {height}":
        raise VisualQAError(f"view {view_id} viewBox does not match canvas dimensions")
    return {
        "id": view_id,
        "artifact_name": f"{view_id}.svg",
        "media_type": "image/svg+xml",
        "sha256": hashlib.sha256(data).hexdigest(),
        "byte_length": len(data),
        "width": width,
        "height": height,
        "evidence_class": "canonical_offline_preview",
    }


def _validate_views(views: object, *, build_ir_sha: str) -> tuple[list[dict[str, object]], dict[str, str]]:
    value = _require_object(views, "views")
    if set(value) != set(VIEW_IDS):
        raise VisualQAError("views must contain exactly the canonical C8 view ids")
    descriptors: list[dict[str, object]] = []
    hashes: dict[str, str] = {}
    for view_id in VIEW_IDS:
        descriptor = _validate_svg(view_id, value[view_id], build_ir_sha=build_ir_sha)
        descriptors.append(descriptor)
        hashes[view_id] = str(descriptor["sha256"])
    return descriptors, hashes


def _project_block(view_id: str, block: dict[str, int], size: dict[str, int]) -> tuple[int, int, int]:
    x, y, z = block["x"], block["y"], block["z"]
    if view_id == "front":
        return x, y, z
    if view_id == "back":
        return size["x"] - 1 - x, y, z
    if view_id == "left":
        return size["z"] - 1 - z, y, x
    if view_id == "right":
        return z, y, x
    if view_id == "top":
        return x, size["z"] - 1 - z, y
    raise VisualQAError(f"unsupported orthographic view: {view_id}")


def _nearer(view_id: str, candidate_depth: int, current_depth: int) -> bool:
    if view_id in {"front", "left"}:
        return candidate_depth < current_depth
    return candidate_depth > current_depth


def _projected_size(view_id: str, size: dict[str, int]) -> tuple[int, int]:
    if view_id in {"front", "back"}:
        return size["x"], size["y"]
    if view_id in {"left", "right"}:
        return size["z"], size["y"]
    if view_id == "top":
        return size["x"], size["z"]
    raise VisualQAError(f"unsupported orthographic view: {view_id}")


def _orthographic_grid(
    view_id: str,
    blocks: list[dict[str, int]],
    size: dict[str, int],
) -> dict[tuple[int, int], tuple[int, int]]:
    winners: dict[tuple[int, int], tuple[int, int]] = {}
    for block in blocks:
        u, v, depth = _project_block(view_id, block, size)
        key = (u, v)
        current = winners.get(key)
        if current is None or _nearer(view_id, depth, current[1]):
            winners[key] = (block["palette_index"], depth)
    return winners


def _components(nodes: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    remaining = set(nodes)
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining, key=lambda item: (item[1], item[0]))
        queue = [start]
        remaining.remove(start)
        component: list[tuple[int, int]] = []
        while queue:
            current = queue.pop(0)
            component.append(current)
            u, v = current
            for neighbor in ((u - 1, v), (u + 1, v), (u, v - 1), (u, v + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component, key=lambda item: (item[1], item[0])))
    components.sort(key=lambda item: (-len(item), item[0] if item else (0, 0)))
    return components


def _occupancy_metrics(
    blocks: list[dict[str, int]],
    palette: list[dict[str, Any]],
    size: dict[str, int],
) -> dict[str, object]:
    count = len(blocks)
    if not blocks:
        minimum = maximum = None
        extent = {"x": 0, "y": 0, "z": 0}
        volume = 0
    else:
        minimum = {axis: min(block[axis] for block in blocks) for axis in ("x", "y", "z")}
        maximum = {axis: max(block[axis] for block in blocks) for axis in ("x", "y", "z")}
        extent = {axis: maximum[axis] - minimum[axis] + 1 for axis in ("x", "y", "z")}
        volume = extent["x"] * extent["y"] * extent["z"]
    return {
        "occupied_block_count": count,
        "palette_state_count": len(palette),
        "occupied_min": minimum,
        "occupied_max": maximum,
        "occupied_extent": extent,
        "occupied_bounding_box_volume": volume,
        "occupied_density": _fraction(count, volume) if volume else {"numerator": 0, "denominator": 1},
        "full_bounds_density": _fraction(count, size["x"] * size["y"] * size["z"]),
    }


def _projection_metrics(
    view_id: str,
    winners: dict[tuple[int, int], tuple[int, int]],
) -> dict[str, object]:
    nodes = set(winners)
    if nodes:
        min_u = min(item[0] for item in nodes)
        max_u = max(item[0] for item in nodes)
        min_v = min(item[1] for item in nodes)
        max_v = max(item[1] for item in nodes)
        width = max_u - min_u + 1
        height = max_v - min_v + 1
        area = width * height
        components = _components(nodes)
        dominant = len(components[0])
        aspect = _fraction(width, height)
    else:
        width = height = area = 0
        components = []
        dominant = 0
        aspect = {"numerator": 0, "denominator": 1}
    return {
        "id": view_id,
        "occupied_cell_count": len(nodes),
        "bounding_width": width,
        "bounding_height": height,
        "occupancy_ratio": _fraction(len(nodes), area) if area else {"numerator": 0, "denominator": 1},
        "component_count": len(components),
        "dominant_component_size": dominant,
        "aspect_ratio": aspect,
    }


def _longest_adjacent_run(signatures: list[tuple[str, ...]]) -> int:
    if not signatures:
        return 0
    longest = current = 1
    for index in range(1, len(signatures)):
        if signatures[index] == signatures[index - 1]:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


def _repetition_metrics(
    view_id: str,
    winners: dict[tuple[int, int], tuple[int, int]],
    logical_width: int,
    logical_height: int,
    state_keys: list[str],
) -> dict[str, object]:
    empty = "<c8-empty>"
    rows = [
        tuple(state_keys[winners[(u, v)][0]] if (u, v) in winners else empty for u in range(logical_width))
        for v in range(logical_height)
    ]
    columns = [
        tuple(state_keys[winners[(u, v)][0]] if (u, v) in winners else empty for v in range(logical_height))
        for u in range(logical_width)
    ]
    distinct_rows = len(set(rows))
    distinct_columns = len(set(columns))
    repeated_rows = len(rows) - distinct_rows
    repeated_columns = len(columns) - distinct_columns
    return {
        "id": view_id,
        "distinct_row_signature_count": distinct_rows,
        "distinct_column_signature_count": distinct_columns,
        "repeated_row_signature_count": repeated_rows,
        "repeated_column_signature_count": repeated_columns,
        "longest_adjacent_identical_row_run": _longest_adjacent_run(rows),
        "longest_adjacent_identical_column_run": _longest_adjacent_run(columns),
        "repeated_row_ratio": _fraction(repeated_rows, len(rows)),
        "repeated_column_ratio": _fraction(repeated_columns, len(columns)),
    }


def _facade_depth_metrics(
    view_id: str,
    winners: dict[tuple[int, int], tuple[int, int]],
) -> dict[str, object]:
    depths = [value[1] for value in winners.values()]
    minimum = min(depths) if depths else None
    maximum = max(depths) if depths else None
    distinct = len(set(depths))
    pair_count = transition_count = 0
    for (u, v), (_, depth) in winners.items():
        for neighbor in ((u + 1, v), (u, v + 1)):
            other = winners.get(neighbor)
            if other is None:
                continue
            pair_count += 1
            if other[1] != depth:
                transition_count += 1
    return {
        "id": view_id,
        "distinct_visible_depth_count": distinct,
        "minimum_visible_depth": minimum,
        "maximum_visible_depth": maximum,
        "depth_range": 0 if minimum is None or maximum is None else maximum - minimum,
        "adjacent_visible_pair_count": pair_count,
        "adjacent_depth_transition_count": transition_count,
        "transition_ratio": _fraction(transition_count, pair_count) if pair_count else {"numerator": 0, "denominator": 1},
    }


def _layer_metrics(
    blocks: list[dict[str, int]],
    size: dict[str, int],
    state_keys: list[str],
) -> dict[str, object]:
    footprint = size["x"] * size["z"]
    by_level: dict[int, list[dict[str, int]]] = {y: [] for y in range(size["y"])}
    for block in blocks:
        by_level[block["y"]].append(block)
    levels: list[dict[str, object]] = []
    counts: list[int] = []
    for y in range(size["y"]):
        level_blocks = by_level[y]
        counts.append(len(level_blocks))
        palette_counts = [0] * len(state_keys)
        for block in level_blocks:
            palette_counts[block["palette_index"]] += 1
        levels.append(
            {
                "y": y,
                "occupied_cells": len(level_blocks),
                "footprint_area": footprint,
                "density": _fraction(len(level_blocks), footprint),
                "palette_counts": [
                    {"state": state_key, "count": palette_counts[index]}
                    for index, state_key in enumerate(state_keys)
                ],
            }
        )
    ordered = sorted(counts)
    if len(ordered) % 2:
        middle = ordered[len(ordered) // 2]
        pair = [middle, middle]
    else:
        pair = [ordered[len(ordered) // 2 - 1], ordered[len(ordered) // 2]]
    return {
        "levels": levels,
        "level_count": len(levels),
        "minimum_occupied_cells": min(counts),
        "maximum_occupied_cells": max(counts),
        "median_middle_pair": pair,
    }


def _metrics(
    build_ir: dict[str, Any],
    *,
    c2,
    role_labels: dict[str, list[str]],
) -> dict[str, object]:
    size = build_ir["bounds"]["size"]
    blocks = build_ir["blocks"]
    palette = build_ir["palette"]
    state_keys = [c2.canonical_block_state_string(state) for state in palette]
    grids = {view_id: _orthographic_grid(view_id, blocks, size) for view_id in ORTHO_IDS}
    projections = [_projection_metrics(view_id, grids[view_id]) for view_id in ORTHO_IDS]

    occupied_counts = [0] * len(palette)
    visible_counts = {view_id: [0] * len(palette) for view_id in ORTHO_IDS}
    for block in blocks:
        occupied_counts[block["palette_index"]] += 1
    for view_id in ORTHO_IDS:
        for palette_index, _depth in grids[view_id].values():
            visible_counts[view_id][palette_index] += 1
    total = len(blocks)
    palette_distribution = [
        {
            "state": state_key,
            "occupied_block_count": occupied_counts[index],
            "fraction": _fraction(occupied_counts[index], total) if total else {"numerator": 0, "denominator": 1},
            "visible_counts": {view_id: visible_counts[view_id][index] for view_id in ORTHO_IDS},
            "roles": role_labels.get(state_key, []),
        }
        for index, state_key in enumerate(state_keys)
    ]

    repetition: list[dict[str, object]] = []
    for view_id in ORTHO_IDS:
        logical_width, logical_height = _projected_size(view_id, size)
        repetition.append(
            _repetition_metrics(view_id, grids[view_id], logical_width, logical_height, state_keys)
        )

    return {
        "occupancy": _occupancy_metrics(blocks, palette, size),
        "projections": projections,
        "palette_distribution": palette_distribution,
        "repetition": repetition,
        "facade_depth": [_facade_depth_metrics(view_id, grids[view_id]) for view_id in FACADE_IDS],
        "layers": _layer_metrics(blocks, size, state_keys),
    }


def _validate_review_evidence(
    review_evidence: object | None,
    *,
    build_spec_sha: str,
    build_ir_sha: str,
    view_hashes: dict[str, str],
) -> tuple[str | None, dict[str, dict[str, object]]]:
    if review_evidence is None:
        return None, {}
    value = _require_object(review_evidence, "review_evidence")
    expected_keys = {
        "schema_version",
        "build_spec_sha256",
        "build_ir_sha256",
        "renderer_version",
        "views",
        "reviewer",
        "decisions",
    }
    _require_exact_keys(value, expected_keys, "review_evidence")
    if value["schema_version"] != 1:
        raise VisualQAError("review_evidence schema_version must be 1")
    if value["build_spec_sha256"] != build_spec_sha:
        raise VisualQAError("review_evidence BuildSpec fingerprint does not match")
    if value["build_ir_sha256"] != build_ir_sha:
        raise VisualQAError("review_evidence Build IR fingerprint does not match")
    if value["renderer_version"] != RENDERER_VERSION:
        raise VisualQAError("review_evidence renderer version does not match")

    review_views = value["views"]
    if not isinstance(review_views, list) or len(review_views) != len(VIEW_IDS):
        raise VisualQAError("review_evidence views must contain exactly seven canonical records")
    observed_ids: list[str] = []
    for index, raw_record in enumerate(review_views):
        record = _require_object(raw_record, f"review_evidence.views[{index}]")
        _require_exact_keys(record, {"id", "sha256"}, f"review_evidence.views[{index}]")
        view_id = _require_string(record["id"], f"review_evidence.views[{index}].id")
        observed_ids.append(view_id)
        sha = _require_sha(record["sha256"], f"review_evidence.views[{index}].sha256")
        if view_id not in view_hashes or sha != view_hashes[view_id]:
            raise VisualQAError(f"review_evidence view {view_id} hash does not match current artifact")
    if tuple(observed_ids) != VIEW_IDS:
        raise VisualQAError("review_evidence views must use canonical C8 order without duplicates")

    reviewer = _require_object(value["reviewer"], "review_evidence.reviewer")
    _require_exact_keys(reviewer, {"kind", "id"}, "review_evidence.reviewer")
    if reviewer["kind"] not in {"human", "agent"}:
        raise VisualQAError("review_evidence reviewer.kind must be human or agent")
    _require_string(reviewer["id"], "review_evidence.reviewer.id")

    raw_decisions = value["decisions"]
    if not isinstance(raw_decisions, list):
        raise VisualQAError("review_evidence.decisions must be an array")
    decisions: dict[str, dict[str, object]] = {}
    for index, raw_decision in enumerate(raw_decisions):
        item = _require_object(raw_decision, f"review_evidence.decisions[{index}]")
        _require_exact_keys(item, {"check_id", "status", "evidence_views", "summary"}, f"review_evidence.decisions[{index}]")
        check_id = _require_string(item["check_id"], f"review_evidence.decisions[{index}].check_id")
        if check_id not in SUBJECTIVE_CHECKS:
            raise VisualQAError(f"review_evidence decision {check_id} is not a resolvable C8 subjective check")
        if check_id in decisions:
            raise VisualQAError(f"duplicate review decision for {check_id}")
        status = item["status"]
        if status not in {"PASS", "FAIL"}:
            raise VisualQAError(f"review_evidence decision {check_id} status must be PASS or FAIL")
        evidence_views = item["evidence_views"]
        if not isinstance(evidence_views, list) or not evidence_views:
            raise VisualQAError(f"review_evidence decision {check_id} must cite at least one view")
        if any(not isinstance(view_id, str) for view_id in evidence_views):
            raise VisualQAError(f"review_evidence decision {check_id} evidence views are invalid")
        if len(evidence_views) != len(set(evidence_views)):
            raise VisualQAError(f"review_evidence decision {check_id} evidence views must be unique")
        allowed = set(ALLOWED_EVIDENCE_VIEWS[check_id])
        if any(view_id not in allowed for view_id in evidence_views):
            raise VisualQAError(f"review_evidence decision {check_id} cites a disallowed view")
        summary = _require_string(item["summary"], f"review_evidence.decisions[{index}].summary")
        normalized_views = [view_id for view_id in VIEW_IDS if view_id in evidence_views]
        decisions[check_id] = {
            "check_id": check_id,
            "status": status,
            "evidence_views": normalized_views,
            "summary": summary,
        }
    return _sha256_json(value), decisions


def _check(
    check_id: str,
    *,
    required: bool,
    status: str,
    severity: str,
    summary: str,
    evidence_views: list[str],
    findings: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "id": check_id,
        "required": required,
        "status": status,
        "severity": severity,
        "summary": summary,
        "evidence_views": evidence_views,
        "findings": findings or [],
    }


def _checks(decisions: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = [
        _check(
            "canonical_preview_integrity",
            required=True,
            status="PASS",
            severity="info",
            summary="All canonical C8 offline preview artifacts are safe and bound to the exact Build IR.",
            evidence_views=list(VIEW_IDS),
        )
    ]
    for check_id in SUBJECTIVE_CHECKS:
        review = decisions.get(check_id)
        if review is None:
            result.append(
                _check(
                    check_id,
                    required=True,
                    status="DEFERRED",
                    severity="warning",
                    summary="Visual acceptance is deferred because no matching explicit review evidence was supplied.",
                    evidence_views=list(ALLOWED_EVIDENCE_VIEWS[check_id]),
                )
            )
        else:
            status = str(review["status"])
            result.append(
                _check(
                    check_id,
                    required=True,
                    status=status,
                    severity="info" if status == "PASS" else "error",
                    summary=str(review["summary"]),
                    evidence_views=list(review["evidence_views"]),
                )
            )
    result.append(
        _check(
            "runtime_visual_fidelity",
            required=False,
            status="DEFERRED",
            severity="info",
            summary="Minecraft runtime visual fidelity is outside C8 and remains deferred to C12 runtime evidence.",
            evidence_views=[],
        )
    )
    return result


def _derive_overall(checks: list[dict[str, object]]) -> str:
    required = [item for item in checks if item["required"]]
    if any(item["status"] == "FAIL" for item in required):
        return "FAIL"
    if any(item["status"] == "DEFERRED" for item in required):
        return "DEFERRED"
    return "PASS"


def _validate_fraction(value: object, label: str) -> None:
    item = _require_object(value, label)
    _require_exact_keys(item, {"numerator", "denominator"}, label)
    if not _is_int(item["numerator"]):
        raise VisualQAError(f"{label}.numerator must be an integer")
    if not _is_int(item["denominator"]) or item["denominator"] < 1:
        raise VisualQAError(f"{label}.denominator must be a positive integer")
    expected = _fraction(item["numerator"], item["denominator"])
    if item != expected:
        raise VisualQAError(f"{label} must be reduced to canonical form")


def _validate_report_metrics(metrics: object) -> None:
    value = _require_object(metrics, "report.metrics")
    _require_exact_keys(value, {"occupancy", "projections", "palette_distribution", "repetition", "facade_depth", "layers"}, "report.metrics")

    occupancy = _require_object(value["occupancy"], "report.metrics.occupancy")
    occupancy_keys = {
        "occupied_block_count",
        "palette_state_count",
        "occupied_min",
        "occupied_max",
        "occupied_extent",
        "occupied_bounding_box_volume",
        "occupied_density",
        "full_bounds_density",
    }
    _require_exact_keys(occupancy, occupancy_keys, "report.metrics.occupancy")
    for field in ("occupied_block_count", "palette_state_count", "occupied_bounding_box_volume"):
        if not _is_int(occupancy[field]) or occupancy[field] < 0:
            raise VisualQAError(f"report.metrics.occupancy.{field} must be non-negative")
    for field in ("occupied_density", "full_bounds_density"):
        _validate_fraction(occupancy[field], f"report.metrics.occupancy.{field}")
    for field in ("occupied_min", "occupied_max"):
        position = occupancy[field]
        if position is not None:
            position_obj = _require_object(position, f"report.metrics.occupancy.{field}")
            _require_exact_keys(position_obj, {"x", "y", "z"}, f"report.metrics.occupancy.{field}")
            if any(not _is_int(position_obj[axis]) for axis in ("x", "y", "z")):
                raise VisualQAError(f"report.metrics.occupancy.{field} axes must be integers")
    extent = _require_object(occupancy["occupied_extent"], "report.metrics.occupancy.occupied_extent")
    _require_exact_keys(extent, {"x", "y", "z"}, "report.metrics.occupancy.occupied_extent")
    if any(not _is_int(extent[axis]) or extent[axis] < 0 for axis in ("x", "y", "z")):
        raise VisualQAError("report.metrics.occupancy.occupied_extent axes must be non-negative integers")

    projections = value["projections"]
    if not isinstance(projections, list) or [item.get("id") if isinstance(item, dict) else None for item in projections] != list(ORTHO_IDS):
        raise VisualQAError("report.metrics.projections must use canonical C8 view order")
    for index, raw in enumerate(projections):
        item = _require_object(raw, f"report.metrics.projections[{index}]")
        expected = {"id", "occupied_cell_count", "bounding_width", "bounding_height", "occupancy_ratio", "component_count", "dominant_component_size", "aspect_ratio"}
        _require_exact_keys(item, expected, f"report.metrics.projections[{index}]")
        for field in ("occupied_cell_count", "bounding_width", "bounding_height", "component_count", "dominant_component_size"):
            if not _is_int(item[field]) or item[field] < 0:
                raise VisualQAError(f"report.metrics.projections[{index}].{field} must be non-negative")
        _validate_fraction(item["occupancy_ratio"], f"report.metrics.projections[{index}].occupancy_ratio")
        _validate_fraction(item["aspect_ratio"], f"report.metrics.projections[{index}].aspect_ratio")

    palette_distribution = value["palette_distribution"]
    if not isinstance(palette_distribution, list):
        raise VisualQAError("report.metrics.palette_distribution must be an array")
    last_state = None
    for index, raw in enumerate(palette_distribution):
        item = _require_object(raw, f"report.metrics.palette_distribution[{index}]")
        _require_exact_keys(item, {"state", "occupied_block_count", "fraction", "visible_counts", "roles"}, f"report.metrics.palette_distribution[{index}]")
        state = _require_string(item["state"], f"report.metrics.palette_distribution[{index}].state")
        if last_state is not None and state <= last_state:
            raise VisualQAError("report.metrics.palette_distribution must be in canonical state order")
        last_state = state
        if not _is_int(item["occupied_block_count"]) or item["occupied_block_count"] < 0:
            raise VisualQAError("palette occupied count must be non-negative")
        _validate_fraction(item["fraction"], f"report.metrics.palette_distribution[{index}].fraction")
        visible = _require_object(item["visible_counts"], f"report.metrics.palette_distribution[{index}].visible_counts")
        _require_exact_keys(visible, set(ORTHO_IDS), f"report.metrics.palette_distribution[{index}].visible_counts")
        if any(not _is_int(visible[view_id]) or visible[view_id] < 0 for view_id in ORTHO_IDS):
            raise VisualQAError("palette visible counts must be non-negative integers")
        roles = item["roles"]
        if not isinstance(roles, list) or any(not isinstance(role, str) or not role for role in roles) or roles != sorted(set(roles)):
            raise VisualQAError("palette role labels must be sorted unique strings")

    repetition = value["repetition"]
    if not isinstance(repetition, list) or [item.get("id") if isinstance(item, dict) else None for item in repetition] != list(ORTHO_IDS):
        raise VisualQAError("report.metrics.repetition must use canonical C8 view order")
    for index, raw in enumerate(repetition):
        item = _require_object(raw, f"report.metrics.repetition[{index}]")
        expected = {
            "id",
            "distinct_row_signature_count",
            "distinct_column_signature_count",
            "repeated_row_signature_count",
            "repeated_column_signature_count",
            "longest_adjacent_identical_row_run",
            "longest_adjacent_identical_column_run",
            "repeated_row_ratio",
            "repeated_column_ratio",
        }
        _require_exact_keys(item, expected, f"report.metrics.repetition[{index}]")
        for field in expected - {"id", "repeated_row_ratio", "repeated_column_ratio"}:
            if not _is_int(item[field]) or item[field] < 0:
                raise VisualQAError(f"report.metrics.repetition[{index}].{field} must be non-negative")
        _validate_fraction(item["repeated_row_ratio"], f"report.metrics.repetition[{index}].repeated_row_ratio")
        _validate_fraction(item["repeated_column_ratio"], f"report.metrics.repetition[{index}].repeated_column_ratio")

    facade = value["facade_depth"]
    if not isinstance(facade, list) or [item.get("id") if isinstance(item, dict) else None for item in facade] != list(FACADE_IDS):
        raise VisualQAError("report.metrics.facade_depth must use canonical C8 facade order")
    for index, raw in enumerate(facade):
        item = _require_object(raw, f"report.metrics.facade_depth[{index}]")
        expected = {"id", "distinct_visible_depth_count", "minimum_visible_depth", "maximum_visible_depth", "depth_range", "adjacent_visible_pair_count", "adjacent_depth_transition_count", "transition_ratio"}
        _require_exact_keys(item, expected, f"report.metrics.facade_depth[{index}]")
        for field in ("distinct_visible_depth_count", "depth_range", "adjacent_visible_pair_count", "adjacent_depth_transition_count"):
            if not _is_int(item[field]) or item[field] < 0:
                raise VisualQAError(f"report.metrics.facade_depth[{index}].{field} must be non-negative")
        for field in ("minimum_visible_depth", "maximum_visible_depth"):
            if item[field] is not None and not _is_int(item[field]):
                raise VisualQAError(f"report.metrics.facade_depth[{index}].{field} must be integer or null")
        _validate_fraction(item["transition_ratio"], f"report.metrics.facade_depth[{index}].transition_ratio")

    layers = _require_object(value["layers"], "report.metrics.layers")
    _require_exact_keys(layers, {"levels", "level_count", "minimum_occupied_cells", "maximum_occupied_cells", "median_middle_pair"}, "report.metrics.layers")
    for field in ("level_count", "minimum_occupied_cells", "maximum_occupied_cells"):
        if not _is_int(layers[field]) or layers[field] < 0:
            raise VisualQAError(f"report.metrics.layers.{field} must be non-negative")
    levels = layers["levels"]
    if not isinstance(levels, list) or layers["level_count"] != len(levels):
        raise VisualQAError("report.metrics.layers.levels must match level_count")
    if [item.get("y") if isinstance(item, dict) else None for item in levels] != list(range(len(levels))):
        raise VisualQAError("report.metrics.layers levels must cover ascending y positions")
    for index, raw in enumerate(levels):
        item = _require_object(raw, f"report.metrics.layers.levels[{index}]")
        _require_exact_keys(item, {"y", "occupied_cells", "footprint_area", "density", "palette_counts"}, f"report.metrics.layers.levels[{index}]")
        if not _is_int(item["occupied_cells"]) or item["occupied_cells"] < 0:
            raise VisualQAError("layer occupied_cells must be non-negative")
        if not _is_int(item["footprint_area"]) or item["footprint_area"] < 1:
            raise VisualQAError("layer footprint_area must be positive")
        _validate_fraction(item["density"], f"report.metrics.layers.levels[{index}].density")
        palette_counts = item["palette_counts"]
        if not isinstance(palette_counts, list):
            raise VisualQAError("layer palette_counts must be an array")
        for raw_count in palette_counts:
            count = _require_object(raw_count, "layer palette count")
            _require_exact_keys(count, {"state", "count"}, "layer palette count")
            _require_string(count["state"], "layer palette count state")
            if not _is_int(count["count"]) or count["count"] < 0:
                raise VisualQAError("layer palette count must be non-negative")
    middle = layers["median_middle_pair"]
    if not isinstance(middle, list) or len(middle) != 2 or any(not _is_int(item) or item < 0 for item in middle):
        raise VisualQAError("report.metrics.layers.median_middle_pair is invalid")


def validate_visual_qa_report(report: dict) -> None:
    value = _require_object(report, "C8 report")
    _require_exact_keys(value, REPORT_KEYS, "C8 report")
    if value["schema_version"] != 1:
        raise VisualQAError("C8 report schema_version must be 1")
    for field in ("build_spec_sha256", "build_ir_sha256", "content_sha256"):
        _require_sha(value[field], f"C8 report {field}")
    for field in ("structural_report_sha256", "palette_resolution_sha256", "review_evidence_sha256"):
        if value[field] is not None:
            _require_sha(value[field], f"C8 report {field}")
    if value["renderer_version"] != RENDERER_VERSION:
        raise VisualQAError("C8 report renderer_version is invalid")

    views = value["views"]
    if not isinstance(views, list) or [item.get("id") if isinstance(item, dict) else None for item in views] != list(VIEW_IDS):
        raise VisualQAError("C8 report views are not in canonical order")
    for index, raw_view in enumerate(views):
        item = _require_object(raw_view, f"C8 report views[{index}]")
        _require_exact_keys(item, {"id", "artifact_name", "media_type", "sha256", "byte_length", "width", "height", "evidence_class"}, f"C8 report views[{index}]")
        view_id = VIEW_IDS[index]
        if item["artifact_name"] != f"{view_id}.svg" or item["media_type"] != "image/svg+xml" or item["evidence_class"] != "canonical_offline_preview":
            raise VisualQAError(f"C8 report view {view_id} descriptor is invalid")
        _require_sha(item["sha256"], f"C8 report view {view_id} sha256")
        for field in ("byte_length", "width", "height"):
            if not _is_int(item[field]) or item[field] < 1:
                raise VisualQAError(f"C8 report view {view_id} {field} must be positive")

    _validate_report_metrics(value["metrics"])

    checks = value["checks"]
    if not isinstance(checks, list) or [item.get("id") if isinstance(item, dict) else None for item in checks] != list(CHECK_ORDER):
        raise VisualQAError("C8 report checks are not in canonical order")
    for index, raw_check in enumerate(checks):
        item = _require_object(raw_check, f"C8 report checks[{index}]")
        _require_exact_keys(item, {"id", "required", "status", "severity", "summary", "evidence_views", "findings"}, f"C8 report checks[{index}]")
        if not isinstance(item["required"], bool):
            raise VisualQAError("C8 report check required flag must be boolean")
        if item["status"] not in {"PASS", "FAIL", "DEFERRED", "NOT_APPLICABLE"}:
            raise VisualQAError("C8 report check status is invalid")
        if item["severity"] not in {"error", "warning", "info"}:
            raise VisualQAError("C8 report check severity is invalid")
        _require_string(item["summary"], "C8 report check summary")
        evidence_views = item["evidence_views"]
        if not isinstance(evidence_views, list) or len(evidence_views) != len(set(evidence_views)) or any(view_id not in VIEW_IDS for view_id in evidence_views):
            raise VisualQAError("C8 report check evidence_views are invalid")
        if evidence_views != [view_id for view_id in VIEW_IDS if view_id in evidence_views]:
            raise VisualQAError("C8 report check evidence_views must use canonical order")
        findings = item["findings"]
        if not isinstance(findings, list):
            raise VisualQAError("C8 report check findings must be an array")
        for raw_finding in findings:
            finding = _require_object(raw_finding, "C8 report finding")
            if set(finding) not in ({"code", "message"}, {"code", "message", "subject"}):
                raise VisualQAError("C8 report finding fields are invalid")
            code = _require_string(finding["code"], "C8 report finding code")
            if FINDING_CODE_RE.fullmatch(code) is None:
                raise VisualQAError("C8 report finding code has invalid format")
            _require_string(finding["message"], "C8 report finding message")
            if "subject" in finding:
                _require_string(finding["subject"], "C8 report finding subject")

    if checks[0]["required"] is not True or checks[0]["status"] != "PASS":
        raise VisualQAError("canonical_preview_integrity must be required PASS")
    for check_id in SUBJECTIVE_CHECKS:
        item = checks[CHECK_ORDER.index(check_id)]
        if item["required"] is not True:
            raise VisualQAError(f"C8 subjective check {check_id} must be required")
    runtime = checks[-1]
    if runtime["required"] is not False or runtime["status"] != "DEFERRED" or runtime["severity"] != "info":
        raise VisualQAError("runtime_visual_fidelity must remain non-required DEFERRED info")
    expected_overall = _derive_overall(checks)
    if value["overall_status"] != expected_overall:
        raise VisualQAError("C8 report overall_status does not match required check statuses")
    if value["overall_status"] not in {"PASS", "FAIL", "DEFERRED"}:
        raise VisualQAError("C8 report overall_status is invalid")

    payload = {key: item for key, item in value.items() if key != "content_sha256"}
    if _sha256_json(payload) != value["content_sha256"]:
        raise VisualQAError("C8 report content_sha256 does not match report content")


def run_visual_qa(
    build_spec: dict,
    build_ir: dict,
    views: dict[str, bytes],
    structural_report: dict | None = None,
    palette_resolution: dict | None = None,
    review_evidence: dict | None = None,
) -> dict:
    spec, ir, c2, build_spec_sha, build_ir_sha = _validate_build_inputs(build_spec, build_ir)
    structural_sha = _validate_structural_report(
        structural_report,
        build_spec_sha=build_spec_sha,
        build_ir_sha=build_ir_sha,
    )
    palette_sha, role_labels = _validate_palette_resolution(
        palette_resolution,
        build_spec_sha=build_spec_sha,
        c2=c2,
    )
    view_descriptors, view_hashes = _validate_views(views, build_ir_sha=build_ir_sha)
    review_sha, decisions = _validate_review_evidence(
        review_evidence,
        build_spec_sha=build_spec_sha,
        build_ir_sha=build_ir_sha,
        view_hashes=view_hashes,
    )
    metrics = _metrics(ir, c2=c2, role_labels=role_labels)
    checks = _checks(decisions)
    report: dict[str, object] = {
        "schema_version": 1,
        "build_spec_sha256": build_spec_sha,
        "build_ir_sha256": build_ir_sha,
        "structural_report_sha256": structural_sha,
        "palette_resolution_sha256": palette_sha,
        "review_evidence_sha256": review_sha,
        "renderer_version": RENDERER_VERSION,
        "views": view_descriptors,
        "metrics": metrics,
        "checks": checks,
        "overall_status": _derive_overall(checks),
    }
    report["content_sha256"] = _sha256_json(report)
    validate_visual_qa_report(report)
    return report
