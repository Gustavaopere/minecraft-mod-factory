import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tooling' / 'golden_check.py'


def load_module():
    spec = importlib.util.spec_from_file_location('golden_check', MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class GoldenCompatibilityTests(unittest.TestCase):
    def test_profile_compatibility_is_additive_within_same_revision(self):
        mod = load_module()
        previous = {'profile_contract_revision': 1, 'required_keys': ['story_root', 'entity_types']}
        current = {'profile_contract_revision': 1, 'required_keys': ['story_root', 'entity_types'], 'optional_keys': ['chronology_contract']}
        self.assertEqual([], mod.compatibility_issues(previous, current))

    def test_profile_revision_change_requires_migration_note(self):
        mod = load_module()
        previous = {'profile_contract_revision': 1, 'required_keys': ['story_root']}
        current = {'profile_contract_revision': 2, 'required_keys': ['story_root']}
        codes = {issue.code for issue in mod.compatibility_issues(previous, current)}
        self.assertIn('profile-revision-changed-without-migration', codes)
        current['migration'] = {'from_revision': 1, 'document': 'narrative/migrations/profile-v1-to-v2.md'}
        self.assertEqual([], mod.compatibility_issues(previous, current))

    def test_golden_manifest_detects_output_mismatch(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            expected = root / 'expected.txt'
            actual = root / 'actual.txt'
            expected.write_text('expected\n', encoding='utf-8')
            actual.write_text('actual\n', encoding='utf-8')
            manifest = {
                'schema_version': 1,
                'profile_contract_revision': 1,
                'goldens': [{'name': 'diagnostics', 'expected': 'expected.txt', 'actual': 'actual.txt'}]
            }
            manifest_path = root / 'manifest.json'
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            codes = {issue.code for issue in mod.check_materialized_goldens(manifest_path, root)}
            self.assertIn('golden-output-mismatch', codes)

    def test_golden_manifest_accepts_exact_materialized_outputs(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            expected = root / 'expected.txt'
            actual = root / 'actual.txt'
            expected.write_text('same\n', encoding='utf-8')
            actual.write_text('same\n', encoding='utf-8')
            manifest = {
                'schema_version': 1,
                'profile_contract_revision': 1,
                'goldens': [{'name': 'inventory', 'expected': 'expected.txt', 'actual': 'actual.txt'}]
            }
            manifest_path = root / 'manifest.json'
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            self.assertEqual([], mod.check_materialized_goldens(manifest_path, root))


if __name__ == '__main__':
    unittest.main()
