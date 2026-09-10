#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA_VERSION = 1
TARGET = {"minecraft": "1.21.1", "loader": "neoforge", "java": 21}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
CURSEFORGE_HASH_RE = re.compile(r"^[0-9]+$")
MOD_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
MODS_COUNT_RE = re.compile(r"^Mods count:\s*(\d+)\s*$")


def _workspace_path(value, *, label, must_exist=False):
    workspace = Path.cwd().resolve()
    raw = Path(value)
    candidate = raw.resolve(strict=must_exist) if raw.is_absolute() else (workspace / raw).resolve(strict=must_exist)
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside workspace: {workspace}") from exc
    if candidate == workspace:
        raise ValueError(f"{label} must identify a path inside workspace, not the workspace root")
    return candidate


def _parse_declared_count(lines):
    for line in lines:
        match = MODS_COUNT_RE.match(line.strip())
        if match:
            return int(match.group(1))
    raise ValueError("missing 'Mods count:' declaration")


def _find_table_start(lines):
    header_index = None
    for index, line in enumerate(lines):
        if "jar name" in line and "mod id" in line and "mod version" in line:
            header_index = index
            break
    if header_index is None:
        raise ValueError("missing modlist table header")
    if header_index + 1 >= len(lines) or "+" not in lines[header_index + 1]:
        raise ValueError("missing modlist table separator")
    return header_index + 2


def _split_mixins(value):
    return [part.strip() for part in value.split(",") if part.strip()]


def _normalized_loader_version(version):
    return version[len("neoforge-"):] if version.startswith("neoforge-") else version


def parse_modlist_text(text, *, captured_at, source_sha256=None, source_name="modlist.txt"):
    if not isinstance(captured_at, str) or not captured_at.strip():
        raise ValueError("captured_at must be a non-empty string")
    lines = text.splitlines()
    declared_top_level_mods = _parse_declared_count(lines)
    start = _find_table_start(lines)
    entries = []
    stack = {}

    for source_line, line in enumerate(lines[start:], start=start + 1):
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 8:
            raise ValueError(f"line {source_line}: expected 8 table columns, got {len(parts)}")
        raw_jar = parts[0]
        leading_spaces = len(raw_jar) - len(raw_jar.lstrip(" "))
        if leading_spaces % 4 != 0:
            raise ValueError(f"line {source_line}: nesting indentation must be a multiple of 4 spaces")
        nesting_depth = leading_spaces // 4
        jar = raw_jar.strip()
        if not jar:
            raise ValueError(f"line {source_line}: jar name must not be empty")
        if nesting_depth > 0 and not jar.startswith("/META-INF/"):
            raise ValueError(f"line {source_line}: nested JAR must use a /META-INF/ path")

        if nesting_depth == 0:
            parent_jar = None
            parent_ordinal = None
            container_path = []
        else:
            parent = stack.get(nesting_depth - 1)
            if parent is None:
                raise ValueError(f"line {source_line}: nested JAR has no parent at depth {nesting_depth - 1}")
            parent_jar = parent["jar"]
            parent_ordinal = parent["ordinal"]
            container_path = [*parent["container_path"], parent["jar"]]

        entry = {
            "ordinal": len(entries),
            "jar": jar,
            "notes": parts[1].strip(),
            "mod_id": parts[2].strip(),
            "mod_name": parts[3].strip(),
            "version": parts[4].strip(),
            "mixin_configs": _split_mixins(parts[5].strip()),
            "modrinth_hash": parts[6].strip(),
            "curseforge_hash": parts[7].strip(),
            "top_level": nesting_depth == 0,
            "nesting_depth": nesting_depth,
            "parent_jar": parent_jar,
            "parent_ordinal": parent_ordinal,
            "container_path": container_path,
        }
        entries.append(entry)
        stack[nesting_depth] = entry
        for depth in [depth for depth in stack if depth > nesting_depth]:
            del stack[depth]

    parsed_top_level_mods = sum(1 for entry in entries if entry["top_level"])
    parsed_nested_mods = len(entries) - parsed_top_level_mods
    if parsed_top_level_mods != declared_top_level_mods:
        raise ValueError(
            f"declared top-level mod count {declared_top_level_mods} does not match "
            f"parsed top-level mod count {parsed_top_level_mods}"
        )

    loader_entry = next(
        (entry for entry in entries if entry["top_level"] and entry["mod_id"] == "neoforge"),
        None,
    )
    if loader_entry is None:
        raise ValueError("top-level NeoForge loader entry not found")

    return {
        "schema_version": SCHEMA_VERSION,
        "captured_at": captured_at,
        "source_name": source_name,
        "source_sha256": source_sha256 or hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "target": dict(TARGET),
        "loader": {"mod_id": "neoforge", "version": _normalized_loader_version(loader_entry["version"])},
        "declared_top_level_mods": declared_top_level_mods,
        "parsed_top_level_mods": parsed_top_level_mods,
        "parsed_nested_mods": parsed_nested_mods,
        "entries": entries,
    }


