#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PROVENANCE_PATH = "migration/M4-ART-TEMPLATES-PROVENANCE.json"
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

REQUIRED_TEMPLATES = tuple(
    f"art/templates/{source.rsplit('/', 1)[-1]}" for source in SOURCE_BLOBS
)
EXPECTED_DESTINATIONS = dict(zip(SOURCE_BLOBS, REQUIRED_TEMPLATES))

REQUIRED_TOKENS = {
    "ANIMATION-BRIEF.md": ("Gameplay/presentation owner:", "Trigger/boundary real:", "provider coexistence + evidence:", "QA evidence:"),
    "ASSET-BRIEF.md": ("Owner/repositório:", "Proveniência/licença:", "Evidência final exigida:"),
    "AUDIO-CUE-SHEET.md": ("Gameplay owner:", "verify exact API", "target runtime mix", "Provenance/license:"),
    "MODEL-BRIEF.md": ("Source `.bbmodel`:", "Structural validator profile:", "In-game QA scenes:"),
    "SPELL-BRIEF.md": ("Gameplay provider/owner:", "Authoritative cast boundary:", "Dedicated-server separation:", "Acceptance evidence:"),
    "VFX-BRIEF.md": ("Backend candidate + evidence:", "Accessibility/reduced-effects path:", "Performance evidence required:"),
    "VISUAL-QA.md": ("Structural validator:", "Visual result: PASS / FAIL / PENDING", "Evidence links/screenshots:", "Remaining risk:"),
}

FORBIDDEN = (
    "PROJECT-INSTRUCTIONS/",
    "Gustavaopere/neoforge-rpg-skilltree",
    "Epic Fight/Fresh Animations/provider coexistence",
    "modpack mix",
)

ABSENT_DESTINATIONS = (
    "art/templates/VISUAL-QA-CHECKLIST.md",
    "art/templates/README.md",
    "art/templates/blockbench",
)

EXPECTED_META = {
    "schema_version": 1,
    "migration_wave": "M4_ART_TEMPLATES",
    "classification": "MIGRATE_ADAPTED",
    "source_repository": SOURCE_REPOSITORY,
    "source_revision": SOURCE_REVISION,
    "destination_repository": "Gustavaopere/minecraft-mod-factory",
    "destination_authority": "art/templates/",
}

EXPECTED_RECONCILIATION = {
    "matrix_named_path": "PROJECT-INSTRUCTIONS/skills/templates/VISUAL-QA-CHECKLIST.md",
    "matrix_named_path_state": "ABSENT",
    "physical_source_path": "PROJECT-INSTRUCTIONS/skills/templates/VISUAL-QA.md",
    "resolution": "PHYSICAL_TREE_WINS",
    "templates_readme_state": "ABSENT",
    "blockbench_specialization_state": "ABSENT",
}


def validate_templates(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_TEMPLATES:
        path = root / relative
        if not path.is_file():
            errors.append(f"missing {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            errors.append(f"{relative}: empty template")
            continue
        lowered = text.lower()
        errors.extend(
            f"{relative}: forbidden token {token}"
            for token in FORBIDDEN
            if token.lower() in lowered
        )
        errors.extend(
            f"{relative}: missing token {token!r}"
            for token in REQUIRED_TOKENS[path.name]
            if token not in text
        )
    errors.extend(
        f"unexpected stale-matrix artifact: {relative}"
        for relative in ABSENT_DESTINATIONS
        if (root / relative).exists()
    )
    return errors


def validate_migration_provenance(root: Path) -> list[str]:
    path = root / MIGRATION_PROVENANCE_PATH
    if not path.is_file():
        return [f"missing {MIGRATION_PROVENANCE_PATH}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"invalid provenance JSON: {exc}"]

    errors = [
        f"provenance {key} drift: {data.get(key)!r}"
        for key, expected in EXPECTED_META.items()
        if data.get(key) != expected
    ]
    allowed_keys = set(EXPECTED_META) | {"matrix_reconciliation", "files"}
    if set(data) != allowed_keys:
        errors.append("provenance top-level keys drift")
    if data.get("matrix_reconciliation") != EXPECTED_RECONCILIATION:
        errors.append("matrix reconciliation drift")

    files = data.get("files")
    if not isinstance(files, list):
        return errors + ["provenance files must be a list"]

    by_source = {
        item.get("source"): item
        for item in files
        if isinstance(item, dict) and isinstance(item.get("source"), str)
    }
    if len(files) != len(SOURCE_BLOBS) or set(by_source) != set(SOURCE_BLOBS):
        errors.append("provenance source set drift")
        return errors

    expected_item_keys = {"source", "source_blob_sha", "destination", "adaptation_mode"}
    for source, blob in SOURCE_BLOBS.items():
        item = by_source[source]
        if set(item) != expected_item_keys:
            errors.append(f"{source}: provenance item keys drift")
        if item.get("source_blob_sha") != blob:
            errors.append(f"{source}: source blob drift")
        if item.get("destination") != EXPECTED_DESTINATIONS[source]:
            errors.append(f"{source}: destination drift")
        if not isinstance(item.get("adaptation_mode"), str) or not item["adaptation_mode"]:
            errors.append(f"{source}: missing adaptation mode")
    return errors


def run_validation(root: Path = ROOT) -> list[str]:
    return [*validate_templates(root), *validate_migration_provenance(root)]


def main() -> int:
    errors = run_validation(ROOT)
    if errors:
        print("M4 ART TEMPLATES VALIDATION: FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("M4 ART TEMPLATES VALIDATION: PASS")
    print("7 physical-source templates + provenance + matrix reconciliation validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
