#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PROVENANCE_PATH = "migration/M4-VISUAL-STYLE-PROVENANCE.json"

REQUIRED_DOCUMENTS = (
    "art/VISUAL-STYLE-BIBLE.md",
    "art/provenance/ART-PIPELINE-SOURCES.md",
    "art/provenance/VISUAL-STYLE-SOURCES.md",
    "art/provenance/SPELL-VFX-AUDIO-SOURCES.md",
)

SOURCE_REPOSITORY = "Gustavaopere/neoforge-rpg-skilltree"
SOURCE_REVISION = "2ecea4178aa7ac80f99955ab045e296da25376ec"
SOURCE_BLOBS = {
    "docs/art/VISUAL-STYLE-BIBLE.md": "85d437d2e16f77f2024bb5333dd742dcd8e44f14",
    "PROJECT-INSTRUCTIONS/skills/ART-PIPELINE-SOURCES.md": "44a814300a413edc0ab18efb37d7f5af49ec8332",
    "PROJECT-INSTRUCTIONS/skills/VISUAL-STYLE-SOURCES.md": "8a18d1d277dd9e40d5e87c15f0793548ac4e5e7a",
    "PROJECT-INSTRUCTIONS/skills/SPELL-VFX-AUDIO-SOURCES.md": "b50bfe68d929a2455f83d882ab675c31b37a04e1",
}

EXPECTED_DESTINATIONS = {
    "docs/art/VISUAL-STYLE-BIBLE.md": "art/VISUAL-STYLE-BIBLE.md",
    "PROJECT-INSTRUCTIONS/skills/ART-PIPELINE-SOURCES.md": "art/provenance/ART-PIPELINE-SOURCES.md",
    "PROJECT-INSTRUCTIONS/skills/VISUAL-STYLE-SOURCES.md": "art/provenance/VISUAL-STYLE-SOURCES.md",
    "PROJECT-INSTRUCTIONS/skills/SPELL-VFX-AUDIO-SOURCES.md": "art/provenance/SPELL-VFX-AUDIO-SOURCES.md",
}

EXPECTED_PROVIDERS = {
    "photon": {"presence": "PRESENT", "version": "2.2.6.a", "state": "CONFIRMED"},
    "geckolib": {"presence": "PRESENT", "version": "4.9.2", "state": "CONFIRMED"},
    "irons_spellbooks": {"presence": "PRESENT", "version": "1.21.1-3.16.3", "state": "CONFIRMED"},
    "playeranimator": {"presence": "PRESENT", "version": "2.0.4+1.21.1", "state": "CONFIRMED"},
    "aaa_particles": {"presence": "ABSENT", "version": "UNRESOLVED", "state": "UNAVAILABLE"},
    "aaa_particles_world": {"presence": "ABSENT", "version": "UNRESOLVED", "state": "UNAVAILABLE"},
}

FORBIDDEN_DOC_TOKENS = (
    "PROJECT-INSTRUCTIONS/",
    "modlist(2).txt",
)

REQUIRED_TOKENS = {
    "art/VISUAL-STYLE-BIBLE.md": (
        "../skills/VERSION-AUTHORITY.md",
        "Contexto histórico do pack",
        "não é regra global da Factory",
        "standards/MODEL-ASSET-CONTRACT.md",
        "standards/VISUAL-QA.md",
        "AAA Particles/Effekseer",
    ),
    "art/provenance/ART-PIPELINE-SOURCES.md": (
        "Historical source check: 2026-09-07",
        "../../skills/VERSION-AUTHORITY.md",
        "Blockbench",
        "GeckoLib `4.9.2`",
        "does not claim they were freshly reverified",
    ),
    "art/provenance/VISUAL-STYLE-SOURCES.md": (
        "snapshot editorial histórico de 2026-09-08",
        "não prova presença atual",
        "modlist física 2026-09-09",
        "AAA Particles",
    ),
    "art/provenance/SPELL-VFX-AUDIO-SOURCES.md": (
        "Photon `2.2.6.a`",
        "GeckoLib `4.9.2`",
        "Iron's Spells 'n Spellbooks `1.21.1-3.16.3`",
        "ausente no snapshot físico 2026-09-09",
        "UNAVAILABLE",
    ),
}


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_documents(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_DOCUMENTS:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"{relative}: cannot read UTF-8: {exc}")
            continue
        if not text.strip():
            errors.append(f"{relative}: empty document")
            continue
        for token in FORBIDDEN_DOC_TOKENS:
            if token in text:
                errors.append(f"{relative}: historical path token remains: {token}")
        for token in REQUIRED_TOKENS[relative]:
            if token not in text:
                errors.append(f"{relative}: missing required boundary/evidence token {token!r}")

    bible = root / "art" / "VISUAL-STYLE-BIBLE.md"
    if bible.is_file():
        text = bible.read_text(encoding="utf-8")
        if "skills/library/minecraft-visual-qa" in text:
            errors.append("art/VISUAL-STYLE-BIBLE.md: links to a visual-QA skill not yet migrated")
        for linked in (
            root / "skills" / "VERSION-AUTHORITY.md",
            root / "art" / "standards" / "MODEL-ASSET-CONTRACT.md",
            root / "art" / "standards" / "VISUAL-QA.md",
            root / "art" / "provenance" / "VISUAL-STYLE-SOURCES.md",
            root / "art" / "provenance" / "SPELL-VFX-AUDIO-SOURCES.md",
        ):
            if not linked.is_file():
                errors.append(f"art/VISUAL-STYLE-BIBLE.md: required local target missing: {linked.relative_to(root)}")

    for linked in (
        root / "art" / "provenance" / "ART-PIPELINE-SOURCES.md",
        root / "art" / "provenance" / "SPELL-VFX-AUDIO-SOURCES.md",
        root / "skills" / "VERSION-AUTHORITY.md",
    ):
        if not linked.is_file():
            errors.append(f"visual provenance local target missing: {linked.relative_to(root)}")
    return errors


