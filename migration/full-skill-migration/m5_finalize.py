#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

CANONICAL_PACKAGE = "@minecraft-mod-factory/asset-mcp-sidecar"


def update_json(path: Path, *, lockfile: bool = False) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["name"] = CANONICAL_PACKAGE
    if lockfile:
        packages = data.get("packages")
        if not isinstance(packages, dict) or not isinstance(packages.get(""), dict):
            raise RuntimeError(f"unexpected npm lockfile structure: {path}")
        packages[""]["name"] = CANONICAL_PACKAGE
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize M5 neutral package identity")
    parser.add_argument("--factory-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    sidecar = args.factory_root.resolve() / "art/tooling/blockbench/asset-toolkit/mcp-sidecar"
    update_json(sidecar / "package.json")
    update_json(sidecar / "package-lock.json", lockfile=True)
    print(f"M5 package identity: {CANONICAL_PACKAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