def parse_modlist_bytes(data, *, captured_at, source_name="modlist.txt"):
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"modlist source is not UTF-8: {exc}") from exc
    return parse_modlist_text(
        text,
        captured_at=captured_at,
        source_sha256=hashlib.sha256(data).hexdigest(),
        source_name=source_name,
    )


def build_provider_catalog(snapshot):
    grouped = {}
    for entry in snapshot.get("entries", []):
        mod_id = entry.get("mod_id", "")
        if not mod_id:
            continue
        provider = grouped.setdefault(
            mod_id,
            {
                "mod_id": mod_id,
                "versions": set(),
                "top_level_occurrences": 0,
                "nested_occurrences": 0,
                "occurrences": [],
            },
        )
        version = entry.get("version", "")
        if version:
            provider["versions"].add(version)
        if entry.get("top_level") is True:
            provider["top_level_occurrences"] += 1
        else:
            provider["nested_occurrences"] += 1
        provider["occurrences"].append(
            {
                "ordinal": entry.get("ordinal"),
                "jar": entry.get("jar", ""),
                "version": version,
                "top_level": bool(entry.get("top_level")),
                "nesting_depth": entry.get("nesting_depth", 0),
                "parent_jar": entry.get("parent_jar"),
                "parent_ordinal": entry.get("parent_ordinal"),
                "container_path": list(entry.get("container_path", [])),
                "modrinth_hash": entry.get("modrinth_hash", ""),
                "curseforge_hash": entry.get("curseforge_hash", ""),
            }
        )

    result = {}
    for mod_id in sorted(grouped):
        provider = grouped[mod_id]
        provider["versions"] = sorted(provider["versions"])
        provider["occurrences"] = sorted(provider["occurrences"], key=lambda occurrence: occurrence["ordinal"])
        result[mod_id] = provider
    return result


def _topology_signature(provider):
    return sorted(
        (
            occurrence["top_level"],
            occurrence["nesting_depth"],
            tuple(occurrence.get("container_path", [])),
            occurrence["parent_jar"],
        )
        for occurrence in provider["occurrences"]
    )


def _artifact_signature(provider):
    return sorted(
        (occurrence["jar"], occurrence["modrinth_hash"], occurrence["curseforge_hash"])
        for occurrence in provider["occurrences"]
    )


def compare_snapshots(before, after):
    before_catalog = build_provider_catalog(before)
    after_catalog = build_provider_catalog(after)
    before_ids = set(before_catalog)
    after_ids = set(after_catalog)
    common = before_ids & after_ids
    return {
        "before_captured_at": before.get("captured_at"),
        "after_captured_at": after.get("captured_at"),
        "added_mod_ids": sorted(after_ids - before_ids),
        "removed_mod_ids": sorted(before_ids - after_ids),
        "version_changed_mod_ids": sorted(
            mod_id for mod_id in common
            if before_catalog[mod_id]["versions"] != after_catalog[mod_id]["versions"]
        ),
        "topology_changed_mod_ids": sorted(
            mod_id for mod_id in common
            if _topology_signature(before_catalog[mod_id]) != _topology_signature(after_catalog[mod_id])
        ),
        "artifact_changed_mod_ids": sorted(
            mod_id for mod_id in common
            if _artifact_signature(before_catalog[mod_id]) != _artifact_signature(after_catalog[mod_id])
        ),
    }


