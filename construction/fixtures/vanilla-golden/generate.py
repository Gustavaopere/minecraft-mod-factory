from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMATICA_SCRIPTS = ROOT / "construction" / "upstream" / "snapshots" / "schematica" / "scripts"
BUILD_SPEC_PATH = Path(__file__).with_name("build-spec.json")

SCHEMATICA_PIN = "0c88770005e7bbd7246997c81e810ba935c8e4cf"
PRODUCER = "schematica"
PRODUCER_VERSION = SCHEMATICA_PIN

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCHEMATICA_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCHEMATICA_SCRIPTS))

from construction.core.build_ir import canonicalize_build_ir
from schematica.session.session import Session
from schematica.shapes.primitives import Box


def _state_properties(block) -> dict[str, str]:
    properties: dict[str, str] = {}
    for key, value in block.states:
        if isinstance(value, bool):
            properties[key] = "true" if value else "false"
        else:
            properties[key] = str(value)
    return properties


def _placements_from_session(session: Session) -> list[dict[str, object]]:
    placements: list[dict[str, object]] = []
    size_x, size_y, size_z = session.grid.shape
    for x in range(size_x):
        for y in range(size_y):
            for z in range(size_z):
                block = session.grid.get(x, y, z)
                if block.name == "minecraft:air":
                    continue
                placements.append(
                    {
                        "x": x,
                        "y": y,
                        "z": z,
                        "block_state": {
                            "name": block.name,
                            "properties": _state_properties(block),
                        },
                    }
                )
    return placements


def generate_golden() -> dict[str, object]:
    build_spec = json.loads(BUILD_SPEC_PATH.read_text(encoding="utf-8"))
    session = Session.new((7, 5, 7), version="1.21.1")

    session.add(Box(0, 0, 0, 6, 0, 6), "minecraft:stone_bricks")
    session.add(Box(0, 4, 0, 6, 4, 6), "minecraft:oak_planks")
    for x, z in ((0, 0), (0, 6), (6, 0), (6, 6)):
        session.add(Box(x, 1, z, x, 3, z), "minecraft:oak_log")

    return canonicalize_build_ir(
        build_spec,
        _placements_from_session(session),
        producer=PRODUCER,
        producer_version=PRODUCER_VERSION,
    )


if __name__ == "__main__":
    print(json.dumps(generate_golden(), indent=2, ensure_ascii=False))