def validate_migration_provenance(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / MIGRATION_PROVENANCE_PATH
    if not path.is_file():
        return [f"missing {MIGRATION_PROVENANCE_PATH}"]
    try:
        data = _load_json(path)
    except Exception as exc:
        return [f"{MIGRATION_PROVENANCE_PATH}: invalid JSON: {exc}"]

    expected_top = {
        "schema_version",
        "migration_wave",
        "classification",
        "source_repository",
        "source_revision",
        "destination_repository",
        "destination_authority",
        "physical_snapshot",
        "context_snapshots",
        "files",
    }
    if set(data) != expected_top:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: top-level keys must be exactly {sorted(expected_top)}")
    if data.get("schema_version") != 1:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: schema_version must be 1")
    if data.get("migration_wave") != "M4_VISUAL_STYLE_PROVENANCE":
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: wrong migration_wave")
    if data.get("classification") != "MIGRATE_ADAPTED":
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: classification must be MIGRATE_ADAPTED")
    if data.get("source_repository") != SOURCE_REPOSITORY:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: wrong source_repository")
    if data.get("source_revision") != SOURCE_REVISION:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: wrong source_revision")
    if data.get("destination_repository") != "Gustavaopere/minecraft-mod-factory":
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: wrong destination_repository")
    if data.get("destination_authority") != "art/":
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: destination_authority must be art/")

    snapshot = data.get("physical_snapshot")
    if not isinstance(snapshot, dict):
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: physical_snapshot must be object")
    else:
        if snapshot.get("date") != "2026-09-09":
            errors.append(f"{MIGRATION_PROVENANCE_PATH}: physical snapshot date must be 2026-09-09")
        if snapshot.get("sha256") != "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00":
            errors.append(f"{MIGRATION_PROVENANCE_PATH}: physical snapshot SHA-256 drift")
        if snapshot.get("authority") != "external physical modlist snapshot":
            errors.append(f"{MIGRATION_PROVENANCE_PATH}: physical snapshot authority drift")
        if snapshot.get("providers") != EXPECTED_PROVIDERS:
            errors.append(f"{MIGRATION_PROVENANCE_PATH}: provider presence/version matrix drift")

    contexts = data.get("context_snapshots")
    if not isinstance(contexts, list) or len(contexts) != 1:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: exactly one editorial context snapshot required")
    else:
        context = contexts[0]
        if context.get("date") != "2026-09-08" or context.get("state") != "REFERENCE_ONLY":
            errors.append(f"{MIGRATION_PROVENANCE_PATH}: editorial snapshot must remain 2026-09-08 REFERENCE_ONLY")

    files = data.get("files")
    if not isinstance(files, list) or len(files) != len(SOURCE_BLOBS):
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: files must contain exactly {len(SOURCE_BLOBS)} entries")
    else:
        seen = set()
        for index, item in enumerate(files):
            prefix = f"{MIGRATION_PROVENANCE_PATH}:files[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix}: entry must be object")
                continue
            if set(item) != {"source", "source_blob_sha", "destination", "adaptation_mode"}:
                errors.append(f"{prefix}: unexpected keys")
                continue
            source = item.get("source")
            if source not in SOURCE_BLOBS:
                errors.append(f"{prefix}: unexpected source {source!r}")
                continue
            if source in seen:
                errors.append(f"{prefix}: duplicate source {source!r}")
                continue
            seen.add(source)
            if item.get("source_blob_sha") != SOURCE_BLOBS[source]:
                errors.append(f"{prefix}: source blob drift for {source}")
            if item.get("destination") != EXPECTED_DESTINATIONS[source]:
                errors.append(f"{prefix}: destination drift for {source}")
            mode = item.get("adaptation_mode")
            if not isinstance(mode, str) or not mode or mode == "BYTE_IDENTICAL_RELOCATION":
                errors.append(f"{prefix}: adapted migration must name a non-byte-identical adaptation mode")
        missing = set(SOURCE_BLOBS) - seen
        if missing:
            errors.append(f"{MIGRATION_PROVENANCE_PATH}: missing sources: {', '.join(sorted(missing))}")
    return errors


def run_validation(root: Path = ROOT) -> list[str]:
    return validate_documents(root) + validate_migration_provenance(root)


def main() -> int:
    errors = run_validation(ROOT)
    if errors:
        print("M4 VISUAL STYLE PROVENANCE VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("M4 VISUAL STYLE PROVENANCE VALIDATION: PASS")
    print("Visual Style Bible + 3 provenance docs + physical/context authority boundaries validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
