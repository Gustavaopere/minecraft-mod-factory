from __future__ import annotations

import json
import pathlib
from pathlib import PurePosixPath
from typing import NamedTuple


class Issue(NamedTuple):
    code: str
    ref: str


def compatibility_issues(previous, current) -> list[Issue]:
    if not isinstance(previous, dict) or not isinstance(current, dict):
        return [Issue('invalid-profile-contract', '')]
    old_revision = previous.get('profile_contract_revision')
    new_revision = current.get('profile_contract_revision')
    if not isinstance(old_revision, int) or not isinstance(new_revision, int) or old_revision < 1 or new_revision < 1:
        return [Issue('invalid-profile-contract-revision', '')]
    old_required = set(previous.get('required_keys', []))
    new_required = set(current.get('required_keys', []))
    issues: list[Issue] = []
    if old_revision == new_revision:
        for key in sorted(new_required - old_required):
            issues.append(Issue('required-key-added-without-revision', key))
        for key in sorted(old_required - new_required):
            issues.append(Issue('required-key-removed-without-revision', key))
        return issues
    migration = current.get('migration')
    if not (
        isinstance(migration, dict)
        and migration.get('from_revision') == old_revision
        and isinstance(migration.get('document'), str)
        and migration['document'].strip()
    ):
        issues.append(Issue('profile-revision-changed-without-migration', f'{old_revision}->{new_revision}'))
    return issues


def _relative_path(value, field: str) -> pathlib.PurePosixPath:
    if not isinstance(value, str) or not value.strip() or '\\' in value:
        raise ValueError(f'{field} must be a relative POSIX path')
    pure = PurePosixPath(value)
    if pure.is_absolute() or '..' in pure.parts:
        raise ValueError(f'{field} must not be absolute or contain ..')
    return pure


def _resolve_inside(workspace: pathlib.Path, pure: PurePosixPath, *, strict: bool) -> pathlib.Path:
    candidate = (workspace / pathlib.Path(*pure.parts)).resolve(strict=strict)
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise ValueError('golden path resolved outside trusted workspace') from exc
    return candidate


def check_materialized_goldens(manifest_path: pathlib.Path, workspace_root: pathlib.Path) -> list[Issue]:
    workspace = pathlib.Path(workspace_root).resolve(strict=True)
    supplied = pathlib.Path(manifest_path)
    resolved_manifest = supplied.resolve(strict=True) if supplied.is_absolute() else (workspace / supplied).resolve(strict=True)
    try:
        resolved_manifest.relative_to(workspace)
    except ValueError as exc:
        raise ValueError('golden manifest resolved outside trusted workspace') from exc
    manifest = json.loads(resolved_manifest.read_text(encoding='utf-8'))
    if not isinstance(manifest, dict):
        return [Issue('invalid-golden-manifest', '')]
    issues: list[Issue] = []
    if manifest.get('schema_version') != 1:
        issues.append(Issue('unsupported-golden-schema', str(manifest.get('schema_version', ''))))
    revision = manifest.get('profile_contract_revision')
    if not isinstance(revision, int) or revision < 1:
        issues.append(Issue('invalid-profile-contract-revision', str(revision or '')))
    entries = manifest.get('goldens')
    if not isinstance(entries, list):
        issues.append(Issue('invalid-golden-entries', ''))
        return sorted(issues)
    seen_names: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            issues.append(Issue('invalid-golden-entry', str(index)))
            continue
        name = entry.get('name')
        if not isinstance(name, str) or not name.strip():
            issues.append(Issue('invalid-golden-name', str(index)))
            name = f'#{index}'
        elif name in seen_names:
            issues.append(Issue('duplicate-golden-name', name))
        seen_names.add(name)
        try:
            expected = _resolve_inside(workspace, _relative_path(entry.get('expected'), f'{name}.expected'), strict=True)
            actual = _resolve_inside(workspace, _relative_path(entry.get('actual'), f'{name}.actual'), strict=True)
        except (OSError, ValueError):
            issues.append(Issue('missing-golden-output', name))
            continue
        if expected.read_bytes() != actual.read_bytes():
            issues.append(Issue('golden-output-mismatch', name))
    return sorted(issues)


def main(argv=None, workspace_root=None):
    import argparse
    parser = argparse.ArgumentParser(description='Check materialized narrative golden outputs and compatibility metadata.')
    parser.add_argument('--manifest', required=True)
    args = parser.parse_args(argv)
    workspace = pathlib.Path(workspace_root or pathlib.Path.cwd()).resolve(strict=True)
    try:
        issues = check_materialized_goldens(pathlib.Path(args.manifest), workspace)
    except (OSError, ValueError, json.JSONDecodeError):
        print('ERROR golden-check: invalid manifest, path, or materialized output')
        return 2
    if issues:
        counts: dict[str, int] = {}
        for issue in issues:
            counts[issue.code] = counts.get(issue.code, 0) + 1
        for code, count in sorted(counts.items()):
            print(f'ERROR {code}: {count}')
        return 1
    print('OK narrative golden outputs are exact')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
