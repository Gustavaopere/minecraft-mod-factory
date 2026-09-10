#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_ROOT = REPO_ROOT / "engineering" / "templates" / "neoforge-mod"

EXPECTED_TARGET = {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "neoforge": "21.1.248",
    "java": 21,
}
REQUIRED_CONFIG_KEYS = (
    "project_name",
    "java_package",
    "mod_group_id",
    "mod_version",
    "main_class",
    "client_class",
    "license",
    "authors",
    "description",
)
PACKAGE_RE = re.compile(r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*$")
CLASS_RE = re.compile(r"^[A-Z][A-Za-z0-9_]*$")
PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
MOD_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
UNRESOLVED_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")

TEXT_TEMPLATES = {
    "settings.gradle.tmpl": "settings.gradle",
    "gradle.properties.tmpl": "gradle.properties",
    "build.gradle.tmpl": "build.gradle",
    "neoforge.mods.toml.tmpl": "src/main/resources/META-INF/neoforge.mods.toml",
    "MainMod.java.tmpl": None,
    "ClientMod.java.tmpl": None,
    "ModTest.java.tmpl": None,
    "ci.yml.tmpl": ".github/workflows/ci.yml",
}
WRAPPER_FILES = (
    ("gradlew", "gradlew"),
    ("gradlew.bat", "gradlew.bat"),
    ("gradle/wrapper/gradle-wrapper.properties", "gradle/wrapper/gradle-wrapper.properties"),
    ("gradle/wrapper/gradle-wrapper.jar", "gradle/wrapper/gradle-wrapper.jar"),
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _require_nonempty_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"scaffold config requires explicit non-empty string: {key}")
    return value


def _validate_line_value(label: str, value: str) -> None:
    if "\n" in value or "\r" in value:
        raise ValueError(f"{label} must be a single line")


def _validate_inputs(mod_spec: dict[str, Any], config: dict[str, Any]) -> None:
    if mod_spec.get("schema_version") != 1:
        raise ValueError("mod spec schema_version must be 1")
    if config.get("schema_version") != 1:
        raise ValueError("scaffold config schema_version must be 1")

    identity = mod_spec.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("mod spec identity is required")
    target = identity.get("target")
    if target != EXPECTED_TARGET:
        raise ValueError(f"unsupported target; expected exact {EXPECTED_TARGET}")

    mod_id = identity.get("mod_id")
    mod_name = identity.get("name")
    if not isinstance(mod_id, str) or not MOD_ID_RE.fullmatch(mod_id):
        raise ValueError("mod spec identity.mod_id is invalid")
    if not isinstance(mod_name, str) or not mod_name.strip():
        raise ValueError("mod spec identity.name is required")

    for key in REQUIRED_CONFIG_KEYS:
        _require_nonempty_string(config, key)

    project_name = config["project_name"]
    java_package = config["java_package"]
    group = config["mod_group_id"]
    main_class = config["main_class"]
    client_class = config["client_class"]

    if not PROJECT_RE.fullmatch(project_name):
        raise ValueError("project_name must be a safe Gradle project name")
    if not PACKAGE_RE.fullmatch(java_package):
        raise ValueError("java_package must be an explicit lowercase Java package")
    if not PACKAGE_RE.fullmatch(group):
        raise ValueError("mod_group_id must be an explicit Java-style group")
    if not CLASS_RE.fullmatch(main_class) or not CLASS_RE.fullmatch(client_class):
        raise ValueError("main_class/client_class must be explicit Java class names")
    if main_class == client_class:
        raise ValueError("main_class and client_class must be distinct")

    release = mod_spec.get("release")
    if not isinstance(release, dict) or release.get("license") != config["license"]:
        raise ValueError("scaffold config license must match mod spec release.license")

    for label, value in (
        ("mod name", mod_name),
        ("project_name", project_name),
        ("mod_group_id", group),
        ("mod_version", config["mod_version"]),
        ("license", config["license"]),
        ("authors", config["authors"]),
        ("description", config["description"]),
    ):
        _validate_line_value(label, value)

    if '"' in mod_name or '"' in config["authors"]:
        raise ValueError("mod name/authors cannot contain double quotes in the canonical metadata template")
    if "'''" in config["description"]:
        raise ValueError("description cannot contain TOML triple-single-quote delimiter")


def _replacement_values(mod_spec: dict[str, Any], config: dict[str, Any]) -> dict[str, str]:
    identity = mod_spec["identity"]
    return {
        "PROJECT_NAME": config["project_name"],
        "JAVA_PACKAGE": config["java_package"],
        "MOD_GROUP_ID": config["mod_group_id"],
        "MOD_VERSION": config["mod_version"],
        "MAIN_CLASS": config["main_class"],
        "CLIENT_CLASS": config["client_class"],
        "MOD_ID": identity["mod_id"],
        "MOD_NAME": identity["name"],
        "LICENSE": config["license"],
        "AUTHORS": config["authors"],
        "DESCRIPTION": config["description"],
    }


def _render(template: str, values: dict[str, str], template_name: str) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    unresolved = sorted(set(UNRESOLVED_TOKEN_RE.findall(rendered)))
    if unresolved:
        raise ValueError(f"unresolved tokens in {template_name}: {unresolved}")
    return rendered


def _output_for_template(template_name: str, values: dict[str, str]) -> str:
    if template_name == "MainMod.java.tmpl":
        package_path = values["JAVA_PACKAGE"].replace(".", "/")
        return f"src/main/java/{package_path}/{values['MAIN_CLASS']}.java"
    if template_name == "ClientMod.java.tmpl":
        package_path = values["JAVA_PACKAGE"].replace(".", "/")
        return f"src/main/java/{package_path}/client/{values['CLIENT_CLASS']}.java"
    if template_name == "ModTest.java.tmpl":
        package_path = values["JAVA_PACKAGE"].replace(".", "/")
        return f"src/test/java/{package_path}/{values['MAIN_CLASS']}Test.java"
    output = TEXT_TEMPLATES[template_name]
    assert output is not None
    return output


def _validate_wrapper_source(wrapper_source: Path) -> None:
    if not wrapper_source.is_dir():
        raise ValueError(f"explicit wrapper authority missing: {wrapper_source}")
    for source_relative, _ in WRAPPER_FILES:
        source = wrapper_source / source_relative
        if not source.is_file():
            raise ValueError(f"wrapper authority missing required file: {source_relative}")
    properties = (wrapper_source / "gradle/wrapper/gradle-wrapper.properties").read_text(encoding="utf-8")
    if "gradle-8.14-bin.zip" not in properties:
        raise ValueError("wrapper authority must target canonical Gradle 8.14 binary distribution")


def _copy_wrapper_files(output: Path, wrapper_source: Path) -> None:
    for source_relative, output_relative in WRAPPER_FILES:
        source = wrapper_source / source_relative
        destination = output / output_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def generate_project(
    mod_spec_path: Path | str,
    scaffold_config_path: Path | str,
    output_dir: Path | str,
    wrapper_source: Path | str,
) -> Path:
    mod_spec_path = Path(mod_spec_path)
    scaffold_config_path = Path(scaffold_config_path)
    output = Path(output_dir)
    wrapper_source = Path(wrapper_source)

    _validate_wrapper_source(wrapper_source)

    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise FileExistsError(f"refusing to overwrite non-empty target: {output}")
    else:
        output.mkdir(parents=True)

    mod_spec = _load_json(mod_spec_path)
    config = _load_json(scaffold_config_path)
    _validate_inputs(mod_spec, config)
    values = _replacement_values(mod_spec, config)

    if not TEMPLATE_ROOT.is_dir():
        raise ValueError(f"canonical template root missing: {TEMPLATE_ROOT}")

    for template_name in TEXT_TEMPLATES:
        template_path = TEMPLATE_ROOT / template_name
        if not template_path.is_file():
            raise ValueError(f"canonical template missing: {template_name}")
        rendered = _render(template_path.read_text(encoding="utf-8"), values, template_name)
        destination = output / _output_for_template(template_name, values)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8", newline="\n")

    _copy_wrapper_files(output, wrapper_source)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a canonical NeoForge 1.21.1 mod project.")
    parser.add_argument("--mod-spec", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--wrapper-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    generated = generate_project(args.mod_spec, args.config, args.output, args.wrapper_source)
    print(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
