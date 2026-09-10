#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

HISTORICAL_BUNDLE_INDENT = ".map((line) => `${prefix}${line}`)"
RECONCILED_BUNDLE_INDENT = ".map((line) => line.trim().length === 0 ? '' : `${prefix}${line}`)"


def reconcile_bundle_builder(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if RECONCILED_BUNDLE_INDENT in text:
        return False
    occurrences = text.count(HISTORICAL_BUNDLE_INDENT)
    if occurrences != 1:
        raise RuntimeError(
            f"unexpected historical Asset Toolkit bundle indent pattern count={occurrences}: {path}"
        )
    path.write_text(
        text.replace(HISTORICAL_BUNDLE_INDENT, RECONCILED_BUNDLE_INDENT, 1),
        encoding="utf-8",
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile Factory-owned deltas after frozen skill materialization")
    parser.add_argument("--factory-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    builder = args.factory_root.resolve() / "art/tooling/blockbench/asset-toolkit/build_toolkit_bundle.js"
    changed = reconcile_bundle_builder(builder)
    print(f"post-migration reconciliation: bundle whitespace {'updated' if changed else 'already current'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
