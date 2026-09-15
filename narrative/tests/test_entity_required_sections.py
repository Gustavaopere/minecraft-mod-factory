import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLING = ROOT / 'tooling'
sys.path.insert(0, str(TOOLING))
import profile as profile_module
import validate_story as story_module


class EntityRequiredSectionsProfileTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.profile_path = self.root / 'profile.json'
        self.base_profile = {
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'QST', 'DLG', 'EVD'],
            'editorial_state_prefixes': ['DRAFT'],
            'editorial_state_headings': ['Editorial state'],
            'dialogue_required_sections': {'state': ['editorial state'], 'qa': ['qa']},
        }
        self.addCleanup(self.td.cleanup)

    def write_profile(self, required_sections=None):
        data = dict(self.base_profile)
        if required_sections is not None:
            data['entity_required_sections'] = required_sections
        self.profile_path.write_text(json.dumps(data), encoding='utf-8')

    def test_profile_loads_entity_required_sections(self):
        self.write_profile({
            'EVD': {
                'provenance': ['Provenance', 'Origem/proveniência'],
                'limits': ['What it does NOT prove'],
            },
        })
        profile = profile_module.load_profile(self.profile_path, self.root)
        self.assertEqual(('Provenance', 'Origem/proveniência'), profile.entity_required_sections['EVD']['provenance'])
        self.assertEqual(('What it does NOT prove',), profile.entity_required_sections['EVD']['limits'])

    def test_profile_without_entity_required_sections_is_backward_compatible(self):
        self.write_profile()
        profile = profile_module.load_profile(self.profile_path, self.root)
        self.assertEqual({}, profile.entity_required_sections)

    def test_entity_required_sections_reject_unknown_entity_type(self):
        self.write_profile({'ARC': {'premise': ['Premise']}})
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_entity_required_sections_reject_empty_aliases(self):
        self.write_profile({'EVD': {'provenance': []}})
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)


class EntityRequiredSectionsValidationTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.story = self.root / 'story'
        self.story.mkdir()
        self.profile_path = self.root / 'profile.json'
        self.profile_path.write_text(json.dumps({
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'QST', 'DLG', 'EVD'],
            'editorial_state_prefixes': ['DRAFT'],
            'editorial_state_headings': ['Editorial state'],
            'dialogue_required_sections': {'state': ['editorial state'], 'qa': ['qa']},
            'entity_required_sections': {
                'EVD': {
                    'provenance': ['Provenance', 'Origem/proveniência'],
                    'supports': ['What it supports'],
                    'limits': ['What it does NOT prove'],
                },
            },
        }), encoding='utf-8')
        self.profile = profile_module.load_profile(self.profile_path, self.root)
        self.addCleanup(self.td.cleanup)

    def write(self, name, text):
        path = self.story / name
        path.write_text(text, encoding='utf-8')
        return path

    def test_configured_record_with_populated_required_sections_passes(self):
        self.write(
            'EVD-0001-record.md',
            '# EVD-0001 — Record\n\n'
            '## Provenance\nRecovered from the archive.\n\n'
            '## What it supports\nSupports the date of the evacuation.\n\n'
            '## What it does NOT prove\nDoes not identify the saboteur.\n',
        )
        self.assertEqual([], story_module.validate(self.story, self.profile))

    def test_missing_required_section_is_fatal(self):
        self.write(
            'EVD-0001-record.md',
            '# EVD-0001 — Record\n\n'
            '## Provenance\nRecovered from the archive.\n\n'
            '## What it supports\nSupports the date of the evacuation.\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(issue.code == 'missing-required-section' and issue.ref == 'EVD-0001:limits' for issue in issues))
        self.assertEqual(1, story_module.exit_code(issues))

    def test_empty_required_section_is_fatal(self):
        self.write(
            'EVD-0001-record.md',
            '# EVD-0001 — Record\n\n'
            '## Provenance\nRecovered from the archive.\n\n'
            '## What it supports\n\n'
            '## What it does NOT prove\nDoes not identify the saboteur.\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(issue.code == 'empty-required-section' and issue.ref == 'EVD-0001:supports' for issue in issues))
        self.assertEqual(1, story_module.exit_code(issues))

    def test_section_aliases_are_case_insensitive(self):
        self.write(
            'EVD-0001-record.md',
            '# EVD-0001 — Record\n\n'
            '## ORIGEM/PROVENIÊNCIA\nRecovered from the archive.\n\n'
            '## WHAT IT SUPPORTS\nSupports the date of the evacuation.\n\n'
            '## WHAT IT DOES NOT PROVE\nDoes not identify the saboteur.\n',
        )
        self.assertEqual([], story_module.validate(self.story, self.profile))

    def test_unconfigured_entity_types_are_not_structurally_constrained(self):
        self.write('NPC-0001-person.md', '# NPC-0001 — Person\n')
        self.assertEqual([], story_module.validate(self.story, self.profile))

    def test_auxiliary_file_without_entity_declaration_is_ignored(self):
        self.write('EVD-0001-notes.md', '# Authoring notes — EVD-0001\n')
        issues = story_module.validate(self.story, self.profile)
        self.assertFalse(any(issue.code in {'missing-required-section', 'empty-required-section'} for issue in issues))


if __name__ == '__main__':
    unittest.main()
