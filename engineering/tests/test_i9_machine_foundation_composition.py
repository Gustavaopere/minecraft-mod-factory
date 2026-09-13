import contextlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = ROOT / "engineering/tooling/machine-foundation/materialize_i9.py"
OVERLAY = ROOT / "engineering/tests/golden/i9-machine-foundation/overlay"
MANIFEST = ROOT / "engineering" / "tests" / "golden" / "i9-machine-foundation" / "manifest.json"


def load_materializer():
    if not MATERIALIZER.is_file():
        raise AssertionError("I9 RED: materializer is missing")
    spec = importlib.util.spec_from_file_location("i9_materializer_composition", MATERIALIZER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_manifest():
    if not MANIFEST.is_file():
        raise AssertionError("I9 RED: manifest is missing")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def file_map(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class I9MachineFoundationCompositionTest(unittest.TestCase):
    def test_output_is_contained_and_workspace_root_is_rejected(self):
        module = load_materializer()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            outside = workspace.parent / (workspace.name + "-outside")
            with contextlib.chdir(workspace):
                with self.assertRaises(module.MaterializationError):
                    module.materialize_i9(workspace)
                with self.assertRaises(module.MaterializationError):
                    module.materialize_i9(outside)

    def test_manifest_root_keys_are_closed(self):
        module = load_materializer()
        manifest = canonical_manifest()
        manifest["unexpected"] = True
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            path = workspace / "manifest.json"
            write_json(path, manifest)
            with contextlib.chdir(workspace), mock.patch.object(module, "MANIFEST_PATH", path):
                with self.assertRaises(module.MaterializationError):
                    module.materialize_i9("generated")
            self.assertFalse((workspace / "generated").exists())

    def test_manifest_cannot_delegate_write_mapping_authority(self):
        module = load_materializer()
        manifest = canonical_manifest()
        manifest["files"][0]["destination"] = "ALTERNATE-I9.md"
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            path = workspace / "manifest.json"
            write_json(path, manifest)
            with contextlib.chdir(workspace), mock.patch.object(module, "MANIFEST_PATH", path):
                with self.assertRaises(module.MaterializationError):
                    module.materialize_i9("generated")
            self.assertFalse((workspace / "generated").exists())

    def test_overlay_rejects_duplicate_paths(self):
        module = load_materializer()
        manifest = canonical_manifest()
        manifest["files"].append(dict(manifest["files"][0]))
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            path = workspace / "manifest.json"
            write_json(path, manifest)
            with contextlib.chdir(workspace), mock.patch.object(module, "MANIFEST_PATH", path):
                with self.assertRaises(module.MaterializationError):
                    module.materialize_i9("generated")
            self.assertFalse((workspace / "generated").exists())

    def test_overlay_rejects_existing_generated_destination(self):
        module = load_materializer()
        manifest = canonical_manifest()
        manifest["files"][0]["destination"] = "build.gradle"
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            path = workspace / "manifest.json"
            write_json(path, manifest)
            with contextlib.chdir(workspace), mock.patch.object(module, "MANIFEST_PATH", path):
                with self.assertRaises(module.MaterializationError):
                    module.materialize_i9("generated")
            self.assertFalse((workspace / "generated").exists())

    def test_existing_output_is_preserved(self):
        module = load_materializer()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            output = workspace / "generated"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("preserve", encoding="utf-8")
            with contextlib.chdir(workspace):
                with self.assertRaises(module.MaterializationError):
                    module.materialize_i9(output)
            self.assertEqual("preserve", marker.read_text(encoding="utf-8"))

    def test_zero_and_multiple_constructor_anchor_matches_fail_closed(self):
        module = load_materializer()
        cases = (("missing-constructor-anchor", "replacement"), ("\n", "\n"))
        for anchor, replacement in cases:
            with self.subTest(anchor=anchor):
                manifest = canonical_manifest()
                manifest["main_class_patch"]["anchor"] = anchor
                manifest["main_class_patch"]["replacement"] = replacement
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp)
                    path = workspace / "manifest.json"
                    write_json(path, manifest)
                    with contextlib.chdir(workspace), mock.patch.object(module, "MANIFEST_PATH", path):
                        with self.assertRaises(module.MaterializationError):
                            module.materialize_i9("generated")
                    self.assertFalse((workspace / "generated").exists())

    def test_materialization_is_deterministic_and_overlay_is_byte_exact(self):
        module = load_materializer()
        manifest = canonical_manifest()
        entry = manifest["files"][0]
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with contextlib.chdir(workspace):
                first = module.materialize_i9("first")
                second = module.materialize_i9("second")
            self.assertEqual(file_map(first), file_map(second))
            self.assertEqual((OVERLAY / entry["source"]).read_bytes(), (first / entry["destination"]).read_bytes())

    def test_main_patch_preserves_canonical_constructor_signature(self):
        module = load_materializer()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with contextlib.chdir(workspace):
                generated = module.materialize_i9("generated")
            main_class = generated / "src/main/java/dev/example/i9machine/I9MachineMod.java"
            text = main_class.read_text(encoding="utf-8")
            self.assertIn("public I9MachineMod(IEventBus modBus, ModContainer container)", text)
            self.assertIn("dev.example.i9machine.machine.I9MachineContent.register(modBus);", text)
            self.assertIn("modBus.addListener(dev.example.i9machine.machine.I9MachineContent::registerCapabilities);", text)


if __name__ == "__main__":
    unittest.main()
