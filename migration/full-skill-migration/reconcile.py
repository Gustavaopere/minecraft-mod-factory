#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

HISTORICAL_BUNDLE_INDENT = ".map((line) => `${prefix}${line}`)"
RECONCILED_BUNDLE_INDENT = ".map((line) => line.trim().length === 0 ? '' : `${prefix}${line}`)"
HISTORICAL_NEOFORGE_TARGET = "NeoForge: **21.1.x**"
RECONCILED_NEOFORGE_TARGET = "NeoForge: **21.1.248**"
HISTORICAL_NEOFORGE_PROSE = "NeoForge 21.1.x"
RECONCILED_NEOFORGE_PROSE = "NeoForge 21.1.248"


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


def reconcile_version_authority(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    historical_targets = text.count(HISTORICAL_NEOFORGE_TARGET)
    reconciled_targets = text.count(RECONCILED_NEOFORGE_TARGET)
    if historical_targets == 0 and reconciled_targets == 1:
        updated = text.replace(HISTORICAL_NEOFORGE_PROSE, RECONCILED_NEOFORGE_PROSE)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            return True
        return False
    if historical_targets != 1 or reconciled_targets != 0:
        raise RuntimeError(
            "unexpected NeoForge version authority state "
            f"historical={historical_targets} reconciled={reconciled_targets}: {path}"
        )
    updated = text.replace(HISTORICAL_NEOFORGE_TARGET, RECONCILED_NEOFORGE_TARGET, 1)
    updated = updated.replace(HISTORICAL_NEOFORGE_PROSE, RECONCILED_NEOFORGE_PROSE)
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile Factory-owned deltas after frozen skill materialization")
    parser.add_argument("--factory-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.factory_root.resolve()
    builder = root / "art/tooling/blockbench/asset-toolkit/build_toolkit_bundle.js"
    version_authority = root / "skills/VERSION-AUTHORITY.md"
    bundle_changed = reconcile_bundle_builder(builder)
    version_changed = reconcile_version_authority(version_authority)
    print(f"post-migration reconciliation: bundle whitespace {'updated' if bundle_changed else 'already current'}")
    print(f"post-migration reconciliation: NeoForge authority {'updated' if version_changed else 'already current'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
