import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "art" / "tooling" / "validate-m4-standards-core.py"
spec = importlib.util.spec_from_file_location("m4_standards_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class M4StandardsCoreTest(unittest.TestCase):
    def test_m4_standards_core_is_complete(self):
        self.assertEqual([], validator.run_validation(ROOT))

    def test_required_standard_set_is_exact(self):
        self.assertEqual(
            {
                "MODEL-ASSET-CONTRACT.md",
                "VISUAL-QA.md",
                "VFX-QA.md",
                "AUDIO-QA.md",
                "SPELL-PRESENTATION-CONTRACT.md",
            },
            set(validator.REQUIRED_STANDARDS),
        )

    def test_standards_do_not_retain_historical_repo_paths(self):
        for name in validator.REQUIRED_STANDARDS:
            text = (ROOT / "art" / "standards" / name).read_text(encoding="utf-8")
            self.assertNotIn("PROJECT-INSTRUCTIONS/", text, name)
            self.assertNotIn("Gustavaopere/neoforge-rpg-skilltree", text, name)

    def test_model_contract_preserves_native_authoring_rule(self):
        text = (ROOT / "art" / "standards" / "MODEL-ASSET-CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn(".bbmodel", text)
        self.assertIn("UNRESOLVED", text)
        self.assertIn("VISUAL-QA.md", text)

    def test_spell_contract_preserves_runtime_authority_boundary(self):
        text = (ROOT / "art" / "standards" / "SPELL-PRESENTATION-CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("não substitui o contrato de gameplay do provider", text)
        self.assertIn("VFX-QA.md", text)
        self.assertIn("AUDIO-QA.md", text)

    def test_provenance_records_exact_historical_source(self):
        data = json.loads((ROOT / "migration" / "M4-STANDARDS-CORE-PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertEqual("Gustavaopere/neoforge-rpg-skilltree", data["source_repository"])
        self.assertEqual("2ecea4178aa7ac80f99955ab045e296da25376ec", data["source_revision"])
        self.assertEqual(sorted(validator.REQUIRED_STANDARDS), sorted(item["destination"].split("/")[-1] for item in data["files"]))

    def test_git_blob_sha_uses_git_plumbing_without_direct_sha1(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("hashlib.sha1", source)
        self.assertEqual(
            "47d05ff6403c8e6c3cf635ea6eb9263738432773",
            validator._git_blob_sha(b"payload"),
        )


if __name__ == "__main__":
    unittest.main()
