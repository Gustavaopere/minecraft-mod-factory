from __future__ import annotations

import json
import pathlib
import re
from typing import NamedTuple


ID_RE = re.compile(r'^[A-Z][A-Z0-9_]*-\d{4}$')


class Issue(NamedTuple):
    code: str
    ref: str


def _non_empty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_snapshot(snapshot) -> list[Issue]:
    issues: list[Issue] = []
    if not isinstance(snapshot, dict):
        return [Issue('invalid-snapshot-root', '')]
    if snapshot.get('schema_version') != 1:
        issues.append(Issue('unsupported-snapshot-schema', str(snapshot.get('schema_version', ''))))
    provenance = snapshot.get('provenance')
    if not isinstance(provenance, dict):
        issues.append(Issue('missing-snapshot-provenance', ''))
    else:
        for key in ('source', 'revision', 'captured_at'):
            if not _non_empty_string(provenance.get(key)):
                issues.append(Issue('invalid-snapshot-provenance', key))
    records = snapshot.get('records')
    if not isinstance(records, list):
        issues.append(Issue('invalid-snapshot-records', ''))
        return issues
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            issues.append(Issue('invalid-snapshot-record', str(index)))
            continue
        record_id = record.get('id')
        if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
            issues.append(Issue('invalid-snapshot-id', str(record_id or index)))
            continue
        if record_id in seen:
            issues.append(Issue('duplicate-snapshot-id', record_id))
        seen.add(record_id)
        if not isinstance(record.get('fields'), dict):
            issues.append(Issue('invalid-snapshot-fields', record_id))
    return sorted(issues)


def _records_by_id(snapshot):
    return {
        record['id']: record['fields']
        for record in snapshot.get('records', [])
        if isinstance(record, dict) and isinstance(record.get('fields'), dict)
    }


def compare_snapshots(local, external, compare_fields=()) -> list[Issue]:
    local_issues = validate_snapshot(local)
    external_issues = validate_snapshot(external)
    if local_issues or external_issues:
        return [Issue('invalid-local-snapshot', issue.ref) for issue in local_issues] + [
            Issue('invalid-external-snapshot', issue.ref) for issue in external_issues
        ]
    local_records = _records_by_id(local)
    external_records = _records_by_id(external)
    issues: list[Issue] = []
    for record_id in sorted(set(local_records) - set(external_records)):
        issues.append(Issue('missing-external-record', record_id))
    for record_id in sorted(set(external_records) - set(local_records)):
        issues.append(Issue('missing-local-record', record_id))
    fields = tuple(dict.fromkeys(compare_fields))
    for record_id in sorted(set(local_records) & set(external_records)):
        for field in fields:
            local_value = local_records[record_id].get(field)
            external_value = external_records[record_id].get(field)
            if local_value != external_value:
                issues.append(Issue('authority-field-divergence', f'{record_id}:{field}'))
    return sorted(issues)


def snapshot_from_inventory(inventory, *, source: str, revision: str, captured_at: str):
    if not isinstance(inventory, dict) or not isinstance(inventory.get('records'), list):
        raise ValueError('inventory must contain a records list')
    if not all(_non_empty_string(value) for value in (source, revision, captured_at)):
        raise ValueError('source, revision, and captured_at must be non-empty strings')
    records = []
    for record in inventory['records']:
        if not isinstance(record, dict) or not isinstance(record.get('id'), str):
            raise ValueError('inventory records must contain stable ids')
        fields = {
            key: record[key]
            for key in ('type', 'title', 'state', 'path', 'references')
            if key in record
        }
        records.append({'id': record['id'], 'fields': fields})
    return {
        'schema_version': 1,
        'provenance': {'source': source, 'revision': revision, 'captured_at': captured_at},
        'records': sorted(records, key=lambda item: item['id']),
    }


def _normalized_workspace_relpath(path: str | pathlib.Path) -> str:
    raw = path.as_posix() if isinstance(path, pathlib.Path) else path
    if not isinstance(raw, str) or not raw or '\\' in raw or raw.startswith('/'):
        raise ValueError('path must be a normalized workspace-relative path')
    parts = raw.split('/')
    if any(part in {'', '.', '..'} for part in parts):
        raise ValueError('path must be a normalized workspace-relative path')
    normalized = pathlib.PurePosixPath(raw).as_posix()
    if normalized != raw:
        raise ValueError('path must be a normalized workspace-relative path')
    return normalized


def _workspace_path(path: str | pathlib.Path, workspace: pathlib.Path, *, must_exist: bool) -> pathlib.Path:
    normalized = _normalized_workspace_relpath(path)
    workspace = workspace.resolve(strict=True)
    candidate = workspace.joinpath(*pathlib.PurePosixPath(normalized).parts)
    if candidate.is_symlink():
        raise ValueError('workspace path may not be a symlink')
    resolved = candidate.resolve(strict=must_exist)
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError('path is outside the trusted workspace') from exc
    return resolved


def _load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding='utf-8'))


def _print_issues(issues: list[Issue], reveal: bool):
    if reveal:
        for issue in issues:
            print(f'ERROR {issue.code} {issue.ref}'.rstrip())
        return
    counts: dict[str, int] = {}
    for issue in issues:
        counts[issue.code] = counts.get(issue.code, 0) + 1
    for code, count in sorted(counts.items()):
        print(f'ERROR {code}: {count}')
    if issues:
        print('Details hidden by spoiler-safe mode. Use --reveal for editorial debugging.')


def main(argv=None, workspace_root=None):
    import argparse

    parser = argparse.ArgumentParser(
        description='Reconcile neutral narrative authority snapshots without mutating canon.'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    compare = subparsers.add_parser('compare')
    compare.add_argument('--local', required=True)
    compare.add_argument('--external', required=True)
    compare.add_argument('--field', action='append', default=[])
    compare.add_argument('--required-external', action='store_true')
    compare.add_argument('--reveal', action='store_true')

    export = subparsers.add_parser('export-inventory')
    export.add_argument('--inventory', required=True)
    export.add_argument('--source', required=True)
    export.add_argument('--revision', required=True)
    export.add_argument('--captured-at', required=True)

    args = parser.parse_args(argv)
    workspace = pathlib.Path(workspace_root or pathlib.Path.cwd()).resolve(strict=True)
    try:
        if args.command == 'compare':
            local_path = _workspace_path(args.local, workspace, must_exist=True)
            try:
                external_path = _workspace_path(args.external, workspace, must_exist=True)
            except FileNotFoundError:
                if args.required_external:
                    print('ERROR required external authority is unavailable')
                    return 2
                print('WARN optional external authority is unavailable; comparison skipped')
                return 0
            local = _load_json(local_path)
            external = _load_json(external_path)
            issues = compare_snapshots(local, external, compare_fields=tuple(args.field))
            _print_issues(issues, args.reveal)
            if not issues:
                print('OK no authority divergence found')
            return 1 if issues else 0

        inventory_path = _workspace_path(args.inventory, workspace, must_exist=True)
        payload = snapshot_from_inventory(
            _load_json(inventory_path),
            source=args.source,
            revision=args.revision,
            captured_at=args.captured_at,
        )
        validation = validate_snapshot(payload)
        if validation:
            _print_issues(validation, reveal=False)
            return 2
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError):
        print('ERROR authority-reconcile: invalid input or workspace path')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
