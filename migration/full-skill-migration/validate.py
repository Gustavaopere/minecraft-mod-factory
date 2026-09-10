#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

SOURCE_REPOSITORY = "Gustavaopere/neoforge-rpg-skilltree"
SOURCE_REVISION = "2ecea4178aa7ac80f99955ab045e296da25376ec"
MANIFEST_REL = Path("migration/provenance/FULL-SKILL-MIGRATION-MANIFEST.json")

ART_ACTIVE_SKILLS = {
    "minecraft-asset-art-direction",
    "minecraft-audio-design",
    "minecraft-blockbench-geckolib",
    "minecraft-spell-production",
    "minecraft-spell-vfx-engineering",
    "minecraft-vfx-engineering",
    "minecraft-visual-qa",
}

SHARED_ACTIVE_SKILLS = {
    "minecraft-ci-release",
    "minecraft-dependency-compatibility-graph",
    "minecraft-jar-reverse-engineering",
    "minecraft-modpack-bisect",
    "minecraft-neoforge-engineering",
    "minecraft-neoforge-modpack-debugging",
    "minecraft-testing",
    "modpack-inventory-redundancy-audit",
}

REFERENCE_ONLY_SKILLS = {
    "minecraft-commands-scripting",
    "minecraft-datapack",
    "minecraft-essentials-ops",
    "minecraft-imagegen",
    "minecraft-mod-dev",
    "minecraft-modding",
    "minecraft-multiloader",
    "minecraft-plugin-dev",
    "minecraft-resource-pack",
    "minecraft-server-admin",
    "minecraft-world-generation",
    "minecraft-worldedit-ops",
}

ROOT_MAPPINGS = {
    "README.md": ("skills/README.md", "MIGRATE_ADAPTED", "ADAPTED"),
    "ROUTER.md": ("skills/ROUTER.md", "MIGRATE_ADAPTED", "ADAPTED"),
    "VERSION-AUTHORITY.md": ("skills/VERSION-AUTHORITY.md", "MIGRATE_ADAPTED", "ADAPTED"),
    "USER-GUIDED-WORKFLOW.md": ("skills/USER-GUIDED-WORKFLOW.md", "MIGRATE_CANONICAL", "SOURCE_EXACT"),
    "SOURCE-MANIFEST.md": ("migration/provenance/USER-SKILL-SOURCE-MANIFEST.md", "REFERENCE_ONLY", "SOURCE_EXACT"),
    "SOURCE-AUDIT.md": ("migration/provenance/USER-SKILL-SOURCE-AUDIT.md", "REFERENCE_ONLY", "SOURCE_EXACT"),
    "FULL-USER-SKILL-IMPORT.md": ("migration/provenance/FULL-USER-SKILL-IMPORT.md", "REFERENCE_ONLY", "SOURCE_EXACT"),
    "ART-PIPELINE-SOURCES.md": ("art/provenance/ART-PIPELINE-SOURCES.md", "MIGRATE_ADAPTED", "PREEXISTING_RECONCILED"),
    "VISUAL-STYLE-SOURCES.md": ("art/provenance/VISUAL-STYLE-SOURCES.md", "MIGRATE_ADAPTED", "PREEXISTING_RECONCILED"),
    "SPELL-VFX-AUDIO-SOURCES.md": ("art/provenance/SPELL-VFX-AUDIO-SOURCES.md", "MIGRATE_ADAPTED", "PREEXISTING_RECONCILED"),
}

PREEXISTING_STANDARDS = {
    "AUDIO-QA.md",
    "MODEL-ASSET-CONTRACT.md",
    "SPELL-PRESENTATION-CONTRACT.md",
    "VFX-QA.md",
    "VISUAL-QA.md",
}

PREEXISTING_TEMPLATES = {
    "ANIMATION-BRIEF.md",
    "ASSET-BRIEF.md",
    "AUDIO-CUE-SHEET.md",
    "MODEL-BRIEF.md",
    "SPELL-BRIEF.md",
    "VFX-BRIEF.md",
    "VISUAL-QA.md",
}

