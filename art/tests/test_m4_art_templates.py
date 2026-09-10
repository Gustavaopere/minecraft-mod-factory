import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "art" / "tooling" / "validate-m4-art-templates.py"
spec = importlib.util.spec_from_file_location("m4_art_templates_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class M4ArtTemplatesTest(unittest.TestCase):
    def test_block_is_complete(self):
        self.assertEqual([], validator.run_validation(ROOT))

    def test_required_template_set_matches_physical_source_tree(self):
        self.assertEqual(
            {
                "art/templates/ANIMATION-BRIEF.md",
                "art/templates/ASSET-BRIEF.md",
                "art/templates/AUDIO-CUE-SHEET.md",
                "art/templates/MODEL-BRIEF.md",
                "art/templates/SPELL-BRIEF.md",
                "art/templates/VFX-BRIEF.md",
                "art/templates/VISUAL-QA.md",
            },
            set(validator.REQUIRED_TEMPLATES),
        )
        self.assertNotIn("art/templates/VISUAL-QA-CHECKLIST.md", validator.REQUIRED_TEMPLATES)
        self.assertNotIn("art/templates/README.md", validator.REQUIRED_TEMPLATES)

    def test_native_authoring_format_is_preserved(self):
        text = (ROOT / "art" / "templates" / "MODEL-BRIEF.md").read_text(encoding="utf-8")
        self.assertIn(".bbmodel", text)

    def test_historical_provider_names_are_not_global_defaults(self):
        text = (ROOT / "art" / "templates" / "ANIMATION-BRIEF.md").read_text(encoding="utf-8")
        self.assertNotIn("Epic Fight/Fresh Animations/provider coexistence", text)
        self.assertIn("provider", text.lower())
        self.assertIn("evidence", text.lower())

    def test_audio_template_is_runtime_neutral(self):
        text = (ROOT / "art" / "templates" / "AUDIO-CUE-SHEET.md").read_text(encoding="utf-8")
        self.assertNotIn("modpack mix", text.lower())
        self.assertIn("runtime", text.lower())
        self.assertIn("verify exact API", text)

    def test_visual_qa_does_not_promote_structural_pass(self):
        text = (ROOT / "art" / "templates" / "VISUAL-QA.md").read_text(encoding="utf-8")
        self.assertIn("Visual result: PASS / FAIL / PENDING", text)
        self.assertIn("Evidence links/screenshots", text)
        self.assertIn("Structural validator", text)

    def test_no_historical_repository_paths_are_promoted(self):
        for relative in validator.REQUIRED_TEMPLATES:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("PROJECT-INSTRUCTIONS/", text, relative)
            self.assertNotIn("Gustavaopere/neoforge-rpg-skilltree", text, relative)

    def test_provenance_records_exact_source_blobs_and_matrix_reconciliation(self):
        data = json.loads((ROOT / validator.MIGRATION_PROVENANCE_PATH).read_text(encoding="utf-8"))
        self.assertEqual("Gustavaopere/neoforge-rpg-skilltree", data["source_repository"])
        self.assertEqual("2ecea4178aa7ac80f99955ab045e296da25376ec", data["source_revision"])
        self.assertEqual(validator.SOURCE_BLOBS, {item["source"]: item["source_blob_sha"] for item in data["files"]})
        reconciliation = data["matrix_reconciliation"]
        self.assertEqual("PROJECT-INSTRUCTIONS/skills/templates/VISUAL-QA-CHECKLIST.md", reconciliation["matrix_named_path"])
        self.assertEqual("PROJECT-INSTRUCTIONS/skills/templates/VISUAL-QA.md", reconciliation["physical_source_path"])
        self.assertEqual("PHYSICAL_TREE_WINS", reconciliation["resolution"])
        self.assertEqual("ABSENT", reconciliation["matrix_named_path_state"])
        self.assertEqual("ABSENT", reconciliation["templates_readme_state"])
        self.assertEqual("ABSENT", reconciliation["blockbench_specialization_state"])


if __name__ == "__main__":
    unittest.main()
