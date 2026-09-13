from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from inventory_core import Record, display, inventory, summary
from profile import load_profile


def render_json(records, root):
    payload = {'summary': summary(records), 'records': [
        {'id': r.id, 'type': r.type, 'title': r.title, 'state': r.state, 'path': display(r.path, pathlib.Path(root)), 'references': list(r.references)}
        for r in records
    ]}
    return json.dumps(payload, ensure_ascii=False, indent=2) + '\n'


def render_markdown(records, root):
    data = summary(records)
    lines = ['# Story Inventory', '', f"Total: {data['total']}", '', '## By type', '']
    lines += [f'- {kind}: {count}' for kind, count in data['by_type'].items()]
    lines += ['', '## Records', '', '| ID | Title | Editorial state | File | References |', '| --- | --- | --- | --- | --- |']
    for r in records:
        lines.append(f"| {r.id} | {r.title or '—'} | {r.state} | {display(r.path, pathlib.Path(root))} | {', '.join(r.references) or '—'} |")
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
