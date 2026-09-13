from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter
from typing import NamedTuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from profile import NarrativeProfile, load_profile


class Record(NamedTuple):
    id: str
    type: str
    title: str
    state: str
    path: pathlib.Path
    references: tuple[str, ...]


def _patterns(profile: NarrativeProfile):
    types = '|'.join(re.escape(item) for item in profile.entity_types)
    return (
        re.compile(r'\b(?:' + types + r')-\d{4}\b'),
        re.compile(r'^#\s+((?:' + types + r')-\d{4})\b(?:\s*[—-]\s*(.*?))?\s*$', re.MULTILINE),
    )


def _extract_state(text: str, profile: NarrativeProfile) -> str:
    lines = text.splitlines()
    normalized_headings = {'## ' + heading.strip().casefold() for heading in profile.editorial_state_headings}
    for index, line in enumerate(lines):
        if line.strip().casefold() not in normalized_headings:
            continue
        for candidate in lines[index + 1:]:
            stripped = candidate.strip()
            if stripped.startswith('#'):
                return 'NOT DECLARED'
            if stripped:
                return stripped
    return 'NOT DECLARED'


def inventory(root: pathlib.Path, profile: NarrativeProfile) -> list[Record]:
    id_re, decl_re = _patterns(profile)
    records = []
    for path in sorted(p for p in pathlib.Path(root).rglob('*.md') if p.is_file()):
        text = path.read_text(encoding='utf-8')
        decl = decl_re.search(text)
        if not decl:
            continue
        record_id = decl.group(1)
        refs = tuple(sorted(set(id_re.findall(text)) - {record_id}))
        records.append(Record(record_id, record_id.split('-', 1)[0], (decl.group(2) or '').strip(), _extract_state(text, profile), path, refs))
    return sorted(records, key=lambda record: record.id)


def _summary(records):
    return {
        'total': len(records),
        'by_type': dict(sorted(Counter(r.type for r in records).items())),
        'by_state': dict(sorted(Counter(r.state for r in records).items())),
    }


def _display(path, root):
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def render_json(records, root):
    payload = {
        'summary': _summary(records),
        'records': [
            {'id': r.id, 'type': r.type, 'title': r.title, 'state': r.state, 'path': _display(r.path, pathlib.Path(root)), 'references': list(r.references)}
            for r in records
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + '\n'


def render_markdown(records, root):
    summary = _summary(records)
    lines = ['# Story Inventory', '', f"Total: {summary['total']}", '', '## By type', '']
    for entity_type, count in summary['by_type'].items():
        lines.append(f'- {entity_type}: {count}')
    lines += ['', '## Records', '', '| ID | Title | Editorial state | File | References |', '| --- | --- | --- | --- | --- |']
    for r in records:
        lines.append(f"| {r.id} | {r.title or '—'} | {r.state} | {_display(r.path, pathlib.Path(root))} | {', '.join(r.references) or '—'} |")
    return '\n'.join(lines) + '\n'


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='Inventory profile-driven narrative records.')
    parser.add_argument('--profile', required=True)
    parser.add_argument('--root', help='story root override; defaults to profile story_root')
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    args = parser.parse_args(argv)
    profile = load_profile(args.profile)
    root = pathlib.Path(args.root or profile.story_root)
    records = inventory(root, profile)
    print(render_json(records, root) if args.format == 'json' else render_markdown(records, root), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
