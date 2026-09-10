#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENG = ROOT / "engineering"

SCHEMA_EXAMPLES = {
    "mod-spec.schema.json": "mod-spec.example.json",
    "dependency-profile.schema.json": "dependency-profile.example.json",
    "asset-handoff.schema.json": "asset-handoff.example.json",
    "compatibility-matrix.schema.json": "compatibility-matrix.example.json",
    "test-manifest.schema.json": "test-manifest.example.json",
}

EVIDENCE_STATES = {
    "CONFIRMED",
    "IMPLEMENTED",
    "MERGED",
    "PASS",
    "PENDING",
    "UNRESOLVED",
    "UNAVAILABLE",
    "DEFERRED",
    "REFERENCE_ONLY",
    "INCOMPATIBLE",
    "BLOCKED",
    "SUPERSEDED",
}

CANONICAL_AUTHORITY_ORDER = [
    "runtime_mod_repository",
    "physical_runtime_artifact_or_jar",
    "latest_physical_modlist",
    "exact_provider_source_ref",
    "official_target_documentation",
    "factory_engineering_control_plane",
    "factory_art_authority",
    "editorial_or_community_reference",
]

REQUIRED_I1_SOURCE_IDS = {
    "integration_control_plane",
    "repo_textura",
    "historical_rpg_repository",
    "latest_physical_modlist_2026_09_09",
    "mod_engineering_plan_v1_1",
    "repo_textura_plan_v5_1",
}

ALLOWED_SOURCE_TYPES = {
    "git_repository",
    "git_repository_domain",
    "physical_snapshot_external",
    "local_artifact",
}

FACTORY_SCHEMA_ID_PREFIX = (
    "https://github.com/Gustavaopere/minecraft-mod-factory/engineering/schemas/"
)
HISTORICAL_RPG_SCHEMA_ID_PREFIX = (
    "https://github.com/Gustavaopere/neoforge-rpg-skilltree/"
)

ASCII_LOWER = frozenset("abcdefghijklmnopqrstuvwxyz")
ASCII_LOWER_DIGIT_UNDERSCORE = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
LOWER_HEX = frozenset("0123456789abcdef")

MOD_ID_PATTERN = "^[a-z][a-z0-9_]{1,63}$"
VISUAL_INPUT_NAME_PATTERN = "^[a-z][a-z0-9_]{0,63}$"
SOURCE_REVISION_PATTERN = "^(?:[0-9a-f]{40}|UNRESOLVED)$"
SHA256_OR_UNRESOLVED_PATTERN = "^(?:[0-9a-f]{64}|UNRESOLVED)$"


def _matches_registry_id(value, minimum_tail_length):
    return (
        isinstance(value, str)
        and minimum_tail_length + 1 <= len(value) <= 64
        and value[0] in ASCII_LOWER
        and all(char in ASCII_LOWER_DIGIT_UNDERSCORE for char in value[1:])
    )


def _matches_mod_id(value):
    return _matches_registry_id(value, 1)


def _matches_visual_input_name(value):
    return _matches_registry_id(value, 0)


def _matches_hex_or_unresolved(value, length):
    return value == "UNRESOLVED" or (
        isinstance(value, str)
        and len(value) == length
        and all(char in LOWER_HEX for char in value)
    )


def _matches_source_revision(value):
    return _matches_hex_or_unresolved(value, 40)


def _matches_sha256_or_unresolved(value):
    return _matches_hex_or_unresolved(value, 64)


