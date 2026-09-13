#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

SCHEMA_VERSION = 1
POLICY_CLASSES = {"GLOBAL_READ_ONLY", "SCOPED_READ_ONLY", "MUTATING_EXEMPT"}
CANONICAL_GROUP = "${{ github.workflow }}-${{ github.ref }}-${{ github.ref == 'refs/heads/main' && github.run_id || 'dedupe' }}"
CANONICAL_CANCEL = "${{ github.ref != 'refs/heads/main' }}"


class QueueControlError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def errors_text(self) -> str:
        return "\n".join(self.errors)


@dataclass(frozen=True)
class WorkflowContract:
    has_push: bool
    has_pull_request: bool
    push_branches: tuple[str, ...]
    push_paths: tuple[str, ...]
    pull_request_paths: tuple[str, ...]
    concurrency_group: str | None
    cancel_in_progress: str | None


def _no_duplicate_object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise QueueControlError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_policy(path: Path) -> dict[str, object]:
    try:
        policy = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_no_duplicate_object_pairs,
        )
    except (OSError, json.JSONDecodeError, QueueControlError) as exc:
        raise QueueControlError(f"invalid queue-control policy {path}: {exc}") from exc

    if not isinstance(policy, dict):
        raise QueueControlError("policy root must be an object")
    if policy.get("schema_version") != SCHEMA_VERSION:
        raise QueueControlError(
            f"unsupported schema_version: {policy.get('schema_version')!r}; expected {SCHEMA_VERSION}"
        )
    classes = policy.get("classes")
    if not isinstance(classes, list) or set(classes) != POLICY_CLASSES or len(classes) != len(POLICY_CLASSES):
        raise QueueControlError("classes must contain each supported policy class exactly once")
    workflows = policy.get("workflows")
    if not isinstance(workflows, dict) or not workflows:
        raise QueueControlError("workflows must be a non-empty object")
    for workflow_path, entry in workflows.items():
        if not isinstance(workflow_path, str) or not workflow_path.startswith(".github/workflows/factory-"):
            raise QueueControlError(f"invalid workflow policy path: {workflow_path!r}")
        if not isinstance(entry, dict):
            raise QueueControlError(f"policy entry must be an object: {workflow_path}")
        workflow_class = entry.get("class")
        if workflow_class not in POLICY_CLASSES:
            raise QueueControlError(f"unknown class for {workflow_path}: {workflow_class!r}")
        unknown = set(entry) - {"class", "allowed_path_difference"}
        if unknown:
            raise QueueControlError(f"unsupported policy keys for {workflow_path}: {sorted(unknown)}")
        if "allowed_path_difference" in entry and not isinstance(entry["allowed_path_difference"], bool):
            raise QueueControlError(
                f"allowed_path_difference must be boolean for {workflow_path}"
            )
    return policy


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _top_level_block(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    marker = f"{key}:"
    start = next((index for index, line in enumerate(lines) if line == marker), None)
    if start is None:
        return []
    block = [lines[start]]
    for line in lines[start + 1 :]:
        if line and _indent(line) == 0:
            break
        block.append(line)
    return block


def _nested_block(parent: list[str], key: str, indent: int) -> list[str]:
    marker = " " * indent + f"{key}:"
    start = next((index for index, line in enumerate(parent) if line == marker), None)
    if start is None:
        for line in parent:
            if line.strip().startswith(f"{key}:") and _indent(line) == indent:
                raise QueueControlError(f"unsupported inline structure for {key}: {line.strip()}")
        return []
    block = [parent[start]]
    for line in parent[start + 1 :]:
        if line and _indent(line) <= indent:
            break
        block.append(line)
    return block


def _strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _list_value(block: list[str], key: str, indent: int) -> tuple[str, ...]:
    marker = " " * indent + f"{key}:"
    start = next((index for index, line in enumerate(block) if line == marker), None)
    if start is None:
        for line in block:
            if line.strip().startswith(f"{key}:") and _indent(line) == indent:
                raise QueueControlError(f"unsupported inline list for {key}: {line.strip()}")
        return ()

    values: list[str] = []
    for line in block[start + 1 :]:
        if line and _indent(line) <= indent:
            break
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("- "):
            raise QueueControlError(f"unsupported {key} entry: {stripped}")
        value = _strip_yaml_scalar(stripped[2:])
        if not value:
            raise QueueControlError(f"empty {key} entry")
        values.append(value)
    return tuple(values)


def _mapping_scalar(block: list[str], key: str, indent: int) -> str | None:
    prefix = " " * indent + f"{key}:"
    for line in block:
        if not line.startswith(prefix) or _indent(line) != indent:
            continue
        value = line[len(prefix) :].strip()
        if not value:
            raise QueueControlError(f"missing scalar value for {key}")
        return _strip_yaml_scalar(value)
    return None


def parse_workflow_contract(text: str, workflow_path: str = "<workflow>") -> WorkflowContract:
    on_block = _top_level_block(text, "on")
    if not on_block:
        raise QueueControlError(f"{workflow_path}: missing top-level on block")

    push = _nested_block(on_block, "push", 2)
    pull_request = _nested_block(on_block, "pull_request", 2)
    if not push and not pull_request:
        raise QueueControlError(f"{workflow_path}: neither push nor pull_request trigger is declared")

    concurrency = _top_level_block(text, "concurrency")
    group = _mapping_scalar(concurrency, "group", 2) if concurrency else None
    cancel = _mapping_scalar(concurrency, "cancel-in-progress", 2) if concurrency else None

    return WorkflowContract(
        has_push=bool(push),
        has_pull_request=bool(pull_request),
        push_branches=_list_value(push, "branches", 4) if push else (),
        push_paths=_list_value(push, "paths", 4) if push else (),
        pull_request_paths=_list_value(pull_request, "paths", 4) if pull_request else (),
        concurrency_group=group,
        cancel_in_progress=cancel,
    )


def _factory_workflow_paths(root: Path) -> tuple[Path, ...]:
    return tuple(sorted((root / ".github" / "workflows").glob("factory-*.yml")))


def validate_repository(root: Path) -> ValidationResult:
    errors: list[str] = []
    policy_path = root / "engineering" / "tooling" / "ci" / "queue-control-policy.json"
    try:
        policy = load_policy(policy_path)
    except QueueControlError as exc:
        return ValidationResult((str(exc),))

    workflow_entries = policy["workflows"]
    assert isinstance(workflow_entries, dict)
    actual = {
        str(path.relative_to(root)).replace("\\", "/")
        for path in _factory_workflow_paths(root)
    }
    declared = set(workflow_entries)
    for path in sorted(actual - declared):
        errors.append(f"unclassified workflow: {path}")
    for path in sorted(declared - actual):
        errors.append(f"policy points to missing workflow: {path}")

    for workflow_path in sorted(actual & declared):
        entry = workflow_entries[workflow_path]
        assert isinstance(entry, dict)
        workflow_class = entry["class"]
        path = root / workflow_path
        try:
            contract = parse_workflow_contract(path.read_text(encoding="utf-8"), workflow_path)
        except (OSError, QueueControlError) as exc:
            errors.append(f"{workflow_path}: {exc}")
            continue

        if workflow_class == "GLOBAL_READ_ONLY":
            if contract.push_paths or contract.pull_request_paths:
                errors.append(f"{workflow_path}: global workflow must not use domain paths")
        elif workflow_class == "SCOPED_READ_ONLY":
            if contract.has_push and "main" in contract.push_branches and not contract.push_paths:
                errors.append(f"{workflow_path}: missing push.paths for main")
            if contract.has_pull_request and not contract.pull_request_paths:
                errors.append(f"{workflow_path}: missing pull_request.paths")
            if (
                contract.has_push
                and contract.has_pull_request
                and contract.push_paths != contract.pull_request_paths
                and not entry.get("allowed_path_difference", False)
            ):
                errors.append(f"{workflow_path}: push.paths != pull_request.paths")

        if workflow_class in {"GLOBAL_READ_ONLY", "SCOPED_READ_ONLY"}:
            if contract.concurrency_group != CANONICAL_GROUP or contract.cancel_in_progress != CANONICAL_CANCEL:
                errors.append(f"{workflow_path}: missing canonical concurrency")
        elif workflow_class == "MUTATING_EXEMPT" and contract.cancel_in_progress is not None:
            errors.append(f"{workflow_path}: mutating workflow must not use cancel-in-progress")

    return ValidationResult(tuple(errors))


def _path_matches(pattern: str, changed_path: str) -> bool:
    pattern = pattern.lstrip("/")
    changed_path = changed_path.lstrip("/")
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return changed_path == prefix or changed_path.startswith(prefix + "/")
    return fnmatch.fnmatchcase(changed_path, pattern)


def workflows_for_changed_paths(root: Path, changed_paths: Sequence[str]) -> tuple[str, ...]:
    policy = load_policy(root / "engineering" / "tooling" / "ci" / "queue-control-policy.json")
    workflow_entries = policy["workflows"]
    assert isinstance(workflow_entries, dict)
    scheduled: list[str] = []

    for workflow_path in sorted(workflow_entries):
        entry = workflow_entries[workflow_path]
        assert isinstance(entry, dict)
        workflow_class = entry["class"]
        contract = parse_workflow_contract(
            (root / workflow_path).read_text(encoding="utf-8"), workflow_path
        )
        if not contract.has_push or "main" not in contract.push_branches:
            continue
        if workflow_class == "GLOBAL_READ_ONLY":
            scheduled.append(workflow_path)
            continue
        if workflow_class == "MUTATING_EXEMPT":
            continue
        if any(
            _path_matches(pattern, changed_path)
            for pattern in contract.push_paths
            for changed_path in changed_paths
        ):
            scheduled.append(workflow_path)

    return tuple(scheduled)


def _class_counts(policy: dict[str, object]) -> dict[str, int]:
    counts = {workflow_class: 0 for workflow_class in POLICY_CLASSES}
    workflows = policy["workflows"]
    assert isinstance(workflows, dict)
    for entry in workflows.values():
        assert isinstance(entry, dict)
        counts[entry["class"]] += 1
    return counts


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    result = validate_repository(root)
    try:
        policy = load_policy(root / "engineering" / "tooling" / "ci" / "queue-control-policy.json")
    except QueueControlError as exc:
        print(f"CI_QUEUE_CONTROL=FAIL\n{exc}", file=sys.stderr)
        return 1

    counts = _class_counts(policy)
    print(f"TOTAL_FACTORY_WORKFLOWS={sum(counts.values())}")
    for workflow_class in ("GLOBAL_READ_ONLY", "SCOPED_READ_ONLY", "MUTATING_EXEMPT"):
        print(f"{workflow_class}={counts[workflow_class]}")

    if not result.ok:
        print("CI_QUEUE_CONTROL=FAIL", file=sys.stderr)
        print(result.errors_text, file=sys.stderr)
        return 1

    docs_only = workflows_for_changed_paths(root, ("plans/example.md",))
    print(f"DOCS_ONLY_SCHEDULED={len(docs_only)}")
    print("CI_QUEUE_CONTROL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
