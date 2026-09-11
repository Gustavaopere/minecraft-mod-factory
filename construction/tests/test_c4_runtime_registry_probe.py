import contextlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE_ROOT = ROOT / "construction" / "runtime" / "neoforge-registry-probe"
PROBE_SOURCE = PROBE_ROOT / "FactoryConstructionRegistryProbe.java"
PROBE_MOD_SPEC = PROBE_ROOT / "mod-spec.json"
PROBE_CONFIG = PROBE_ROOT / "scaffold-config.json"
PREPARE_SCRIPT = ROOT / "construction" / "scripts" / "prepare_neoforge_registry_probe.py"
WORKFLOW = ROOT / ".github" / "workflows" / "factory-construction-c4-modpack-registry.yml"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ConstructionC4RuntimeRegistryProbeTest(unittest.TestCase):
    def require_probe(self):
        required = (PROBE_SOURCE, PROBE_MOD_SPEC, PROBE_CONFIG, PREPARE_SCRIPT)
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        if missing:
            self.skipTest(f"C4 runtime producer intentionally absent during RED: {missing}")

    def test_runtime_probe_required_files_exist(self):
        required = (PROBE_SOURCE, PROBE_MOD_SPEC, PROBE_CONFIG, PREPARE_SCRIPT)
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        self.assertEqual([], missing, f"C4 runtime producer RED: missing required files: {missing}")

    def test_probe_uses_post_registry_neoforge_runtime_authority(self):
        self.require_probe()
        source = PROBE_SOURCE.read_text(encoding="utf-8")
        self.assertIn("BuiltInRegistries.BLOCK", source)
        self.assertIn("getPossibleStates()", source)
        self.assertIn("ServerStartedEvent", source)
        self.assertIn("NeoForge.EVENT_BUS.addListener", source)
        self.assertIn("factory.construction.registryOutput", source)
        self.assertIn("factory.construction.physicalSnapshotSha256", source)
        self.assertIn('"21.1.248"', source)
        self.assertNotIn("BuiltInRegistries.BLOCK.entrySet()", source, "iterate registry keys to avoid relying on entry generic shape")

    def test_probe_materializer_reuses_shared_i3_scaffolder(self):
        self.require_probe()
        module = load_module(PREPARE_SCRIPT, "construction_c4_prepare_probe")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with contextlib.chdir(root):
                generated = module.prepare_runtime_probe(Path("probe"))
            properties = (generated / "gradle.properties").read_text(encoding="utf-8")
            wrapper = (generated / "gradle/wrapper/gradle-wrapper.properties").read_text(encoding="utf-8")
            generated_source = generated / "src/main/java/dev/minecraftmodfactory/constructionprobe/FactoryConstructionRegistryProbe.java"
            self.assertIn("minecraft_version=1.21.1", properties)
            self.assertIn("neo_version=21.1.248", properties)
            self.assertIn("java_version=21", properties)
            self.assertIn("gradle-8.14-bin.zip", wrapper)
            self.assertEqual(PROBE_SOURCE.read_bytes(), generated_source.read_bytes())

    def test_workflow_compiles_materialized_probe_with_java_21(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Set up Java 21", workflow)
        self.assertIn("java-version: '21'", workflow)
        self.assertIn("prepare_neoforge_registry_probe.py", workflow)
        self.assertIn("./gradlew test build --no-daemon", workflow)
        self.assertIn("test_c4_runtime_registry_probe.py", workflow)


if __name__ == "__main__":
    unittest.main()
