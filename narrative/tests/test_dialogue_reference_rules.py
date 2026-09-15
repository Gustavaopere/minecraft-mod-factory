import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILE_MODULE = ROOT / 'tooling' / 'profile.py'


def load_profile_module():
    spec = importlib.util.spec_from_file_location('narrative_profile_reference_rules', PROFILE_MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
        mod = load_profile_module()
        profile = mod.load_profile(self.profile_path, self.root)
        rule = profile.dialogue_reference_rules['participants']
        self.assertEqual(('NPC',), rule.allowed_types)
        self.assertEqual(1, rule.min_references)


if __name__ == '__main__':
    unittest.main()