PATTERN_VALIDATORS = {
    MOD_ID_PATTERN: _matches_mod_id,
    VISUAL_INPUT_NAME_PATTERN: _matches_visual_input_name,
    SOURCE_REVISION_PATTERN: _matches_source_revision,
    SHA256_OR_UNRESOLVED_PATTERN: _matches_sha256_or_unresolved,
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _type_ok(value, expected):
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def validate_instance(schema, value, path="$"):
    errors = []
    expected = schema.get("type")
    if isinstance(expected, list):
        if not any(_type_ok(value, item) for item in expected):
            return [f"{path}: expected one of {expected}, got {type(value).__name__}"]
    elif expected and not _type_ok(value, expected):
        return [f"{path}: expected {expected}, got {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength")
        if "pattern" in schema:
            pattern = schema["pattern"]
            validator = PATTERN_VALIDATORS.get(pattern)
            if validator is None:
                errors.append(f"{path}: unsupported pattern {pattern!r}")
            elif not validator(value):
                errors.append(f"{path}: does not match pattern {pattern}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems")
        if schema.get("uniqueItems"):
            seen = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            if len(seen) != len(set(seen)):
                errors.append(f"{path}: duplicate array items")
        if "items" in schema:
            for index, item in enumerate(value):
                errors += validate_instance(schema["items"], item, f"{path}[{index}]")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                errors += validate_instance(properties[key], item, f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property {key!r}")

    return errors


def iter_declared_patterns(node, path="$"):
    if isinstance(node, dict):
        pattern = node.get("pattern")
        if isinstance(pattern, str):
            yield path, pattern
        for key, value in node.items():
            yield from iter_declared_patterns(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from iter_declared_patterns(value, f"{path}[{index}]")


def validate_schema_document(path: Path, schema):
    errors = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append(f"{path}: wrong or missing $schema")

    schema_id = schema.get("$id")
    expected_id = FACTORY_SCHEMA_ID_PREFIX + path.name
    if schema_id != expected_id:
        errors.append(f"{path}: $id must be {expected_id!r}")
    if isinstance(schema_id, str) and schema_id.startswith(HISTORICAL_RPG_SCHEMA_ID_PREFIX):
        errors.append(f"{path}: historical RPG repository must not remain schema authority")

    if schema.get("type") != "object":
        errors.append(f"{path}: root type must be object")
    if not isinstance(schema.get("properties"), dict):
        errors.append(f"{path}: root properties must be object")
    if not isinstance(schema.get("required"), list):
        errors.append(f"{path}: root required must be array")
    if schema.get("additionalProperties") is not False:
        errors.append(f"{path}: root must fail closed with additionalProperties=false")

    for pattern_path, pattern in iter_declared_patterns(schema):
        if not (pattern.startswith("^") and pattern.endswith("$")):
            errors.append(
                f"{path}:{pattern_path}: pattern must be explicitly anchored for JSON Schema search semantics"
            )
        if pattern not in PATTERN_VALIDATORS:
            errors.append(f"{path}:{pattern_path}: unsupported pattern {pattern!r}")
    return errors


def validate_asset_handoff_semantics(value, path="$"):
    errors = []
    if not isinstance(value, dict) or not isinstance(value.get("artifacts"), list):
        return errors
    for index, artifact in enumerate(value["artifacts"]):
        if not isinstance(artifact, dict):
            continue
        subject = f"{path}.artifacts[{index}]"
        source_format = artifact.get("source_format")
        delivery_format = artifact.get("delivery_format")
        conversion = artifact.get("conversion")
        if not (
            isinstance(source_format, str)
            and isinstance(delivery_format, str)
            and isinstance(conversion, dict)
        ):
            continue
        expected_performed = source_format != delivery_format
        performed = conversion.get("performed")
        if isinstance(performed, bool) and performed != expected_performed:
            errors.append(
                f"{subject}.conversion.performed: must be {expected_performed} when "
                f"source_format={source_format!r} and delivery_format={delivery_format!r}"
            )
        if conversion.get("from_format") != source_format:
            errors.append(f"{subject}.conversion.from_format: must equal source_format")
        if conversion.get("to_format") != delivery_format:
            errors.append(f"{subject}.conversion.to_format: must equal delivery_format")
    return errors


def validate_source_registry_data(data, path="SOURCE-REGISTRY.json"):
    errors = []
    if not isinstance(data, dict):
        return [f"{path}: registry root must be object"]
    if data.get("schema_version") != 2:
        errors.append(f"{path}: schema_version must be 2")
    if data.get("authority_order") != CANONICAL_AUTHORITY_ORDER:
        errors.append(f"{path}: authority_order must exactly match Factory governance")

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        return errors + [f"{path}: sources must be non-empty array"]

    ids = []
    for index, source in enumerate(sources):
        subject = f"{path}:sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{subject}: source must be object")
            continue
        for key in ("source_id", "source_type", "authority_scope", "state", "locator"):
            if key not in source:
                errors.append(f"{subject}: missing {key}")
        source_id = source.get("source_id")
        if isinstance(source_id, str):
            ids.append(source_id)
        if source.get("state") not in EVIDENCE_STATES:
            errors.append(f"{subject}: invalid evidence state")
        if source.get("source_type") not in ALLOWED_SOURCE_TYPES:
            errors.append(f"{subject}: invalid source_type")
        if not isinstance(source.get("locator"), dict) or not source.get("locator"):
            errors.append(f"{subject}: locator must be non-empty object")

    if len(ids) != len(set(ids)):
        errors.append(f"{path}: duplicate source_id")
    missing = sorted(REQUIRED_I1_SOURCE_IDS.difference(ids))
    if missing:
        errors.append(f"{path}: missing required I1 source_id(s): {', '.join(missing)}")
    return errors


def validate_source_registry(path: Path):
    return validate_source_registry_data(load_json(path), str(path))


def run_validation(root=ROOT):
    eng = root / "engineering"
    errors = []
    schemas_dir = eng / "schemas"
    examples_dir = eng / "examples"

    for schema_name, example_name in SCHEMA_EXAMPLES.items():
        schema_path = schemas_dir / schema_name
        example_path = examples_dir / example_name
        if not schema_path.is_file():
            errors.append(f"missing {schema_path.relative_to(root)}")
            continue
        if not example_path.is_file():
            errors.append(f"missing {example_path.relative_to(root)}")
            continue
        try:
            schema = load_json(schema_path)
            example = load_json(example_path)
        except Exception as exc:
            errors.append(f"{schema_name}/{example_name}: JSON parse failed: {exc}")
            continue
        errors += validate_schema_document(schema_path, schema)
        errors += [f"{example_path}: {error}" for error in validate_instance(schema, example)]
        if schema_name == "asset-handoff.schema.json":
            errors += [
                f"{example_path}: {error}"
                for error in validate_asset_handoff_semantics(example)
            ]

    source_registry = eng / "catalog" / "sources" / "SOURCE-REGISTRY.json"
    if not source_registry.is_file():
        errors.append(f"missing {source_registry.relative_to(root)}")
    else:
        try:
            errors += validate_source_registry(source_registry)
        except Exception as exc:
            errors.append(f"{source_registry}: validation failed: {exc}")

    contract = eng / "contracts" / "MOD-SPEC-CONTRACT.md"
    if not contract.is_file():
        errors.append(f"missing {contract.relative_to(root)}")
    else:
        text = contract.read_text(encoding="utf-8")
        for token in (
            "mod-spec.schema.json",
            "UNRESOLVED",
            "runtime authority",
            "art/",
            "engineering/tooling/validate-i1-foundation.py",
        ):
            if token not in text:
                errors.append(f"{contract}: missing contract token {token!r}")
        if "PROJECT-INSTRUCTIONS/engineering" in text:
            errors.append(f"{contract}: historical RPG engineering path must not remain canonical")

    return errors


def main():
    errors = run_validation()
    if errors:
        print("I1 FOUNDATION VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("I1 FOUNDATION VALIDATION: PASS")
    print("5 schemas + 5 examples + source registry v2 + mod-spec contract validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
