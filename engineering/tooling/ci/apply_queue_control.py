#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from validate_queue_control import QueueControlError, parse_workflow_contract

ROOT = Path(__file__).resolve().parents[3]
POLICY = ROOT / "engineering" / "tooling" / "ci" / "queue-control-policy.json"
# Temporary branch-local materializer; final PR removes this file after batch generation.
CONCURRENCY_LINES = [
    "concurrency:",
    "  group: ${{ github.workflow }}-${{ github.ref }}-${{ github.ref == 'refs/heads/main' && github.run_id || 'dedupe' }}",
    "  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}",
]


def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def block_span(lines: list[str], key: str, level: int) -> tuple[int, int]:
    marker = " " * level + f"{key}:"
    start = next((i for i, line in enumerate(lines) if line == marker), None)
    if start is None:
        raise QueueControlError(f"missing block {key!r} at indent {level}")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line and indent(line) <= level:
            end = i
            break
    return start, end


def insert_push_paths(text: str, paths: tuple[str, ...]) -> str:
    lines = text.splitlines()
    push_start, push_end = block_span(lines, "push", 2)
    branches_start = next(
        (i for i in range(push_start + 1, push_end) if lines[i] == "    branches:"),
        None,
    )
    if branches_start is None:
        raise QueueControlError("push-to-main workflow is missing branches list")

    insert_at = branches_start + 1
    while insert_at < push_end:
        line = lines[insert_at]
        if line and indent(line) <= 4:
            break
        insert_at += 1

    path_lines = ["    paths:"] + [f"      - '{path}'" for path in paths]
    lines[insert_at:insert_at] = path_lines
    return "\n".join(lines) + "\n"


def insert_concurrency(text: str) -> str:
    lines = text.splitlines()
    _, on_end = block_span(lines, "on", 0)
    insertion = CONCURRENCY_LINES + [""]
    lines[on_end:on_end] = insertion
    return "\n".join(lines) + "\n"


def transform(workflow_path: Path, workflow_class: str) -> bool:
    original = workflow_path.read_text(encoding="utf-8")
    text = original
    contract = parse_workflow_contract(text, str(workflow_path.relative_to(ROOT)))

    if workflow_class == "SCOPED_READ_ONLY":
        if contract.has_push and "main" in contract.push_branches and not contract.push_paths:
            if not contract.pull_request_paths:
                raise QueueControlError(
                    f"{workflow_path}: cannot derive push.paths without pull_request.paths"
                )
            text = insert_push_paths(text, contract.pull_request_paths)
            contract = parse_workflow_contract(text, str(workflow_path.relative_to(ROOT)))

    if workflow_class in {"GLOBAL_READ_ONLY", "SCOPED_READ_ONLY"}:
        if contract.concurrency_group is None and contract.cancel_in_progress is None:
            text = insert_concurrency(text)
        elif (
            contract.concurrency_group
            != "${{ github.workflow }}-${{ github.ref }}-${{ github.ref == 'refs/heads/main' && github.run_id || 'dedupe' }}"
            or contract.cancel_in_progress != "${{ github.ref != 'refs/heads/main' }}"
        ):
            raise QueueControlError(f"{workflow_path}: pre-existing noncanonical concurrency")

    if text != original:
        workflow_path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    changed: list[str] = []
    for relative_path, entry in sorted(policy["workflows"].items()):
        path = ROOT / relative_path
        if transform(path, entry["class"]):
            changed.append(relative_path)
    print(f"QUEUE_CONTROL_MATERIALIZED={len(changed)}")
    for path in changed:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