def validate_normalized_snapshot(snapshot):
    errors = []
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1")
    if snapshot.get("target") != TARGET:
        errors.append("target must match Minecraft 1.21.1 / NeoForge / Java 21")
    if not isinstance(snapshot.get("captured_at"), str) or not snapshot.get("captured_at"):
        errors.append("captured_at must be a non-empty string")
    if not isinstance(snapshot.get("source_name"), str) or not snapshot.get("source_name"):
        errors.append("source_name must be a non-empty string")
    source_sha256 = snapshot.get("source_sha256")
    if not isinstance(source_sha256, str) or SHA256_RE.fullmatch(source_sha256) is None:
        errors.append("source_sha256 must be a lowercase SHA-256 digest")
    entries = snapshot.get("entries")
    if not isinstance(entries, list):
        return errors + ["entries must be an array"]

    top_count = sum(1 for entry in entries if isinstance(entry, dict) and entry.get("top_level") is True)
    nested_count = len(entries) - top_count
    if snapshot.get("declared_top_level_mods") != top_count:
        errors.append("declared_top_level_mods does not match entry topology")
    if snapshot.get("parsed_top_level_mods") != top_count:
        errors.append("parsed_top_level_mods does not match entries")
    if snapshot.get("parsed_nested_mods") != nested_count:
        errors.append("parsed_nested_mods does not match entries")

    required = {
        "ordinal", "jar", "notes", "mod_id", "mod_name", "version", "mixin_configs",
        "modrinth_hash", "curseforge_hash", "top_level", "nesting_depth",
        "parent_jar", "parent_ordinal", "container_path",
    }
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entries[{index}] must be an object")
            continue
        missing = sorted(required.difference(entry))
        if missing:
            errors.append(f"entries[{index}] missing fields: {', '.join(missing)}")
            continue
        if entry["ordinal"] != index:
            errors.append(f"entries[{index}].ordinal must equal its array index")
        if not isinstance(entry["jar"], str) or not entry["jar"]:
            errors.append(f"entries[{index}].jar must be a non-empty string")
        for field in ("notes", "mod_id", "mod_name", "version", "modrinth_hash", "curseforge_hash"):
            if not isinstance(entry[field], str):
                errors.append(f"entries[{index}].{field} must be a string")
        if isinstance(entry.get("mod_id"), str):
            if not entry["mod_id"]:
                errors.append(f"entries[{index}].mod_id must be a non-empty physical identifier")
            elif MOD_ID_RE.fullmatch(entry["mod_id"]) is None:
                errors.append(f"entries[{index}].mod_id has invalid physical identifier syntax")
        if not isinstance(entry["mixin_configs"], list) or not all(isinstance(v, str) and v for v in entry["mixin_configs"]):
            errors.append(f"entries[{index}].mixin_configs must be an array of non-empty strings")
        if isinstance(entry.get("modrinth_hash"), str) and entry["modrinth_hash"] and SHA1_RE.fullmatch(entry["modrinth_hash"]) is None:
            errors.append(f"entries[{index}].modrinth_hash must be a lowercase SHA-1 when present")
        if isinstance(entry.get("curseforge_hash"), str) and entry["curseforge_hash"] and CURSEFORGE_HASH_RE.fullmatch(entry["curseforge_hash"]) is None:
            errors.append(f"entries[{index}].curseforge_hash must be decimal digits when present")
        if not isinstance(entry["top_level"], bool):
            errors.append(f"entries[{index}].top_level must be boolean")
        depth = entry["nesting_depth"]
        if not isinstance(depth, int) or isinstance(depth, bool) or depth < 0:
            errors.append(f"entries[{index}].nesting_depth must be a non-negative integer")
            continue
        if entry["top_level"] != (depth == 0):
            errors.append(f"entries[{index}].top_level conflicts with nesting_depth")
        if not isinstance(entry["container_path"], list) or not all(isinstance(v, str) and v for v in entry["container_path"]):
            errors.append(f"entries[{index}].container_path must be an array of non-empty strings")
            continue
        if len(entry["container_path"]) != depth:
            errors.append(f"entries[{index}].container_path length must equal nesting_depth")
        if depth == 0:
            if entry["parent_jar"] is not None:
                errors.append(f"entries[{index}].parent_jar must be null for top-level entries")
            if entry["parent_ordinal"] is not None:
                errors.append(f"entries[{index}].parent_ordinal must be null for top-level entries")
            if entry["container_path"] != []:
                errors.append(f"entries[{index}].container_path must be empty for top-level entries")
        else:
            if not entry["jar"].startswith("/META-INF/"):
                errors.append(f"entries[{index}].jar must be a /META-INF/ path for nested entries")
            parent_ordinal = entry["parent_ordinal"]
            if not isinstance(parent_ordinal, int) or isinstance(parent_ordinal, bool) or not (0 <= parent_ordinal < index):
                errors.append(f"entries[{index}].parent_ordinal must reference an earlier entry")
                continue
            parent = entries[parent_ordinal]
            if not isinstance(parent, dict):
                errors.append(f"entries[{index}].parent_ordinal must reference an object entry")
                continue
            if parent.get("ordinal") != parent_ordinal:
                errors.append(f"entries[{index}].parent_ordinal references an entry with invalid ordinal")
            if parent.get("nesting_depth") != depth - 1:
                errors.append(f"entries[{index}].parent_ordinal must reference depth {depth - 1}")
            if entry["parent_jar"] != parent.get("jar"):
                errors.append(f"entries[{index}].parent_jar must equal referenced parent jar")
            expected_container_path = [*parent.get("container_path", []), parent.get("jar")]
            if entry["container_path"] != expected_container_path:
                errors.append(f"entries[{index}].container_path must equal the full referenced parent chain")

    loader = snapshot.get("loader")
    if not isinstance(loader, dict) or loader.get("mod_id") != "neoforge" or not loader.get("version"):
        errors.append("loader must identify the physical NeoForge entry")
    else:
        physical_loaders = [
            entry for entry in entries
            if isinstance(entry, dict) and entry.get("top_level") is True and entry.get("mod_id") == "neoforge"
        ]
        if len(physical_loaders) != 1:
            errors.append("snapshot must contain exactly one top-level NeoForge entry")
        elif loader.get("version") != _normalized_loader_version(physical_loaders[0].get("version", "")):
            errors.append("loader.version must match the physical NeoForge entry")
    return errors


