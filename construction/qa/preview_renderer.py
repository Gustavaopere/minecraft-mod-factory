from __future__ import annotations

import hashlib
import importlib.util
import math
from pathlib import Path
from typing import Any

RENDERER_VERSION = "c8-svg-v1"
VIEW_IDS = ("front", "back", "left", "right", "top", "isometric", "layers")
ORTHO_IDS = ("front", "back", "left", "right", "top")
ORTHO_CELL = 16
ORTHO_PADDING = 16
LAYER_CELL = 8
LAYER_GAP = 8
LAYER_PADDING = 8
ISO_HALF_WIDTH = 8
ISO_HALF_HEIGHT = 4
ISO_VERTICAL = 8
ISO_PADDING = 16


class PreviewRenderError(ValueError):
    """Raised when C8 cannot render a deterministic preview from authoritative C2 input."""


def _c2_module():
    path = Path(__file__).resolve().parents[1] / "core" / "build_ir.py"
    spec = importlib.util.spec_from_file_location("construction_c2_build_ir_for_c8_renderer", path)
    if spec is None or spec.loader is None:
        raise PreviewRenderError(f"cannot load C2 Build IR authority: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validated_ir(build_ir: object):
    c2 = _c2_module()
    errors = c2.validate_build_ir(build_ir)
    if errors:
        raise PreviewRenderError("invalid C2 Build IR: " + "; ".join(errors))
    assert isinstance(build_ir, dict)
    size = build_ir["bounds"]["size"]
    palette = build_ir["palette"]
    blocks = build_ir["blocks"]
    fingerprint = c2.fingerprint_build_ir(build_ir)
    return c2, size, palette, blocks, fingerprint


def _state_key(c2, palette: list[dict[str, Any]], index: int) -> str:
    return c2.canonical_block_state_string(palette[index])


def _base_rgb(state_key: str) -> tuple[int, int, int]:
    digest = hashlib.sha256(state_key.encode("utf-8")).digest()
    return tuple(64 + value % 128 for value in digest[:3])


def _shade(rgb: tuple[int, int, int], percent: int) -> tuple[int, int, int]:
    return tuple(channel * percent // 100 for channel in rgb)


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02x}" for channel in rgb)


def _svg_open(width: int, height: int, build_ir_sha256: str, view_id: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" data-renderer-version="{RENDERER_VERSION}" '
        f'data-build-ir-sha256="{build_ir_sha256}" data-view-id="{view_id}">\n'
    )


def _orthographic_dimensions(view_id: str, size: dict[str, int]) -> tuple[int, int, int, int]:
    if view_id in {"front", "back"}:
        logical_width, logical_height = size["x"], size["y"]
    elif view_id in {"left", "right"}:
        logical_width, logical_height = size["z"], size["y"]
    elif view_id == "top":
        logical_width, logical_height = size["x"], size["z"]
    else:
        raise PreviewRenderError(f"unsupported orthographic view: {view_id}")
    return (
        logical_width,
        logical_height,
        logical_width * ORTHO_CELL + ORTHO_PADDING * 2,
        logical_height * ORTHO_CELL + ORTHO_PADDING * 2,
    )


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
    raise PreviewRenderError(f"unsupported orthographic view: {view_id}")


def _nearer(view_id: str, candidate_depth: int, current_depth: int) -> bool:
    if view_id in {"front", "left"}:
        return candidate_depth < current_depth
    if view_id in {"back", "right", "top"}:
        return candidate_depth > current_depth
    raise PreviewRenderError(f"unsupported orthographic view: {view_id}")


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


def _render_orthographic(
    view_id: str,
    c2,
    size: dict[str, int],
    palette: list[dict[str, Any]],
    blocks: list[dict[str, int]],
    build_ir_sha256: str,
) -> bytes:
    _, logical_height, width, height = _orthographic_dimensions(view_id, size)
    winners = _orthographic_grid(view_id, blocks, size)
    parts = [_svg_open(width, height, build_ir_sha256, view_id)]
    for (u, v), (palette_index, _) in sorted(winners.items(), key=lambda item: (item[0][1], item[0][0])):
        if view_id == "top":
            px = ORTHO_PADDING + u * ORTHO_CELL
            py = ORTHO_PADDING + v * ORTHO_CELL
        else:
            px = ORTHO_PADDING + u * ORTHO_CELL
            py = ORTHO_PADDING + (logical_height - 1 - v) * ORTHO_CELL
        fill = _hex(_base_rgb(_state_key(c2, palette, palette_index)))
        parts.append(
            f'<rect x="{px}" y="{py}" width="{ORTHO_CELL}" height="{ORTHO_CELL}" fill="{fill}"/>\n'
        )
    parts.append("</svg>\n")
    return "".join(parts).encode("utf-8")


def _iso_raw_faces(x: int, y: int, z: int) -> dict[str, tuple[tuple[int, int], ...]]:
    base_x = (x - z) * ISO_HALF_WIDTH
    base_y = (x + z) * ISO_HALF_HEIGHT - y * ISO_VERTICAL
    return {
        "top": (
            (base_x, base_y - ISO_HALF_HEIGHT),
            (base_x + ISO_HALF_WIDTH, base_y),
            (base_x, base_y + ISO_HALF_HEIGHT),
            (base_x - ISO_HALF_WIDTH, base_y),
        ),
        "negative_x": (
            (base_x - ISO_HALF_WIDTH, base_y),
            (base_x, base_y + ISO_HALF_HEIGHT),
            (base_x, base_y + ISO_HALF_HEIGHT + ISO_VERTICAL),
            (base_x - ISO_HALF_WIDTH, base_y + ISO_VERTICAL),
        ),
        "negative_z": (
            (base_x + ISO_HALF_WIDTH, base_y),
            (base_x, base_y + ISO_HALF_HEIGHT),
            (base_x, base_y + ISO_HALF_HEIGHT + ISO_VERTICAL),
            (base_x + ISO_HALF_WIDTH, base_y + ISO_VERTICAL),
        ),
    }


def _iso_canvas(size: dict[str, int]) -> tuple[int, int, int, int]:
    xs = (0, size["x"] - 1)
    ys = (0, size["y"] - 1)
    zs = (0, size["z"] - 1)
    points: list[tuple[int, int]] = []
    for x in xs:
        for y in ys:
            for z in zs:
                faces = _iso_raw_faces(x, y, z)
                for face_name in ("negative_z", "negative_x", "top"):
                    points.extend(faces[face_name])
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    width = max_x - min_x + ISO_PADDING * 2
    height = max_y - min_y + ISO_PADDING * 2
    return width, height, ISO_PADDING - min_x, ISO_PADDING - min_y


def _render_isometric(
    c2,
    size: dict[str, int],
    palette: list[dict[str, Any]],
    blocks: list[dict[str, int]],
    build_ir_sha256: str,
) -> bytes:
    width, height, translate_x, translate_y = _iso_canvas(size)
    occupancy = {(block["x"], block["y"], block["z"]) for block in blocks}
    ordered = sorted(blocks, key=lambda block: (block["x"] + block["z"], block["y"], block["z"], block["x"]))
    parts = [_svg_open(width, height, build_ir_sha256, "isometric")]
    for block in ordered:
        x, y, z = block["x"], block["y"], block["z"]
        raw_faces = _iso_raw_faces(x, y, z)
        state_rgb = _base_rgb(_state_key(c2, palette, block["palette_index"]))
        faces = (
            ("negative_z", (x, y, z - 1), _shade(state_rgb, 70)),
            ("negative_x", (x - 1, y, z), _shade(state_rgb, 85)),
            ("top", (x, y + 1, z), state_rgb),
        )
        for face_name, neighbor, rgb in faces:
            if neighbor in occupancy:
                continue
            points = " ".join(
                f"{px + translate_x},{py + translate_y}" for px, py in raw_faces[face_name]
            )
            parts.append(f'<polygon points="{points}" fill="{_hex(rgb)}"/>\n')
    parts.append("</svg>\n")
    return "".join(parts).encode("utf-8")


def _ceil_sqrt(value: int) -> int:
    root = math.isqrt(value)
    return root if root * root == value else root + 1


def _ceil_div(value: int, divisor: int) -> int:
    return (value + divisor - 1) // divisor


def _render_layers(
    c2,
    size: dict[str, int],
    palette: list[dict[str, Any]],
    blocks: list[dict[str, int]],
    build_ir_sha256: str,
) -> bytes:
    cols = _ceil_sqrt(size["y"])
    rows = _ceil_div(size["y"], cols)
    tile_width = size["x"] * LAYER_CELL
    tile_height = size["z"] * LAYER_CELL
    width = LAYER_PADDING * 2 + cols * tile_width + (cols - 1) * LAYER_GAP
    height = LAYER_PADDING * 2 + rows * tile_height + (rows - 1) * LAYER_GAP
    by_level: dict[int, list[dict[str, int]]] = {y: [] for y in range(size["y"])}
    for block in blocks:
        by_level[block["y"]].append(block)

    parts = [_svg_open(width, height, build_ir_sha256, "layers")]
    for y in range(size["y"]):
        column = y % cols
        row = y // cols
        tile_x = LAYER_PADDING + column * (tile_width + LAYER_GAP)
        tile_y = LAYER_PADDING + row * (tile_height + LAYER_GAP)
        parts.append(f'<g data-y="{y}">\n')
        cells: list[tuple[int, int, dict[str, int]]] = []
        for block in by_level[y]:
            u = block["x"]
            v = size["z"] - 1 - block["z"]
            cells.append((u, v, block))
        for u, v, block in sorted(cells, key=lambda item: (item[1], item[0])):
            px = tile_x + u * LAYER_CELL
            py = tile_y + v * LAYER_CELL
            fill = _hex(_base_rgb(_state_key(c2, palette, block["palette_index"])))
            parts.append(
                f'<rect x="{px}" y="{py}" width="{LAYER_CELL}" height="{LAYER_CELL}" fill="{fill}"/>\n'
            )
        parts.append("</g>\n")
    parts.append("</svg>\n")
    return "".join(parts).encode("utf-8")


def render_canonical_views(build_ir: dict) -> dict[str, bytes]:
    c2, size, palette, blocks, fingerprint = _validated_ir(build_ir)
    result: dict[str, bytes] = {}
    for view_id in ORTHO_IDS:
        result[view_id] = _render_orthographic(view_id, c2, size, palette, blocks, fingerprint)
    result["isometric"] = _render_isometric(c2, size, palette, blocks, fingerprint)
    result["layers"] = _render_layers(c2, size, palette, blocks, fingerprint)
    return result
