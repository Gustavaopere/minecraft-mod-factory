import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "art" / "tooling" / "validate-m4-visual-style-provenance.py"
spec = importlib.util.spec_from_file_location("m4_visual_style_validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class M4VisualStyleProvenanceTest(unittest.TestCase):
    def test_block_is_complete(self):
        self.assertEqual([], validator.run_validation(ROOT))

    def test_required_document_set_is_exact(self):
        self.assertEqual(
            {
                "art/VISUAL-STYLE-BIBLE.md",
                "art/provenance/ART-PIPELINE-SOURCES.md",
                "art/provenance/VISUAL-STYLE-SOURCES.md",
                "art/provenance/SPELL-VFX-AUDIO-SOURCES.md",
            },
            set(validator.REQUIRED_DOCUMENTS),
        )

    def test_historical_paths_are_not_promoted_into_canonical_docs(self):
        for relative in validator.REQUIRED_DOCUMENTS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("PROJECT-INSTRUCTIONS/", text, relative)
            self.assertNotIn("modlist(2).txt", text, relative)

    def test_visual_bible_separates_reusable_grammar_from_pack_snapshot(self):
        text = (ROOT / "art" / "VISUAL-STYLE-BIBLE.md").read_text(encoding="utf-8")
        self.assertIn("../skills/VERSION-AUTHORITY.md", text)
        self.assertIn("Contexto histórico do pack", text)
        self.assertIn("não é regra global da Factory", text)
        self.assertIn("standards/MODEL-ASSET-CONTRACT.md", text)
        self.assertIn("standards/VISUAL-QA.md", text)
        self.assertNotIn("skills/library/minecraft-visual-qa", text)

    def test_current_physical_snapshot_revalidates_provider_presence(self):
        data = json.loads((ROOT / validator.MIGRATION_PROVENANCE_PATH).read_text(encoding="utf-8"))
        snapshot = data["physical_snapshot"]
        self.assertEqual("2026-09-09", snapshot["date"])
        self.assertEqual(
            "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00",
            snapshot["sha256"],
        )
        providers = snapshot["providers"]
        self.assertEqual("2.2.6.a", providers["photon"]["version"])
        self.assertEqual("4.9.2", providers["geckolib"]["version"])
        self.assertEqual("1.21.1-3.16.3", providers["irons_spellbooks"]["version"])
        self.assertEqual("2.0.4+1.21.1", providers["playeranimator"]["version"])
        self.assertEqual("ABSENT", providers["aaa_particles"]["presence"])
        self.assertEqual("UNAVAILABLE", providers["aaa_particles"]["state"])
        self.assertEqual("ABSENT", providers["aaa_particles_world"]["presence"])

    def test_visual_context_is_marked_historical_not_current_authority(self):
        text = (ROOT / "art" / "provenance" / "VISUAL-STYLE-SOURCES.md").read_text(encoding="utf-8")
        self.assertIn("snapshot editorial histórico de 2026-09-08", text)
        self.assertIn("não prova presença atual", text)
        self.assertIn("modlist física 2026-09-09", text)

    def test_aaa_is_not_claimed_as_current_backend(self):
        text = (ROOT / "art" / "provenance" / "SPELL-VFX-AUDIO-SOURCES.md").read_text(encoding="utf-8")
        self.assertIn("AAA Particles", text)
        self.assertIn("ausente no snapshot físico 2026-09-09", text)
        self.assertIn("UNAVAILABLE", text)
        self.assertIn("Photon `2.2.6.a`", text)

    def test_migration_provenance_keeps_exact_historical_blobs(self):
        data = json.loads((ROOT / validator.MIGRATION_PROVENANCE_PATH).read_text(encoding="utf-8"))
        self.assertEqual("Gustavaopere/neoforge-rpg-skilltree", data["source_repository"])
        self.assertEqual("2ecea4178aa7ac80f99955ab045e296da25376ec", data["source_revision"])
        self.assertEqual(validator.SOURCE_BLOBS, {item["source"]: item["source_blob_sha"] for item in data["files"]})


if __name__ == "__main__":
    unittest.main()
