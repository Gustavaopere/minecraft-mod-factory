#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import zipfile
from pathlib import Path


INTEGRATION_ROOT = Path(__file__).resolve().parents[3]
ENGINEERING = INTEGRATION_ROOT / "engineering"
I1_VALIDATOR = ENGINEERING / "tooling" / "validate-i1-foundation.py"
MOD_SPEC_SCHEMA = ENGINEERING / "schemas" / "mod-spec.schema.json"
ASSET_HANDOFF_SCHEMA = ENGINEERING / "schemas" / "asset-handoff.schema.json"

JAVA_PACKAGE_RE = re.compile(r"(?m)^\s*package\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*;")
JAVA_CLASS_RE = re.compile(r"\b(?:class|record|enum|interface)\s+([A-Za-z_$][\w$]*)\b")
MOD_ID_LITERAL_RE = re.compile(r'\bMOD_ID\s*=\s*"([a-z][a-z0-9_]{1,63})"')
RESOURCE_NAMESPACE_RE = re.compile(r"^[a-z0-9_.-]+$")
RESOURCE_PATH_RE = re.compile(r"^[a-z0-9/._-]+$")
SECTION_HEADER_RE = re.compile(r"(?m)^\s*\[\[([^\]]+)\]\]\s*")
CLIENT_ONLY_TOKENS = (
    "net.minecraft.client",
    "com.mojang.blaze3d",
)


