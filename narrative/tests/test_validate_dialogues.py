import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tooling' / 'validate_dialogues.py'


def load_module():
    spec = importlib.util.spec_from_file_location('validate_dialogues', MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class DialogueValidationTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.profile_path = self.root / 'profile.json'
        self.profile_path.write_text(json.dumps({
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'QST', 'DLG'],
            'editorial_state_prefixes': ['DRAFT', 'EXPERIMENTAL'],
            'editorial_state_headings': ['Editorial state', 'Estado editorial'],
            'dialogue_required_sections': {
                'editorial-state': ['editorial state'],
                'participants': ['participants'],
                'context': ['context'],
                'qa': ['qa']
            },
            'dialogue_entity_type': 'DLG'
        }), encoding='utf-8')
        self.dialogues = self.root / 'story' / 'dialogues'
        self.dialogues.mkdir(parents=True)
        self.addCleanup(self.td.cleanup)

    def test_valid_dialogue_passes(self):
        mod = load_module()
        (self.dialogues / 'DLG-0001-test.md').write_text(
            '# DLG-0001 — Test\n\n## Editorial state\nDRAFT\n\n## Participants\n- NPC\n\n## Context\nTest\n\n## QA\n- [x] checked\n',
            encoding='utf-8')
        self.assertEqual([], mod.validate(self.dialogues, mod.load_profile(self.profile_path)))

    def test_missing_required_section_is_reported(self):
        mod = load_module()
        (self.dialogues / 'DLG-0001-test.md').write_text('# DLG-0001 — Test\n', encoding='utf-8')
        issues = mod.validate(self.dialogues, mod.load_profile(self.profile_path))
        self.assertTrue(any(i.code == 'missing-section' and i.detail == 'participants' for i in issues))

    def test_placeholder_id_is_reported(self):
        mod = load_module()
        (self.dialogues / 'DLG-0001-test.md').write_text(
            '# DLG-0001 — Test\n\n## Editorial state\nDRAFT\n\n## Participants\nNPC-####\n\n## Context\nX\n\n## QA\n- [x] checked\n',
            encoding='utf-8')
        issues = mod.validate(self.dialogues, mod.load_profile(self.profile_path))
        self.assertTrue(any(i.code == 'placeholder-id' for i in issues))


if __name__ == '__main__':
    unittest.main()

class DialogueValidationAdditionalTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.profile_path = self.root / 'profile.json'
        self.profile_path.write_text(json.dumps({
            'story_root': 'historia',
            'dialogue_root': 'historia/dialogos',
            'entity_types': ['NPC', 'QST', 'DLG'],
            'editorial_state_prefixes': ['RASCUNHO', 'EXPERIMENTAL'],
            'editorial_state_headings': ['Estado editorial'],
            'dialogue_entity_type': 'DLG',
            'dialogue_required_sections': {
                'editorial-state': ['estado editorial'],
                'participants': ['participantes'],
                'context': ['contexto'],
                'preconditions': ['precondicoes'],
                'knowledge': ['knowledge exigido'],
                'opening': ['abertura', 'entrada padrao'],
                'qa': ['qa']
            }
        }, ensure_ascii=False), encoding='utf-8')
        self.dialogues = self.root / 'historia' / 'dialogos'
        self.dialogues.mkdir(parents=True)
        self.addCleanup(self.td.cleanup)
        self.valid = '''# DLG-0001 — Teste\n\n## Estado editorial\nRASCUNHO\n\n## Participantes\n- NPC-0001\n\n## Contexto\nTeste\n\n## Precondições editoriais\nNenhuma\n\n## Knowledge exigido\nSomente fatos\n\n## Entrada padrão — início\nOlá\n\n## QA\n- [x] ok\n'''

    def test_semantic_heading_alias_abertura_is_accepted(self):
        mod = load_module()
        text = self.valid.replace('## Entrada padrão — início', '## Abertura')
        (self.dialogues / 'DLG-0001-test.md').write_text(text, encoding='utf-8')
        self.assertEqual([], mod.validate(self.dialogues, mod.load_profile(self.profile_path)))

    def test_empty_participants_is_reported(self):
        mod = load_module()
        text = self.valid.replace('## Participantes\n- NPC-0001', '## Participantes\n')
        (self.dialogues / 'DLG-0001-test.md').write_text(text, encoding='utf-8')
        issues = mod.validate(self.dialogues, mod.load_profile(self.profile_path))
        self.assertTrue(any(i.code == 'empty-section' and i.detail == 'participants' for i in issues))

    def test_qa_requires_checkbox(self):
        mod = load_module()
        text = self.valid.replace('- [x] ok', 'ok')
        (self.dialogues / 'DLG-0001-test.md').write_text(text, encoding='utf-8')
        issues = mod.validate(self.dialogues, mod.load_profile(self.profile_path))
        self.assertTrue(any(i.code == 'qa-without-checkbox' for i in issues))

    def test_non_dialogue_markdown_is_ignored(self):
        mod = load_module()
        (self.dialogues / 'README.md').write_text('# Dialogues\n', encoding='utf-8')
        self.assertEqual([], mod.validate(self.dialogues, mod.load_profile(self.profile_path)))

    def test_default_cli_hides_section_and_filename(self):
        mod = load_module()
        text = self.valid.replace('## Knowledge exigido\nSomente fatos\n\n', '')
        (self.dialogues / 'DLG-0001-secret.md').write_text(text, encoding='utf-8')
        from contextlib import redirect_stdout
        from io import StringIO
        out = StringIO()
        with redirect_stdout(out):
            code = mod.main(['--profile', str(self.profile_path), '--root', str(self.dialogues)])
        rendered = out.getvalue()
        self.assertEqual(1, code)
        self.assertIn('ERROR missing-section: 1', rendered)
        self.assertNotIn('knowledge', rendered)
        self.assertNotIn('DLG-0001-secret.md', rendered)

    def test_reveal_cli_shows_section_and_filename(self):
        mod = load_module()
        text = self.valid.replace('## Knowledge exigido\nSomente fatos\n\n', '')
        (self.dialogues / 'DLG-0001-secret.md').write_text(text, encoding='utf-8')
        from contextlib import redirect_stdout
        from io import StringIO
        out = StringIO()
        with redirect_stdout(out):
            code = mod.main(['--profile', str(self.profile_path), '--root', str(self.dialogues), '--reveal'])
        self.assertEqual(1, code)
        self.assertIn('ERROR missing-section knowledge', out.getvalue())
        self.assertIn('DLG-0001-secret.md', out.getvalue())
