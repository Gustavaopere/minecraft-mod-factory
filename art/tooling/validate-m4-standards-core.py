#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_STANDARDS = (
    "MODEL-ASSET-CONTRACT.md",
    "VISUAL-QA.md",
    "VFX-QA.md",
    "AUDIO-QA.md",
    "SPELL-PRESENTATION-CONTRACT.md",
)

SOURCE_REPOSITORY = "Gustavaopere/neoforge-rpg-skilltree"
SOURCE_REVISION = "2ecea4178aa7ac80f99955ab045e296da25376ec"
DESTINATION_REPOSITORY = "Gustavaopere/minecraft-mod-factory"
PROVENANCE_PATH = "migration/M4-STANDARDS-CORE-PROVENANCE.json"

SOURCE_BLOBS = {
    "MODEL-ASSET-CONTRACT.md": "3442c8c287e12ce66f8cc2fab441abcd1a90fb72",
    "VISUAL-QA.md": "0652b9b5dd9f19f62a454c5aff5db5d903c15dc9",
    "VFX-QA.md": "a1cfb2e3d870d8975e43dc919b5890f6bc6682a2",
    "AUDIO-QA.md": "c48ec6e9558f655ee17dc1fce913b93278faa42f",
    "SPELL-PRESENTATION-CONTRACT.md": "d5bb4c4c1e918c6537e623f81336bdda3fd15801",
}

REQUIRED_TOKENS = {
    "MODEL-ASSET-CONTRACT.md": (".bbmodel", "UNRESOLVED", "VISUAL-QA.md"),
    "VISUAL-QA.md": ("PENDING VISUAL QA", "dedicated server", "screenshots or captures"),
    "VFX-QA.md": ("versão física", "dedicated server", "PASS WITH DOCUMENTED LIMITATION"),
    "AUDIO-QA.md": ("## 6. Proveniência", "Dedicated server", "PASS WITH DOCUMENTED LIMITATION"),
    "SPELL-PRESENTATION-CONTRACT.md": (
        "não substitui o contrato de gameplay do provider",
        "VFX-QA.md",
        "AUDIO-QA.md",
        "Versão física/JAR confirmada",
    ),
}

FORBIDDEN_STANDARD_TOKENS = (
    "PROJECT-INSTRUCTIONS/",
    "Gustavaopere/neoforge-rpg-skilltree",
)


