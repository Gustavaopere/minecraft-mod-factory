from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import defaultdict
from typing import NamedTuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from advanced_contracts import AdvancedContracts, parse_advanced_contracts
from profile import NarrativeProfile, load_profile, resolve_workspace_path


class Issue(NamedTuple):
    code: str
    ref: str
    path: pathlib.Path
    line: int


FATAL_CODES = {
    'missing-knowledge-required-section',
    'empty-knowledge-required-section',
    'missing-knowledge-section-reference',
    'invalid-knowledge-reference-type',
    'missing-knowledge-reference-target',
    'missing-relationship-required-section',
    'empty-relationship-required-section',
    'empty-relationship-dimension',
    'missing-relationship-section-reference',
    'invalid-relationship-reference-type',
    'missing-relationship-reference-target',
    'invalid-relationship-kind',
    'invalid-autonomy-state',
    'relationship-self-reference',
    'chronology-self-reference',
    'chronology-invalid-event-reference-type',
    'chronology-missing-event-reference',
    'chronology-conflicting-edge',
    'chronology-cycle',
    'causality-self-reference',
    'causality-invalid-event-reference-type',
    'causality-missing-event-reference',
    'causality-cycle',
}


def _patterns(profile: NarrativeProfile):
    types = '|'.join(re.escape(item) for item in profile.entity_types)
    return (
        re.compile(r'\b(?:' + types + r')-\d{4}\b'),
        re.compile(r'^#\s+((?:' + types + r')-\d{4})\b'),
    )


