from __future__ import annotations

from typing import Any

SCHEMATIC_VERSION = 3
MINECRAFT_DATA_VERSION = 3955


class SpongeV3Error(ValueError):
    """Raised when a Sponge Schematic v3 payload cannot be exported safely."""


def export_sponge_v3(
    build_ir: dict[str, Any],
    *,
    required_mods=(),
    block_entities=(),
) -> bytes:
    raise SpongeV3Error("C6 Sponge v3 exporter not implemented yet")


def validate_sponge_v3(payload: bytes) -> list[str]:
    return ["C6 Sponge v3 validator not implemented yet"]
