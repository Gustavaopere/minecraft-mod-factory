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


def source_exact_destinations(manifest: dict) -> set[str]:
    return {
        entry["destination"]
        for entry in manifest.get("entries", [])
        if entry.get("materialization_mode") == "SOURCE_EXACT" and entry.get("destination")
    }


def checkable_paths(changed_paths: Iterable[str], preserved_paths: set[str]) -> list[str]:
    return [path for path in changed_paths if path not in preserved_paths]


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
    parser.add_argument("--base", default="HEAD^", help="Git base used for the diff")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    preserved = source_exact_destinations(manifest)
    changed = git_changed_paths(args.base)
    checkable = checkable_paths(changed, preserved)
    skipped = [path for path in changed if path in preserved]
    print(
        "FULL SKILL WHITESPACE POLICY: "
        f"changed={len(changed)} checkable={len(checkable)} source_exact_skipped={len(skipped)}"
    )
    return run_whitespace_check(args.base, checkable)


if __name__ == "__main__":
    raise SystemExit(main())
