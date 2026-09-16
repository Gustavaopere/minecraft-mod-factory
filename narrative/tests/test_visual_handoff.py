import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tooling' / 'visual_handoff.py'


def load_module():
    spec = importlib.util.spec_from_file_location('visual_handoff', MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class VisualHandoffTests(unittest.TestCase):
    def test_valid_manifest_preserves_entity_asset_and_provenance(self):
        mod = load_module()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            asset = root / 'art' / 'portraits' / 'npc-0001.png'
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b'not-a-real-png-but-present')
            manifest = {
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
            self.assertEqual([], mod.validate_manifest(manifest, root, check_files=True))

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


if __name__ == '__main__':
    unittest.main()
