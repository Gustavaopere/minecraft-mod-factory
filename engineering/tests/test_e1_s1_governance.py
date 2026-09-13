import contextlib
import hashlib
import io
import json
import pathlib
import runpy
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

ENGINEERING_PLAN = "plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md"
ART_PLAN = "plans/textura/PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md"
SONAR_WORKFLOW = ROOT / ".github/workflows/factory-sonar-ci.yml"
VALIDATOR = ROOT / "engineering/tooling/validate-e1-s1-governance.py"
SOURCE_REGISTRY = ROOT / "engineering/catalog/sources/SOURCE-REGISTRY.json"

EXPECTED_FILES = [
    "engineering/README.md",
    "engineering/REPO-ROUTING.md",
    "engineering/AGENT-WORKFLOW.md",
    "engineering/DIAGNOSTICS.md",
    "engineering/TESTING.md",
    "engineering/catalog/sources/SOURCE-REGISTRY.json",
    "engineering/tooling/validate-e1-s1-governance.py",
    "skills/README.md",
    "skills/ROUTER.md",
    "skills/VERSION-AUTHORITY.md",
    "skills/USER-GUIDED-WORKFLOW.md",
    ENGINEERING_PLAN,
    ART_PLAN,
]


def run_validator_in_process():
    stream = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(stream):
        try:
            runpy.run_path(str(VALIDATOR), run_name="__main__")
        except SystemExit as exc:
            code = int(exc.code or 0)
    return code, stream.getvalue()


class GovernanceMigrationTests(unittest.TestCase):
    def test_expected_governance_files_exist(self):
        missing = [path for path in EXPECTED_FILES if not (ROOT / path).is_file()]
        self.assertEqual([], missing, f"missing E1/S1 files: {missing}")

    def test_source_registry_binds_both_factory_authorities(self):
        data = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))
        by_id = {entry["source_id"]: entry for entry in data["sources"]}

        control = by_id["integration_control_plane"]
        self.assertEqual("CONFIRMED", control["state"])
        self.assertEqual(
            "Gustavaopere/minecraft-mod-factory",
            control["locator"]["repository_full_name"],
        )
        self.assertEqual("engineering/", control["locator"]["authority_root"])

        art = by_id["repo_textura"]
        self.assertEqual("CONFIRMED", art["state"])
        self.assertEqual(
            "Gustavaopere/minecraft-mod-factory",
            art["locator"]["repository_full_name"],
        )
        self.assertEqual("art/", art["locator"]["authority_root"])

    def test_source_registry_binds_canonical_plans(self):
        data = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))
        by_id = {entry["source_id"]: entry for entry in data["sources"]}

        expected = {
            "mod_engineering_plan_v1_1": ENGINEERING_PLAN,
            "repo_textura_plan_v5_1": ART_PLAN,
        }
        for source_id, rel in expected.items():
            source = by_id[source_id]
            self.assertEqual("CONFIRMED", source["state"])
            self.assertEqual(rel, source["locator"]["path"])
            actual_hash = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            self.assertEqual(actual_hash, source["locator"]["sha256"])

    def test_version_authority_uses_cycle_resolved_neoforge_policy(self):
        text = (ROOT / "skills/VERSION-AUTHORITY.md").read_text(encoding="utf-8")
        self.assertIn("Minecraft: **1.21.1**", text)
        self.assertIn(
            "NeoForge: **21.1.x estável mais recente compatível com Minecraft 1.21.1**",
            text,
        )
        self.assertIn("Java: **21**", text)
        self.assertIn("resolvida no início de cada ciclo relevante de implementação ou validação", text)
        self.assertIn("Não atualizar silenciosamente o NeoForge no meio de um gate já iniciado", text)
        self.assertIn("A resolução exata do ciclo I10 atual é NeoForge **21.1.250**", text)
        self.assertIn("modlist física", text)
        self.assertNotIn("NeoForge: **21.1.248**", text)

    def test_routing_keeps_runtime_outside_factory(self):
        text = (ROOT / "engineering/REPO-ROUTING.md").read_text(encoding="utf-8")
        self.assertIn("Gustavaopere/minecraft-mod-factory", text)
        self.assertIn("runtime authority", text)
        self.assertIn("art/", text)
        self.assertNotIn(
            "Gustavaopere/neoforge-rpg-skilltree` is the canonical integration/control-plane repository",
            text,
        )

    def test_sonar_ci_runs_governance_tests_under_validator_coverage(self):
        workflow = SONAR_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("--include=engineering/tooling/validate-e1-s1-governance.py", workflow)
        self.assertIn("-m unittest engineering/tests/test_e1_s1_governance.py", workflow)

    def test_validator_in_process_accepts_canonical_workspace(self):
        code, output = run_validator_in_process()
        self.assertEqual(0, code, output)
        self.assertIn("E1/S1 governance validation: PASS", output)

    def test_validator_in_process_rejects_registry_plan_drift(self):
        original = SOURCE_REGISTRY.read_bytes()
        try:
            data = json.loads(original.decode("utf-8"))
            by_id = {entry["source_id"]: entry for entry in data["sources"]}
            by_id["repo_textura_plan_v5_1"]["locator"]["path"] = "plans/not-canonical.md"
            by_id["repo_textura_plan_v5_1"]["locator"]["sha256"] = "0" * 64
            SOURCE_REGISTRY.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            code, output = run_validator_in_process()
        finally:
            SOURCE_REGISTRY.write_bytes(original)
        self.assertEqual(1, code, output)
        self.assertIn("wrong canonical plan path for repo_textura_plan_v5_1", output)
        self.assertIn("wrong canonical plan hash for repo_textura_plan_v5_1", output)

    def test_validator_in_process_rejects_factory_authority_drift(self):
        original = SOURCE_REGISTRY.read_bytes()
        try:
            data = json.loads(original.decode("utf-8"))
            by_id = {entry["source_id"]: entry for entry in data["sources"]}
            control = by_id["integration_control_plane"]
            control["state"] = "PENDING"
            control["locator"]["repository_full_name"] = "example/wrong"
            control["locator"]["authority_root"] = "wrong/"
            SOURCE_REGISTRY.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            code, output = run_validator_in_process()
        finally:
            SOURCE_REGISTRY.write_bytes(original)
        self.assertEqual(1, code, output)
        self.assertIn("source not CONFIRMED: integration_control_plane", output)
        self.assertIn("wrong Factory repository binding: integration_control_plane", output)
        self.assertIn("wrong authority root for integration_control_plane", output)

    def test_validator_in_process_rejects_invalid_registry_json(self):
        original = SOURCE_REGISTRY.read_bytes()
        try:
            SOURCE_REGISTRY.write_text("{\n", encoding="utf-8")
            code, output = run_validator_in_process()
        finally:
            SOURCE_REGISTRY.write_bytes(original)
        self.assertEqual(1, code, output)
        self.assertIn("invalid source registry:", output)

    def test_validator_passes_as_cli(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertIn("E1/S1 governance validation: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
