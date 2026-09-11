from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import tomllib
import zipfile
from pathlib import Path

SCHEMA_VERSION = 1
MINECRAFT_VERSION = "1.21.1"
LOADER = "neoforge"
RESOURCE_LOCATION_RE = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
MOD_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
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
MAX_ARCHIVE_ENTRIES = 100_000
MAX_NESTED_JAR_BYTES = 128 * 1024 * 1024
MAX_NESTING_DEPTH = 4


def _engineering_i2():
    root = Path(__file__).resolve().parents[2]
    path = root / "engineering" / "tooling" / "import-physical-modlist.py"
    spec = importlib.util.spec_from_file_location("factory_engineering_i2_modlist", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load shared Engineering I2 importer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def normalize_physical_snapshot(snapshot):
    i2 = _engineering_i2()
    errors = i2.validate_normalized_snapshot(snapshot)
    if errors:
        raise ValueError("invalid physical snapshot: " + "; ".join(errors))
    providers = i2.build_provider_catalog(snapshot)
    entries = snapshot["entries"]
    return {
        "captured_at": snapshot["captured_at"],
        "source_name": snapshot["source_name"],
        "source_sha256": snapshot["source_sha256"],
        "loader_version": snapshot["loader"]["version"],
        "top_level_mods": snapshot["parsed_top_level_mods"],
        "nested_mods": snapshot["parsed_nested_mods"],
        "total_entries": len(entries),
        "provider_count": len(providers),
        "unidentified_entries": sum(1 for entry in entries if not entry.get("mod_id")),
    }


def _resource_from_asset(name, marker, suffix):
    if not name.startswith("assets/") or marker not in name or not name.endswith(suffix):
        return None
    parts = name.split("/", 2)
    if len(parts) != 3 or not parts[1]:
        return None
    namespace = parts[1]
    prefix = f"assets/{namespace}/{marker}"
    if not name.startswith(prefix):
        return None
    path = name[len(prefix):-len(suffix)]
    value = f"{namespace}:{path}"
    return value if RESOURCE_LOCATION_RE.fullmatch(value) else None


def _mod_ids_from_metadata(archive):
    result = set()
    for name in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
        try:
            raw = archive.read(name)
        except KeyError:
            continue
        try:
            document = tomllib.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError):
            continue
        mods = document.get("mods", [])
        if not isinstance(mods, list):
            continue
        for mod in mods:
            if not isinstance(mod, dict):
                continue
            mod_id = mod.get("modId")
            if isinstance(mod_id, str) and MOD_ID_RE.fullmatch(mod_id):
                result.add(mod_id)
    return sorted(result)


def _index_zip(data, *, jar_name, depth):
    if depth > MAX_NESTING_DEPTH:
        raise ValueError(f"nested JAR depth exceeds {MAX_NESTING_DEPTH}: {jar_name}")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data), "r")
    except zipfile.BadZipFile as exc:
        raise ValueError(f"invalid JAR/ZIP archive: {jar_name}") from exc
    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARCHIVE_ENTRIES:
            raise ValueError(f"archive entry count exceeds {MAX_ARCHIVE_ENTRIES}: {jar_name}")
        names = sorted(info.filename for info in infos if not info.is_dir())
        blockstates = set()
        block_models = set()
        block_textures = set()
        for name in names:
            value = _resource_from_asset(name, "blockstates/", ".json")
            if value:
                blockstates.add(value)
            value = _resource_from_asset(name, "models/block/", ".json")
            if value:
                block_models.add(value)
            value = _resource_from_asset(name, "textures/block/", ".png")
            if value:
                block_textures.add(value)

        nested_jars = []
        for info in sorted(infos, key=lambda item: item.filename):
            name = info.filename
            if info.is_dir() or not name.endswith(".jar"):
                continue
            if not (
                name.startswith("META-INF/jarjar/")
                or name.startswith("META-INF/jars/")
                or name.startswith("META-INF/optional-libs/")
            ):
                continue
            if info.file_size > MAX_NESTED_JAR_BYTES:
                raise ValueError(f"nested JAR exceeds {MAX_NESTED_JAR_BYTES} bytes: {name}")
            nested_data = archive.read(info)
            nested_jars.append(_index_zip(nested_data, jar_name=name, depth=depth + 1))

        return {
            "jar": jar_name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "mod_ids": _mod_ids_from_metadata(archive),
            "blockstates": sorted(blockstates),
            "block_models": sorted(block_models),
            "block_textures": sorted(block_textures),
            "nested_jars": nested_jars,
        }


def index_jar_file(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"JAR does not exist: {path}")
    if path.suffix.lower() != ".jar":
        raise ValueError(f"expected .jar input: {path}")
    return _index_zip(path.read_bytes(), jar_name=path.name, depth=0)