def build_persisted_snapshot(snapshot):
    entry_fields = (
        "ordinal", "jar", "notes", "mod_id", "mod_name", "version", "mixin_configs",
        "modrinth_hash", "curseforge_hash", "top_level", "nesting_depth",
        "parent_jar", "parent_ordinal", "container_path",
    )
    return {
        "schema_version": snapshot["schema_version"],
        "captured_at": snapshot["captured_at"],
        "source_name": snapshot["source_name"],
        "source_sha256": snapshot["source_sha256"],
        "target": snapshot["target"],
        "loader": snapshot["loader"],
        "declared_top_level_mods": snapshot["declared_top_level_mods"],
        "parsed_top_level_mods": snapshot["parsed_top_level_mods"],
        "parsed_nested_mods": snapshot["parsed_nested_mods"],
        "entries": [{field: entry[field] for field in entry_fields} for entry in snapshot["entries"]],
    }


def build_persisted_provider_catalog(snapshot):
    providers = build_provider_catalog(snapshot)
    return {
        "schema_version": SCHEMA_VERSION,
        "captured_at": snapshot["captured_at"],
        "source_sha256": snapshot["source_sha256"],
        "provider_count": len(providers),
        "providers": [
            {
                "mod_id": mod_id,
                "versions": provider["versions"],
                "top_level_occurrences": provider["top_level_occurrences"],
                "nested_occurrences": provider["nested_occurrences"],
                "entry_ordinals": [occurrence["ordinal"] for occurrence in provider["occurrences"]],
            }
            for mod_id, provider in providers.items()
        ],
    }


