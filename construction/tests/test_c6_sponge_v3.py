from __future__ import annotations

import copy
import gzip
import importlib.util
import io
import unittest
from pathlib import Path

import nbtlib
from nbtlib import Compound, Int, String

ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION = ROOT / "construction"
MODULE_PATH = CONSTRUCTION / "core" / "sponge_v3.py"
C2_MODULE_PATH = CONSTRUCTION / "core" / "build_ir.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "factory-construction-c6-sponge-v3.yml"
IMPLEMENTATION_READY = MODULE_PATH.is_file()

MINECRAFT_1_21_1_DATA_VERSION = 3955


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_module():
    return load_path(MODULE_PATH, "construction_c6_sponge_v3")


def c2_module():
    return load_path(C2_MODULE_PATH, "construction_c2_for_c6")


def build_ir(
    *,
    size: tuple[int, int, int] = (2, 2, 2),
    placements: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if placements is None:
        placements = [
            {
                "x": 1,
                "y": 0,
                "z": 0,
                "block_state": {
                    "name": "minecraft:stone_bricks",
                    "properties": {},
                },
            },
            {
                "x": 0,
                "y": 1,
                "z": 1,
                "block_state": {
                    "name": "minecraft:oak_log",
                    "properties": {"axis": "y"},
                },
            },
        ]
    build_spec = {
        "schema_version": 1,
        "identity": {"name": "c6-test", "seed": 6006},
        "target": {
            "minecraft_version": "1.21.1",
            "loader": "neoforge",
            "modpack_snapshot": "physical-modlist-test",
        },
        "geometry": {
            "max_size": {"x": size[0], "y": size[1], "z": size[2]},
            "terrain_policy": "flat",
            "architectural_brief": "C6 Sponge v3 contract fixture",
            "required_spaces": [],
        },
        "palette": {
            "allow_modded": True,
            "allowed_namespaces": ["minecraft", "alpha", "test"],
            "forbidden_blocks": [],
        },
        "qa": {"require_determinism": True},
        "outputs": {"formats": ["sponge_v3"]},
    }
    return c2_module().canonicalize_build_ir(
        build_spec,
        placements,
        producer="construction-c6-test",
        producer_version="1",
    )


def parse_payload(payload: bytes) -> tuple[nbtlib.File, Compound]:
    if not payload.startswith(b"\x1f\x8b"):
        raise AssertionError("Sponge v3 payload must be GZip-compressed NBT")
    raw = gzip.decompress(payload)
    parsed = nbtlib.File.parse(io.BytesIO(raw))
    schematic = parsed.get("Schematic")
    if not isinstance(schematic, Compound):
        raise AssertionError("missing Schematic root compound")
    return parsed, schematic


def repack(parsed: nbtlib.File) -> bytes:
    buffer = io.BytesIO()
    parsed.write(buffer, byteorder="big")
    return gzip.compress(buffer.getvalue(), mtime=0)


def decode_varints(data) -> list[int]:
    decoded: list[int] = []
    value = 0
    shift = 0
    for raw_byte in data:
        byte = int(raw_byte) & 0xFF
        value |= (byte & 0x7F) << shift
        if byte & 0x80:
            shift += 7
            if shift >= 35:
                raise AssertionError("varint exceeds 5 bytes")
            continue
        decoded.append(value)
        value = 0
        shift = 0
    if shift:
        raise AssertionError("truncated varint")
    return decoded


class ConstructionC6SpongeV3Test(unittest.TestCase):
    def test_required_c6_production_file_exists(self) -> None:
        self.assertTrue(
            MODULE_PATH.is_file(),
            "C6 production module is required at construction/core/sponge_v3.py",
        )

    def test_c6_workflow_is_pinned_read_only_and_runs_regressions(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn(
            "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            workflow,
        )
        self.assertIn(
            "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
            workflow,
        )
        self.assertIn(
            "construction/upstream/harness/schematica-test-lock.txt",
            workflow,
        )
        for test_path in (
            "construction/tests/test_c6_sponge_v3.py",
            "construction/tests/test_c5_modded_palette.py",
            "construction/tests/test_c4_modpack_registry.py",
            "construction/tests/test_c3_vanilla_golden.py",
            "construction/tests/test_c2_build_ir.py",
            "construction/tests/test_c0_foundation.py",
        ):
            self.assertIn(test_path, workflow)
        self.assertIn("construction/scripts/validate_c0.py", workflow)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C6 implementation not present yet")
    def test_export_is_deterministic_gzip_sponge_v3_for_minecraft_1_21_1(self) -> None:
        module = load_module()
        source = build_ir()
        first = module.export_sponge_v3(source)
        second = module.export_sponge_v3(source)

        self.assertEqual(first, second)
        self.assertEqual(first[4:8], b"\x00\x00\x00\x00")
        _, schematic = parse_payload(first)
        self.assertEqual(int(schematic["Version"]), 3)
        self.assertEqual(int(schematic["DataVersion"]), MINECRAFT_1_21_1_DATA_VERSION)
        self.assertEqual(int(schematic["Width"]) & 0xFFFF, 2)
        self.assertEqual(int(schematic["Height"]) & 0xFFFF, 2)
        self.assertEqual(int(schematic["Length"]) & 0xFFFF, 2)
        self.assertEqual([int(value) for value in schematic["Offset"]], [0, 0, 0])

    @unittest.skipUnless(IMPLEMENTATION_READY, "C6 implementation not present yet")
    def test_palette_states_sparse_air_and_official_block_index_order_are_preserved(self) -> None:
        module = load_module()
        payload = module.export_sponge_v3(build_ir())
        _, schematic = parse_payload(payload)

        palette = schematic["Blocks"]["Palette"]
        self.assertEqual(int(palette["minecraft:air"]), 0)
        self.assertIn("minecraft:oak_log[axis=y]", palette)
        self.assertIn("minecraft:stone_bricks", palette)

        indices = decode_varints(schematic["Blocks"]["Data"])
        self.assertEqual(len(indices), 8)
        expected = [0] * 8
        expected[1] = int(palette["minecraft:stone_bricks"])
        expected[6] = int(palette["minecraft:oak_log[axis=y]"])
        self.assertEqual(indices, expected)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C6 implementation not present yet")
    def test_state_properties_are_serialized_in_c2_canonical_order(self) -> None:
        module = load_module()
        source = build_ir(
            size=(1, 1, 1),
            placements=[
                {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "block_state": {
                        "name": "test:ordered_state",
                        "properties": {
                            "waterlogged": "false",
                            "facing": "north",
                        },
                    },
                }
            ],
        )
        _, schematic = parse_payload(module.export_sponge_v3(source))
        self.assertIn(
            "test:ordered_state[facing=north,waterlogged=false]",
            schematic["Blocks"]["Palette"],
        )

    @unittest.skipUnless(IMPLEMENTATION_READY, "C6 implementation not present yet")
    def test_palette_data_uses_varints_for_indices_above_127(self) -> None:
        module = load_module()
        placements: list[dict[str, object]] = []
        for x in range(130):
            placements.append(
                {
                    "x": x,
                    "y": 0,
                    "z": 0,
                    "block_state": {
                        "name": f"test:block_{x:03d}",
                        "properties": {},
                    },
                }
            )
        source = build_ir(size=(130, 1, 1), placements=placements)
        _, schematic = parse_payload(module.export_sponge_v3(source))
        palette = schematic["Blocks"]["Palette"]
        indices = decode_varints(schematic["Blocks"]["Data"])

        self.assertEqual(len(indices), 130)
        self.assertGreaterEqual(max(indices), 128)
        self.assertEqual(len(set(indices)), 130)
        self.assertEqual(len(palette), 131)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C6 implementation not present yet")
    def test_required_mods_and_controlled_block_entities_are_preserved(self) -> None:
        module = load_module()
        source = build_ir(
            size=(2, 1, 1),
            placements=[
                {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "block_state": {
                        "name": "alpha:test_block_entity",
                        "properties": {"facing": "north"},
                    },
                }
            ],
        )
        entity_data = Compound(
            {
                "Energy": Int(42),
                "CustomName": String("Factory C6"),
            }
        )
        payload = module.export_sponge_v3(
            source,
            required_mods=("alpha", "beta"),
            block_entities=(
                {
                    "id": "alpha:test_block_entity",
                    "pos": (0, 0, 0),
                    "data": entity_data,
                },
            ),
        )
        _, schematic = parse_payload(payload)

        required_mods = [str(value) for value in schematic["Metadata"]["RequiredMods"]]
        self.assertEqual(required_mods, ["alpha", "beta"])

        entities = schematic["Blocks"]["BlockEntities"]
        self.assertEqual(len(entities), 1)
        self.assertEqual(str(entities[0]["Id"]), "alpha:test_block_entity")
        self.assertEqual([int(value) for value in entities[0]["Pos"]], [0, 0, 0])
        self.assertEqual(int(entities[0]["Data"]["Energy"]), 42)
        self.assertIsInstance(entities[0]["Data"]["Energy"], Int)
        self.assertEqual(str(entities[0]["Data"]["CustomName"]), "Factory C6")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C6 implementation not present yet")
    def test_export_fails_closed_on_invalid_ir_and_invalid_block_entities(self) -> None:
        module = load_module()
        invalid_ir = copy.deepcopy(build_ir())
        invalid_ir["target"]["minecraft_version"] = "1.20.1"
        with self.assertRaises(module.SpongeV3Error):
            module.export_sponge_v3(invalid_ir)

        with self.assertRaises(module.SpongeV3Error):
            module.export_sponge_v3(
                build_ir(),
                block_entities=(
                    {
                        "id": "alpha:test_block_entity",
                        "pos": (2, 0, 0),
                        "data": Compound(),
                    },
                ),
            )

    @unittest.skipUnless(IMPLEMENTATION_READY, "C6 implementation not present yet")
    def test_validator_accepts_canonical_output_and_rejects_wrong_version(self) -> None:
        module = load_module()
        payload = module.export_sponge_v3(build_ir())
        self.assertEqual(module.validate_sponge_v3(payload), [])

        parsed, schematic = parse_payload(payload)
        schematic["Version"] = Int(2)
        invalid = repack(parsed)
        errors = module.validate_sponge_v3(invalid)
        self.assertTrue(any("Version" in error for error in errors), errors)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C6 implementation not present yet")
    def test_validator_rejects_wrong_data_version_and_non_gzip_payload(self) -> None:
        module = load_module()
        payload = module.export_sponge_v3(build_ir())
        parsed, schematic = parse_payload(payload)
        schematic["DataVersion"] = Int(3465)
        invalid = repack(parsed)

        errors = module.validate_sponge_v3(invalid)
        self.assertTrue(any("DataVersion" in error for error in errors), errors)
        self.assertTrue(module.validate_sponge_v3(b"not-gzip"))


if __name__ == "__main__":
    unittest.main()
