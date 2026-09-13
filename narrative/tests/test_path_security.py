import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLING = ROOT / 'tooling'


def load_module(filename, name):
    sys.path.insert(0, str(TOOLING))
    spec = importlib.util.spec_from_file_location(name, TOOLING / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def write_profile(path):
    path.write_text(json.dumps({
        'story_root': 'story',
        'dialogue_root': 'story/dialogues',
        'entity_types': ['NPC', 'QST', 'DLG'],
        'editorial_state_prefixes': ['DRAFT'],
        'editorial_state_headings': ['Editorial state'],
        'dialogue_required_sections': {'state': ['editorial state']},
        'dialogue_entity_type': 'DLG',
    }), encoding='utf-8')


class PathSecurityTests(unittest.TestCase):
    def setUp(self):
        self.workspace_td = tempfile.TemporaryDirectory()
        self.outside_td = tempfile.TemporaryDirectory()
        self.workspace = pathlib.Path(self.workspace_td.name)
        self.outside = pathlib.Path(self.outside_td.name)
        self.profile = self.workspace / 'profile.json'
        write_profile(self.profile)
        self.addCleanup(self.workspace_td.cleanup)
        self.addCleanup(self.outside_td.cleanup)

    def test_story_cli_rejects_root_outside_workspace(self):
        mod = load_module('validate_story.py', 'validate_story_security')
        code = mod.main([
            '--profile', str(self.profile), '--root', str(self.outside)
        ], workspace_root=self.workspace)
        self.assertEqual(2, code)

    def test_dialogue_cli_rejects_root_outside_workspace(self):
        mod = load_module('validate_dialogues.py', 'validate_dialogues_security')
        code = mod.main([
            '--profile', str(self.profile), '--root', str(self.outside)
        ], workspace_root=self.workspace)
        self.assertEqual(2, code)

    def test_inventory_cli_rejects_root_outside_workspace(self):
        mod = load_module('story_inventory.py', 'story_inventory_security')
        code = mod.main([
            '--profile', str(self.profile), '--root', str(self.outside), '--format', 'json'
        ], workspace_root=self.workspace)
        self.assertEqual(2, code)


if __name__ == '__main__':
    unittest.main()
