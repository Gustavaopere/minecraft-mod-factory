from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION = ROOT / "construction"
RENDERER_PATH = CONSTRUCTION / "qa" / "preview_renderer.py"
VISUAL_QA_PATH = CONSTRUCTION / "core" / "visual_qa.py"
C2_MODULE_PATH = CONSTRUCTION / "core" / "build_ir.py"
C7_MODULE_PATH = CONSTRUCTION / "core" / "structural_qa.py"
SCHEMA_PATH = CONSTRUCTION / "schemas" / "visual-qa-report.schema.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "factory-construction-c8-visual-qa.yml"
SPEC_PATH = ROOT / "docs" / "superpowers" / "specs" / "2026-09-11-construction-c8-visual-qa-design.md"
PLAN_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-09-11-construction-c8-visual-qa.md"
GOLDEN = CONSTRUCTION / "fixtures" / "vanilla-golden"
C8_GOLDEN = GOLDEN / "c8"
IMPLEMENTATION_READY = RENDERER_PATH.is_file() and VISUAL_QA_PATH.is_file()

VIEW_IDS = ("front", "back", "left", "right", "top", "isometric", "layers")
ORTHO_IDS = ("front", "back", "left", "right", "top")
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
RENDERER_VERSION = "c8-svg-v1"


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def c2_module():
    return load_path(C2_MODULE_PATH, "construction_c2_for_c8")


def c7_module():
    return load_path(C7_MODULE_PATH, "construction_c7_for_c8")


def renderer_module():
    return load_path(RENDERER_PATH, "construction_c8_preview_renderer")


def visual_module():
    return load_path(VISUAL_QA_PATH, "construction_c8_visual_qa")


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def make_build_spec(
    *,
    size: tuple[int, int, int] = (3, 3, 3),
    loader: str = "none",
    allow_modded: bool = False,
    require_determinism: bool = True,
    seed: int = 8008,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "identity": {
            "name": "c8-visual-qa-test",
            "seed": seed,
            "description": "Deterministic C8 Visual QA fixture",
        },
        "target": {
            "minecraft_version": "1.21.1",
            "loader": loader,
            **({"modpack_snapshot": "c8-test-snapshot"} if loader == "neoforge" else {}),
        },
        "geometry": {
            "max_size": {"x": size[0], "y": size[1], "z": size[2]},
            "terrain_policy": "flat",
            "architectural_brief": "C8 diagnostic visual fixture",
            "required_spaces": ["test_space"],
        },
        "palette": {
            "allow_modded": allow_modded,
            "allowed_namespaces": ["minecraft", "test"] if allow_modded else ["minecraft"],
            "forbidden_blocks": [],
        },
        "qa": {
            "require_walkability": False,
            "require_complete_interior": False,
            "require_determinism": require_determinism,
        },
        "outputs": {"formats": ["sponge_v3"]},
    }


def placement(
    x: int,
    y: int,
    z: int,
    name: str = "minecraft:stone_bricks",
    properties: dict[str, str] | None = None,
) -> dict[str, object]:
    return {
        "x": x,
        "y": y,
        "z": z,
        "block_state": {"name": name, "properties": dict(properties or {})},
    }


def make_ir(build_spec: dict[str, object], placements: list[dict[str, object]]):
    return c2_module().canonicalize_build_ir(
        build_spec,
        placements,
        producer="construction-c8-test",
        producer_version="1",
    )


def render(build_ir: dict[str, object]) -> dict[str, bytes]:
    return renderer_module().render_canonical_views(build_ir)


def run_visual(
    build_spec: dict[str, object],
    build_ir: dict[str, object],
    *,
    structural_report: dict[str, object] | None = None,
    palette_resolution: dict[str, object] | None = None,
    review_evidence: dict[str, object] | None = None,
):
    views = render(build_ir)
    return visual_module().run_visual_qa(
        build_spec,
        build_ir,
        views,
        structural_report=structural_report,
        palette_resolution=palette_resolution,
        review_evidence=review_evidence,
    )


def check(report: dict[str, object], check_id: str) -> dict[str, object]:
    for item in report["checks"]:
        if item["id"] == check_id:
            return item
    raise AssertionError(f"missing check: {check_id}")


def projection(report: dict[str, object], view_id: str) -> dict[str, object]:
    for item in report["metrics"]["projections"]:
        if item["id"] == view_id:
            return item
    raise AssertionError(f"missing projection metric: {view_id}")


