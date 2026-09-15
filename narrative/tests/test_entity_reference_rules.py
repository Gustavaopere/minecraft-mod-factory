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


class EntityReferenceRuleProfileTests(unittest.TestCase):
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
            'entity_required_sections': {
                'EVD': {
                    'known-by': ['Known by'],
                    'supports': ['What it supports'],
                },
            },
        }
        self.addCleanup(self.td.cleanup)

    def write_profile(self, rules=None):
        data = dict(self.base_profile)
        if rules is not None:
            data['entity_reference_rules'] = rules
        self.profile_path.write_text(json.dumps(data), encoding='utf-8')

    def test_profile_loads_entity_reference_rule(self):
        self.write_profile({
            'EVD': {
                'known-by': {
                    'allowed_types': ['NPC'],
                    'min_references': 1,
                },
            },
        })
        profile = profile_module.load_profile(self.profile_path, self.root)
        rule = profile.entity_reference_rules['EVD']['known-by']
        self.assertEqual(('NPC',), rule.allowed_types)
        self.assertEqual(1, rule.min_references)

    def test_profile_without_entity_reference_rules_is_backward_compatible(self):
        self.write_profile()
        profile = profile_module.load_profile(self.profile_path, self.root)
        self.assertEqual({}, profile.entity_reference_rules)

    def test_entity_reference_rules_reject_non_object_root(self):
        self.write_profile(['EVD'])
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_entity_reference_rules_reject_unknown_entity_type(self):
        self.write_profile({'ARC': {'known-by': {'allowed_types': ['NPC']}}})
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_entity_reference_rules_reject_empty_type_contract(self):
        self.write_profile({'EVD': {}})
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_entity_reference_rules_require_declared_required_section(self):
        self.write_profile({'EVD': {'provenance': {'allowed_types': ['NPC']}}})
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_entity_reference_rules_reject_non_object_rule(self):
        self.write_profile({'EVD': {'known-by': ['NPC']}})
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_entity_reference_rules_reject_empty_allowed_types(self):
        self.write_profile({'EVD': {'known-by': {'allowed_types': []}}})
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_entity_reference_rules_reject_unknown_allowed_entity_type(self):
        self.write_profile({'EVD': {'known-by': {'allowed_types': ['ARC']}}})
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_entity_reference_rules_reject_invalid_minimum(self):
        for invalid in (-1, True, '1'):
            with self.subTest(invalid=invalid):
                self.write_profile({
                    'EVD': {
                        'known-by': {
                            'allowed_types': ['NPC'],
                            'min_references': invalid,
                        },
                    },
                })
                with self.assertRaises(ValueError):
                    profile_module.load_profile(self.profile_path, self.root)


class EntityReferenceRuleValidationTests(unittest.TestCase):
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
                    'known-by': ['Known by', 'Initial knowers'],
                    'supports': ['What it supports'],
                },
            },
            'entity_reference_rules': {
                'EVD': {
                    'known-by': {
                        'allowed_types': ['NPC'],
                        'min_references': 1,
                    },
                    'supports': {
                        'allowed_types': ['QST'],
                        'min_references': 0,
                    },
                },
            },
        }), encoding='utf-8')
        self.profile = profile_module.load_profile(self.profile_path, self.root)
        self.write('NPC-0001-person.md', '# NPC-0001 — Person\n')
        self.write('QST-0001-quest.md', '# QST-0001 — Quest\n')
        self.addCleanup(self.td.cleanup)

    def write(self, name, text):
        path = self.story / name
        path.write_text(text, encoding='utf-8')
        return path

    def write_evidence(self, known_by: str, supports: str = 'QST-0001'):
        return self.write(
            'EVD-0001-record.md',
            '# EVD-0001 — Record\n\n'
            f'## Known by\n{known_by}\n\n'
            f'## What it supports\n{supports}\n',
        )

    def test_allowed_reference_types_pass(self):
        self.write_evidence('NPC-0001')
        self.assertEqual([], story_module.validate(self.story, self.profile))

    def test_populated_alias_satisfies_reference_rule(self):
        self.write(
            'EVD-0001-record.md',
            '# EVD-0001 — Record\n\n'
            '## Known by\n\n'
            '## Initial knowers\nNPC-0001\n\n'
            '## What it supports\nQST-0001\n',
        )
        self.assertEqual([], story_module.validate(self.story, self.profile))

    def test_missing_minimum_section_reference_is_fatal(self):
        self.write_evidence('The local witnesses')
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(
            issue.code == 'missing-entity-section-reference'
            and issue.ref == 'EVD-0001:known-by'
            for issue in issues
        ))
        self.assertEqual(1, story_module.exit_code(issues))

    def test_reference_with_disallowed_entity_type_is_fatal(self):
        self.write_evidence('QST-0001')
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(
            issue.code == 'invalid-entity-reference-type'
            and issue.ref == 'EVD-0001:known-by:QST-0001'
            for issue in issues
        ))
        self.assertEqual(1, story_module.exit_code(issues))

    def test_duplicate_reference_does_not_satisfy_minimum_cardinality(self):
        profile_data = json.loads(self.profile_path.read_text(encoding='utf-8'))
        profile_data['entity_reference_rules']['EVD']['known-by']['min_references'] = 2
        self.profile_path.write_text(json.dumps(profile_data), encoding='utf-8')
        profile = profile_module.load_profile(self.profile_path, self.root)
        self.write_evidence('NPC-0001 and NPC-0001')
        issues = story_module.validate(self.story, profile)
        self.assertTrue(any(issue.code == 'missing-entity-section-reference' for issue in issues))

    def test_missing_required_section_does_not_duplicate_reference_error(self):
        self.write(
            'EVD-0001-record.md',
            '# EVD-0001 — Record\n\n'
            '## What it supports\nQST-0001\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(issue.code == 'missing-required-section' and issue.ref == 'EVD-0001:known-by' for issue in issues))
        self.assertFalse(any(issue.code == 'missing-entity-section-reference' for issue in issues))

    def test_empty_required_section_does_not_duplicate_reference_error(self):
        self.write(
            'EVD-0001-record.md',
            '# EVD-0001 — Record\n\n'
            '## Known by\n\n'
            '## What it supports\nQST-0001\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(issue.code == 'empty-required-section' and issue.ref == 'EVD-0001:known-by' for issue in issues))
        self.assertFalse(any(issue.code == 'missing-entity-section-reference' for issue in issues))

    def test_unconfigured_entity_types_are_not_reference_constrained(self):
        self.write('QST-0002-other.md', '# QST-0002 — Other\n\n## Known by\nEVD-9999\n')
        issues = story_module.validate(self.story, self.profile)
        self.assertFalse(any(
            issue.code in {'missing-entity-section-reference', 'invalid-entity-reference-type'}
            and issue.ref.startswith('QST-0002:')
            for issue in issues
        ))


if __name__ == '__main__':
    unittest.main()
