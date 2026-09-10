#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PROVENANCE_PATH = "migration/M4-ART-TEMPLATES-PROVENANCE.json"

REQUIRED_TEMPLATES = (
    "art/templates/ANIMATION-BRIEF.md",
    "art/templates/ASSET-BRIEF.md",
    "art/templates/AUDIO-CUE-SHEET.md",
    "art/templates/MODEL-BRIEF.md",
    "art/templates/SPELL-BRIEF.md",
    "art/templates/VFX-BRIEF.md",
    "art/templates/VISUAL-QA.md",
)

SOURCE_REPOSITORY = "Gustavaopere/neoforge-rpg-skilltree"
SOURCE_REVISION = "2ecea4178aa7ac80f99955ab045e296da25376ec"
SOURCE_BLOBS = {
    "PROJECT-INSTRUCTIONS/skills/templates/ANIMATION-BRIEF.md": "efc7357301e109639a760bbda22eaafdd8c6a267",
    "PROJECT-INSTRUCTIONS/skills/templates/ASSET-BRIEF.md": "2be877eb332c8b56f4d2a152d89426c4ea2ad875",
    "PROJECT-INSTRUCTIONS/skills/templates/AUDIO-CUE-SHEET.md": "1c010f6379276291484ef278426635525161b3d0",
    "PROJECT-INSTRUCTIONS/skills/templates/MODEL-BRIEF.md": "c02894b55948d43c53283e14b45d21784c970c01",
    "PROJECT-INSTRUCTIONS/skills/templates/SPELL-BRIEF.md": "35854860642e2ebd2a0d871b61422fc8b4c63b01",
    "PROJECT-INSTRUCTIONS/skills/templates/VFX-BRIEF.md": "7db8337b8f567557ff3edfd2a8026a9e413facc9",
    "PROJECT-INSTRUCTIONS/skills/templates/VISUAL-QA.md": "d3f9d57c2bc2f51237693d2622f6ec3bf881a286",
}

EXPECTED_DESTINATIONS = {
    source: "art/templates/" + source.rsplit("/", 1)[-1]
    for source in SOURCE_BLOBS
}

REQUIRED_TOKENS = {
    "art/templates/ANIMATION-BRIEF.md": (
        "Gameplay/presentation owner:",
        "Trigger/boundary real:",
        "provider coexistence + evidence:",
        "QA evidence:",
    ),
    "art/templates/ASSET-BRIEF.md": (
        "Owner/repositório:",
        "Proveniência/licença:",
        "Evidência final exigida:",
    ),
    "art/templates/AUDIO-CUE-SHEET.md": (
        "Gameplay owner:",
        "verify exact API",
        "target runtime mix",
        "Provenance/license:",
    ),
    "art/templates/MODEL-BRIEF.md": (
        "Source `.bbmodel`:",
        "Structural validator profile:",
        "In-game QA scenes:",
    ),
    "art/templates/SPELL-BRIEF.md": (
        "Gameplay provider/owner:",
        "Authoritative cast boundary:",
        "Dedicated-server separation:",
        "Acceptance evidence:",
    ),
    "art/templates/VFX-BRIEF.md": (
        "Backend candidate + evidence:",
        "Accessibility/reduced-effects path:",
        "Performance evidence required:",
    ),
    "art/templates/VISUAL-QA.md": (
        "Structural validator:",
        "Visual result: PASS / FAIL / PENDING",
        "Evidence links/screenshots:",
        "Remaining risk:",
    ),
}

FORBIDDEN_TEMPLATE_TOKENS = (
    "PROJECT-INSTRUCTIONS/",
    "Gustavaopere/neoforge-rpg-skilltree",
    "Epic Fight/Fresh Animations/provider coexistence",
    "modpack mix",
)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_templates(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_TEMPLATES:
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
            errors.append(f"{relative}: empty template")
            continue
        for token in FORBIDDEN_TEMPLATE_TOKENS:
            if token.lower() in text.lower():
                errors.append(f"{relative}: forbidden historical/default token remains: {token}")
        for token in REQUIRED_TOKENS[relative]:
            if token not in text:
                errors.append(f"{relative}: missing required contract/evidence token {token!r}")

    for absent in (
        "art/templates/VISUAL-QA-CHECKLIST.md",
        "art/templates/README.md",
        "art/templates/blockbench",
    ):
        if (root / absent).exists():
            errors.append(f"unexpected migration artifact from stale matrix entry: {absent}")
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
        "matrix_reconciliation",
        "files",
    }
    if set(data) != expected_top:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: top-level keys must be exactly {sorted(expected_top)}")
    if data.get("schema_version") != 1:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: schema_version must be 1")
    if data.get("migration_wave") != "M4_ART_TEMPLATES":
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: wrong migration_wave")
    if data.get("classification") != "MIGRATE_ADAPTED":
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: classification must be MIGRATE_ADAPTED")
    if data.get("source_repository") != SOURCE_REPOSITORY:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: wrong source_repository")
    if data.get("source_revision") != SOURCE_REVISION:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: wrong source_revision")
    if data.get("destination_repository") != "Gustavaopere/minecraft-mod-factory":
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: wrong destination_repository")
    if data.get("destination_authority") != "art/templates/":
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: destination_authority must be art/templates/")

    reconciliation = data.get("matrix_reconciliation")
    expected_reconciliation = {
        "matrix_named_path": "PROJECT-INSTRUCTIONS/skills/templates/VISUAL-QA-CHECKLIST.md",
        "matrix_named_path_state": "ABSENT",
        "physical_source_path": "PROJECT-INSTRUCTIONS/skills/templates/VISUAL-QA.md",
        "resolution": "PHYSICAL_TREE_WINS",
        "templates_readme_state": "ABSENT",
        "blockbench_specialization_state": "ABSENT",
    }
    if reconciliation != expected_reconciliation:
        errors.append(f"{MIGRATION_PROVENANCE_PATH}: matrix reconciliation drift")

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
            if not isinstance(mode, str) or not mode:
                errors.append(f"{prefix}: adaptation_mode must be non-empty")
        missing = set(SOURCE_BLOBS) - seen
        if missing:
            errors.append(f"{MIGRATION_PROVENANCE_PATH}: missing sources: {', '.join(sorted(missing))}")
    return errors


def run_validation(root: Path = ROOT) -> list[str]:
    return validate_templates(root) + validate_migration_provenance(root)


def main() -> int:
    errors = run_validation(ROOT)
    if errors:
        print("M4 ART TEMPLATES VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("M4 ART TEMPLATES VALIDATION: PASS")
    print("7 physical-source templates + provenance + matrix reconciliation validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
