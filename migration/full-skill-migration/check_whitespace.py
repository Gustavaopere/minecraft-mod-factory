#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "migration/provenance/FULL-SKILL-MIGRATION-MANIFEST.json"
FIXED_BASE_REF = "HEAD^"
LOWER_HEX = frozenset("0123456789abcdef")


def source_exact_destinations(manifest: dict) -> set[str]:
    return {
        entry["destination"]
        for entry in manifest.get("entries", [])
        if entry.get("materialization_mode") == "SOURCE_EXACT" and entry.get("destination")
    }


def checkable_paths(changed_paths: Iterable[str], preserved_paths: set[str]) -> list[str]:
    return [path for path in changed_paths if path not in preserved_paths]


def resolve_git_base() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{FIXED_BASE_REF}^{{commit}}"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    resolved = result.stdout.strip().lower()
    if len(resolved) != 40 or any(char not in LOWER_HEX for char in resolved):
        raise RuntimeError(f"git rev-parse returned an invalid commit SHA: {resolved!r}")
    return resolved


def git_changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", FIXED_BASE_REF, "--"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def run_whitespace_check(paths: list[str]) -> int:
    if not paths:
        print("FULL SKILL WHITESPACE: PASS (only SOURCE_EXACT paths changed)")
        return 0
    result = subprocess.run(
        ["git", "diff", "--check", FIXED_BASE_REF, "--", *paths],
        cwd=REPO_ROOT,
        check=False,
    )
    if result.returncode == 0:
        print(f"FULL SKILL WHITESPACE: PASS ({len(paths)} non-preserved changed paths checked)")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run git diff --check against HEAD^ without rewriting byte-preserved SOURCE_EXACT migration payloads"
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    preserved = source_exact_destinations(manifest)
    resolve_git_base()
    changed = git_changed_paths()
    checkable = checkable_paths(changed, preserved)
    skipped = [path for path in changed if path in preserved]
    print(
        "FULL SKILL WHITESPACE POLICY: "
        f"changed={len(changed)} checkable={len(checkable)} source_exact_skipped={len(skipped)}"
    )
    return run_whitespace_check(checkable)


if __name__ == "__main__":
    raise SystemExit(main())