def _markdown_files(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(path for path in root.rglob('*.md') if path.is_file())


def _heading_locations(lines: list[str], sections: dict[str, tuple[str, ...]]) -> dict[str, list[int]]:
    aliases = {
        key: {alias.strip().casefold() for alias in values}
        for key, values in sections.items()
    }
    result: dict[str, list[int]] = {key: [] for key in sections}
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith('## '):
            continue
        heading = stripped[3:].strip().casefold()
        for key, accepted in aliases.items():
            if heading in accepted:
                result[key].append(index)
    return result


def _section_lines(lines: list[str], locations: list[int]) -> list[str]:
    content: list[str] = []
    for heading_index in locations:
        for candidate in lines[heading_index + 1:]:
            stripped = candidate.strip()
            if stripped.startswith('## '):
                break
            if stripped:
                content.append(candidate)
    return content


def _section_value(lines: list[str], locations: list[int]) -> str | None:
    content = _section_lines(lines, locations)
    return content[0].strip() if content else None


def _contract_matches(root: pathlib.Path, includes: tuple[str, ...]) -> list[pathlib.Path]:
    trusted_root = root.resolve(strict=True)
    matches: dict[str, pathlib.Path] = {}
    for pattern in includes:
        for candidate in root.glob(pattern):
            if not candidate.is_file() or candidate.suffix.casefold() != '.md':
                continue
            resolved = candidate.resolve(strict=True)
            try:
                resolved.relative_to(trusted_root)
            except ValueError as exc:
                raise ValueError('advanced contract document resolved outside trusted story_root') from exc
            matches[candidate.relative_to(root).as_posix()] = candidate
    return [matches[key] for key in sorted(matches)]


def _structural_issues(path, lines, contract_name, sections, missing_code, empty_code) -> list[Issue]:
    locations = _heading_locations(lines, sections)
    issues: list[Issue] = []
    for key in sections:
        found = locations[key]
        if not found:
            issues.append(Issue(missing_code, f'{contract_name}:{key}', path, 1))
        elif not _section_lines(lines, found):
            issues.append(Issue(empty_code, f'{contract_name}:{key}', path, found[0] + 1))
    return issues


def _reference_issues(
    path,
    lines,
    contract_name,
    sections,
    rules,
    id_re,
    declared_ids,
    missing_count_code,
    invalid_type_code,
    missing_target_code,
) -> list[Issue]:
    locations = _heading_locations(lines, sections)
    issues: list[Issue] = []
    for key, rule in rules.items():
        found = locations.get(key, [])
        if not found:
            continue
        content = _section_lines(lines, found)
        if not content:
            continue
        refs = sorted({ref for line in content for ref in id_re.findall(line)})
        line_no = found[0] + 1
        if len(refs) < rule.min_references:
            issues.append(Issue(missing_count_code, f'{contract_name}:{key}', path, line_no))
        for ref in refs:
            if ref.split('-', 1)[0] not in rule.allowed_types:
                issues.append(Issue(invalid_type_code, f'{contract_name}:{key}:{ref}', path, line_no))
            elif ref not in declared_ids:
                issues.append(Issue(missing_target_code, f'{contract_name}:{key}:{ref}', path, line_no))
    return issues


def _knowledge_issues(root, docs, contracts, id_re, declared_ids) -> list[Issue]:
    issues: list[Issue] = []
    for name, contract in contracts.items():
        sections = {**contract.required_sections, **contract.knowledge_state_sections}
        for path in _contract_matches(root, contract.include):
            lines = docs[path]
            issues.extend(_structural_issues(
                path,
                lines,
                name,
                contract.required_sections,
                'missing-knowledge-required-section',
                'empty-knowledge-required-section',
            ))
            issues.extend(_reference_issues(
                path,
                lines,
                name,
                sections,
                contract.reference_rules,
                id_re,
                declared_ids,
                'missing-knowledge-section-reference',
                'invalid-knowledge-reference-type',
                'missing-knowledge-reference-target',
            ))
    return issues


def _relationship_issues(root, docs, contracts, id_re, declared_ids) -> list[Issue]:
    issues: list[Issue] = []
    for name, contract in contracts.items():
        sections = {**contract.required_sections, **contract.dimension_sections}
        for path in _contract_matches(root, contract.include):
            lines = docs[path]
            locations = _heading_locations(lines, sections)
            issues.extend(_structural_issues(
                path,
                lines,
                name,
                contract.required_sections,
                'missing-relationship-required-section',
                'empty-relationship-required-section',
            ))
            for key in contract.dimension_sections:
                found = locations.get(key, [])
                if found and not _section_lines(lines, found):
                    issues.append(Issue('empty-relationship-dimension', f'{name}:{key}', path, found[0] + 1))
            issues.extend(_reference_issues(
                path,
                lines,
                name,
                sections,
                contract.reference_rules,
                id_re,
                declared_ids,
                'missing-relationship-section-reference',
                'invalid-relationship-reference-type',
                'missing-relationship-reference-target',
            ))

            if contract.kind_section is not None:
                found = locations.get(contract.kind_section, [])
                value = _section_value(lines, found)
                if value is not None and value.casefold() not in {item.casefold() for item in contract.allowed_kinds}:
                    issues.append(Issue('invalid-relationship-kind', f'{name}:{contract.kind_section}', path, found[0] + 1))
            if contract.autonomy_section is not None:
                found = locations.get(contract.autonomy_section, [])
                value = _section_value(lines, found)
                if value is not None and value.casefold() not in {item.casefold() for item in contract.allowed_autonomy_states}:
                    issues.append(Issue('invalid-autonomy-state', f'{name}:{contract.autonomy_section}', path, found[0] + 1))

            if not contract.allow_self_relation and contract.source_actor_section and contract.target_actor_section:
                source_refs = set()
                target_refs = set()
                for line in _section_lines(lines, locations.get(contract.source_actor_section, [])):
                    source_refs.update(id_re.findall(line))
                for line in _section_lines(lines, locations.get(contract.target_actor_section, [])):
                    target_refs.update(id_re.findall(line))
                overlap = sorted(source_refs & target_refs)
                if overlap:
                    line_no = locations.get(contract.target_actor_section, [0])[0] + 1
                    for ref in overlap:
                        issues.append(Issue('relationship-self-reference', f'{name}:{ref}', path, line_no))
    return issues


def _relation_refs(lines, headings, id_re):
    if not headings:
        return []
    locations = _heading_locations(lines, {'relation': headings})['relation']
    result = []
    for heading_index in locations:
        refs = sorted({ref for line in _section_lines(lines, [heading_index]) for ref in id_re.findall(line)})
        result.append((heading_index + 1, refs))
    return result


def _find_cycle(edges: set[tuple[str, str]]) -> tuple[str, ...] | None:
    graph: dict[str, list[str]] = defaultdict(list)
    for source, target in sorted(edges):
        graph[source].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str):
        if node in visiting:
            start = stack.index(node)
            return tuple(stack[start:] + [node])
        if node in visited:
            return None
        visiting.add(node)
        stack.append(node)
        for neighbor in graph.get(node, []):
            cycle = visit(neighbor)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(graph):
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def _chronology_issues(docs, declarations, contract, id_re) -> list[Issue]:
    if contract is None:
        return []
    issues: list[Issue] = []
    event_ids = {record_id for record_id in declarations if record_id.split('-', 1)[0] in contract.event_types}
    chronological_edges: set[tuple[str, str]] = set()
    causal_edges: set[tuple[str, str]] = set()
    edge_locations: dict[tuple[str, str, str], tuple[pathlib.Path, int]] = {}

    def add_relation(current, ref, path, line_no, edge_set, relation_kind, reverse=False):
        prefix = 'chronology' if relation_kind == 'chronology' else 'causality'
        if ref == current:
            issues.append(Issue(f'{prefix}-self-reference', current, path, line_no))
            return
        if ref.split('-', 1)[0] not in contract.event_types:
            issues.append(Issue(f'{prefix}-invalid-event-reference-type', ref, path, line_no))
            return
        if ref not in event_ids:
            issues.append(Issue(f'{prefix}-missing-event-reference', ref, path, line_no))
            return
        edge = (ref, current) if reverse else (current, ref)
        edge_set.add(edge)
        edge_locations[(relation_kind, edge[0], edge[1])] = (path, line_no)

    for record_id in sorted(event_ids):
        path, _ = declarations[record_id][0]
        lines = docs[path]
        for line_no, refs in _relation_refs(lines, contract.before_headings, id_re):
            for ref in refs:
                add_relation(record_id, ref, path, line_no, chronological_edges, 'chronology')
        for line_no, refs in _relation_refs(lines, contract.after_headings, id_re):
            for ref in refs:
                add_relation(record_id, ref, path, line_no, chronological_edges, 'chronology', reverse=True)
        for line_no, refs in _relation_refs(lines, contract.causes_headings, id_re):
            for ref in refs:
                add_relation(record_id, ref, path, line_no, causal_edges, 'causality')
        for line_no, refs in _relation_refs(lines, contract.caused_by_headings, id_re):
            for ref in refs:
                add_relation(record_id, ref, path, line_no, causal_edges, 'causality', reverse=True)

    seen_conflicts: set[frozenset[str]] = set()
    for source, target in sorted(chronological_edges):
        if (target, source) not in chronological_edges:
            continue
        pair = frozenset((source, target))
        if pair in seen_conflicts:
            continue
        seen_conflicts.add(pair)
        path, line_no = edge_locations.get(('chronology', source, target), declarations[source][0])
        issues.append(Issue('chronology-conflicting-edge', f'{source}<->{target}', path, line_no))

    cycle = _find_cycle(chronological_edges)
    if cycle:
        anchor = cycle[0]
        path, line_no = declarations[anchor][0]
        issues.append(Issue('chronology-cycle', '->'.join(cycle), path, line_no))
    if contract.causality_acyclic:
        causal_cycle = _find_cycle(causal_edges)
        if causal_cycle:
            anchor = causal_cycle[0]
            path, line_no = declarations[anchor][0]
            issues.append(Issue('causality-cycle', '->'.join(causal_cycle), path, line_no))
    return issues


