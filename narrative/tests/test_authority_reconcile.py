import importlib.util
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
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

    def test_required_external_source_fails_closed_when_missing(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            local_path = root / 'local.json'
            local_path.write_text(json.dumps(snapshot([])), encoding='utf-8')
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'compare', '--local', str(local_path), '--external', str(root / 'missing.json'),
                    '--required-external'
                ], workspace_root=root)
        self.assertEqual(2, code)
        self.assertIn('required external authority is unavailable', out.getvalue())

    def test_default_comparison_output_is_spoiler_safe(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            local_path = root / 'local.json'
            external_path = root / 'external.json'
            local_path.write_text(json.dumps(snapshot([{'id': 'NPC-0001', 'fields': {'state': 'CANON'}}])), encoding='utf-8')
            external_path.write_text(json.dumps(snapshot([{'id': 'NPC-0001', 'fields': {'state': 'DRAFT'}}], revision='r2')), encoding='utf-8')
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main([
                    'compare', '--local', str(local_path), '--external', str(external_path), '--field', 'state'
                ], workspace_root=root)
        self.assertEqual(1, code)
        self.assertIn('authority-field-divergence: 1', out.getvalue())
        self.assertNotIn('NPC-0001', out.getvalue())


if __name__ == '__main__':
    unittest.main()
