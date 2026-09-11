from __future__ import annotations

import gzip
import importlib.util
import io
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import nbtlib
from nbtlib import ByteArray, Compound, Int, IntArray, List as NbtList, Short, String

SCHEMATIC_VERSION = 3
MINECRAFT_DATA_VERSION = 3955
BLOCK_ID_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
NAMESPACE_RE = re.compile(r"^[a-z0-9_.-]+$")


class SpongeV3Error(ValueError):
    """Raised when a Sponge Schematic v3 payload cannot be exported safely."""


def _load_build_ir_module():
    path = Path(__file__).with_name("build_ir.py")
    spec = importlib.util.spec_from_file_location("construction_c2_for_c6_runtime", path)
    if spec is None or spec.loader is None:
        raise SpongeV3Error(f"unable to load canonical Build IR module at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BUILD_IR = _load_build_ir_module()


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _unsigned_short(value: int, label: str) -> Short:
    if not _is_int(value) or value < 1 or value > 0xFFFF:
        raise SpongeV3Error(f"{label} must fit Sponge's unsigned 16-bit dimension range")
    return Short(value if value <= 0x7FFF else value - 0x10000)


def _encode_varints(values: list[int]) -> ByteArray:
    encoded: list[int] = []
    for value in values:
        if not _is_int(value) or value < 0 or value > 0xFFFFFFFF:
            raise SpongeV3Error("palette index must be an unsigned 32-bit integer")
        current = value
        while True:
            byte = current & 0x7F
            current >>= 7
            if current:
                byte |= 0x80
            encoded.append(byte if byte < 0x80 else byte - 0x100)
            if not current:
                break
    return ByteArray(encoded)


def _decode_varints(data: ByteArray) -> tuple[list[int], str | None]:
    decoded: list[int] = []
    value = 0
    shift = 0
    for raw_byte in data:
        byte = int(raw_byte) & 0xFF
        value |= (byte & 0x7F) << shift
        if byte & 0x80:
            shift += 7
            if shift >= 35:
                return [], "Blocks.Data contains a varint longer than 5 bytes"
            continue
        decoded.append(value)
        value = 0
        shift = 0
    if shift:
        return [], "Blocks.Data ends with a truncated varint"
    return decoded, None


def _normalize_required_mods(required_mods: object) -> tuple[str, ...]:
    if isinstance(required_mods, (str, bytes)):
        raise SpongeV3Error("required_mods must be a sequence of namespace strings")
    try:
        values = tuple(required_mods)  # type: ignore[arg-type]
    except TypeError as exc:
        raise SpongeV3Error("required_mods must be iterable") from exc

    normalized: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str) or NAMESPACE_RE.fullmatch(value) is None:
            raise SpongeV3Error(f"required_mods[{index}] must be a valid namespace")
        normalized.append(value)
    if len(normalized) != len(set(normalized)):
        raise SpongeV3Error("required_mods must not contain duplicates")
    return tuple(normalized)


def _normalize_block_entities(
    block_entities: object,
    *,
    width: int,
    height: int,
    length: int,
) -> list[Compound]:
    if isinstance(block_entities, (str, bytes)):
        raise SpongeV3Error("block_entities must be a sequence")
    try:
        values = tuple(block_entities)  # type: ignore[arg-type]
    except TypeError as exc:
        raise SpongeV3Error("block_entities must be iterable") from exc

    result: list[Compound] = []
    seen_positions: set[tuple[int, int, int]] = set()
    for index, entity in enumerate(values):
        if not isinstance(entity, dict) or set(entity) != {"id", "pos", "data"}:
            raise SpongeV3Error(
                f"block_entities[{index}] must contain exactly id, pos and data"
            )
        entity_id = entity["id"]
        if not isinstance(entity_id, str) or BLOCK_ID_RE.fullmatch(entity_id) is None:
            raise SpongeV3Error(f"block_entities[{index}].id must be a namespaced id")
        pos = entity["pos"]
        if not isinstance(pos, (tuple, list)) or len(pos) != 3:
            raise SpongeV3Error(f"block_entities[{index}].pos must contain x, y and z")
        if not all(_is_int(axis) for axis in pos):
            raise SpongeV3Error(f"block_entities[{index}].pos values must be integers")
        position = (int(pos[0]), int(pos[1]), int(pos[2]))
        if not (
            0 <= position[0] < width
            and 0 <= position[1] < height
            and 0 <= position[2] < length
        ):
            raise SpongeV3Error(f"block_entities[{index}].pos is out of bounds")
        if position in seen_positions:
            raise SpongeV3Error("block_entities must not contain duplicate positions")
        seen_positions.add(position)

        data = entity["data"]
        if not isinstance(data, Compound):
            raise SpongeV3Error(f"block_entities[{index}].data must be an NBT Compound")
        result.append(
            Compound(
                {
                    "Pos": IntArray(position),
                    "Id": String(entity_id),
                    "Data": deepcopy(data),
                }
            )
        )
    return result


