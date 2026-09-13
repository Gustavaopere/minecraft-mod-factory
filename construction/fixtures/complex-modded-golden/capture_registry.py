from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
I2_IMPORTER = ROOT / "engineering" / "tooling" / "import-physical-modlist.py"
C4_REGISTRY = ROOT / "construction" / "core" / "modpack_registry.py"


def _load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_i2_importer():
    return _load_path(I2_IMPORTER, "construction_c11_i2_importer")


def load_c4_registry():
    return _load_path(C4_REGISTRY, "construction_c11_c4_registry")


def _load_runtime_snapshot(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"runtime snapshot does not exist: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"runtime snapshot is not valid JSON: {exc}") from exc


def compose_registry(
    physical_modlist: Path,
    mods_dir: Path,
    runtime_snapshot: Path,
    *,
    captured_at: str,
) -> dict:
    i2 = load_i2_importer()
    c4 = load_c4_registry()
    physical = i2.parse_modlist_bytes(
        physical_modlist.read_bytes(),
        captured_at=captured_at,
        source_name=physical_modlist.name,
    )
    jar_names = sorted(
        entry["jar"]
        for entry in physical["entries"]
        if entry["top_level"] and entry["jar"].lower().endswith(".jar")
    )
    missing = [name for name in jar_names if not (mods_dir / name).is_file()]
    if missing:
        raise ValueError("missing physical top-level JARs: " + ", ".join(missing))

    runtime = _load_runtime_snapshot(runtime_snapshot)
    static_indexes = [c4.index_jar_file(mods_dir / name) for name in jar_names]
    registry = c4.build_modpack_registry(physical, static_indexes, runtime)
    errors = c4.validate_modpack_registry(registry)
    if errors:
        raise ValueError("invalid composed C4 registry: " + "; ".join(errors))
    return registry


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose the canonical C11 C4 registry")
    parser.add_argument("--physical-modlist", type=Path, required=True)
    parser.add_argument("--mods-dir", type=Path, required=True)
    parser.add_argument("--runtime-snapshot", type=Path, required=True)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    registry = compose_registry(
        args.physical_modlist,
        args.mods_dir,
        args.runtime_snapshot,
        captured_at=args.captured_at,
    )
    c4 = load_c4_registry()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(c4.canonical_json_bytes(registry))

    written = json.loads(args.output.read_text(encoding="utf-8"))
    errors = c4.validate_modpack_registry(written)
    if errors:
        raise ValueError("written C4 registry failed validation: " + "; ".join(errors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
