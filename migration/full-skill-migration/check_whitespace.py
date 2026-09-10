#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "migration/provenance/FULL-SKILL-MIGRATION-MANIFEST.json"
FULL_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def source_exact_destinations(manifest: dict) -> set[str]:
    return {
        entry["destination"]
        for entry in manifest.get("entries", [])
        if entry.get("materialization_mode") == "SOURCE_EXACT" and entry.get("destination")
    }


def checkable_paths(changed_paths: Iterable[str], preserved_paths: set[str]) -> list[str]:
    return [path for path in changed_paths if path not in preserved_paths]


def resolve_git_base(base: str) -> str:
    if base == "HEAD^":
        safe_base = base
    elif isinstance(base, str) and FULL_SHA_RE.fullmatch(base):
        safe_base = base.lower()
    else:
        raise ValueError("git base must be HEAD^ or a full 40-character hexadecimal commit SHA")

    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{safe_base}^{{commit}}"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    resolved = result.stdout.strip().lower()
    if not FULL_SHA_RE.fullmatch(resolved):
        raise RuntimeError(f"git rev-parse returned an invalid commit SHA: {resolved!r}")
    return resolved


def git_changed_paths(base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", base, "--"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def run_whitespace_check(base: str, paths: list[str]) -> int:
    if not paths:
        print("FULL SKILL WHITESPACE: PASS (only SOURCE_EXACT paths changed)")
        return 0
    result = subprocess.run(
        ["git", "diff", "--check", base, "--", *paths],
        cwd=REPO_ROOT,
        check=False,
    )
    if result.returncode == 0:
        print(f"FULL SKILL WHITESPACE: PASS ({len(paths)} non-preserved changed paths checked)")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run git diff --check without rewriting byte-preserved SOURCE_EXACT migration payloads"
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    preserved = source_exact_destinations(manifest)
    base = resolve_git_base("HEAD^")
    changed = git_changed_paths(base)
    checkable = checkable_paths(changed, preserved)
    skipped = [path for path in changed if path in preserved]
    print(
        "FULL SKILL WHITESPACE POLICY: "
        f"changed={len(changed)} checkable={len(checkable)} source_exact_skipped={len(skipped)}"
    )
    return run_whitespace_check(base, checkable)


if __name__ == "__main__":
    raise SystemExit(main())