def validate_persisted_provider_catalog(snapshot, catalog):
    errors = []
    if catalog.get("schema_version") != SCHEMA_VERSION:
        errors.append("provider catalog schema_version must be 1")
    if catalog.get("captured_at") != snapshot.get("captured_at"):
        errors.append("provider catalog captured_at must match snapshot")
    if catalog.get("source_sha256") != snapshot.get("source_sha256"):
        errors.append("provider catalog source_sha256 must match snapshot")
    expected = build_persisted_provider_catalog(snapshot)
    if catalog != expected:
        errors.append("provider catalog must be derived deterministically from the normalized snapshot")
    return errors


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_persisted_snapshot(snapshot, output_path, *, shard_size=100, emit_providers=False):
    if not isinstance(shard_size, int) or isinstance(shard_size, bool) or shard_size < 1:
        raise ValueError("shard_size must be a positive integer")
    output_path = _workspace_path(output_path, label="snapshot output", must_exist=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    persisted = build_persisted_snapshot(snapshot)
    entries = persisted.pop("entries")
    shards = []
    stem = output_path.stem
    for start in range(0, len(entries), shard_size):
        chunk = entries[start:start + shard_size]
        end = start + len(chunk) - 1
        shard_name = f"{stem}.entries.{start:04d}-{end:04d}.json"
        shard_path = output_path.parent / shard_name
        shard_document = {
            "schema_version": SCHEMA_VERSION,
            "start_ordinal": start,
            "entry_count": len(chunk),
            "entries": chunk,
        }
        shard_bytes = _json_bytes(shard_document)
        shard_path.write_bytes(shard_bytes)
        shards.append({
            "path": shard_name,
            "start_ordinal": start,
            "count": len(chunk),
            "sha256": hashlib.sha256(shard_bytes).hexdigest(),
        })
    manifest = {**persisted, "entry_count": len(entries), "entry_shards": shards}
    output_path.write_bytes(_json_bytes(manifest))
    if emit_providers:
        workspace = Path.cwd().resolve()
        provider_path = output_path.with_name(f"{output_path.stem}.providers.json").resolve(strict=False)
        if provider_path == workspace or not provider_path.is_relative_to(workspace):
            raise ValueError(f"provider catalog output must stay inside workspace: {workspace}")
        provider_catalog = build_persisted_provider_catalog(snapshot)
        provider_path.write_bytes(_json_bytes(provider_catalog))
    return manifest


def load_persisted_snapshot(path):
    path = _workspace_path(path, label="snapshot manifest", must_exist=True)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if "entries" in manifest:
        snapshot = manifest
    else:
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("snapshot manifest schema_version must be 1")
        entry_count = manifest.get("entry_count")
        shards = manifest.get("entry_shards")
        if not isinstance(entry_count, int) or isinstance(entry_count, bool) or entry_count < 0:
            raise ValueError("snapshot manifest entry_count must be a non-negative integer")
        if not isinstance(shards, list) or (entry_count and not shards):
            raise ValueError("snapshot manifest entry_shards must be a non-empty array when entries exist")
        entries = []
        expected_start = 0
        for index, shard in enumerate(shards):
            if not isinstance(shard, dict):
                raise ValueError(f"snapshot manifest shard[{index}] must be an object")
            shard_name = shard.get("path")
            if not isinstance(shard_name, str) or not shard_name or Path(shard_name).name != shard_name:
                raise ValueError(f"snapshot manifest shard[{index}].path must be a local basename")
            if shard.get("start_ordinal") != expected_start:
                raise ValueError(f"snapshot manifest shard[{index}] start_ordinal is not contiguous")
            count = shard.get("count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 1:
                raise ValueError(f"snapshot manifest shard[{index}].count must be positive")
            digest = shard.get("sha256")
            if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
                raise ValueError(f"snapshot manifest shard[{index}].sha256 must be a lowercase SHA-256 digest")
            shard_path = _workspace_path(
                path.parent / shard_name,
                label=f"snapshot shard {shard_name}",
                must_exist=True,
            )
            shard_bytes = shard_path.read_bytes()
            if hashlib.sha256(shard_bytes).hexdigest() != digest:
                raise ValueError(f"snapshot shard integrity mismatch: {shard_name}")
            document = json.loads(shard_bytes.decode("utf-8"))
            if document.get("schema_version") != SCHEMA_VERSION:
                raise ValueError(f"snapshot shard schema_version mismatch: {shard_name}")
            if document.get("start_ordinal") != expected_start:
                raise ValueError(f"snapshot shard start_ordinal mismatch: {shard_name}")
            chunk = document.get("entries")
            if not isinstance(chunk, list) or document.get("entry_count") != len(chunk) or len(chunk) != count:
                raise ValueError(f"snapshot shard count mismatch: {shard_name}")
            if any(
                not isinstance(entry, dict) or entry.get("ordinal") != expected_start + offset
                for offset, entry in enumerate(chunk)
            ):
                raise ValueError(f"snapshot shard ordinals are not contiguous: {shard_name}")
            entries.extend(chunk)
            expected_start += count
        if len(entries) != entry_count:
            raise ValueError("snapshot manifest entry_count does not match loaded shards")
        snapshot = {key: value for key, value in manifest.items() if key not in {"entry_count", "entry_shards"}}
        snapshot["entries"] = entries
    errors = validate_normalized_snapshot(snapshot)
    if errors:
        raise ValueError("invalid persisted snapshot: " + "; ".join(errors))
    return snapshot


def _load_snapshot(path):
    return load_persisted_snapshot(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Normalize and validate physical Minecraft modlist snapshots.")
    parser.add_argument("input", nargs="?", help="physical modlist.txt input")
    parser.add_argument("--captured-at")
    parser.add_argument("--output")
    parser.add_argument("--emit-providers", action="store_true")
    parser.add_argument("--check")
    parser.add_argument("--providers")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    parser.add_argument("--shard-size", type=int, default=100)
    args = parser.parse_args(argv)

    if args.check:
        try:
            snapshot = _load_snapshot(args.check)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            print("I2 PHYSICAL MODLIST VALIDATION: FAIL")
            print(f"- {exc}")
            return 1
        errors = validate_normalized_snapshot(snapshot)
        if args.providers:
            try:
                providers_path = _workspace_path(args.providers, label="provider catalog", must_exist=True)
                provider_catalog = json.loads(providers_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                errors.append(f"provider catalog could not be read: {exc}")
            else:
                errors += validate_persisted_provider_catalog(snapshot, provider_catalog)
        if errors:
            print("I2 PHYSICAL MODLIST VALIDATION: FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print("I2 PHYSICAL MODLIST VALIDATION: PASS")
        print(
            f"{snapshot['parsed_top_level_mods']} top-level + "
            f"{snapshot['parsed_nested_mods']} nested entries; "
            f"{len(build_provider_catalog(snapshot))} provider identities"
        )
        return 0

    if args.compare:
        result = compare_snapshots(_load_snapshot(args.compare[0]), _load_snapshot(args.compare[1]))
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    if not args.input or not args.captured_at or not args.output:
        parser.error("import mode requires INPUT, --captured-at and --output")
    input_path = _workspace_path(args.input, label="physical modlist input", must_exist=True)
    snapshot = parse_modlist_bytes(
        input_path.read_bytes(),
        captured_at=args.captured_at,
        source_name=input_path.name,
    )
    errors = validate_normalized_snapshot(snapshot)
    if errors:
        print("I2 PHYSICAL MODLIST VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    persisted_snapshot = build_persisted_snapshot(snapshot)
    write_persisted_snapshot(
        persisted_snapshot,
        args.output,
        shard_size=args.shard_size,
        emit_providers=args.emit_providers,
    )
    if args.emit_providers:
        output_path = _workspace_path(args.output, label="snapshot output", must_exist=True)
        print(f"Wrote {output_path.with_name(f'{output_path.stem}.providers.json')}")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
