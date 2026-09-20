import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tooling' / 'visual_handoff.py'


def load_module():
    spec = importlib.util.spec_from_file_location('visual_handoff', MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def png_header(width, height):
    return (
        b'\x89PNG\r\n\x1a\n'
        + (13).to_bytes(4, 'big')
        + b'IHDR'
        + width.to_bytes(4, 'big')
        + height.to_bytes(4, 'big')
    )


def valid_manifest():
    return {
        'schema_version': 1,
        'asset_roots': ['art'],
        'records': [{
            'entity_id': 'NPC-0001',
            'assets': [{
                'asset_id': 'portrait.main',
                'kind': 'portrait',
                'path': 'art/portraits/npc-0001.png',
                'approved': True,
                'provenance': {'source': 'editorial', 'revision': 'r1'}
            }]
        }]
    }


class VisualHandoffTests(unittest.TestCase):
    def test_valid_manifest_preserves_entity_asset_and_provenance(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            asset = root / 'art' / 'portraits' / 'npc-0001.png'
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b'not-a-real-png-but-present')
            self.assertEqual([], mod.validate_manifest(valid_manifest(), root, check_files=True))

    def test_manifest_verifies_declared_sha256_and_png_dimensions(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            asset = root / 'art' / 'portraits' / 'npc-0001.png'
            asset.parent.mkdir(parents=True)
            payload = png_header(2048, 2048)
            asset.write_bytes(payload)
            manifest = valid_manifest()
            entry = manifest['records'][0]['assets'][0]
            entry['sha256'] = hashlib.sha256(payload).hexdigest()
            entry['pixel_dimensions'] = {'width': 2048, 'height': 2048}
            self.assertEqual([], mod.validate_manifest(manifest, root, check_files=True))

    def test_handoff_checks_declared_dimensions_without_imposing_resolution_policy(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            asset = root / 'art' / 'portraits' / 'npc-0001.png'
            asset.parent.mkdir(parents=True)
            payload = png_header(137, 271)
            asset.write_bytes(payload)
            manifest = valid_manifest()
            entry = manifest['records'][0]['assets'][0]
            entry['pixel_dimensions'] = {'width': 137, 'height': 271}
            self.assertEqual([], mod.validate_manifest(manifest, root, check_files=True))

    def test_manifest_rejects_invalid_integrity_metadata(self):
        mod = load_module()
        manifest = valid_manifest()
        entry = manifest['records'][0]['assets'][0]
        entry['sha256'] = 'NOT-A-SHA256'
        entry['pixel_dimensions'] = {'width': 0, 'height': True}
        codes = {issue.code for issue in mod.validate_manifest(manifest, pathlib.Path('.'))}
        self.assertIn('invalid-asset-sha256', codes)
        self.assertIn('invalid-pixel-dimensions', codes)

    def test_manifest_reports_hash_and_pixel_dimension_mismatch(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            asset = root / 'art' / 'portraits' / 'npc-0001.png'
            asset.parent.mkdir(parents=True)
            asset.write_bytes(png_header(2048, 2048))
            manifest = valid_manifest()
            entry = manifest['records'][0]['assets'][0]
            entry['sha256'] = '0' * 64
            entry['pixel_dimensions'] = {'width': 1024, 'height': 1024}
            codes = {issue.code for issue in mod.validate_manifest(manifest, root, check_files=True)}
        self.assertIn('asset-sha256-mismatch', codes)
        self.assertIn('asset-pixel-dimensions-mismatch', codes)

    def test_dimension_check_fails_closed_when_declared_for_non_png(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            asset = root / 'art' / 'portraits' / 'npc-0001.dat'
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b'not-a-png')
            manifest = valid_manifest()
            entry = manifest['records'][0]['assets'][0]
            entry['path'] = 'art/portraits/npc-0001.dat'
            entry['pixel_dimensions'] = {'width': 2048, 'height': 2048}
            codes = {issue.code for issue in mod.validate_manifest(manifest, root, check_files=True)}
        self.assertIn('asset-dimensions-unverifiable', codes)

    def test_manifest_rejects_path_traversal_duplicate_asset_ids_and_missing_files(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            manifest = {
                'schema_version': 1,
                'asset_roots': ['art'],
                'records': [{
                    'entity_id': 'NPC-0001',
                    'assets': [
                        {
                            'asset_id': 'skin.main', 'kind': 'skin', 'path': '../outside.png',
                            'approved': True, 'provenance': {'source': 'editorial', 'revision': 'r1'}
                        },
                        {
                            'asset_id': 'skin.main', 'kind': 'skin', 'path': 'art/skins/missing.png',
                            'approved': True, 'provenance': {'source': 'editorial', 'revision': 'r1'}
                        }
                    ]
                }]
            }
            codes = {issue.code for issue in mod.validate_manifest(manifest, root, check_files=True)}
            self.assertIn('asset-path-outside-roots', codes)
            self.assertIn('duplicate-asset-id', codes)
            self.assertIn('missing-asset-file', codes)

    def test_manifest_rejects_unknown_kind_and_missing_provenance(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            manifest = {
                'schema_version': 1,
                'asset_roots': ['art'],
                'records': [{
                    'entity_id': 'NPC-0001',
                    'assets': [{
                        'asset_id': 'auto.face', 'kind': 'auto-generated-face',
                        'path': 'art/generated.png', 'approved': False
                    }]
                }]
            }
            codes = {issue.code for issue in mod.validate_manifest(manifest, root, check_files=False)}
            self.assertIn('invalid-asset-kind', codes)
            self.assertIn('missing-asset-provenance', codes)

    def test_manifest_only_accepts_stable_entity_ids(self):
        mod = load_module()
        manifest = {'schema_version': 1, 'asset_roots': ['art'], 'records': [{'entity_id': 'Alice', 'assets': []}]}
        codes = {issue.code for issue in mod.validate_manifest(manifest, pathlib.Path('.'), check_files=False)}
        self.assertIn('invalid-entity-id', codes)

    def test_manifest_rejects_invalid_root_schema_roots_and_records(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.assertEqual(['invalid-manifest-root'], [issue.code for issue in mod.validate_manifest([], root)])
            manifest = {
                'schema_version': 2,
                'asset_roots': ['../outside', '', 7],
                'records': 'not-a-list',
            }
            codes = [issue.code for issue in mod.validate_manifest(manifest, root)]
        self.assertIn('unsupported-manifest-schema', codes)
        self.assertEqual(3, codes.count('invalid-asset-root'))
        self.assertIn('invalid-asset-records', codes)

    def test_manifest_rejects_invalid_record_asset_entry_id_and_approval(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            manifest = {
                'schema_version': 1,
                'asset_roots': ['art'],
                'records': [
                    'bad-record',
                    {'entity_id': 'NPC-0001', 'assets': 'bad-assets'},
                    {
                        'entity_id': 'NPC-0002',
                        'assets': [
                            'bad-asset',
                            {
                                'asset_id': 'BAD ID',
                                'kind': 'skin',
                                'path': 'art/skin.png',
                                'approved': 'yes',
                                'provenance': {'source': 'editorial', 'revision': 'r1'},
                            },
                        ],
                    },
                    {'entity_id': 'NPC-0002', 'assets': []},
                ],
            }
            codes = [issue.code for issue in mod.validate_manifest(manifest, root)]
        self.assertIn('invalid-asset-record', codes)
        self.assertIn('invalid-assets-list', codes)
        self.assertIn('invalid-asset-entry', codes)
        self.assertIn('invalid-asset-id', codes)
        self.assertIn('invalid-asset-approval', codes)
        self.assertIn('duplicate-entity-asset-record', codes)

    def test_cli_accepts_valid_manifest(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            asset = root / 'art' / 'portraits' / 'npc-0001.png'
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b'present')
            (root / 'manifest.json').write_text(json.dumps(valid_manifest()), encoding='utf-8')
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main(['--manifest', 'manifest.json', '--check-files'], workspace_root=root)
        self.assertEqual(0, code)
        self.assertEqual('OK visual asset handoff is structurally valid\n', out.getvalue())

    def test_cli_is_spoiler_safe_and_reveal_is_explicit(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            manifest = valid_manifest()
            manifest['records'][0]['assets'][0]['kind'] = 'bad-kind'
            (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            safe = StringIO()
            with redirect_stdout(safe):
                safe_code = mod.main(['--manifest', 'manifest.json'], workspace_root=root)
            reveal = StringIO()
            with redirect_stdout(reveal):
                reveal_code = mod.main(['--manifest', 'manifest.json', '--reveal'], workspace_root=root)
        self.assertEqual(1, safe_code)
        self.assertEqual(1, reveal_code)
        self.assertIn('invalid-asset-kind: 1', safe.getvalue())
        self.assertNotIn('NPC-0001', safe.getvalue())
        self.assertIn('NPC-0001:portrait.main', reveal.getvalue())

    def test_cli_invalid_manifest_path_fails_closed(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            out = StringIO()
            with redirect_stdout(out):
                code = mod.main(['--manifest', '../outside.json'], workspace_root=root)
        self.assertEqual(2, code)
        self.assertEqual('ERROR visual-handoff: invalid manifest or workspace path\n', out.getvalue())


if __name__ == '__main__':
    unittest.main()
