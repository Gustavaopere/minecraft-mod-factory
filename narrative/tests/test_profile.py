import json
import pathlib
import tempfile
import unittest
import importlib.util
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'tooling' / 'profile.py'


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class ProfileTests(unittest.TestCase):
    def test_load_profile_normalizes_required_fields(self):
        mod = load_module(PROFILE, 'profile')
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / 'profile.json'
            path.write_text(json.dumps({
                'story_root': 'historia',
                'dialogue_root': 'historia/dialogos',
                'entity_types': ['NPC', 'QST', 'DLG'],
                'editorial_state_prefixes': ['CANON', 'DRAFT'],
                'editorial_state_headings': ['Editorial state', 'Estado editorial'],
                'dialogue_required_sections': {'state': ['state'], 'qa': ['qa']},
            }), encoding='utf-8')
            profile = mod.load_profile(path)
        self.assertEqual(('NPC', 'QST', 'DLG'), profile.entity_types)
        self.assertEqual(('CANON', 'DRAFT'), profile.editorial_state_prefixes)
        self.assertEqual(('state',), profile.dialogue_required_sections['state'])

    def test_invalid_profile_rejects_empty_entity_types(self):
        mod = load_module(PROFILE, 'profile_invalid')
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / 'profile.json'
            path.write_text(json.dumps({
                'story_root': 'story',
                'dialogue_root': 'story/dialogue',
                'entity_types': [],
                'editorial_state_prefixes': ['DRAFT'],
                'editorial_state_headings': ['Editorial state', 'Estado editorial'],
                'dialogue_required_sections': {'state': ['state']},
            }), encoding='utf-8')
            with self.assertRaises(ValueError):
                mod.load_profile(path)


if __name__ == '__main__':
    unittest.main()
