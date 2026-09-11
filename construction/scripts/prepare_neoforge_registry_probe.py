#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAFFOLDER = REPO_ROOT / "engineering" / "tooling" / "scaffolder" / "scaffold_mod.py"
PROBE_ROOT = REPO_ROOT / "construction" / "runtime" / "neoforge-registry-probe"
PROBE_SOURCE = PROBE_ROOT / "FactoryConstructionRegistryProbe.java"
PROBE_MOD_SPEC = PROBE_ROOT / "mod-spec.json"
PROBE_CONFIG = PROBE_ROOT / "scaffold-config.json"
JAVA_PACKAGE_PATH = Path("dev/minecraftmodfactory/constructionprobe")


def _load_scaffolder():
    spec = importlib.util.spec_from_file_location("factory_i3_scaffolder_for_c4", SCAFFOLDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical I3 scaffolder: {SCAFFOLDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_runtime_probe(output_dir: Path | str) -> Path:
    required = (SCAFFOLDER, PROBE_SOURCE, PROBE_MOD_SPEC, PROBE_CONFIG)
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing canonical C4 runtime probe inputs: {missing}")

    scaffolder = _load_scaffolder()
    generated = Path(scaffolder.generate_project(PROBE_MOD_SPEC, PROBE_CONFIG, output_dir))
    destination = generated / "src" / "main" / "java" / JAVA_PACKAGE_PATH / PROBE_SOURCE.name
    if not destination.is_file():
        raise RuntimeError(f"canonical I3 scaffolder did not generate expected main class: {destination}")
    shutil.copyfile(PROBE_SOURCE, destination)
    if destination.read_bytes() != PROBE_SOURCE.read_bytes():
        raise RuntimeError("materialized C4 runtime probe differs from Factory source authority")
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize the Construction C4 NeoForge runtime registry probe through the canonical I3 scaffolder.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    generated = prepare_runtime_probe(args.output)
    print(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
