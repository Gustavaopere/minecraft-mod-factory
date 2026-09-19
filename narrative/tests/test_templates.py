import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'templates'


class TemplateTests(unittest.TestCase):
    def test_expected_generic_templates_exist(self):
        expected = {
            'TEMPLATE-HISTORY.md','TEMPLATE-ARC.md','TEMPLATE-NPC.md','TEMPLATE-NPC-AUTHORING.md',
            'TEMPLATE-QUEST.md','TEMPLATE-QUEST-LIFECYCLE.md','TEMPLATE-FACTION.md','TEMPLATE-SETTLEMENT.md',
            'TEMPLATE-LOCATION.md','TEMPLATE-EVENT.md','TEMPLATE-EVIDENCE.md','TEMPLATE-DIALOGUE.md',
            'TEMPLATE-RELATION.md','TEMPLATE-EPILOGUE.md','TEMPLATE-ASSET-BRIEF.md'
        }
        self.assertEqual(expected, {p.name for p in TEMPLATES.glob('*.md')})

    def test_asset_brief_keeps_resolution_and_provider_consumer_owned(self):
        asset = (TEMPLATES / 'TEMPLATE-ASSET-BRIEF.md').read_text(encoding='utf-8')
        for heading in (
            '## Editorial state',
            '## Production state',
            '## Entity ID',
            '## Asset IDs',
            '## Narrative sources',
            '## Resolution and formats',
            '### Portrait/documentation',
            '### Runtime texture/model',
            '## Provider/runtime evidence',
            '## Provenance/license',
            '## Final evidence required',
            '## Pending decisions',
        ):
            self.assertIn(heading, asset)
        self.assertIn('`{{ENTITY_ID}}`', asset)
        self.assertIn('`{{ASSET_ID}}`', asset)
        self.assertNotEqual('{{ENTITY_ID}}', '{{ASSET_ID}}')
        for forbidden in ('2048×2048', '64×64', 'Easy NPC'):
            self.assertNotIn(forbidden, asset)

    def test_templates_do_not_embed_rpg_specific_ids_or_stage08(self):
        joined = '\n'.join(p.read_text(encoding='utf-8') for p in TEMPLATES.glob('*.md'))
        for forbidden in ('NPC-0001', 'QST-0001', 'Stage 08', 'Grimoire/TTRPG.bot'):
            self.assertNotIn(forbidden, joined)


if __name__ == '__main__':
    unittest.main()
