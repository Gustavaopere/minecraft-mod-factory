import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLING = ROOT / 'tooling'
import sys
sys.path.insert(0, str(TOOLING))
import profile as profile_module
import validate_story as story_module


class AuxiliaryDocumentContractProfileTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.profile_path = self.root / 'profile.json'
        self.base_profile = {
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'QST', 'DLG'],
            'editorial_state_prefixes': ['DRAFT'],
            'editorial_state_headings': ['Editorial state'],
            'dialogue_required_sections': {'state': ['editorial state'], 'qa': ['qa']},
        }
        self.addCleanup(self.td.cleanup)

    def write_profile(self, contracts_marker='OMIT'):
        data = dict(self.base_profile)
        if contracts_marker != 'OMIT':
            data['auxiliary_document_contracts'] = contracts_marker
        self.profile_path.write_text(json.dumps(data), encoding='utf-8')

    def valid_contracts(self):
        return {
            'quest-lifecycle': {
                'include': ['aux/**/*-lifecycle.md'],
                'required_sections': {
                    'availability': ['Availability'],
                    'discovery': ['Discovery'],
                },
                'reference_rules': {
                    'discovery': {
                        'allowed_types': ['NPC'],
                        'min_references': 1,
                    },
                },
            },
        }

    def test_profile_loads_auxiliary_document_contract(self):
        self.write_profile(self.valid_contracts())
        profile = profile_module.load_profile(self.profile_path, self.root)
        contracts = getattr(profile, 'auxiliary_document_contracts', None)
        self.assertIsNotNone(contracts)
        contract = contracts['quest-lifecycle']
        self.assertEqual(('aux/**/*-lifecycle.md',), contract.include)
        self.assertEqual(('Availability',), contract.required_sections['availability'])
        self.assertEqual(('NPC',), contract.reference_rules['discovery'].allowed_types)
        self.assertEqual(1, contract.reference_rules['discovery'].min_references)

    def test_profile_without_auxiliary_contracts_is_backward_compatible(self):
        self.write_profile()
        profile = profile_module.load_profile(self.profile_path, self.root)
        self.assertEqual({}, getattr(profile, 'auxiliary_document_contracts', None))

    def test_rejects_non_object_contract_root(self):
        self.write_profile(['quest-lifecycle'])
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_rejects_blank_contract_name(self):
        contracts = self.valid_contracts()
        contracts[' '] = contracts.pop('quest-lifecycle')
        self.write_profile(contracts)
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_rejects_empty_contract_definition(self):
        self.write_profile({'quest-lifecycle': {}})
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_rejects_invalid_include_list(self):
        for invalid in (None, [], ['']):
            with self.subTest(invalid=invalid):
                contracts = self.valid_contracts()
                contracts['quest-lifecycle']['include'] = invalid
                self.write_profile(contracts)
                with self.assertRaises(ValueError):
                    profile_module.load_profile(self.profile_path, self.root)

    def test_rejects_absolute_and_traversal_include_patterns(self):
        for invalid in ('/tmp/*-lifecycle.md', '../*-lifecycle.md', 'aux/../*-lifecycle.md'):
            with self.subTest(invalid=invalid):
                contracts = self.valid_contracts()
                contracts['quest-lifecycle']['include'] = [invalid]
                self.write_profile(contracts)
                with self.assertRaises(ValueError):
                    profile_module.load_profile(self.profile_path, self.root)

    def test_rejects_missing_or_empty_required_sections(self):
        for invalid in (None, {}):
            with self.subTest(invalid=invalid):
                contracts = self.valid_contracts()
                if invalid is None:
                    del contracts['quest-lifecycle']['required_sections']
                else:
                    contracts['quest-lifecycle']['required_sections'] = invalid
                self.write_profile(contracts)
                with self.assertRaises(ValueError):
                    profile_module.load_profile(self.profile_path, self.root)

    def test_reference_rules_require_declared_section(self):
        contracts = self.valid_contracts()
        contracts['quest-lifecycle']['reference_rules'] = {
            'resolution': {'allowed_types': ['NPC']},
        }
        self.write_profile(contracts)
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_reference_rules_reject_unknown_allowed_type(self):
        contracts = self.valid_contracts()
        contracts['quest-lifecycle']['reference_rules']['discovery']['allowed_types'] = ['ARC']
        self.write_profile(contracts)
        with self.assertRaises(ValueError):
            profile_module.load_profile(self.profile_path, self.root)

    def test_reference_rules_reject_invalid_minimum(self):
        for invalid in (-1, True, '1'):
            with self.subTest(invalid=invalid):
                contracts = self.valid_contracts()
                contracts['quest-lifecycle']['reference_rules']['discovery']['min_references'] = invalid
                self.write_profile(contracts)
                with self.assertRaises(ValueError):
                    profile_module.load_profile(self.profile_path, self.root)


class AuxiliaryDocumentContractValidationTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.story = self.root / 'story'
        self.story.mkdir()
        self.aux = self.story / 'aux' / 'quests'
        self.aux.mkdir(parents=True)
        self.profile_path = self.root / 'profile.json'
        self.profile_path.write_text(json.dumps({
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'QST', 'DLG'],
            'editorial_state_prefixes': ['DRAFT'],
            'editorial_state_headings': ['Editorial state'],
            'dialogue_required_sections': {'state': ['editorial state'], 'qa': ['qa']},
            'auxiliary_document_contracts': {
                'quest-lifecycle': {
                    'include': ['aux/**/*-lifecycle.md'],
                    'required_sections': {
                        'availability': ['Availability'],
                        'discovery': ['Discovery'],
                    },
                    'reference_rules': {
                        'discovery': {
                            'allowed_types': ['NPC'],
                            'min_references': 1,
                        },
                    },
                },
            },
        }), encoding='utf-8')
        self.profile = profile_module.load_profile(self.profile_path, self.root)
        self.write_story('NPC-0001-person.md', '# NPC-0001 — Person\n')
        self.write_story('QST-0001-quest.md', '# QST-0001 — Quest\n')
        self.addCleanup(self.td.cleanup)

    def write_story(self, name, text):
        path = self.story / name
        path.write_text(text, encoding='utf-8')
        return path

    def write_aux(self, name, text):
        path = self.aux / name
        path.write_text(text, encoding='utf-8')
        return path

    def test_matching_auxiliary_document_missing_section_is_fatal(self):
        self.write_aux(
            'QST-0001-lifecycle.md',
            '# Lifecycle editorial de QST-0001 — Quest\n\n'
            '## Availability\nAvailable after the prologue.\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(
            issue.code == 'missing-auxiliary-required-section'
            and issue.ref == 'quest-lifecycle:discovery'
            for issue in issues
        ))
        self.assertEqual(1, story_module.exit_code(issues))

    def test_matching_auxiliary_document_empty_section_is_fatal(self):
        self.write_aux(
            'QST-0001-lifecycle.md',
            '# Lifecycle editorial de QST-0001 — Quest\n\n'
            '## Availability\nAvailable.\n\n'
            '## Discovery\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(
            issue.code == 'empty-auxiliary-required-section'
            and issue.ref == 'quest-lifecycle:discovery'
            for issue in issues
        ))
        self.assertEqual(1, story_module.exit_code(issues))

    def test_missing_minimum_reference_is_fatal(self):
        self.write_aux(
            'QST-0001-lifecycle.md',
            '# Lifecycle editorial de QST-0001 — Quest\n\n'
            '## Availability\nAvailable.\n\n'
            '## Discovery\nA local witness starts the trail.\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(
            issue.code == 'missing-auxiliary-section-reference'
            and issue.ref == 'quest-lifecycle:discovery'
            for issue in issues
        ))

    def test_disallowed_reference_type_is_fatal(self):
        self.write_aux(
            'QST-0001-lifecycle.md',
            '# Lifecycle editorial de QST-0001 — Quest\n\n'
            '## Availability\nAvailable.\n\n'
            '## Discovery\nQST-0001 exposes the lead.\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(
            issue.code == 'invalid-auxiliary-reference-type'
            and issue.ref == 'quest-lifecycle:discovery:QST-0001'
            for issue in issues
        ))

    def test_duplicate_reference_does_not_satisfy_distinct_minimum(self):
        data = json.loads(self.profile_path.read_text(encoding='utf-8'))
        data['auxiliary_document_contracts']['quest-lifecycle']['reference_rules']['discovery']['min_references'] = 2
        self.profile_path.write_text(json.dumps(data), encoding='utf-8')
        profile = profile_module.load_profile(self.profile_path, self.root)
        self.write_aux(
            'QST-0001-lifecycle.md',
            '# Lifecycle editorial de QST-0001 — Quest\n\n'
            '## Availability\nAvailable.\n\n'
            '## Discovery\nNPC-0001 and NPC-0001 know the lead.\n',
        )
        issues = story_module.validate(self.story, profile)
        self.assertTrue(any(issue.code == 'missing-auxiliary-section-reference' for issue in issues))

    def test_missing_section_does_not_duplicate_reference_error(self):
        self.write_aux(
            'QST-0001-lifecycle.md',
            '# Lifecycle editorial de QST-0001 — Quest\n\n'
            '## Availability\nAvailable.\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(issue.code == 'missing-auxiliary-required-section' for issue in issues))
        self.assertFalse(any(issue.code == 'missing-auxiliary-section-reference' for issue in issues))

    def test_empty_section_does_not_duplicate_reference_error(self):
        self.write_aux(
            'QST-0001-lifecycle.md',
            '# Lifecycle editorial de QST-0001 — Quest\n\n'
            '## Availability\nAvailable.\n\n'
            '## Discovery\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(issue.code == 'empty-auxiliary-required-section' for issue in issues))
        self.assertFalse(any(issue.code == 'missing-auxiliary-section-reference' for issue in issues))

    def test_unmatched_auxiliary_document_is_unaffected(self):
        self.write_aux('QST-0001-notes.md', '# Notes for QST-0001\n')
        issues = story_module.validate(self.story, self.profile)
        self.assertFalse(any(issue.code.startswith('missing-auxiliary') or issue.code.startswith('empty-auxiliary') for issue in issues))

    def test_auxiliary_h1_reference_does_not_create_declaration(self):
        self.write_aux(
            'QST-0009-lifecycle.md',
            '# Lifecycle editorial de QST-0009 — Unknown quest\n\n'
            '## Availability\nAvailable.\n\n'
            '## Discovery\nNPC-0001 knows the lead.\n',
        )
        issues = story_module.validate(self.story, self.profile)
        self.assertTrue(any(issue.code == 'unresolved-ref' and issue.ref == 'QST-0009' for issue in issues))

    def test_true_entity_record_matched_by_glob_is_not_auxiliary_validated(self):
        self.write_aux('QST-0002-lifecycle.md', '# QST-0002 — Actual entity record\n')
        issues = story_module.validate(self.story, self.profile)
        self.assertFalse(any(
            issue.code in {
                'missing-auxiliary-required-section',
                'empty-auxiliary-required-section',
                'missing-auxiliary-section-reference',
                'invalid-auxiliary-reference-type',
            }
            and issue.path.name == 'QST-0002-lifecycle.md'
            for issue in issues
        ))

    def test_matching_symlink_outside_story_root_fails_closed(self):
        outside = self.root / 'outside-lifecycle.md'
        outside.write_text(
            '# Lifecycle editorial de QST-0001\n\n'
            '## Availability\nAvailable.\n\n'
            '## Discovery\nNPC-0001 knows the lead.\n',
            encoding='utf-8',
        )
        link = self.aux / 'QST-0001-external-lifecycle.md'
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable on this platform')
        with self.assertRaises(ValueError):
            story_module.validate(self.story, self.profile)


if __name__ == '__main__':
    unittest.main()
