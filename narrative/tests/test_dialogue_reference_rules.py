import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLING = ROOT / 'tooling'
sys.path.insert(0, str(TOOLING))
import profile as profile_module
import validate_dialogues as dialogue_module


class DialogueReferenceRuleProfileTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.profile_path = self.root / 'profile.json'
        self.profile_path.write_text(json.dumps({
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'QST', 'DLG'],
            'editorial_state_prefixes': ['DRAFT'],
            'editorial_state_headings': ['Editorial state'],
            'dialogue_entity_type': 'DLG',
            'dialogue_required_sections': {
                'participants': ['participants'],
                'related-content': ['related content'],
            },
            'dialogue_reference_rules': {
                'participants': {
                    'allowed_types': ['NPC'],
                    'min_references': 1,
                },
            },
        }), encoding='utf-8')
        self.addCleanup(self.td.cleanup)

    def test_profile_loads_dialogue_reference_rule(self):
        profile = profile_module.load_profile(self.profile_path, self.root)
        rule = profile.dialogue_reference_rules['participants']
        self.assertEqual(('NPC',), rule.allowed_types)
        self.assertEqual(1, rule.min_references)


class DialogueReferenceRuleValidationTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.dialogues = self.root / 'story' / 'dialogues'
        self.dialogues.mkdir(parents=True)
        self.profile_path = self.root / 'profile.json'
        self.profile_path.write_text(json.dumps({
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'QST', 'DLG'],
            'editorial_state_prefixes': ['DRAFT'],
            'editorial_state_headings': ['Editorial state'],
            'dialogue_entity_type': 'DLG',
            'dialogue_required_sections': {
                'participants': ['participants'],
                'related-content': ['related content'],
            },
            'dialogue_reference_rules': {
                'participants': {
                    'allowed_types': ['NPC'],
                    'min_references': 1,
                },
                'related-content': {
                    'allowed_types': ['QST'],
                    'min_references': 0,
                },
            },
        }), encoding='utf-8')
        self.profile = profile_module.load_profile(self.profile_path, self.root)
        self.addCleanup(self.td.cleanup)

    def write_dialogue(self, participants: str, related: str = 'QST-0001'):
        path = self.dialogues / 'DLG-0001-test.md'
        path.write_text(
            '# DLG-0001 — Test\n\n'
            f'## Participants\n{participants}\n\n'
            f'## Related content\n{related}\n',
            encoding='utf-8',
        )
        return path

    def test_missing_minimum_section_reference_is_reported(self):
        self.write_dialogue('The local witnesses')
        issues = dialogue_module.validate(self.dialogues, self.profile)
        self.assertTrue(any(issue.code == 'missing-section-reference' and issue.detail == 'participants' for issue in issues))

    def test_reference_with_disallowed_entity_type_is_reported(self):
        self.write_dialogue('QST-0002')
        issues = dialogue_module.validate(self.dialogues, self.profile)
        self.assertTrue(any(issue.code == 'invalid-reference-type' and issue.detail == 'participants:QST-0002' for issue in issues))

    def test_allowed_reference_types_pass(self):
        self.write_dialogue('NPC-0001')
        self.assertEqual([], dialogue_module.validate(self.dialogues, self.profile))


if __name__ == '__main__':
    unittest.main()