def _serialize_file(file: nbtlib.File) -> bytes:
    raw = io.BytesIO()
    file.write(raw, byteorder="big")
    compressed = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=compressed,
        mtime=0,
    ) as stream:
        stream.write(raw.getvalue())
    return compressed.getvalue()


def export_sponge_v3(
    build_ir: dict[str, Any],
    *,
    required_mods=(),
    block_entities=(),
) -> bytes:
    errors = _BUILD_IR.validate_build_ir(build_ir)
    if errors:
        raise SpongeV3Error("invalid Build IR: " + "; ".join(errors))

    size = build_ir["bounds"]["size"]
    width = size["x"]
    height = size["y"]
    length = size["z"]
    width_tag = _unsigned_short(width, "Width")
    height_tag = _unsigned_short(height, "Height")
    length_tag = _unsigned_short(length, "Length")

    required = _normalize_required_mods(required_mods)
    normalized_entities = _normalize_block_entities(
        block_entities,
        width=width,
        height=height,
        length=length,
    )

    palette_strings = [
        _BUILD_IR.canonical_block_state_string(state) for state in build_ir["palette"]
    ]
    sponge_palette: dict[str, Int] = {"minecraft:air": Int(0)}
    for index, state in enumerate(palette_strings, start=1):
        sponge_palette[state] = Int(index)

    volume = width * height * length
    indices = [0] * volume
    for block in build_ir["blocks"]:
        offset = block["x"] + block["z"] * width + block["y"] * width * length
        indices[offset] = block["palette_index"] + 1

    schematic = Compound(
        {
            "Version": Int(SCHEMATIC_VERSION),
            "DataVersion": Int(MINECRAFT_DATA_VERSION),
            "Metadata": Compound(
                {
                    "RequiredMods": NbtList[String]([String(value) for value in required]),
                }
            ),
            "Width": width_tag,
            "Height": height_tag,
            "Length": length_tag,
            "Offset": IntArray([0, 0, 0]),
            "Blocks": Compound(
                {
                    "Palette": Compound(sponge_palette),
                    "Data": _encode_varints(indices),
                    "BlockEntities": NbtList[Compound](normalized_entities),
                }
            ),
            "Entities": NbtList[Compound]([]),
        }
    )
    return _serialize_file(nbtlib.File({"Schematic": schematic}, root_name=""))


def _unsigned_short_value(value: object, label: str, errors: list[str]) -> int | None:
    if not isinstance(value, Short):
        errors.append(f"{label} must be an NBT Short")
        return None
    decoded = int(value) & 0xFFFF
    if decoded < 1:
        errors.append(f"{label} must be greater than zero")
        return None
    return decoded