def repetition_metric(report: dict[str, object], view_id: str) -> dict[str, object]:
    for item in report["metrics"]["repetition"]:
        if item["id"] == view_id:
            return item
    raise AssertionError(f"missing repetition metric: {view_id}")


def facade_metric(report: dict[str, object], view_id: str) -> dict[str, object]:
    for item in report["metrics"]["facade_depth"]:
        if item["id"] == view_id:
            return item
    raise AssertionError(f"missing facade metric: {view_id}")


def parse_svg(data: bytes) -> ET.Element:
    return ET.fromstring(data.decode("utf-8"))


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def base_color(state: dict[str, object]) -> str:
    state_key = c2_module().canonical_block_state_string(state)
    digest = hashlib.sha256(state_key.encode("utf-8")).digest()
    rgb = tuple(64 + value % 128 for value in digest[:3])
    return "#" + "".join(f"{value:02x}" for value in rgb)


def make_review(
    build_spec: dict[str, object],
    build_ir: dict[str, object],
    views: dict[str, bytes],
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    c2 = c2_module()
    return {
        "schema_version": 1,
        "build_spec_sha256": c2.build_spec_fingerprint(build_spec),
        "build_ir_sha256": c2.fingerprint_build_ir(build_ir),
        "renderer_version": RENDERER_VERSION,
        "views": [
            {"id": view_id, "sha256": hashlib.sha256(views[view_id]).hexdigest()}
            for view_id in VIEW_IDS
        ],
        "reviewer": {"kind": "agent", "id": "c8-test-reviewer"},
        "decisions": copy.deepcopy(decisions),
    }


def decision(
    check_id: str,
    status: str,
    evidence_views: list[str],
    summary: str | None = None,
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "status": status,
        "evidence_views": evidence_views,
        "summary": summary or f"C8 test review for {check_id}: {status}",
    }


def matching_c7_report(build_spec: dict[str, object], build_ir: dict[str, object]):
    return c7_module().run_structural_qa(build_spec, build_ir)


def matching_c5_resolution(
    build_spec: dict[str, object],
    build_ir: dict[str, object],
    *,
    include_unresolved: bool = False,
) -> dict[str, object]:
    c2 = c2_module()
    state = copy.deepcopy(build_ir["palette"][0])
    candidate = {
        "block": state["name"],
        "namespace": state["name"].split(":", 1)[0],
        "authority": "runtime_confirmed",
        "safety": "ordinary",
        "state_candidates": [copy.deepcopy(state)],
        "selected_state": copy.deepcopy(state),
    }
    roles: list[dict[str, object]] = [
        {"role": "primary", "selected": candidate, "alternatives": []}
    ]
    if include_unresolved:
        unresolved = copy.deepcopy(candidate)
        unresolved["selected_state"] = None
        unresolved["state_candidates"] = [
            copy.deepcopy(state),
            {"name": state["name"], "properties": {"variant": "alternate"}},
        ]
        roles.append({"role": "unresolved", "selected": unresolved, "alternatives": []})
    return {
        "schema_version": 1,
        "registry_fingerprint": "1" * 64,
        "build_spec_sha256": c2.build_spec_fingerprint(build_spec),
        "request_sha256": "2" * 64,
        "roles": roles,
    }


class C8ContractTests(unittest.TestCase):
    def test_spec_plan_schema_and_workflow_exist(self) -> None:
        for path in (SPEC_PATH, PLAN_PATH, SCHEMA_PATH, WORKFLOW_PATH):
            self.assertTrue(path.is_file(), f"required C8 contract file is missing: {path}")

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(schema["properties"]["renderer_version"]["const"], RENDERER_VERSION)
        self.assertEqual(schema["properties"]["views"]["minItems"], 7)
        self.assertEqual(schema["properties"]["views"]["maxItems"], 7)
        self.assertEqual(schema["properties"]["checks"]["minItems"], 8)
        self.assertEqual(schema["properties"]["checks"]["maxItems"], 8)
        self.assertEqual(schema["$defs"]["check"]["properties"]["id"]["enum"], list(CHECK_ORDER))
        self.assertFalse(schema["properties"]["metrics"]["additionalProperties"])

        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", workflow)
        self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", workflow)
        self.assertIn("actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3", workflow)
        self.assertIn("python-version: '3.11'", workflow)
        self.assertIn("java-version: '21'", workflow)
        self.assertIn("--require-hashes --no-deps", workflow)
        self.assertIn("construction/tests/test_c8_visual_qa.py", workflow)
        self.assertIn("construction/tests/test_c7_architecture_qa.py", workflow)
        self.assertIn("construction/tests/test_c7_registry_authority.py", workflow)
        self.assertIn("construction/tests/test_c6_sponge_v3.py", workflow)
        self.assertIn("construction/tests/test_c5_modded_palette.py", workflow)
        self.assertIn("construction/tests/test_c4_modpack_registry.py", workflow)
        self.assertIn("construction/tests/test_c4_runtime_registry_probe.py", workflow)
        self.assertIn("construction/scripts/prepare_neoforge_registry_probe.py", workflow)
        self.assertIn("./gradlew test build --no-daemon", workflow)
        self.assertIn("construction/tests/test_c3_vanilla_golden.py", workflow)
        self.assertIn("construction/tests/test_c2_build_ir.py", workflow)
        self.assertIn("construction/tests/test_c0_foundation.py", workflow)
        self.assertIn("construction/scripts/validate_c0.py", workflow)
        self.assertIn("git diff --check HEAD^ --", workflow)

    def test_production_modules_exist(self) -> None:
        self.assertTrue(RENDERER_PATH.is_file(), "C8 preview renderer is not implemented")
        self.assertTrue(VISUAL_QA_PATH.is_file(), "C8 visual QA engine is not implemented")


@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")
class C8RendererTests(unittest.TestCase):
    def test_renderer_rejects_invalid_build_ir(self) -> None:
        module = renderer_module()
        with self.assertRaises(module.PreviewRenderError):
            module.render_canonical_views({"schema_version": 1})

    def test_fixed_view_ids_and_byte_determinism(self) -> None:
        spec = make_build_spec(size=(2, 2, 2))
        ir = make_ir(spec, [placement(0, 0, 0), placement(1, 1, 1)])
        first = render(ir)
        second = render(ir)
        self.assertEqual(tuple(first), VIEW_IDS)
        self.assertEqual(first, second)
        for data in first.values():
            self.assertIsInstance(data, bytes)
            self.assertTrue(data.endswith(b"\n"))

    def test_svg_metadata_binds_renderer_and_ir(self) -> None:
        spec = make_build_spec(size=(1, 1, 1))
        ir = make_ir(spec, [placement(0, 0, 0)])
        expected_sha = c2_module().fingerprint_build_ir(ir)
        for view_id, data in render(ir).items():
            root = parse_svg(data)
            self.assertEqual(root.attrib["data-renderer-version"], RENDERER_VERSION, view_id)
            self.assertEqual(root.attrib["data-build-ir-sha256"], expected_sha, view_id)

    def test_front_back_occlusion_and_orientation(self) -> None:
        spec = make_build_spec(size=(2, 1, 2))
        ir = make_ir(
            spec,
            [
                placement(0, 0, 0, "minecraft:stone"),
                placement(0, 0, 1, "minecraft:oak_planks"),
                placement(1, 0, 0, "minecraft:bricks"),
            ],
        )
        palette = {state["name"]: state for state in ir["palette"]}
        views = render(ir)
        front_rects = [child for child in parse_svg(views["front"]) if local_name(child.tag) == "rect"]
        back_rects = [child for child in parse_svg(views["back"]) if local_name(child.tag) == "rect"]
        front_by_x = {int(item.attrib["x"]): item.attrib["fill"] for item in front_rects}
        back_by_x = {int(item.attrib["x"]): item.attrib["fill"] for item in back_rects}
        self.assertEqual(front_by_x[16], base_color(palette["minecraft:stone"]))
        self.assertEqual(front_by_x[32], base_color(palette["minecraft:bricks"]))
        self.assertEqual(back_by_x[32], base_color(palette["minecraft:oak_planks"]))
        self.assertEqual(back_by_x[16], base_color(palette["minecraft:bricks"]))

    def test_left_right_occlusion(self) -> None:
        spec = make_build_spec(size=(2, 1, 2))
        ir = make_ir(
            spec,
            [
                placement(0, 0, 0, "minecraft:stone"),
                placement(1, 0, 0, "minecraft:oak_planks"),
                placement(0, 0, 1, "minecraft:bricks"),
            ],
        )
        palette = {state["name"]: state for state in ir["palette"]}
        views = render(ir)
        left_rects = [child for child in parse_svg(views["left"]) if local_name(child.tag) == "rect"]
        right_rects = [child for child in parse_svg(views["right"]) if local_name(child.tag) == "rect"]
        left_by_x = {int(item.attrib["x"]): item.attrib["fill"] for item in left_rects}
        right_by_x = {int(item.attrib["x"]): item.attrib["fill"] for item in right_rects}
        self.assertEqual(left_by_x[32], base_color(palette["minecraft:stone"]))
        self.assertEqual(left_by_x[16], base_color(palette["minecraft:bricks"]))
        self.assertEqual(right_by_x[16], base_color(palette["minecraft:oak_planks"]))
        self.assertEqual(right_by_x[32], base_color(palette["minecraft:bricks"]))

    def test_top_occlusion(self) -> None:
        spec = make_build_spec(size=(1, 2, 1))
        ir = make_ir(
            spec,
            [placement(0, 0, 0, "minecraft:stone"), placement(0, 1, 0, "minecraft:gold_block")],
        )
        palette = {state["name"]: state for state in ir["palette"]}
        rects = [child for child in parse_svg(render(ir)["top"]) if local_name(child.tag) == "rect"]
        self.assertEqual(len(rects), 1)
        self.assertEqual(rects[0].attrib["fill"], base_color(palette["minecraft:gold_block"]))

    def test_orthographic_canvas_and_cell_placement(self) -> None:
        spec = make_build_spec(size=(3, 2, 4))
        ir = make_ir(spec, [placement(2, 1, 3)])
        views = render(ir)
        expected = {
            "front": (80, 64),
            "back": (80, 64),
            "left": (96, 64),
            "right": (96, 64),
            "top": (80, 96),
        }
        for view_id, dimensions in expected.items():
            root = parse_svg(views[view_id])
            self.assertEqual((int(root.attrib["width"]), int(root.attrib["height"])), dimensions)
        front_rect = next(child for child in parse_svg(views["front"]) if local_name(child.tag) == "rect")
        self.assertEqual((int(front_rect.attrib["x"]), int(front_rect.attrib["y"])), (48, 16))
        top_rect = next(child for child in parse_svg(views["top"]) if local_name(child.tag) == "rect")
        self.assertEqual((int(top_rect.attrib["x"]), int(top_rect.attrib["y"])), (48, 16))

    def test_isometric_geometry_faces_order_and_canvas(self) -> None:
        spec = make_build_spec(size=(1, 1, 1))
        ir = make_ir(spec, [placement(0, 0, 0)])
        root = parse_svg(render(ir)["isometric"])
        self.assertEqual((int(root.attrib["width"]), int(root.attrib["height"])), (48, 48))
        polygons = [child for child in root if local_name(child.tag) == "polygon"]
        self.assertEqual(len(polygons), 3)
        self.assertEqual(
            [item.attrib["points"] for item in polygons],
            [
                "32,20 24,24 24,32 32,28",
                "16,20 24,24 24,32 16,28",
                "24,16 32,20 24,24 16,20",
            ],
        )

        stacked = make_ir(
            make_build_spec(size=(1, 2, 1), seed=8009),
            [placement(0, 0, 0), placement(0, 1, 0)],
        )
        stacked_polygons = [
            child for child in parse_svg(render(stacked)["isometric"]) if local_name(child.tag) == "polygon"
        ]
        self.assertEqual(len(stacked_polygons), 5)

    def test_layers_include_empty_levels_and_exact_layout(self) -> None:
        spec = make_build_spec(size=(2, 3, 1))
        ir = make_ir(spec, [placement(0, 0, 0), placement(1, 2, 0)])
        root = parse_svg(render(ir)["layers"])
        self.assertEqual((int(root.attrib["width"]), int(root.attrib["height"])), (56, 40))
        groups = [child for child in root if local_name(child.tag) == "g"]
        self.assertEqual([group.attrib["data-y"] for group in groups], ["0", "1", "2"])
        self.assertEqual(len([c for c in groups[0] if local_name(c.tag) == "rect"]), 1)
        self.assertEqual(len([c for c in groups[1] if local_name(c.tag) == "rect"]), 0)
        self.assertEqual(len([c for c in groups[2] if local_name(c.tag) == "rect"]), 1)

    def test_digest_pseudo_colors(self) -> None:
        spec = make_build_spec(size=(1, 1, 1))
        ir = make_ir(spec, [placement(0, 0, 0, "minecraft:deepslate_tiles")])
        state = ir["palette"][0]
        expected = base_color(state)
        front_rect = next(child for child in parse_svg(render(ir)["front"]) if local_name(child.tag) == "rect")
        self.assertEqual(front_rect.attrib["fill"], expected)

    def test_svg_safety_contract(self) -> None:
        spec = make_build_spec(size=(1, 1, 1))
        ir = make_ir(spec, [placement(0, 0, 0)])
        views = render(ir)
        forbidden = (b"<script", b"foreignObject", b"onload=", b"href=")
        for data in views.values():
            self.assertIn(b'xmlns="http://www.w3.org/2000/svg"', data)
            for token in forbidden:
                self.assertNotIn(token, data)

        unsafe = dict(views)
        unsafe["front"] = unsafe["front"].replace(b"<svg ", b'<svg onload="evil" ', 1)
        module = visual_module()
        with self.assertRaises(module.VisualQAError):
            module.run_visual_qa(spec, ir, unsafe)


@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")
class C8MetricsTests(unittest.TestCase):
    def test_occupancy_metrics_empty_and_nonempty(self) -> None:
        empty_spec = make_build_spec(size=(2, 2, 2))
        empty = run_visual(empty_spec, make_ir(empty_spec, []))["metrics"]["occupancy"]
        self.assertEqual(empty["occupied_block_count"], 0)
        self.assertIsNone(empty["occupied_min"])
        self.assertIsNone(empty["occupied_max"])
        self.assertEqual(empty["occupied_extent"], {"x": 0, "y": 0, "z": 0})
        self.assertEqual(empty["occupied_bounding_box_volume"], 0)
        self.assertEqual(empty["occupied_density"], {"numerator": 0, "denominator": 1})
        self.assertEqual(empty["full_bounds_density"], {"numerator": 0, "denominator": 1})

        spec = make_build_spec(size=(3, 2, 2), seed=8010)
        ir = make_ir(spec, [placement(0, 0, 0), placement(2, 0, 1)])
        occupied = run_visual(spec, ir)["metrics"]["occupancy"]
        self.assertEqual(occupied["occupied_min"], {"x": 0, "y": 0, "z": 0})
        self.assertEqual(occupied["occupied_max"], {"x": 2, "y": 0, "z": 1})
        self.assertEqual(occupied["occupied_extent"], {"x": 3, "y": 1, "z": 2})
        self.assertEqual(occupied["occupied_bounding_box_volume"], 6)
        self.assertEqual(occupied["occupied_density"], {"numerator": 1, "denominator": 3})
        self.assertEqual(occupied["full_bounds_density"], {"numerator": 1, "denominator": 6})

    def test_projection_metrics_asymmetric_fixture(self) -> None:
        spec = make_build_spec(size=(3, 2, 2))
        ir = make_ir(spec, [placement(0, 0, 0), placement(2, 0, 1)])
        front = projection(run_visual(spec, ir), "front")
        self.assertEqual(front["occupied_cell_count"], 2)
        self.assertEqual((front["bounding_width"], front["bounding_height"]), (3, 1))
        self.assertEqual(front["occupancy_ratio"], {"numerator": 2, "denominator": 3})
        self.assertEqual(front["component_count"], 2)
        self.assertEqual(front["dominant_component_size"], 1)
        self.assertEqual(front["aspect_ratio"], {"numerator": 3, "denominator": 1})

    def test_palette_distribution_metrics(self) -> None:
        spec = make_build_spec(size=(3, 1, 1))
        ir = make_ir(
            spec,
            [
                placement(0, 0, 0, "minecraft:stone"),
                placement(1, 0, 0, "minecraft:stone"),
                placement(2, 0, 0, "minecraft:oak_planks"),
            ],
        )
        metrics = run_visual(spec, ir)["metrics"]["palette_distribution"]
        by_state = {item["state"]: item for item in metrics}
        self.assertEqual(by_state["minecraft:stone"]["occupied_block_count"], 2)
        self.assertEqual(by_state["minecraft:stone"]["fraction"], {"numerator": 2, "denominator": 3})
        self.assertEqual(by_state["minecraft:oak_planks"]["occupied_block_count"], 1)
        self.assertEqual(by_state["minecraft:oak_planks"]["fraction"], {"numerator": 1, "denominator": 3})

    def test_c5_role_labels_match_selected_states_only(self) -> None:
        spec = make_build_spec(size=(1, 1, 1))
        ir = make_ir(spec, [placement(0, 0, 0)])
        c5 = matching_c5_resolution(spec, ir, include_unresolved=True)
        metrics = run_visual(spec, ir, palette_resolution=c5)["metrics"]["palette_distribution"]
        self.assertEqual(metrics[0]["roles"], ["primary"])

    def test_repetition_metrics_without_quality_threshold(self) -> None:
        spec = make_build_spec(size=(2, 3, 1))
        blocks = [placement(x, y, 0) for y in range(3) for x in range(2)]
        report = run_visual(spec, make_ir(spec, blocks))
        front = repetition_metric(report, "front")
        self.assertEqual(front["distinct_row_signature_count"], 1)
        self.assertEqual(front["repeated_row_signature_count"], 2)
        self.assertEqual(front["longest_adjacent_identical_row_run"], 3)
        self.assertEqual(front["repeated_row_ratio"], {"numerator": 2, "denominator": 3})
        self.assertEqual(check(report, "repetition")["status"], "DEFERRED")

    def test_facade_depth_metrics_flat_and_stepped(self) -> None:
        flat_spec = make_build_spec(size=(2, 2, 2))
        flat_ir = make_ir(flat_spec, [placement(0, 0, 0), placement(1, 0, 0)])
        flat = facade_metric(run_visual(flat_spec, flat_ir), "front")
        self.assertEqual(flat["distinct_visible_depth_count"], 1)
        self.assertEqual(flat["adjacent_depth_transition_count"], 0)
        self.assertEqual(flat["transition_ratio"], {"numerator": 0, "denominator": 1})

        stepped_spec = make_build_spec(size=(2, 2, 2), seed=8011)
        stepped_ir = make_ir(stepped_spec, [placement(0, 0, 0), placement(1, 0, 1)])
        stepped = facade_metric(run_visual(stepped_spec, stepped_ir), "front")
        self.assertEqual(stepped["distinct_visible_depth_count"], 2)
        self.assertEqual(stepped["depth_range"], 1)
        self.assertEqual(stepped["adjacent_visible_pair_count"], 1)
        self.assertEqual(stepped["adjacent_depth_transition_count"], 1)
        self.assertEqual(stepped["transition_ratio"], {"numerator": 1, "denominator": 1})

    def test_layer_density_includes_empty_levels(self) -> None:
        spec = make_build_spec(size=(2, 3, 2))
        ir = make_ir(spec, [placement(0, 0, 0), placement(1, 0, 0), placement(0, 2, 0)])
        layers = run_visual(spec, ir)["metrics"]["layers"]
        self.assertEqual(layers["level_count"], 3)
        self.assertEqual([item["occupied_cells"] for item in layers["levels"]], [2, 0, 1])
        self.assertEqual([item["density"] for item in layers["levels"]], [
            {"numerator": 1, "denominator": 2},
            {"numerator": 0, "denominator": 1},
            {"numerator": 1, "denominator": 4},
        ])
        self.assertEqual(layers["minimum_occupied_cells"], 0)
        self.assertEqual(layers["maximum_occupied_cells"], 2)
        self.assertEqual(layers["median_middle_pair"], [1, 1])


@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")
class C8EvidenceAndReportTests(unittest.TestCase):
    def _fixture(self):
        spec = make_build_spec(size=(2, 2, 2))
        ir = make_ir(spec, [placement(0, 0, 0), placement(1, 0, 0)])
        views = render(ir)
        return spec, ir, views

    def test_missing_review_keeps_six_subjective_checks_deferred(self) -> None:
        spec, ir, views = self._fixture()
        report = visual_module().run_visual_qa(spec, ir, views)
        self.assertEqual(check(report, "canonical_preview_integrity")["status"], "PASS")
        for check_id in SUBJECTIVE_CHECKS:
            self.assertEqual(check(report, check_id)["status"], "DEFERRED")
            self.assertTrue(check(report, check_id)["required"])
        self.assertEqual(report["overall_status"], "DEFERRED")
        self.assertEqual(check(report, "runtime_visual_fidelity")["status"], "DEFERRED")
        self.assertFalse(check(report, "runtime_visual_fidelity")["required"])

    def test_valid_review_can_pass_one_subjective_check(self) -> None:
        spec, ir, views = self._fixture()
        review = make_review(spec, ir, views, [decision("silhouette_readability", "PASS", ["front", "isometric"])])
        report = visual_module().run_visual_qa(spec, ir, views, review_evidence=review)
        self.assertEqual(check(report, "silhouette_readability")["status"], "PASS")
        self.assertEqual(check(report, "proportion")["status"], "DEFERRED")
        self.assertEqual(report["overall_status"], "DEFERRED")

    def test_valid_review_can_fail_one_subjective_check(self) -> None:
        spec, ir, views = self._fixture()
        review = make_review(spec, ir, views, [decision("facade_readability", "FAIL", ["front"])])
        report = visual_module().run_visual_qa(spec, ir, views, review_evidence=review)
        self.assertEqual(check(report, "facade_readability")["status"], "FAIL")
        self.assertEqual(report["overall_status"], "FAIL")

    def test_partial_review_keeps_overall_deferred_without_fail(self) -> None:
        spec, ir, views = self._fixture()
        review = make_review(
            spec,
            ir,
            views,
            [
                decision("silhouette_readability", "PASS", ["front"]),
                decision("proportion", "PASS", ["isometric"]),
            ],
        )
        report = visual_module().run_visual_qa(spec, ir, views, review_evidence=review)
        self.assertEqual(report["overall_status"], "DEFERRED")
        self.assertEqual(check(report, "silhouette_readability")["status"], "PASS")
        self.assertEqual(check(report, "material_hierarchy")["status"], "DEFERRED")

    def test_stale_view_hash_fails_closed(self) -> None:
        spec, ir, views = self._fixture()
        review = make_review(spec, ir, views, [decision("silhouette_readability", "PASS", ["front"])])
        review["views"][0]["sha256"] = "0" * 64
        module = visual_module()
        with self.assertRaises(module.VisualQAError):
            module.run_visual_qa(spec, ir, views, review_evidence=review)

    def test_wrong_build_fingerprints_fail_closed(self) -> None:
        spec, ir, views = self._fixture()
        wrong_spec = copy.deepcopy(spec)
        wrong_spec["identity"]["description"] = "changed after C2 generation"
        module = visual_module()
        with self.assertRaises(module.VisualQAError):
            module.run_visual_qa(wrong_spec, ir, views)

        review = make_review(spec, ir, views, [])
        review["build_ir_sha256"] = "f" * 64
        with self.assertRaises(module.VisualQAError):
            module.run_visual_qa(spec, ir, views, review_evidence=review)

    def test_review_view_records_fail_closed(self) -> None:
        spec, ir, views = self._fixture()
        module = visual_module()
        base = make_review(spec, ir, views, [])
        variants: list[dict[str, object]] = []

        missing = copy.deepcopy(base)
        missing["views"] = missing["views"][:-1]
        variants.append(missing)

        duplicate = copy.deepcopy(base)
        duplicate["views"][1] = copy.deepcopy(duplicate["views"][0])
        variants.append(duplicate)

        unknown = copy.deepcopy(base)
        unknown["views"][0]["id"] = "unknown"
        variants.append(unknown)

        out_of_order = copy.deepcopy(base)
        out_of_order["views"][0], out_of_order["views"][1] = out_of_order["views"][1], out_of_order["views"][0]
        variants.append(out_of_order)

        for candidate in variants:
            with self.subTest(candidate=candidate["views"]):
                with self.assertRaises(module.VisualQAError):
                    module.run_visual_qa(spec, ir, views, review_evidence=candidate)

    def test_review_decisions_fail_closed(self) -> None:
        spec, ir, views = self._fixture()
        module = visual_module()
        duplicate = make_review(
            spec,
            ir,
            views,
            [
                decision("proportion", "PASS", ["front"]),
                decision("proportion", "FAIL", ["back"]),
            ],
        )
        unknown = make_review(spec, ir, views, [decision("unknown_check", "PASS", ["front"])])
        disallowed_view = make_review(spec, ir, views, [decision("facade_readability", "PASS", ["layers"])])
        for candidate in (duplicate, unknown, disallowed_view):
            with self.subTest(decisions=candidate["decisions"]):
                with self.assertRaises(module.VisualQAError):
                    module.run_visual_qa(spec, ir, views, review_evidence=candidate)

    def test_runtime_visual_fidelity_cannot_be_resolved(self) -> None:
        spec, ir, views = self._fixture()
        review = make_review(spec, ir, views, [decision("runtime_visual_fidelity", "PASS", ["isometric"])])
        module = visual_module()
        with self.assertRaises(module.VisualQAError):
            module.run_visual_qa(spec, ir, views, review_evidence=review)

    def test_matching_c7_is_provenance_only(self) -> None:
        spec, ir, views = self._fixture()
        c7 = matching_c7_report(spec, ir)
        report = visual_module().run_visual_qa(spec, ir, views, structural_report=c7)
        self.assertEqual(report["structural_report_sha256"], hashlib.sha256(canonical_json_bytes(c7)).hexdigest())
        for check_id in SUBJECTIVE_CHECKS:
            self.assertEqual(check(report, check_id)["status"], "DEFERRED")

    def test_mismatched_c7_fails_closed(self) -> None:
        spec, ir, views = self._fixture()
        c7 = matching_c7_report(spec, ir)
        c7["build_ir_sha256"] = "f" * 64
        module = visual_module()
        with self.assertRaises(module.VisualQAError):
            module.run_visual_qa(spec, ir, views, structural_report=c7)

    def test_matching_c5_is_provenance_and_labels_only(self) -> None:
        spec, ir, views = self._fixture()
        c5 = matching_c5_resolution(spec, ir)
        report = visual_module().run_visual_qa(spec, ir, views, palette_resolution=c5)
        self.assertEqual(report["palette_resolution_sha256"], hashlib.sha256(canonical_json_bytes(c5)).hexdigest())
        self.assertEqual(report["metrics"]["palette_distribution"][0]["roles"], ["primary"])
        self.assertEqual(check(report, "material_hierarchy")["status"], "DEFERRED")

    def test_mismatched_c5_fails_closed(self) -> None:
        spec, ir, views = self._fixture()
        c5 = matching_c5_resolution(spec, ir)
        c5["build_spec_sha256"] = "f" * 64
        module = visual_module()
        with self.assertRaises(module.VisualQAError):
            module.run_visual_qa(spec, ir, views, palette_resolution=c5)

    def test_report_content_sha_detects_tampering(self) -> None:
        spec, ir, views = self._fixture()
        module = visual_module()
        report = module.run_visual_qa(spec, ir, views)
        module.validate_visual_qa_report(report)
        tampered = copy.deepcopy(report)
        tampered["metrics"]["occupancy"]["occupied_block_count"] += 1
        with self.assertRaises(module.VisualQAError):
            module.validate_visual_qa_report(tampered)

    def test_report_validator_and_schema_contract(self) -> None:
        spec, ir, views = self._fixture()
        module = visual_module()
        report = module.run_visual_qa(spec, ir, views)
        module.validate_visual_qa_report(report)

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(report), set(schema["required"]))
        self.assertEqual(tuple(item["id"] for item in report["views"]), VIEW_IDS)
        self.assertEqual(tuple(item["id"] for item in report["checks"]), CHECK_ORDER)
        self.assertIn(report["overall_status"], schema["properties"]["overall_status"]["enum"])
        self.assertEqual(report["renderer_version"], schema["properties"]["renderer_version"]["const"])

    def test_require_determinism_repeats_views_and_report_bytes(self) -> None:
        spec, ir, _ = self._fixture()
        first_views = render(ir)
        second_views = render(ir)
        self.assertEqual(first_views, second_views)
        module = visual_module()
        first = module.run_visual_qa(spec, ir, first_views)
        second = module.run_visual_qa(spec, ir, second_views)
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))


@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")
class C8GoldenTests(unittest.TestCase):
    def test_vanilla_golden_matches_checked_in_c8_artifacts(self) -> None:
        build_spec = json.loads((GOLDEN / "build-spec.json").read_text(encoding="utf-8"))
        build_ir = json.loads((GOLDEN / "expected-build-ir.json").read_text(encoding="utf-8"))
        generated = render(build_ir)

        self.assertTrue(C8_GOLDEN.is_dir(), "C8 Golden evidence directory is not materialized")
        checked_in = {view_id: (C8_GOLDEN / f"{view_id}.svg").read_bytes() for view_id in VIEW_IDS}
        self.assertEqual(generated, checked_in)

        review = json.loads((C8_GOLDEN / "review-evidence.json").read_text(encoding="utf-8"))
        module = visual_module()
        report = module.run_visual_qa(build_spec, build_ir, checked_in, review_evidence=review)
        expected = (C8_GOLDEN / "expected-visual-qa-report.json").read_bytes()
        actual = canonical_json_bytes(report) + b"\n"
        self.assertEqual(actual, expected)
        self.assertEqual(check(report, "runtime_visual_fidelity")["status"], "DEFERRED")
        module.validate_visual_qa_report(report)


if __name__ == "__main__":
    unittest.main()