def _canonical_state(state):
    if not isinstance(state, dict):
        raise ValueError("runtime block states must be objects")
    result = {}
    for key in sorted(state):
        value = state[key]
        if not isinstance(key, str) or not key or not isinstance(value, str) or not value:
            raise ValueError("runtime state properties must be non-empty string pairs")
        result[key] = value
    return result


def _validate_runtime_snapshot(runtime, physical):
    if not isinstance(runtime, dict) or runtime.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("runtime snapshot schema_version must be 1")
    if runtime.get("physical_snapshot_sha256") != physical["source_sha256"]:
        raise ValueError("runtime snapshot must reference the exact physical snapshot SHA-256")
    target = runtime.get("target")
    if not isinstance(target, dict):
        raise ValueError("runtime target must be an object")
    if target.get("minecraft") != MINECRAFT_VERSION or target.get("loader") != LOADER:
        raise ValueError("runtime target must match Minecraft 1.21.1 / NeoForge")
    if target.get("loader_version") != physical["loader_version"]:
        raise ValueError("runtime loader version must match the physical snapshot")
    if not isinstance(runtime.get("captured_at"), str) or not runtime["captured_at"]:
        raise ValueError("runtime captured_at must be a non-empty string")
    blocks = runtime.get("blocks")
    if not isinstance(blocks, list):
        raise ValueError("runtime blocks must be an array")

    normalized = []
    seen = set()
    for block in blocks:
        if not isinstance(block, dict):
            raise ValueError("runtime blocks must contain objects")
        block_id = block.get("id")
        if not isinstance(block_id, str) or RESOURCE_LOCATION_RE.fullmatch(block_id) is None:
            raise ValueError(f"invalid runtime block id: {block_id!r}")
        if block_id in seen:
            raise ValueError(f"duplicate runtime block id: {block_id}")
        seen.add(block_id)
        states = block.get("states")
        if not isinstance(states, list) or not states:
            raise ValueError(f"runtime block states must be a non-empty array: {block_id}")
        canonical_states = [_canonical_state(state) for state in states]
        unique_states = {canonical_json_bytes(state): state for state in canonical_states}
        safety = block.get("safety", "unknown")
        if safety not in SAFETY_CLASSES:
            raise ValueError(f"invalid safety class for {block_id}: {safety}")
        normalized.append({
            "id": block_id,
            "states": [unique_states[key] for key in sorted(unique_states)],
            "safety": safety,
        })
    return sorted(normalized, key=lambda block: block["id"])


def _walk_static_indexes(indexes):
    for index in indexes:
        if not isinstance(index, dict):
            raise ValueError("static indexes must contain objects")
        yield index
        nested = index.get("nested_jars", [])
        if not isinstance(nested, list):
            raise ValueError("nested_jars must be an array")
        yield from _walk_static_indexes(nested)


def build_modpack_registry(physical_snapshot, static_indexes, runtime_snapshot):
    physical = normalize_physical_snapshot(physical_snapshot)
    if not isinstance(static_indexes, list):
        raise ValueError("static indexes must be an array")
    runtime_blocks = _validate_runtime_snapshot(runtime_snapshot, physical)

    flat_static = list(_walk_static_indexes(static_indexes))
    static_block_ids = set()
    for index in flat_static:
        for block_id in index.get("blockstates", []):
            if not isinstance(block_id, str) or RESOURCE_LOCATION_RE.fullmatch(block_id) is None:
                raise ValueError(f"invalid static blockstate id: {block_id!r}")
            static_block_ids.add(block_id)

    runtime_by_id = {block["id"]: block for block in runtime_blocks}
    all_ids = sorted(static_block_ids | set(runtime_by_id))
    blocks = []
    for block_id in all_ids:
        static_discovered = block_id in static_block_ids
        runtime_block = runtime_by_id.get(block_id)
        if runtime_block is None:
            blocks.append({
                "id": block_id,
                "available": False,
                "authority": "static_only_unconfirmed",
                "static_discovered": True,
                "states": [],
                "safety": "unknown",
            })
        else:
            blocks.append({
                "id": block_id,
                "available": True,
                "authority": "runtime_confirmed",
                "static_discovered": static_discovered,
                "states": runtime_block["states"],
                "safety": runtime_block["safety"],
            })

    document = {
        "schema_version": SCHEMA_VERSION,
        "physical": physical,
        "runtime": {
            "captured_at": runtime_snapshot["captured_at"],
            "physical_snapshot_sha256": runtime_snapshot["physical_snapshot_sha256"],
            "target": {
                "minecraft": MINECRAFT_VERSION,
                "loader": LOADER,
                "loader_version": physical["loader_version"],
            },
        },
        "static_index": {
            "jar_count": len(static_indexes),
            "nested_jar_count": max(0, len(flat_static) - len(static_indexes)),
            "discovered_block_count": len(static_block_ids),
        },
        "blocks": blocks,
    }
    document["content_sha256"] = hashlib.sha256(canonical_json_bytes(document)).hexdigest()
    return document
