import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tooling' / 'validate_advanced.py'


def load_module():
    spec = importlib.util.spec_from_file_location('validate_advanced', MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class AdvancedNarrativeContractTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.td.name)
        self.story = self.root / 'story'
        self.story.mkdir()
        self.profile = self.root / 'profile.json'
        self.profile.write_text(json.dumps({
            'story_root': 'story',
            'dialogue_root': 'story/dialogues',
            'entity_types': ['NPC', 'EVT', 'EVD', 'DLG'],
            'editorial_state_prefixes': ['CANON', 'DRAFT'],
            'editorial_state_headings': ['Editorial state'],
            'dialogue_required_sections': {'state': ['editorial state']},
            'knowledge_evidence_contracts': {
                'knowledge': {
                    'include': ['knowledge/**/*.md'],
                    'required_sections': {
                        'origin': ['Origin'],
                        'holder': ['Holder'],
                        'evidence': ['Evidence'],
                        'reliability': ['Reliability'],
                        'limits': ['Limits']
                    },
                    'knowledge_state_sections': {
                        'observed': ['Observed'],
                        'heard': ['Heard'],
                        'confirmed': ['Confirmed']
                    },
                    'reference_rules': {
                        'holder': {'allowed_types': ['NPC'], 'min_references': 1},
                        'evidence': {'allowed_types': ['EVD'], 'min_references': 1}
                    }
                }
            },
            'relationship_memory_contracts': {
                'relationship': {
                    'include': ['relationships/**/*.md'],
                    'required_sections': {
                        'source': ['Source actor'],
                        'target': ['Target actor'],
                        'memory': ['Memory event'],
                        'kind': ['Kind'],
                        'autonomy': ['Autonomy']
                    },
                    'dimension_sections': {'trust': ['Trust']},
                    'reference_rules': {
                        'source': {'allowed_types': ['NPC'], 'min_references': 1},
                        'target': {'allowed_types': ['NPC'], 'min_references': 1},
                        'memory': {'allowed_types': ['EVT'], 'min_references': 1}
                    },
                    'source_actor_section': 'source',
                    'target_actor_section': 'target',
                    'memory_event_section': 'memory',
                    'kind_section': 'kind',
                    'allowed_kinds': ['grievance', 'favor', 'debt'],
                    'autonomy_section': 'autonomy',
                    'allowed_autonomy_states': ['available', 'independent', 'committed'],
                    'allow_self_relation': False
                }
            },
            'chronology_contract': {
                'event_types': ['EVT'],
                'before_headings': ['Before'],
                'after_headings': ['After'],
                'causes_headings': ['Causes'],
                'caused_by_headings': ['Caused by'],
                'causality_acyclic': True
            }
        }), encoding='utf-8')
        self.addCleanup(self.td.cleanup)

    def write(self, rel, text):
        path = self.story / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def seed_entities(self):
        self.write('NPC-0001-a.md', '# NPC-0001 — A\n')
        self.write('NPC-0002-b.md', '# NPC-0002 — B\n')
        self.write('EVD-0001-proof.md', '# EVD-0001 — Proof\n')
        self.write('EVT-0001-first.md', '# EVT-0001 — First\n\n## Before\nEVT-0002\n\n## Causes\nEVT-0002\n')
        self.write('EVT-0002-second.md', '# EVT-0002 — Second\n\n## After\nEVT-0001\n\n## Caused by\nEVT-0001\n')

    def test_valid_opt_in_contracts_accept_structured_documents(self):
        mod = load_module()
        self.seed_entities()
        self.write('knowledge/report.md', '# Knowledge report\n\n## Origin\nField note\n\n## Holder\nNPC-0001\n\n## Evidence\nEVD-0001\n\n## Reliability\ncorroborated\n\n## Limits\ndoes not prove motive\n\n## Observed\nNPC-0001 observed the event\n')
        self.write('relationships/a-b.md', '# Relationship memory\n\n## Source actor\nNPC-0001\n\n## Target actor\nNPC-0002\n\n## Memory event\nEVT-0001\n\n## Kind\ngrievance\n\n## Autonomy\nindependent\n\n## Trust\ndamaged\n')
        profile, contracts = mod.load_advanced_profile(self.profile, self.root)
        issues = mod.validate(self.story, profile, contracts)
        self.assertEqual([], issues)

    def test_contracts_report_missing_targets_self_relation_and_cycles(self):
        mod = load_module()
        self.seed_entities()
        self.write('knowledge/report.md', '# Knowledge report\n\n## Origin\nField note\n\n## Holder\nNPC-9999\n\n## Evidence\nEVD-0001\n\n## Reliability\nuncertain\n\n## Limits\npartial\n')
        self.write('relationships/self.md', '# Relationship memory\n\n## Source actor\nNPC-0001\n\n## Target actor\nNPC-0001\n\n## Memory event\nEVT-0001\n\n## Kind\nfriendship-score\n\n## Autonomy\npuppet\n')
        # Add an explicit reverse edge, creating both an inconsistency and a cycle.
        second = self.story / 'EVT-0002-second.md'
        second.write_text('# EVT-0002 — Second\n\n## Before\nEVT-0001\n\n## Causes\nEVT-0001\n', encoding='utf-8')
        profile, contracts = mod.load_advanced_profile(self.profile, self.root)
        codes = {issue.code for issue in mod.validate(self.story, profile, contracts)}
        self.assertIn('missing-knowledge-reference-target', codes)
        self.assertIn('relationship-self-reference', codes)
        self.assertIn('invalid-relationship-kind', codes)
        self.assertIn('invalid-autonomy-state', codes)
        self.assertIn('chronology-conflicting-edge', codes)
        self.assertIn('chronology-cycle', codes)
        self.assertIn('causality-cycle', codes)

    def test_profile_rejects_actor_role_without_reference_requirement(self):
        mod = load_module()
        data = json.loads(self.profile.read_text(encoding='utf-8'))
        data['relationship_memory_contracts']['relationship']['reference_rules']['source']['min_references'] = 0
        self.profile.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaises(ValueError):
            mod.load_advanced_profile(self.profile, self.root)

    def test_cli_is_spoiler_safe_by_default(self):
        mod = load_module()
        self.seed_entities()
        self.write('knowledge/report.md', '# Knowledge report\n\n## Origin\nField note\n\n## Holder\nNPC-9999\n\n## Evidence\nEVD-0001\n\n## Reliability\nuncertain\n\n## Limits\npartial\n')
        from contextlib import redirect_stdout
        from io import StringIO
        out = StringIO()
        with redirect_stdout(out):
            code = mod.main(['--profile', str(self.profile), '--root', str(self.story)], workspace_root=self.root)
        self.assertEqual(1, code)
        self.assertIn('missing-knowledge-reference-target', out.getvalue())
        self.assertNotIn('NPC-9999', out.getvalue())


if __name__ == '__main__':
    unittest.main()
