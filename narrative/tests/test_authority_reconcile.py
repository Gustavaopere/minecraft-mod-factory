import importlib.util
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tooling' / 'authority_reconcile.py'


def load_module():
    spec = importlib.util.spec_from_file_location('authority_reconcile', MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def snapshot(records, revision='r1'):
    return {
        'schema_version': 1,
        'provenance': {
            'source': 'local-test-authority',
            'revision': revision,
            'captured_at': '2026-09-16T00:00:00Z'
        },
        'records': records,
    }


def write_json(path, payload):
    path.write_text(json.dumps(payload), encoding='utf-8')


class AuthorityReconciliationTests(unittest.TestCase):
    def test_identical_snapshots_have_no_divergence(self):
        mod = load_module()
        left = snapshot([{'id': 'NPC-0001', 'fields': {'state': 'CANON', 'name': 'A'}}])
        right = snapshot([{'id': 'NPC-0001', 'fields': {'state': 'CANON', 'name': 'A'}}], revision='r2')
        self.assertEqual([], mod.compare_snapshots(left, right, compare_fields=('state', 'name')))

    def test_comparison_reports_missing_records_and_field_divergence(self):
        mod = load_module()
        local = snapshot([
            {'id': 'NPC-0001', 'fields': {'state': 'CANON', 'name': 'A'}},
            {'id': 'NPC-0002', 'fields': {'state': 'DRAFT', 'name': 'B'}},
        ])
        external = snapshot([
            {'id': 'NPC-0001', 'fields': {'state': 'DRAFT', 'name': 'A'}},
            {'id': 'NPC-0003', 'fields': {'state': 'CANON', 'name': 'C'}},
        ], revision='r2')
        codes = [item.code for item in mod.compare_snapshots(local, external, compare_fields=('state',))]
        self.assertEqual(
            ['authority-field-divergence', 'missing-external-record', 'missing-local-record'],
            sorted(codes),
        )

    def test_inventory_adapter_round_trips_to_neutral_snapshot(self):
        mod = load_module()
        inventory = {
            'summary': {'total': 1},
            'records': [{
                'id': 'NPC-0001',
                'type': 'NPC',
                'title': 'A',
                'state': 'CANON',
                'path': 'npcs/NPC-0001-a.md',
                'references': ['EVT-0001'],
            }],
        }
        result = mod.snapshot_from_inventory(
            inventory,
            source='story-inventory',
            revision='abc123',
            captured_at='2026-09-16T00:00:00Z',
        )
        self.assertEqual([], mod.validate_snapshot(result))
        self.assertEqual('NPC-0001', result['records'][0]['id'])
        self.assertEqual('CANON', result['records'][0]['fields']['state'])

    def test_validate_snapshot_reports_structural_errors(self):
        mod = load_module()
        self.assertEqual(['invalid-snapshot-root'], [item.code for item in mod.validate_snapshot([])])
        broken = {
            'schema_version': 2,
            'provenance': {'source': '', 'revision': None, 'captured_at': ' '},
            'records': ['not-a-record', {'id': 'bad', 'fields': {}}],
        }
        codes = [item.code for item in mod.validate_snapshot(broken)]
        self.assertIn('unsupported-snapshot-schema', codes)
        self.assertEqual(3, codes.count('invalid-snapshot-provenance'))
        self.assertIn('invalid-snapshot-record', codes)
        self.assertIn('invalid-snapshot-id', codes)
        self.assertIn('invalid-snapshot-records', [item.code for item in mod.validate_snapshot({'schema_version': 1})])
        self.assertIn('missing-snapshot-provenance', [item.code for item in mod.validate_snapshot({'schema_version': 1, 'records': []})])

    def test_validate_snapshot_reports_duplicate_and_invalid_fields(self):
        mod = load_module()
        broken = snapshot([
            {'id': 'NPC-0001', 'fields': {}},
            {'id': 'NPC-0001', 'fields': []},
        ])
        codes = [item.code for item in mod.validate_snapshot(broken)]
        self.assertIn('duplicate-snapshot-id', codes)
        self.assertIn('invalid-snapshot-fields', codes)

    def test_compare_invalid_snapshots_reports_both_sides(self):
        mod = load_module()
        issues = mod.compare_snapshots({'schema_version': 99}, {'records': []})
        codes = [item.code for item in issues]
        self.assertIn('invalid-local-snapshot', codes)
        self.assertIn('invalid-external-snapshot', codes)

    def test_snapshot_adapter_rejects_invalid_inputs(self):
        mod = load_module()
        with self.assertRaises(ValueError):
            mod.snapshot_from_inventory({}, source='s', revision='r', captured_at='t')
        with self.assertRaises(ValueError):
            mod.snapshot_from_inventory({'records': []}, source='', revision='r', captured_at='t')
        with self.assertRaises(ValueError):
            mod.snapshot_from_inventory({'records': [{}]}, source='s', revision='r', captured_at='t')

    def test_workspace_relpath_accepts_nested_posix_path(self):
        mod = load_module()
        self.assertEqual('exports/snapshot.json', mod._normalized_workspace_relpath('exports/snapshot.json'))

    def test_workspace_relpath_rejects_unsafe_shapes(self):
        mod = load_module()
        unsafe = ('', '/absolute.json', '../outside.json', './dot.json', 'a/../b.json', 'a//b.json', 'a\\b.json')
        for value in unsafe:
            with self.subTest(value=value), self.assertRaises(ValueError):
                mod._normalized_workspace_relpath(value)

    def test_required_external_source_fails_closed_when_missing(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            write_json(root / 'local.json', snapshot([]))
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'compare', '--local', 'local.json', '--external', 'missing.json',
                    '--required-external'
                ], workspace_root=root)
        self.assertEqual(2, code)
        self.assertIn('required external authority is unavailable', out.getvalue())

    def test_optional_external_source_warns_and_skips(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            write_json(root / 'local.json', snapshot([]))
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'compare', '--local', 'local.json', '--external', 'missing.json'
                ], workspace_root=root)
        self.assertEqual(0, code)
        self.assertIn('optional external authority is unavailable', out.getvalue())

    def test_default_comparison_output_is_spoiler_safe(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            write_json(root / 'local.json', snapshot([{'id': 'NPC-0001', 'fields': {'state': 'CANON'}}]))
            write_json(root / 'external.json', snapshot([{'id': 'NPC-0001', 'fields': {'state': 'DRAFT'}}], revision='r2'))
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'compare', '--local', 'local.json', '--external', 'external.json', '--field', 'state'
                ], workspace_root=root)
        self.assertEqual(1, code)
        self.assertIn('authority-field-divergence: 1', out.getvalue())
        self.assertNotIn('NPC-0001', out.getvalue())

    def test_identical_comparison_cli_reports_ok(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            write_json(root / 'local.json', snapshot([]))
            write_json(root / 'external.json', snapshot([], revision='r2'))
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'compare', '--local', 'local.json', '--external', 'external.json'
                ], workspace_root=root)
        self.assertEqual(0, code)
        self.assertEqual('OK no authority divergence found\n', out.getvalue())

    def test_reveal_comparison_prints_record_reference(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            write_json(root / 'local.json', snapshot([{'id': 'NPC-0001', 'fields': {'state': 'CANON'}}]))
            write_json(root / 'external.json', snapshot([{'id': 'NPC-0001', 'fields': {'state': 'DRAFT'}}], revision='r2'))
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'compare', '--local', 'local.json', '--external', 'external.json',
                    '--field', 'state', '--reveal'
                ], workspace_root=root)
        self.assertEqual(1, code)
        self.assertIn('NPC-0001:state', out.getvalue())

    def test_export_inventory_emits_valid_snapshot_to_stdout(self):
        mod = load_module()
        inventory = {
            'records': [{
                'id': 'NPC-0001', 'type': 'NPC', 'title': 'A', 'state': 'CANON',
                'path': 'npcs/NPC-0001-a.md', 'references': []
            }]
        }
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            write_json(root / 'inventory.json', inventory)
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'export-inventory', '--inventory', 'inventory.json',
                    '--source', 'story-inventory', '--revision', 'abc123',
                    '--captured-at', '2026-09-16T00:00:00Z'
                ], workspace_root=root)
        exported = json.loads(out.getvalue())
        self.assertEqual(0, code)
        self.assertEqual([], mod.validate_snapshot(exported))
        self.assertEqual('NPC-0001', exported['records'][0]['id'])

    def test_export_invalid_inventory_fails_closed(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            write_json(root / 'inventory.json', {'records': [{}]})
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'export-inventory', '--inventory', 'inventory.json',
                    '--source', 'story-inventory', '--revision', 'abc123',
                    '--captured-at', '2026-09-16T00:00:00Z'
                ], workspace_root=root)
        self.assertEqual(2, code)
        self.assertIn('invalid input or workspace path', out.getvalue())

    def test_export_rejects_legacy_output_argument(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            write_json(root / 'inventory.json', {'records': []})
            stderr = StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
                mod.main([
                    'export-inventory', '--inventory', 'inventory.json', '--output', 'out.json',
                    '--source', 'story-inventory', '--revision', 'abc123',
                    '--captured-at', '2026-09-16T00:00:00Z'
                ], workspace_root=root)
        self.assertEqual(2, caught.exception.code)
        self.assertIn('unrecognized arguments: --output out.json', stderr.getvalue())

    def test_cli_rejects_traversal_input_path(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            write_json(root / 'inventory.json', {'records': []})
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'export-inventory', '--inventory', '../outside.json',
                    '--source', 'story-inventory', '--revision', 'abc123',
                    '--captured-at', '2026-09-16T00:00:00Z'
                ], workspace_root=root)
        self.assertEqual(2, code)
        self.assertIn('invalid input or workspace path', out.getvalue())

    def test_malformed_json_fails_closed(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / 'local.json').write_text('{bad-json', encoding='utf-8')
            write_json(root / 'external.json', snapshot([]))
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'compare', '--local', 'local.json', '--external', 'external.json'
                ], workspace_root=root)
        self.assertEqual(2, code)
        self.assertIn('invalid input or workspace path', out.getvalue())


if __name__ == '__main__':
    unittest.main()
