#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

CANONICAL_PACKAGE = "@minecraft-mod-factory/asset-mcp-sidecar"
REPO_ROOT = Path(__file__).resolve().parents[2]
SIDECAR_REL = Path("art/tooling/blockbench/asset-toolkit/mcp-sidecar")
PACKAGE_JSON = REPO_ROOT / SIDECAR_REL / "package.json"
PACKAGE_LOCK_JSON = REPO_ROOT / SIDECAR_REL / "package-lock.json"


def update_json(*, lockfile: bool = False) -> None:
    path = PACKAGE_LOCK_JSON if lockfile else PACKAGE_JSON
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
    parser.parse_args()
    update_json()
    update_json(lockfile=True)
    print(f"M5 package identity: {CANONICAL_PACKAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
