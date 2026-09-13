import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tooling' / 'story_inventory.py'


def load_module():
    spec = importlib.util.spec_from_file_location('story_inventory', MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class InventoryTests(unittest.TestCase):
    def test_inventory_uses_profile_types_and_ignores_auxiliary_headings(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            profile_path = root / 'profile.json'
            profile_path.write_text(json.dumps({
                'story_root': 'story',
                'dialogue_root': 'story/dialogues',
                'entity_types': ['NPC', 'QST', 'DLG'],
                'editorial_state_prefixes': ['DRAFT'],
                'editorial_state_headings': ['Editorial state', 'Estado editorial'],
                'dialogue_required_sections': {'state': ['editorial state']},
            }), encoding='utf-8')
            story = root / 'story'
            story.mkdir()
            (story / 'NPC-0001-main.md').write_text('# NPC-0001 — A\n\n## Editorial state\nDRAFT\n\nQST-0001\n', encoding='utf-8')
            (story / 'NPC-0001-notes.md').write_text('# Authoring sheet — NPC-0001 — A\n', encoding='utf-8')
            (story / 'QST-0001-q.md').write_text('# QST-0001 — Q\n\n## Editorial state\nDRAFT\n', encoding='utf-8')
            records = mod.inventory(story, mod.load_profile(profile_path, root))
        self.assertEqual(['NPC-0001', 'QST-0001'], [r.id for r in records])
        self.assertEqual(('QST-0001',), records[0].references)


if __name__ == '__main__':
    unittest.main()

class InventoryAdditionalTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.profile_path = self.root / 'profile.json'
        self.profile_path.write_text(json.dumps({
            'story_root': 'historia',
            'dialogue_root': 'historia/dialogos',
            'entity_types': ['NPC', 'QST', 'FAC', 'DLG'],
            'editorial_state_prefixes': ['CANÔNICO', 'RASCUNHO'],
            'editorial_state_headings': ['Estado editorial'],
            'dialogue_required_sections': {'state': ['estado editorial']},
        }, ensure_ascii=False), encoding='utf-8')
        self.story = self.root / 'historia'
        self.story.mkdir()
        self.addCleanup(self.td.cleanup)

    def mod(self):
        return load_module()

    def test_extracts_title_state_and_deduped_references(self):
        mod = self.mod(); profile = mod.load_profile(self.profile_path, self.root)
        (self.story/'npc.md').write_text('# NPC-0001 — Severin\n\n## Estado editorial\nCANÔNICO\n\nQST-0001 QST-0001 FAC-0002\n', encoding='utf-8')
        (self.story/'quest.md').write_text('# QST-0001 — Ecos\n', encoding='utf-8')
        (self.story/'fac.md').write_text('# FAC-0002 — Ordem\n', encoding='utf-8')
        record = {r.id:r for r in mod.inventory(self.story, profile)}['NPC-0001']
        self.assertEqual('Severin', record.title)
        self.assertEqual('CANÔNICO', record.state)
        self.assertEqual(('FAC-0002','QST-0001'), record.references)

    def test_missing_state_is_explicit(self):
        mod = self.mod(); profile = mod.load_profile(self.profile_path, self.root)
        (self.story/'npc.md').write_text('# NPC-0001 — A\n', encoding='utf-8')
        self.assertEqual('NOT DECLARED', mod.inventory(self.story, profile)[0].state)

    def test_template_placeholder_is_ignored(self):
        mod = self.mod(); profile = mod.load_profile(self.profile_path, self.root)
        (self.story/'template.md').write_text('# NPC-#### — Nome\n', encoding='utf-8')
        (self.story/'real.md').write_text('# NPC-0001 — A\n', encoding='utf-8')
        self.assertEqual(['NPC-0001'], [r.id for r in mod.inventory(self.story, profile)])

    def test_auxiliary_heading_does_not_create_record(self):
        mod = self.mod(); profile = mod.load_profile(self.profile_path, self.root)
        (self.story/'NPC-0001-main.md').write_text('# NPC-0001 — A\n', encoding='utf-8')
        (self.story/'NPC-0001-notes.md').write_text('# Authoring sheet — NPC-0001 — A\n', encoding='utf-8')
        self.assertEqual(['NPC-0001'], [r.id for r in mod.inventory(self.story, profile)])

    def test_records_are_sorted_by_id(self):
        mod = self.mod(); profile = mod.load_profile(self.profile_path, self.root)
        for name,text in [('b.md','# QST-0002 — B\n'),('a.md','# NPC-0003 — A\n'),('c.md','# NPC-0001 — C\n')]:
            (self.story/name).write_text(text, encoding='utf-8')
        self.assertEqual(['NPC-0001','NPC-0003','QST-0002'], [r.id for r in mod.inventory(self.story, profile)])

    def test_markdown_report_contains_summary(self):
        mod = self.mod(); profile = mod.load_profile(self.profile_path, self.root)
        (self.story/'a.md').write_text('# NPC-0001 — A\n\n## Estado editorial\nCANÔNICO\n', encoding='utf-8')
        (self.story/'b.md').write_text('# QST-0001 — B\n\n## Estado editorial\nRASCUNHO\n', encoding='utf-8')
        report = mod.render_markdown(mod.inventory(self.story, profile), self.story)
        self.assertIn('NPC: 1', report); self.assertIn('QST: 1', report); self.assertIn('| NPC-0001 | A | CANÔNICO |', report)

    def test_json_report_is_machine_readable(self):
        mod = self.mod(); profile = mod.load_profile(self.profile_path, self.root)
        (self.story/'a.md').write_text('# NPC-0001 — A\n', encoding='utf-8')
        payload = json.loads(mod.render_json(mod.inventory(self.story, profile), self.story))
        self.assertEqual('NPC-0001', payload['records'][0]['id'])
        self.assertEqual(1, payload['summary']['by_type']['NPC'])
