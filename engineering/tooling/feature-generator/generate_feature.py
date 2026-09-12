#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Any


CORE_FEATURE_KINDS = (
    "block",
    "item",
    "block_entity",
    "menu",
    "network_payload",
    "recipe",
)
EXPECTED_TARGET = {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "neoforge": "21.1.248",
    "java": 21,
}
MOD_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
JAVA_PACKAGE_RE = re.compile(r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*$")
CLASS_RE = re.compile(r"^[A-Z][A-Za-z0-9_]*$")
FEATURE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class FeatureGeneratorError(ValueError):
    pass


class ConfirmationRequiredError(FeatureGeneratorError):
    pass


class StalePlanError(FeatureGeneratorError):
    pass


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_project_root(project_root: Path | str) -> Path:
    root = Path(project_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"project root must be a directory: {root}")
    return root


def _safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"planned path must be a safe project-relative path: {value}")
    return path


def _project_child(root: Path, relative: str) -> Path:
    path = _safe_relative_path(relative)
    candidate = (root / path).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"planned path escapes project root: {relative}") from exc
    return candidate


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_nonempty_string(mapping: dict[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}.{key} must be a non-empty string")
    return value


def _validate_request(request: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if request.get("schema_version") != 1:
        raise ValueError("feature request schema_version must be 1")
    target = _require_mapping(request.get("target"), "target")
    if target != EXPECTED_TARGET:
        raise ValueError(f"unsupported target; expected exact {EXPECTED_TARGET}")

    project = _require_mapping(request.get("project"), "project")
    mod_id = _require_nonempty_string(project, "mod_id", "project")
    java_package = _require_nonempty_string(project, "java_package", "project")
    main_class = _require_nonempty_string(project, "main_class", "project")
    if not MOD_ID_RE.fullmatch(mod_id):
        raise ValueError("project.mod_id is invalid")
    if not JAVA_PACKAGE_RE.fullmatch(java_package):
        raise ValueError("project.java_package is invalid")
    if not CLASS_RE.fullmatch(main_class):
        raise ValueError("project.main_class is invalid")

    raw_features = request.get("features")
    if not isinstance(raw_features, list) or not raw_features:
        raise ValueError("features must be a non-empty array")

    features: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_classes: set[str] = set()
    for index, raw_feature in enumerate(raw_features):
        feature = _require_mapping(raw_feature, f"features[{index}]")
        kind = _require_nonempty_string(feature, "kind", f"features[{index}]")
        feature_id = _require_nonempty_string(feature, "id", f"features[{index}]")
        class_name = _require_nonempty_string(feature, "class_name", f"features[{index}]")
        if kind not in CORE_FEATURE_KINDS:
            raise ValueError(f"unsupported I8 core feature kind: {kind}")
        if not FEATURE_ID_RE.fullmatch(feature_id):
            raise ValueError(f"invalid feature id: {feature_id}")
        if not CLASS_RE.fullmatch(class_name):
            raise ValueError(f"invalid feature class_name: {class_name}")
        if feature_id in seen_ids:
            raise ValueError(f"duplicate feature id: {feature_id}")
        if class_name in seen_classes:
            raise ValueError(f"duplicate feature class_name: {class_name}")
        seen_ids.add(feature_id)
        seen_classes.add(class_name)
        features.append(dict(feature))
    return project, features


def _java_package_path(java_package: str) -> str:
    return java_package.replace(".", "/")


def _kind_package(kind: str) -> str:
    return kind


def _feature_source(java_package: str, feature: dict[str, Any]) -> str:
    kind = feature["kind"]
    feature_id = feature["id"]
    class_name = feature["class_name"]
    package = f"{java_package}.feature.{_kind_package(kind)}"
    return (
        f"package {package};\n\n"
        f"public final class {class_name} {{\n"
        f"    public static final String FEATURE_KIND = \"{kind}\";\n"
        f"    public static final String ID = \"{feature_id}\";\n\n"
        f"    private {class_name}() {{\n"
        "    }\n"
        "}\n"
    )


def _generated_test(java_package: str, feature: dict[str, Any]) -> str:
    kind = feature["kind"]
    feature_id = feature["id"]
    class_name = feature["class_name"]
    package = f"{java_package}.feature.{_kind_package(kind)}"
    test_class = f"{class_name}GeneratedTest"
    return (
        f"package {package};\n\n"
        "import org.junit.jupiter.api.Test;\n\n"
        "import static org.junit.jupiter.api.Assertions.assertEquals;\n\n"
        f"class {test_class} {{\n"
        "    @Test\n"
        "    void exposesGeneratedIdentity() {\n"
        f"        assertEquals(\"{kind}\", {class_name}.FEATURE_KIND);\n"
        f"        assertEquals(\"{feature_id}\", {class_name}.ID);\n"
        "    }\n"
        "}\n"
    )


def _registry_source(java_package: str, features: list[dict[str, Any]]) -> str:
    entries = ",\n".join(f'        "{feature["kind"]}:{feature["id"]}"' for feature in features)
    return (
        f"package {java_package}.registry;\n\n"
        "import java.util.List;\n\n"
        "public final class FactoryGeneratedFeatures {\n"
        "    public static final List<String> FEATURES = List.of(\n"
        f"{entries}\n"
        "    );\n\n"
        "    private FactoryGeneratedFeatures() {\n"
        "    }\n"
        "}\n"
    )


def _datagen_source(java_package: str, features: list[dict[str, Any]]) -> str:
    entries = ",\n".join(f'        "{feature["id"]}"' for feature in features)
    return (
        f"package {java_package}.data;\n\n"
        "import java.util.List;\n\n"
        "public final class FactoryGeneratedFeatureData {\n"
        "    public static final List<String> FEATURE_IDS = List.of(\n"
        f"{entries}\n"
        "    );\n\n"
        "    private FactoryGeneratedFeatureData() {\n"
        "    }\n"
        "}\n"
    )


def _unified_diff(path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def _planned_operation(root: Path, path: str, content: str, role: str) -> dict[str, Any]:
    destination = _project_child(root, path)
    if destination.exists():
        if not destination.is_file():
            raise ValueError(f"planned target exists but is not a file: {path}")
        before = destination.read_text(encoding="utf-8")
        if before == content:
            return {
                "action": "noop",
                "role": role,
                "path": path,
                "before_sha256": _sha256_text(before),
                "content": content,
                "diff": "",
                "requires_confirmation": False,
            }
        return {
            "action": "modify",
            "role": role,
            "path": path,
            "before_sha256": _sha256_text(before),
            "content": content,
            "diff": _unified_diff(path, before, content),
            "requires_confirmation": True,
        }
    return {
        "action": "create",
        "role": role,
        "path": path,
        "content": content,
        "diff": _unified_diff(path, "", content),
        "requires_confirmation": False,
    }


def plan_feature_set(project_root: Path | str, request: dict[str, Any]) -> dict[str, Any]:
    root = _safe_project_root(project_root)
    project, features = _validate_request(request)
    java_package = project["java_package"]
    package_path = _java_package_path(java_package)
    main_path = root / "src/main/java" / package_path / f"{project['main_class']}.java"
    if not main_path.is_file():
        raise ValueError(f"target project does not match requested main class: {main_path.relative_to(root)}")

    operations: list[dict[str, Any]] = []
    for feature in features:
        kind = feature["kind"]
        class_name = feature["class_name"]
        relative_package = _kind_package(kind)
        source_path = f"src/main/java/{package_path}/feature/{relative_package}/{class_name}.java"
        test_path = f"src/test/java/{package_path}/feature/{relative_package}/{class_name}GeneratedTest.java"
        operations.append(_planned_operation(root, source_path, _feature_source(java_package, feature), "feature_source"))
        operations.append(_planned_operation(root, test_path, _generated_test(java_package, feature), "generated_test"))

    registry_path = f"src/main/java/{package_path}/registry/FactoryGeneratedFeatures.java"
    operations.append(_planned_operation(root, registry_path, _registry_source(java_package, features), "registry"))
    datagen_path = f"src/main/java/{package_path}/data/FactoryGeneratedFeatureData.java"
    operations.append(_planned_operation(root, datagen_path, _datagen_source(java_package, features), "datagen"))

    operations.sort(key=lambda operation: (operation["path"], operation["role"], operation["action"]))
    return {
        "schema_version": 1,
        "feature_kinds": [feature["kind"] for feature in features],
        "conflicts": [],
        "operations": operations,
    }


def _preflight_operation(root: Path, operation: dict[str, Any], *, confirm_modified: bool) -> tuple[Path, str]:
    action = operation.get("action")
    path_value = operation.get("path")
    content = operation.get("content")
    if action not in {"create", "modify", "noop"}:
        raise ValueError(f"unknown plan action: {action}")
    if not isinstance(path_value, str) or not isinstance(content, str):
        raise ValueError("plan operation requires string path and content")
    destination = _project_child(root, path_value)

    if action == "create":
        if destination.exists():
            raise StalePlanError(f"create target appeared after planning: {path_value}")
        return destination, content

    if not destination.is_file():
        raise StalePlanError(f"planned existing file is missing: {path_value}")
    current = destination.read_text(encoding="utf-8")
    expected_hash = operation.get("before_sha256")
    if not isinstance(expected_hash, str) or _sha256_text(current) != expected_hash:
        raise StalePlanError(f"planned file changed after planning: {path_value}")

    if action == "noop":
        return destination, current

    if operation.get("requires_confirmation") is True and not confirm_modified:
        diff = operation.get("diff", "")
        raise ConfirmationRequiredError(f"modified file requires explicit confirmation; diff follows:\n{diff}")
    return destination, content


def apply_plan(project_root: Path | str, plan: dict[str, Any], *, confirm_modified: bool = False) -> list[Path]:
    root = _safe_project_root(project_root)
    if plan.get("schema_version") != 1:
        raise ValueError("plan schema_version must be 1")
    operations = plan.get("operations")
    if not isinstance(operations, list):
        raise ValueError("plan operations must be an array")

    prepared: list[tuple[dict[str, Any], Path, str]] = []
    seen: set[Path] = set()
    for raw_operation in operations:
        operation = _require_mapping(raw_operation, "plan operation")
        destination, content = _preflight_operation(root, operation, confirm_modified=confirm_modified)
        if destination in seen:
            raise ValueError(f"duplicate planned destination: {destination.relative_to(root)}")
        seen.add(destination)
        prepared.append((operation, destination, content))

    written: list[Path] = []
    for operation, destination, content in prepared:
        if operation["action"] == "noop":
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
        written.append(destination)
    return written


def load_request(path: Path | str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("feature request root must be an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan and apply deterministic I8 feature skeleton generation.")
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-modified", action="store_true")
    args = parser.parse_args()

    request = load_request(args.request)
    plan = plan_feature_set(args.project, request)
    rendered = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    if args.plan_output:
        args.plan_output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    if args.apply:
        apply_plan(args.project, plan, confirm_modified=args.confirm_modified)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