def _git_blob_sha(data: bytes) -> str:
    result = subprocess.run(
        ["git", "hash-object", "--stdin"],
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git hash-object failed: {stderr or f'exit {result.returncode}'}")
    try:
        object_id = result.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise RuntimeError("git hash-object returned a non-ASCII object id") from exc
    if len(object_id) != 40 or any(char not in "0123456789abcdef" for char in object_id):
        raise RuntimeError(f"git hash-object returned an invalid blob id: {object_id!r}")
    return object_id


def _expected_source_path(name: str) -> str:
    return f"PROJECT-INSTRUCTIONS/skills/standards/{name}"


def _expected_destination(name: str) -> str:
    return f"art/standards/{name}"


def validate_provenance(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / PROVENANCE_PATH
    if not path.is_file():
        return [f"missing {PROVENANCE_PATH}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{PROVENANCE_PATH}: invalid JSON: {exc}"]

    expected_top = {
        "schema_version",
        "migration_wave",
        "classification",
        "source_repository",
        "source_revision",
        "destination_repository",
        "destination_authority",
        "adaptation",
        "files",
    }
    if set(data) != expected_top:
        errors.append(f"{PROVENANCE_PATH}: top-level keys must be exactly {sorted(expected_top)}")
    if data.get("schema_version") != 1:
        errors.append(f"{PROVENANCE_PATH}: schema_version must be 1")
    if data.get("migration_wave") != "M4_STANDARDS_CORE":
        errors.append(f"{PROVENANCE_PATH}: migration_wave must be M4_STANDARDS_CORE")
    if data.get("classification") != "MIGRATE_ADAPTED":
        errors.append(f"{PROVENANCE_PATH}: classification must be MIGRATE_ADAPTED")
    if data.get("source_repository") != SOURCE_REPOSITORY:
        errors.append(f"{PROVENANCE_PATH}: wrong source_repository")
    if data.get("source_revision") != SOURCE_REVISION:
        errors.append(f"{PROVENANCE_PATH}: wrong source_revision")
    if data.get("destination_repository") != DESTINATION_REPOSITORY:
        errors.append(f"{PROVENANCE_PATH}: wrong destination_repository")
    if data.get("destination_authority") != "art/standards/":
        errors.append(f"{PROVENANCE_PATH}: destination_authority must be art/standards/")
    if not isinstance(data.get("adaptation"), str) or not data["adaptation"].strip():
        errors.append(f"{PROVENANCE_PATH}: adaptation must be a non-empty string")

    files = data.get("files")
    if not isinstance(files, list):
        return errors + [f"{PROVENANCE_PATH}: files must be an array"]
    if len(files) != len(REQUIRED_STANDARDS):
        errors.append(f"{PROVENANCE_PATH}: files must contain exactly {len(REQUIRED_STANDARDS)} entries")

    seen = set()
    for index, item in enumerate(files):
        prefix = f"{PROVENANCE_PATH}:files[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: entry must be an object")
            continue
        expected_keys = {"source", "source_blob_sha", "destination", "migration_mode"}
        if set(item) != expected_keys:
            errors.append(f"{prefix}: keys must be exactly {sorted(expected_keys)}")
            continue

        destination = item.get("destination")
        if not isinstance(destination, str):
            errors.append(f"{prefix}: destination must be a string")
            continue
        name = destination.rsplit("/", 1)[-1]
        if name not in REQUIRED_STANDARDS:
            errors.append(f"{prefix}: unexpected destination {destination!r}")
            continue
        if name in seen:
            errors.append(f"{prefix}: duplicate destination for {name}")
            continue
        seen.add(name)

        if item.get("source") != _expected_source_path(name):
            errors.append(f"{prefix}: wrong source path for {name}")
        if item.get("source_blob_sha") != SOURCE_BLOBS[name]:
            errors.append(f"{prefix}: wrong source blob for {name}")
        if destination != _expected_destination(name):
            errors.append(f"{prefix}: wrong destination for {name}")
        if item.get("migration_mode") != "BYTE_IDENTICAL_RELOCATION":
            errors.append(f"{prefix}: migration_mode must be BYTE_IDENTICAL_RELOCATION")

    missing = set(REQUIRED_STANDARDS) - seen
    if missing:
        errors.append(f"{PROVENANCE_PATH}: missing destinations: {', '.join(sorted(missing))}")
    return errors


def run_validation(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    standards_dir = root / "art" / "standards"

    for name in REQUIRED_STANDARDS:
        path = standards_dir / name
        if not path.is_file():
            errors.append(f"missing art/standards/{name}")
            continue

        data = path.read_bytes()
        if not data:
            errors.append(f"art/standards/{name}: empty file")
            continue
        text = data.decode("utf-8")

        for token in FORBIDDEN_STANDARD_TOKENS:
            if token in text:
                errors.append(f"art/standards/{name}: historical coupling token remains: {token}")

        for token in REQUIRED_TOKENS[name]:
            if token not in text:
                errors.append(f"art/standards/{name}: missing invariant token {token!r}")

        actual_blob = _git_blob_sha(data)
        if actual_blob != SOURCE_BLOBS[name]:
            errors.append(
                f"art/standards/{name}: content drifted from audited source blob "
                f"{SOURCE_BLOBS[name]} (actual {actual_blob})"
            )

    for source_name, linked_names in {
        "MODEL-ASSET-CONTRACT.md": ("VISUAL-QA.md",),
        "SPELL-PRESENTATION-CONTRACT.md": ("VFX-QA.md", "AUDIO-QA.md"),
    }.items():
        source_path = standards_dir / source_name
        if not source_path.is_file():
            continue
        source_text = source_path.read_text(encoding="utf-8")
        for linked_name in linked_names:
            if linked_name in source_text and not (standards_dir / linked_name).is_file():
                errors.append(f"art/standards/{source_name}: broken local standard link {linked_name}")

    errors.extend(validate_provenance(root))
    return errors


def main() -> int:
    errors = run_validation(ROOT)
    if errors:
        print("M4 STANDARDS CORE VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("M4 STANDARDS CORE VALIDATION: PASS")
    print("5 byte-identical standards + exact historical provenance validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