def validate_sponge_v3(payload: bytes) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, (bytes, bytearray)):
        return ["payload must be bytes"]
    raw_payload = bytes(payload)
    if not raw_payload.startswith(b"\x1f\x8b"):
        return ["payload must be GZip-compressed NBT"]

    try:
        raw_nbt = gzip.decompress(raw_payload)
    except (gzip.BadGzipFile, EOFError, OSError) as exc:
        return [f"payload is not valid GZip data: {exc}"]

    try:
        parsed = nbtlib.File.parse(io.BytesIO(raw_nbt))
    except (EOFError, OSError, TypeError, ValueError, KeyError, IndexError) as exc:
        return [f"payload is not valid NBT: {exc}"]

    if parsed.root_name != "":
        errors.append("NBT root name must be empty")
    schematic = parsed.get("Schematic")
    if not isinstance(schematic, Compound):
        return errors + ["missing Schematic root compound"]

    version = schematic.get("Version")
    if not isinstance(version, Int) or int(version) != SCHEMATIC_VERSION:
        errors.append("Schematic.Version must be 3")
    data_version = schematic.get("DataVersion")
    if not isinstance(data_version, Int) or int(data_version) != MINECRAFT_DATA_VERSION:
        errors.append("Schematic.DataVersion must be 3955 for Minecraft 1.21.1")

    width = _unsigned_short_value(schematic.get("Width"), "Schematic.Width", errors)
    height = _unsigned_short_value(schematic.get("Height"), "Schematic.Height", errors)
    length = _unsigned_short_value(schematic.get("Length"), "Schematic.Length", errors)

    offset = schematic.get("Offset")
    if not isinstance(offset, IntArray) or len(offset) != 3:
        errors.append("Schematic.Offset must be an IntArray of length 3")

    metadata = schematic.get("Metadata")
    if metadata is not None and not isinstance(metadata, Compound):
        errors.append("Schematic.Metadata must be a Compound")
    elif isinstance(metadata, Compound) and "RequiredMods" in metadata:
        required_mods = metadata["RequiredMods"]
        if not isinstance(required_mods, NbtList):
            errors.append("Metadata.RequiredMods must be an NBT List")
        else:
            for index, value in enumerate(required_mods):
                if not isinstance(value, String) or NAMESPACE_RE.fullmatch(str(value)) is None:
                    errors.append(
                        f"Metadata.RequiredMods[{index}] must be a valid namespace string"
                    )

    blocks = schematic.get("Blocks")
    if not isinstance(blocks, Compound):
        return errors + ["Schematic.Blocks must be a Compound"]

    palette = blocks.get("Palette")
    palette_values: set[int] = set()
    if not isinstance(palette, Compound) or not palette:
        errors.append("Blocks.Palette must be a non-empty Compound")
    else:
        for state, palette_id in palette.items():
            if not isinstance(state, str) or not state:
                errors.append("Blocks.Palette contains an invalid block state key")
                continue
            if not isinstance(palette_id, Int) or int(palette_id) < 0:
                errors.append(f"Blocks.Palette[{state!r}] must be a non-negative Int")
                continue
            palette_values.add(int(palette_id))
        expected_values = set(range(len(palette)))
        if palette_values != expected_values:
            errors.append("Blocks.Palette ids must be unique and contiguous from zero")
        if palette.get("minecraft:air") != Int(0):
            errors.append("Blocks.Palette must map minecraft:air to id 0")

    data = blocks.get("Data")
    decoded_data: list[int] = []
    if not isinstance(data, ByteArray):
        errors.append("Blocks.Data must be an NBT ByteArray")
    else:
        decoded_data, varint_error = _decode_varints(data)
        if varint_error is not None:
            errors.append(varint_error)
        if width is not None and height is not None and length is not None:
            expected_volume = width * height * length
            if len(decoded_data) != expected_volume:
                errors.append(
                    f"Blocks.Data must contain exactly {expected_volume} palette indices"
                )
        if palette_values and any(value not in palette_values for value in decoded_data):
            errors.append("Blocks.Data references an unknown palette id")

    block_entities = blocks.get("BlockEntities")
    if block_entities is not None:
        if not isinstance(block_entities, NbtList):
            errors.append("Blocks.BlockEntities must be an NBT List")
        else:
            seen_positions: set[tuple[int, int, int]] = set()
            for index, entity in enumerate(block_entities):
                if not isinstance(entity, Compound):
                    errors.append(f"Blocks.BlockEntities[{index}] must be a Compound")
                    continue
                entity_id = entity.get("Id")
                if not isinstance(entity_id, String) or BLOCK_ID_RE.fullmatch(str(entity_id)) is None:
                    errors.append(f"Blocks.BlockEntities[{index}].Id is invalid")
                pos = entity.get("Pos")
                if not isinstance(pos, IntArray) or len(pos) != 3:
                    errors.append(f"Blocks.BlockEntities[{index}].Pos must contain 3 integers")
                    continue
                position = tuple(int(axis) for axis in pos)
                if position in seen_positions:
                    errors.append("Blocks.BlockEntities contains duplicate positions")
                seen_positions.add(position)
                if width is not None and height is not None and length is not None:
                    if not (
                        0 <= position[0] < width
                        and 0 <= position[1] < height
                        and 0 <= position[2] < length
                    ):
                        errors.append(f"Blocks.BlockEntities[{index}].Pos is out of bounds")
                entity_data = entity.get("Data")
                if entity_data is not None and not isinstance(entity_data, Compound):
                    errors.append(f"Blocks.BlockEntities[{index}].Data must be a Compound")

    entities = schematic.get("Entities")
    if entities is not None and not isinstance(entities, NbtList):
        errors.append("Schematic.Entities must be an NBT List")

    return errors
