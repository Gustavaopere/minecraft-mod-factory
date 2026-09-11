#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from construction.core.modpack_registry import index_jar_file


def _collect_inputs(values):
    jars = []
    for value in values:
        path = Path(value).resolve()
        if path.is_dir():
            jars.extend(sorted(candidate for candidate in path.iterdir() if candidate.is_file() and candidate.suffix.lower() == ".jar"))
        elif path.is_file() and path.suffix.lower() == ".jar":
            jars.append(path)
        else:
            raise ValueError(f"input must be a JAR or directory containing top-level JARs: {value}")
    unique = {str(path): path for path in jars}
    return [unique[key] for key in sorted(unique)]


def _workspace_output(value):
    workspace = Path.cwd().resolve()
    raw = Path(value)
    output = raw.resolve(strict=False) if raw.is_absolute() else (workspace / raw).resolve(strict=False)
    try:
        output.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"output must stay inside workspace: {workspace}") from exc
    if output == workspace:
        raise ValueError("output must identify a file inside workspace")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description="Index discoverable Minecraft block assets in mod JARs without extracting them.")
    parser.add_argument("inputs", nargs="+", help="JAR files or directories of top-level JARs")
    parser.add_argument("--output", help="optional JSON output path inside the current workspace")
    args = parser.parse_args(argv)

    try:
        jars = _collect_inputs(args.inputs)
        document = {
            "schema_version": 1,
            "jars": [index_jar_file(path) for path in jars],
        }
        payload = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        if args.output:
            output = _workspace_output(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(payload, encoding="utf-8")
            print(f"Wrote {output}")
        else:
            print(payload, end="")
    except (OSError, ValueError) as exc:
        print(f"C4 STATIC JAR INDEX: FAIL\n- {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