EXPECTED_LIBRARY_SKILLS = ART_ACTIVE_SKILLS | SHARED_ACTIVE_SKILLS | REFERENCE_ONLY_SKILLS


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def expected_mapping(relative: str) -> tuple[str, str, str] | None:
    if relative in ROOT_MAPPINGS:
        return ROOT_MAPPINGS[relative]

    parts = PurePosixPath(relative).parts
    if not parts:
        return None

    if parts[0] == "library" and len(parts) >= 3:
        skill = parts[1]
        rest = "/".join(parts[2:])
        if skill in ART_ACTIVE_SKILLS:
            return (f"art/skills/{skill}/{rest}", "MIGRATE_ADAPTED", "ADAPTED")
        if skill in SHARED_ACTIVE_SKILLS:
            mode = "ADAPTED" if rest == "PROJECT-OVERLAY.md" else "SOURCE_EXACT"
            return (f"skills/library/{skill}/{rest}", "MIGRATE_ADAPTED", mode)
        if skill in REFERENCE_ONLY_SKILLS:
            return (
                f"migration/provenance/historical-skills/library/{skill}/{rest}",
                "REFERENCE_ONLY",
                "SOURCE_EXACT",
            )
        return None

    if parts[0] == "standards" and len(parts) == 2:
        name = parts[1]
        mode = "PREEXISTING_RECONCILED" if name in PREEXISTING_STANDARDS else "ADAPTED"
        return (f"art/standards/{name}", "MIGRATE_ADAPTED", mode)

    if parts[0] == "templates" and len(parts) == 2:
        name = parts[1]
        if name not in PREEXISTING_TEMPLATES:
            return None
        return (f"art/templates/{name}", "MIGRATE_ADAPTED", "PREEXISTING_RECONCILED")

    if relative == "scripts/validate_skill_repository.py":
        return ("skills/scripts/validate_skill_repository.py", "MIGRATE_ADAPTED", "ADAPTED")
    if relative == "scripts/validate_golden_reference_rendered_edges.js":
        return (
            "art/tooling/validators/validate_golden_reference_rendered_edges.js",
            "MIGRATE_ADAPTED",
            "ADAPTED",
        )

    if relative == "tools/blockbench/minecraft_asset_validator.js":
        return (
            "migration/provenance/historical-skills/tools/blockbench/minecraft_asset_validator.js",
            "SUPERSEDED",
            "SOURCE_EXACT",
        )
    if relative == "tools/blockbench/README.md":
        return ("art/tooling/blockbench/README.md", "MIGRATE_ADAPTED", "ADAPTED")
    toolkit_prefix = "tools/blockbench/rpg-asset-toolkit/"
    if relative.startswith(toolkit_prefix):
        rest = relative[len(toolkit_prefix):]
        return (f"art/tooling/blockbench/asset-toolkit/{rest}", "MIGRATE_ADAPTED", "ADAPTED")

    golden_prefix = "golden-samples/"
    if relative.startswith(golden_prefix):
        rest = relative[len(golden_prefix):]
        return (f"art/golden-samples/{rest}", "MIGRATE_ADAPTED", "ADAPTED")

    return None


def source_inventory(source_root: Path) -> tuple[dict[str, str], list[str]]:
    inventory: dict[str, str] = {}
    errors: list[str] = []
    if not source_root.is_dir():
        return inventory, [f"source root does not exist: {source_root}"]

    for path in sorted(source_root.rglob("*")):
        if path.is_symlink():
            errors.append(f"symlink is not allowed in frozen skills source: {path.relative_to(source_root).as_posix()}")
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(source_root).as_posix()
        inventory[relative] = git_blob_sha(path.read_bytes())

    actual_skills = {
        path.name
        for path in (source_root / "library").iterdir()
        if path.is_dir()
    } if (source_root / "library").is_dir() else set()
    if actual_skills != EXPECTED_LIBRARY_SKILLS:
        missing = sorted(EXPECTED_LIBRARY_SKILLS - actual_skills)
        unexpected = sorted(actual_skills - EXPECTED_LIBRARY_SKILLS)
        errors.append(f"library skill set drift; missing={missing}; unexpected={unexpected}")

    for relative in inventory:
        if expected_mapping(relative) is None:
            errors.append(f"unmapped source file: {relative}")
    return inventory, errors


