from __future__ import annotations

import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_TEST_PATH = ROOT / "construction" / "tests" / "test_c7_architecture_qa.py"


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_path(BASE_TEST_PATH, "construction_c7_registry_authority_base")
MODULE = BASE.load_module()


def rehash_registry(registry: dict[str, object]) -> None:
    payload = copy.deepcopy(registry)
    payload.pop("content_sha256", None)
    registry["content_sha256"] = hashlib.sha256(BASE.canonical_json_bytes(payload)).hexdigest()


class ConstructionC7RegistryAuthorityTest(unittest.TestCase):
    def test_c4_public_validator_preserves_valid_report_bytes(self) -> None:
        spec = BASE.make_build_spec(loader="neoforge", allow_modded=True, require_walkability=True)
        ir = BASE.make_ir(
            spec,
            [
                BASE.placement(0, 0, 0, "test:bricks", {"facing": "north"}),
                BASE.placement(1, 0, 0, "test:bricks", {"facing": "north"}),
            ],
        )
        registry = BASE.matching_registry(ir)
        report = MODULE.run_structural_qa(spec, ir, registry)
        digest = hashlib.sha256(BASE.canonical_json_bytes(report)).hexdigest()
        self.assertEqual("6fb8c89accfbc84cd607e7fe9e961f196ca95496e6848fb226e01130da530ee7", digest)

    def test_c4_cross_authority_mismatches_fail_closed(self) -> None:
        spec = BASE.make_build_spec(loader="neoforge", allow_modded=True)
        ir = BASE.make_ir(
            spec,
            [BASE.placement(0, 0, 0, "test:bricks", {"facing": "north"})],
        )
        canonical = BASE.matching_registry(ir)

        def runtime_physical_sha_mismatch(registry: dict[str, object]) -> None:
            registry["runtime"]["physical_snapshot_sha256"] = "2" * 64

        def loader_version_mismatch(registry: dict[str, object]) -> None:
            registry["runtime"]["target"]["loader_version"] = "21.1.999"

        def minecraft_target_mismatch(registry: dict[str, object]) -> None:
            registry["runtime"]["target"]["minecraft"] = "1.21"

        def loader_target_mismatch(registry: dict[str, object]) -> None:
            registry["runtime"]["target"]["loader"] = "forge"

        def missing_physical_source_sha(registry: dict[str, object]) -> None:
            del registry["physical"]["source_sha256"]

        mutations = {
            "runtime physical snapshot SHA mismatch": runtime_physical_sha_mismatch,
            "runtime/physical loader version mismatch": loader_version_mismatch,
            "runtime Minecraft target mismatch": minecraft_target_mismatch,
            "runtime loader target mismatch": loader_target_mismatch,
            "missing physical source SHA": missing_physical_source_sha,
        }

        for label, mutate in mutations.items():
            with self.subTest(label=label):
                registry = copy.deepcopy(canonical)
                mutate(registry)
                rehash_registry(registry)
                with self.assertRaises(MODULE.StructuralQAError):
                    MODULE.run_structural_qa(spec, ir, registry)


if __name__ == "__main__":
    unittest.main()