def validate(root: pathlib.Path, profile: NarrativeProfile, contracts: AdvancedContracts) -> list[Issue]:
    root = pathlib.Path(root)
    id_re, decl_re = _patterns(profile)
    docs: dict[pathlib.Path, list[str]] = {}
    declarations: dict[str, list[tuple[pathlib.Path, int]]] = defaultdict(list)
    for path in _markdown_files(root):
        lines = path.read_text(encoding='utf-8').splitlines()
        docs[path] = lines
        for line_no, line in enumerate(lines, start=1):
            match = decl_re.match(line)
            if match:
                declarations[match.group(1)].append((path, line_no))
    declared_ids = set(declarations)
    issues = []
    issues.extend(_knowledge_issues(root, docs, contracts.knowledge_evidence_contracts, id_re, declared_ids))
    issues.extend(_relationship_issues(root, docs, contracts.relationship_memory_contracts, id_re, declared_ids))
    issues.extend(_chronology_issues(docs, declarations, contracts.chronology_contract, id_re))
    return sorted(issues, key=lambda issue: (str(issue.path), issue.line, issue.code, issue.ref))


def exit_code(issues: list[Issue]) -> int:
    return 1 if any(issue.code in FATAL_CODES for issue in issues) else 0


def load_advanced_profile(path, workspace_root):
    profile_path = resolve_workspace_path(path, workspace_root)
    profile = load_profile(profile_path, workspace_root)
    data = json.loads(profile_path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('profile root must be an object')
    return profile, parse_advanced_contracts(data, profile.entity_types)


def main(argv=None, workspace_root=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description='Validate advanced opt-in narrative contracts.')
    parser.add_argument('--profile', required=True, help='path to narrative project profile JSON')
    parser.add_argument('--root', help='story root override; defaults to profile story_root')
    parser.add_argument('--reveal', action='store_true', help='show IDs/paths/lines for editorial debugging')
    args = parser.parse_args(argv)
    workspace = pathlib.Path(workspace_root or pathlib.Path.cwd()).resolve(strict=True)
    try:
        profile, contracts = load_advanced_profile(args.profile, workspace)
        root = resolve_workspace_path(args.root or profile.story_root, workspace)
        issues = validate(root, profile, contracts)
    except (OSError, ValueError, json.JSONDecodeError):
        print('ERROR advanced-contract: invalid profile, contract, or workspace path')
        return 2

    if issues:
        if args.reveal:
            for issue in issues:
                try:
                    display = issue.path.relative_to(root)
                except ValueError:
                    display = issue.path
                print(f'ERROR {issue.code} {issue.ref} {display}:{issue.line}')
        else:
            counts: dict[str, int] = {}
            for issue in issues:
                counts[issue.code] = counts.get(issue.code, 0) + 1
            for code, count in sorted(counts.items()):
                print(f'ERROR {code}: {count}')
            print('Details hidden by spoiler-safe mode. Use --reveal for editorial debugging.')
    else:
        print('OK no advanced narrative contract issues found')
    return exit_code(issues)


if __name__ == '__main__':
    raise SystemExit(main())