def validate_manifest(source_root: Path, factory_root: Path) -> list[str]:
    inventory, errors = source_inventory(source_root)
    if errors:
        return errors

    manifest_path = factory_root / MANIFEST_REL
    if not manifest_path.is_file():
        return [f"missing {MANIFEST_REL.as_posix()}; full skill migration is not materialized"]

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{MANIFEST_REL.as_posix()}: invalid JSON: {exc}"]

    expected_top = {"schema_version", "source_repository", "source_revision", "entries"}
    if set(data) != expected_top:
        errors.append(f"manifest top-level keys must be exactly {sorted(expected_top)}")
    if data.get("schema_version") != 1:
        errors.append("manifest schema_version must be 1")
    if data.get("source_repository") != SOURCE_REPOSITORY:
        errors.append("manifest source_repository drift")
    if data.get("source_revision") != SOURCE_REVISION:
        errors.append("manifest source_revision drift")

    entries = data.get("entries")
    if not isinstance(entries, list):
        return errors + ["manifest entries must be an array"]

    by_source: dict[str, dict] = {}
    required_entry_keys = {
        "source_path",
        "source_blob_sha",
        "classification",
        "destination",
        "materialization_mode",
    }
    for index, entry in enumerate(entries):
        prefix = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        if set(entry) != required_entry_keys:
            errors.append(f"{prefix}: keys must be exactly {sorted(required_entry_keys)}")
            continue
        source_path = entry.get("source_path")
        if not isinstance(source_path, str) or not source_path:
            errors.append(f"{prefix}: invalid source_path")
            continue
        if source_path in by_source:
            errors.append(f"{prefix}: duplicate source_path {source_path}")
            continue
        by_source[source_path] = entry

    source_set = set(inventory)
    manifest_set = set(by_source)
    missing = sorted(source_set - manifest_set)
    extra = sorted(manifest_set - source_set)
    if missing:
        errors.append(f"manifest missing {len(missing)} source files; first={missing[:10]}")
    if extra:
        errors.append(f"manifest has {len(extra)} unexpected source files; first={extra[:10]}")

    for source_path in sorted(source_set & manifest_set):
        entry = by_source[source_path]
        expected = expected_mapping(source_path)
        if expected is None:
            errors.append(f"{source_path}: no frozen mapping")
            continue
        destination, classification, mode = expected
        if entry.get("source_blob_sha") != inventory[source_path]:
            errors.append(f"{source_path}: source_blob_sha drift")
        if entry.get("classification") != classification:
            errors.append(f"{source_path}: classification must be {classification}")
        if entry.get("destination") != destination:
            errors.append(f"{source_path}: destination must be {destination}")
        if entry.get("materialization_mode") != mode:
            errors.append(f"{source_path}: materialization_mode must be {mode}")

        destination_path = factory_root / destination
        if not destination_path.is_file():
            errors.append(f"{source_path}: missing destination {destination}")
            continue
        if destination_path.stat().st_size == 0:
            errors.append(f"{destination}: destination is empty")
            continue
        if mode == "SOURCE_EXACT":
            actual_sha = git_blob_sha(destination_path.read_bytes())
            if actual_sha != inventory[source_path]:
                errors.append(f"{destination}: SOURCE_EXACT blob mismatch for {source_path}")

    if len(by_source) != len(inventory):
        errors.append(f"coverage count mismatch: source={len(inventory)} manifest={len(by_source)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate 100% coverage of the frozen historical IMPLEMENTAR SKILL tree")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--factory-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    errors = validate_manifest(args.source_root.resolve(), args.factory_root.resolve())
    if errors:
        print("FULL SKILL MIGRATION VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("FULL SKILL MIGRATION VALIDATION: PASS")
    print(f"source={SOURCE_REPOSITORY}@{SOURCE_REVISION}")
    print("all historical skills blobs are classified, materialized and covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
