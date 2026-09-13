import importlib.util
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tooling' / 'validate_story.py'


def load_module():
    spec = importlib.util.spec_from_file_location('validate_story', MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class StoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.profile = self.root / 'profile.json'
        self.profile.write_text(json.dumps({
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'QST', 'DLG'],
            'editorial_state_prefixes': ['CANON', 'DRAFT', 'EXPERIMENTAL', 'OBSOLETE'],
            'editorial_state_headings': ['Editorial state', 'Estado editorial'],
            'dialogue_required_sections': {'state': ['editorial state'], 'qa': ['qa']},
        }), encoding='utf-8')
        (self.root / 'story').mkdir()
        self.addCleanup(self.td.cleanup)

    def write(self, rel, text):
        path = self.root / 'story' / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def test_valid_graph_and_stable_state(self):
        mod = load_module()
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n\n## Editorial state\nDRAFT STRUCTURED\n\nQuest QST-0001\n')
        self.write('QST-0001-q.md', '# QST-0001 — Q\n\n## Editorial state\nCANON\n\nNPC NPC-0001\n')
        issues = mod.validate(self.root / 'story', mod.load_profile(self.profile))
        self.assertEqual([], issues)

    def test_duplicate_id_is_fatal(self):
        mod = load_module()
        self.write('a.md', '# NPC-0001 — A\n')
        self.write('b.md', '# NPC-0001 — B\n')
        issues = mod.validate(self.root / 'story', mod.load_profile(self.profile))
        self.assertTrue(any(i.code == 'duplicate-id' for i in issues))
        self.assertEqual(1, mod.exit_code(issues))

    def test_filename_heading_mismatch_is_fatal(self):
        mod = load_module()
        self.write('NPC-0002-wrong.md', '# NPC-0001 — A\n')
        issues = mod.validate(self.root / 'story', mod.load_profile(self.profile))
        self.assertTrue(any(i.code == 'filename-id-mismatch' for i in issues))
        self.assertEqual(1, mod.exit_code(issues))

    def test_auxiliary_heading_does_not_redeclare_entity(self):
        mod = load_module()
        self.write('NPC-0001-main.md', '# NPC-0001 — A\n')
        self.write('NPC-0001-notes.md', '# Authoring sheet — NPC-0001 — A\n')
        issues = mod.validate(self.root / 'story', mod.load_profile(self.profile))
        self.assertFalse(any(i.code == 'duplicate-id' for i in issues))

    def test_unresolved_ref_warns_unless_strict(self):
        mod = load_module()
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n\nQuest QST-9999\n')
        issues = mod.validate(self.root / 'story', mod.load_profile(self.profile))
        self.assertTrue(any(i.code == 'unresolved-ref' for i in issues))
        self.assertEqual(0, mod.exit_code(issues, strict_references=False))
        self.assertEqual(1, mod.exit_code(issues, strict_references=True))

    def test_transient_editorial_state_is_fatal(self):
        mod = load_module()
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n\n## Editorial state\nPROPOSED UNTIL MERGE\n')
        issues = mod.validate(self.root / 'story', mod.load_profile(self.profile))
        self.assertTrue(any(i.code == 'invalid-editorial-state' for i in issues))
        self.assertEqual(1, mod.exit_code(issues))

    def test_default_cli_is_spoiler_safe_and_reveal_is_explicit(self):
        mod = load_module()
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n\nQuest QST-9999\n')
        out = StringIO()
        with redirect_stdout(out):
            code = mod.main(['--profile', str(self.profile), '--root', str(self.root / 'story')])
        text = out.getvalue()
        self.assertEqual(0, code)
        self.assertIn('WARN unresolved-ref: 1', text)
        self.assertNotIn('QST-9999', text)
        out = StringIO()
        with redirect_stdout(out):
            mod.main(['--profile', str(self.profile), '--root', str(self.root / 'story'), '--reveal'])
        self.assertIn('QST-9999', out.getvalue())


if __name__ == '__main__':
    unittest.main()

class StoryValidationAdditionalTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.profile = self.root / 'profile.json'
        self.profile.write_text(json.dumps({
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'QST', 'DLG'],
            'editorial_state_prefixes': ['CANÔNICO', 'RASCUNHO', 'EXPERIMENTAL', 'OBSOLETO'],
            'editorial_state_headings': ['Estado editorial', 'Editorial state'],
            'dialogue_required_sections': {'state': ['estado editorial'], 'qa': ['qa']},
        }, ensure_ascii=False), encoding='utf-8')
        self.story = self.root / 'story'
        self.story.mkdir()
        self.addCleanup(self.td.cleanup)

    def write(self, name, text):
        p = self.story / name
        p.write_text(text, encoding='utf-8')
        return p

    def test_profile_driven_portuguese_state_heading_is_validated(self):
        mod = load_module()
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n\n## Estado editorial\nPROPOSTO ATÉ MERGE\n')
        issues = mod.validate(self.story, mod.load_profile(self.profile))
        self.assertTrue(any(i.code == 'invalid-editorial-state' for i in issues))

    def test_missing_editorial_state_value_is_fatal(self):
        mod = load_module()
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n\n## Estado editorial\n\n## Outra\nX\n')
        issues = mod.validate(self.story, mod.load_profile(self.profile))
        self.assertTrue(any(i.code == 'missing-editorial-state-value' for i in issues))
        self.assertEqual(1, mod.exit_code(issues))

    def test_template_placeholders_are_ignored(self):
        mod = load_module()
        self.write('TEMPLATE-NPC.md', '# NPC-#### — Nome\n\nQuest QST-####\n')
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n')
        self.assertEqual([], mod.validate(self.story, mod.load_profile(self.profile)))

    def test_declaration_reference_is_not_unresolved(self):
        mod = load_module()
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n')
        issues = mod.validate(self.story, mod.load_profile(self.profile))
        self.assertFalse(any(i.code == 'unresolved-ref' for i in issues))

    def test_strict_cli_reports_unresolved_as_error_without_reveal(self):
        mod = load_module()
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n\nQST-9999\n')
        out = StringIO()
        with redirect_stdout(out):
            code = mod.main(['--profile', str(self.profile), '--root', str(self.story), '--strict-references'])
        self.assertEqual(1, code)
        self.assertIn('ERROR unresolved-ref: 1', out.getvalue())
        self.assertNotIn('QST-9999', out.getvalue())

    def test_stable_state_can_have_qualifier(self):
        mod = load_module()
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n\n## Estado editorial\nRASCUNHO ESTRUTURADO / BLOQUEADO\n')
        issues = mod.validate(self.story, mod.load_profile(self.profile))
        self.assertFalse(any(i.code.startswith('invalid-editorial') for i in issues))