def _load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_i1_validator():
    spec = importlib.util.spec_from_file_location("engineering_i1_validator", I1_VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical I1 validator from {I1_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_against_schema(value, schema_path: Path, label: str) -> list[str]:
    i1 = _load_i1_validator()
    schema = _load_json(schema_path)
    return [f"{label}: {error}" for error in i1.validate_instance(schema, value)]


def _load_mod_spec(path: Path) -> tuple[dict | None, list[str]]:
    try:
        value = _load_json(path)
    except Exception as exc:
        return None, [f"mod spec {path}: JSON parse failed: {exc}"]
    errors = _validate_against_schema(value, MOD_SPEC_SCHEMA, f"mod spec {path}")
    return value, errors


def _read_gradle_properties(project_root: Path) -> tuple[dict[str, str], list[str]]:
    path = Path(project_root) / "gradle.properties"
    if not path.is_file():
        return {}, [f"missing {path}"]
    values: dict[str, str] = {}
    errors: list[str] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in values:
            errors.append(f"{path}:{number}: duplicate property {key!r}")
        values[key] = value.strip()
    return values, errors


def _java_sources(project_root: Path) -> list[Path]:
    root = Path(project_root) / "src" / "main" / "java"
    return sorted(path for path in root.rglob("*.java") if path.is_file()) if root.is_dir() else []


def _metadata_path(project_root: Path) -> Path:
    return Path(project_root) / "src" / "main" / "resources" / "META-INF" / "neoforge.mods.toml"


def validate_package(project_root: Path) -> list[str]:
    project_root = Path(project_root)
    source_root = project_root / "src" / "main" / "java"
    errors: list[str] = []
    if not source_root.is_dir():
        return [f"missing Java source root {source_root}"]

    sources = _java_sources(project_root)
    if not sources:
        return [f"no Java sources under {source_root}"]

    for path in sources:
        text = path.read_text(encoding="utf-8")
        match = JAVA_PACKAGE_RE.search(text)
        if match is None:
            errors.append(f"{path}: missing package declaration")
            continue
        declared = match.group(1)
        expected = ".".join(path.relative_to(source_root).parts[:-1])
        if declared != expected:
            errors.append(f"{path}: package {declared!r} does not match source path package {expected!r}")
    return errors


def validate_mod_id(project_root: Path, mod_spec_path: Path) -> list[str]:
    project_root = Path(project_root)
    mod_spec, errors = _load_mod_spec(Path(mod_spec_path))
    if mod_spec is None:
        return errors
    expected = mod_spec["identity"]["mod_id"]

    properties, property_errors = _read_gradle_properties(project_root)
    errors += property_errors
    actual_property = properties.get("mod_id")
    if actual_property is None:
        errors.append(f"{project_root / 'gradle.properties'}: missing mod_id")
    elif actual_property != expected:
        errors.append(f"gradle.properties mod_id {actual_property!r} does not match Mod Spec {expected!r}")

    literal_ids: set[str] = set()
    for source in _java_sources(project_root):
        literal_ids.update(MOD_ID_LITERAL_RE.findall(source.read_text(encoding="utf-8")))
    for literal in sorted(literal_ids):
        if literal != expected:
            errors.append(f"Java MOD_ID {literal!r} does not match Mod Spec {expected!r}")

    metadata = _metadata_path(project_root)
    if not metadata.is_file():
        errors.append(f"missing {metadata}")
    else:
        text = metadata.read_text(encoding="utf-8")
        mods_section = text.split("[[dependencies.", 1)[0]
        match = re.search(r'(?m)^\s*modId\s*=\s*"([^"]+)"\s*$', mods_section)
        if match is None:
            errors.append(f"{metadata}: missing [[mods]] modId")
        else:
            value = match.group(1)
            if value not in {expected, "${mod_id}"}:
                errors.append(f"{metadata}: modId {value!r} does not match Mod Spec {expected!r}")
    return errors


def _metadata_dependencies(metadata_text: str) -> tuple[list[tuple[str, str]], list[str]]:
    entries: list[tuple[str, str]] = []
    errors: list[str] = []
    headers = list(SECTION_HEADER_RE.finditer(metadata_text))
    dependency_index = 0
    for header_index, match in enumerate(headers):
        if not match.group(1).startswith("dependencies."):
            continue
        body_end = headers[header_index + 1].start() if header_index + 1 < len(headers) else len(metadata_text)
        body = metadata_text[match.end():body_end]
        mod_match = re.search(r'(?m)^\s*modId\s*=\s*"([^"]+)"\s*$', body)
        type_match = re.search(r'(?m)^\s*type\s*=\s*"([^"]+)"\s*$', body)
        if mod_match is None:
            errors.append(f"dependency block {dependency_index}: missing modId")
            dependency_index += 1
            continue
        dep_type = type_match.group(1) if type_match is not None else "required"
        entries.append((mod_match.group(1), dep_type))
        dependency_index += 1
    return entries, errors


def validate_dependencies(project_root: Path, mod_spec_path: Path) -> list[str]:
    project_root = Path(project_root)
    mod_spec, errors = _load_mod_spec(Path(mod_spec_path))
    if mod_spec is None:
        return errors

    metadata = _metadata_path(project_root)
    if not metadata.is_file():
        return errors + [f"missing {metadata}"]
    entries, parse_errors = _metadata_dependencies(metadata.read_text(encoding="utf-8"))
    errors += [f"{metadata}: {error}" for error in parse_errors]

    expected_types: dict[str, str] = {"neoforge": "required", "minecraft": "required"}
    for mod_id in mod_spec["dependencies"]["required"]:
        expected_types[mod_id] = "required"
    for mod_id in mod_spec["dependencies"]["optional"]:
        expected_types[mod_id] = "optional"
    for mod_id in mod_spec["dependencies"]["incompatible"]:
        expected_types[mod_id] = "incompatible"

    actual_types: dict[str, str] = {}
    for mod_id, dep_type in entries:
        if mod_id in actual_types:
            errors.append(f"{metadata}: duplicate dependency declaration for {mod_id!r}")
        actual_types[mod_id] = dep_type

    for mod_id, dep_type in expected_types.items():
        if mod_id not in actual_types:
            errors.append(f"{metadata}: missing dependency {mod_id!r}")
        elif actual_types[mod_id] != dep_type:
            errors.append(
                f"{metadata}: dependency {mod_id!r} type {actual_types[mod_id]!r} does not match {dep_type!r}"
            )
    for mod_id in sorted(set(actual_types).difference(expected_types)):
        errors.append(f"{metadata}: undeclared dependency {mod_id!r}")
    return errors


def validate_resource_paths(project_root: Path) -> list[str]:
    resources = Path(project_root) / "src" / "main" / "resources"
    if not resources.is_dir():
        return [f"missing resource root {resources}"]
    errors: list[str] = []
    for domain in ("assets", "data"):
        domain_root = resources / domain
        if not domain_root.exists():
            continue
        for path in sorted(p for p in domain_root.rglob("*") if p.is_file()):
            relative = path.relative_to(domain_root).as_posix()
            parts = relative.split("/", 1)
            if len(parts) != 2:
                errors.append(f"{path}: resource must be under {domain}/<namespace>/<path>")
                continue
            namespace, resource_path = parts
            if RESOURCE_NAMESPACE_RE.fullmatch(namespace) is None:
                errors.append(f"{path}: invalid resource namespace {namespace!r}")
            if RESOURCE_PATH_RE.fullmatch(resource_path) is None:
                errors.append(f"{path}: invalid ResourceLocation path {resource_path!r}")
    return errors


def validate_side_boundaries(project_root: Path) -> list[str]:
    source_root = Path(project_root) / "src" / "main" / "java"
    if not source_root.is_dir():
        return [f"missing Java source root {source_root}"]
    errors: list[str] = []
    for path in _java_sources(Path(project_root)):
        relative_parts = path.relative_to(source_root).parts[:-1]
        is_client_source = "client" in relative_parts
        if is_client_source:
            continue
        text = path.read_text(encoding="utf-8")
        for token in CLIENT_ONLY_TOKENS:
            if token in text:
                errors.append(f"{path}: common source references client-only namespace {token!r}")
    return errors


def validate_assets_manifest(
    project_root: Path,
    mod_spec_path: Path,
    asset_handoff_path: Path,
) -> list[str]:
    del project_root  # Project layout is validated by the other I4 gates.
    mod_spec, errors = _load_mod_spec(Path(mod_spec_path))
    if mod_spec is None:
        return errors
    try:
        handoff = _load_json(Path(asset_handoff_path))
    except Exception as exc:
        return errors + [f"asset handoff {asset_handoff_path}: JSON parse failed: {exc}"]

    errors += _validate_against_schema(handoff, ASSET_HANDOFF_SCHEMA, f"asset handoff {asset_handoff_path}")
    i1 = _load_i1_validator()
    errors += [
        f"asset handoff {asset_handoff_path}: {error}"
        for error in i1.validate_asset_handoff_semantics(handoff)
    ]

    expected_mod_id = mod_spec["identity"]["mod_id"]
    if handoff.get("mod_id") != expected_mod_id:
        errors.append(
            f"asset handoff mod_id {handoff.get('mod_id')!r} does not match Mod Spec {expected_mod_id!r}"
        )

    expected_manifest = mod_spec["visual"]["handoff_manifest"]
    supplied = Path(asset_handoff_path)
    expected_path = Path(expected_manifest)
    if not expected_path.is_absolute():
        root_candidate = INTEGRATION_ROOT / expected_path
        spec_candidate = Path(mod_spec_path).resolve().parent / expected_path
        if supplied.resolve() not in {root_candidate.resolve(), spec_candidate.resolve()}:
            errors.append(
                f"asset handoff path {supplied} does not match Mod Spec handoff_manifest {expected_manifest!r}"
            )

    for index, artifact in enumerate(handoff.get("artifacts", [])):
        delivery_path = artifact.get("delivery_path")
        if not isinstance(delivery_path, str):
            continue
        normalized = delivery_path.replace("\\", "/")
        expected_prefix = f"src/main/resources/assets/{expected_mod_id}/"
        if not normalized.startswith(expected_prefix):
            errors.append(
                f"asset handoff artifact {index}: delivery_path must start with {expected_prefix!r}"
            )
        resource_relative = normalized[len("src/main/resources/assets/") :] if normalized.startswith("src/main/resources/assets/") else ""
        if resource_relative:
            parts = resource_relative.split("/", 1)
            if len(parts) != 2 or RESOURCE_NAMESPACE_RE.fullmatch(parts[0]) is None or RESOURCE_PATH_RE.fullmatch(parts[1]) is None:
                errors.append(f"asset handoff artifact {index}: invalid canonical delivery resource path {delivery_path!r}")
    return errors


def validate_datagen_drift(project_root: Path) -> list[str]:
    project_root = Path(project_root)
    wrapper = project_root / "gradlew"
    if not wrapper.is_file():
        return [f"missing Gradle wrapper {wrapper}"]
    if not wrapper.stat().st_mode & 0o111:
        return [f"Gradle wrapper is not executable: {wrapper}"]

    errors: list[str] = []
    try:
        generated = subprocess.run(
            [str(wrapper), "runData", "--no-daemon"],
            cwd=project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except Exception as exc:
        return [f"official datagen command failed to start: {exc}"]
    if generated.returncode != 0:
        output = generated.stdout.strip()
        errors.append(f"official datagen command exited {generated.returncode}: {output}")
        return errors

    for diff_command, label in (
        (["git", "diff", "--check"], "git diff --check"),
        (["git", "diff", "--exit-code"], "git diff --exit-code"),
    ):
        result = subprocess.run(
            diff_command,
            cwd=project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if result.returncode != 0:
            output = result.stdout.strip()
            errors.append(f"datagen drift: {label} failed" + (f": {output}" if output else ""))
    return errors


def _mod_entrypoint_classes(project_root: Path) -> list[str]:
    classes: list[str] = []
    for source in _java_sources(Path(project_root)):
        text = source.read_text(encoding="utf-8")
        if "@Mod(" not in text and "@Mod(" not in text.replace(" ", ""):
            continue
        package_match = JAVA_PACKAGE_RE.search(text)
        class_match = JAVA_CLASS_RE.search(text)
        if package_match is None or class_match is None:
            continue
        classes.append(f"{package_match.group(1).replace('.', '/')}/{class_match.group(1)}.class")
    return sorted(set(classes))


def inspect_jar(project_root: Path, jar_path: Path) -> list[str]:
    project_root = Path(project_root)
    jar_path = Path(jar_path)
    if not jar_path.is_file():
        return [f"missing JAR {jar_path}"]
    errors: list[str] = []
    try:
        with zipfile.ZipFile(jar_path) as jar:
            names = set(jar.namelist())
            metadata_name = "META-INF/neoforge.mods.toml"
            if metadata_name not in names:
                errors.append(f"{jar_path}: missing {metadata_name}")
            else:
                try:
                    metadata_text = jar.read(metadata_name).decode("utf-8")
                except UnicodeDecodeError as exc:
                    errors.append(f"{jar_path}: {metadata_name} is not UTF-8: {exc}")
                else:
                    properties, property_errors = _read_gradle_properties(project_root)
                    errors += property_errors
                    mod_id = properties.get("mod_id")
                    if mod_id and not re.search(rf'(?m)^\s*modId\s*=\s*"{re.escape(mod_id)}"\s*$', metadata_text):
                        errors.append(f"{jar_path}: metadata does not contain project mod_id {mod_id!r}")
            entrypoints = _mod_entrypoint_classes(project_root)
            if not entrypoints:
                errors.append(f"{project_root}: no @Mod entrypoint Java classes found")
            for class_path in entrypoints:
                if class_path not in names:
                    errors.append(f"{jar_path}: missing compiled mod entrypoint {class_path}")
    except (OSError, zipfile.BadZipFile) as exc:
        return [f"cannot inspect JAR {jar_path}: {exc}"]
    return errors
