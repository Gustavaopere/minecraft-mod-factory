import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLING = ROOT / 'tooling'
sys.path.insert(0, str(TOOLING))
import profile as profile_module


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


if __name__ == '__main__':
    unittest.main()
