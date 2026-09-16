from __future__ import annotations

import json
import pathlib
import re
from pathlib import PurePosixPath
from typing import NamedTuple


ENTITY_ID_RE = re.compile(r'^[A-Z][A-Z0-9_]*-\d{4}$')
ASSET_ID_RE = re.compile(r'^[a-z0-9][a-z0-9._-]*$')
ALLOWED_KINDS = {'skin', 'portrait', 'concept-art', 'variation'}


class Issue(NamedTuple):
    code: str
    ref: str


def _safe_relative(value) -> bool:
    if not isinstance(value, str) or not value.strip() or '\\' in value:
        return False
    pure = PurePosixPath(value)
    return not pure.is_absolute() and '..' not in pure.parts


def _inside(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _valid_provenance(value) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get('source'), str)
        and bool(value['source'].strip())
        and isinstance(value.get('revision'), str)
        and bool(value['revision'].strip())
    )


def validate_manifest(manifest, workspace_root: pathlib.Path, *, check_files: bool = False) -> list[Issue]:
    root = pathlib.Path(workspace_root).resolve()
    issues: list[Issue] = []
    if not isinstance(manifest, dict):
        return [Issue('invalid-manifest-root', '')]
    if manifest.get('schema_version') != 1:
        issues.append(Issue('unsupported-manifest-schema', str(manifest.get('schema_version', ''))))
    raw_roots = manifest.get('asset_roots')
    if not isinstance(raw_roots, list) or not raw_roots:
        issues.append(Issue('invalid-asset-roots', ''))
        raw_roots = []
    valid_roots: list[pathlib.Path] = []
    for asset_root in raw_roots:
        if not _safe_relative(asset_root):
            issues.append(Issue('invalid-asset-root', str(asset_root)))
            continue
        resolved_root = (root / asset_root).resolve(strict=False)
        if not _inside(resolved_root, root):
            issues.append(Issue('invalid-asset-root', str(asset_root)))
            continue
        valid_roots.append(resolved_root)

    records = manifest.get('records')
    if not isinstance(records, list):
        issues.append(Issue('invalid-asset-records', ''))
        return sorted(issues)
    seen_entities: set[str] = set()
    seen_asset_keys: set[tuple[str, str]] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            issues.append(Issue('invalid-asset-record', str(index)))
            continue
        entity_id = record.get('entity_id')
        if not isinstance(entity_id, str) or not ENTITY_ID_RE.fullmatch(entity_id):
            issues.append(Issue('invalid-entity-id', str(entity_id or index)))
            entity_key = f'#{index}'
        else:
            entity_key = entity_id
            if entity_id in seen_entities:
                issues.append(Issue('duplicate-entity-asset-record', entity_id))
            seen_entities.add(entity_id)
        assets = record.get('assets')
        if not isinstance(assets, list):
            issues.append(Issue('invalid-assets-list', entity_key))
            continue
        for asset_index, asset in enumerate(assets):
            if not isinstance(asset, dict):
                issues.append(Issue('invalid-asset-entry', f'{entity_key}:{asset_index}'))
                continue
            asset_id = asset.get('asset_id')
            if not isinstance(asset_id, str) or not ASSET_ID_RE.fullmatch(asset_id):
                issues.append(Issue('invalid-asset-id', f'{entity_key}:{asset_id or asset_index}'))
                asset_key = str(asset_id or asset_index)
            else:
                asset_key = asset_id
                compound = (entity_key, asset_id)
                if compound in seen_asset_keys:
                    issues.append(Issue('duplicate-asset-id', f'{entity_key}:{asset_id}'))
                seen_asset_keys.add(compound)
            kind = asset.get('kind')
            if kind not in ALLOWED_KINDS:
                issues.append(Issue('invalid-asset-kind', f'{entity_key}:{asset_key}'))
            if not isinstance(asset.get('approved'), bool):
                issues.append(Issue('invalid-asset-approval', f'{entity_key}:{asset_key}'))
            if not _valid_provenance(asset.get('provenance')):
                issues.append(Issue('missing-asset-provenance', f'{entity_key}:{asset_key}'))
            rel_path = asset.get('path')
            if not _safe_relative(rel_path):
                issues.append(Issue('asset-path-outside-roots', f'{entity_key}:{asset_key}'))
                continue
            resolved = (root / rel_path).resolve(strict=False)
            if not _inside(resolved, root) or not any(_inside(resolved, asset_root) for asset_root in valid_roots):
                issues.append(Issue('asset-path-outside-roots', f'{entity_key}:{asset_key}'))
                continue
            if check_files and not resolved.is_file():
                issues.append(Issue('missing-asset-file', f'{entity_key}:{asset_key}'))
    return sorted(issues)


def main(argv=None, workspace_root=None):
    import argparse
    parser = argparse.ArgumentParser(description='Validate narrative-to-visual asset handoff manifests.')
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--check-files', action='store_true')
    parser.add_argument('--reveal', action='store_true')
    args = parser.parse_args(argv)
    workspace = pathlib.Path(workspace_root or pathlib.Path.cwd()).resolve(strict=True)
    supplied = pathlib.Path(args.manifest)
    candidate = supplied if supplied.is_absolute() else workspace / supplied
    try:
        path = candidate.resolve(strict=True)
        path.relative_to(workspace)
        manifest = json.loads(path.read_text(encoding='utf-8'))
        issues = validate_manifest(manifest, workspace, check_files=args.check_files)
    except (OSError, ValueError, json.JSONDecodeError):
        print('ERROR visual-handoff: invalid manifest or workspace path')
        return 2
    if issues:
        if args.reveal:
            for issue in issues:
                print(f'ERROR {issue.code} {issue.ref}'.rstrip())
        else:
            counts: dict[str, int] = {}
            for issue in issues:
                counts[issue.code] = counts.get(issue.code, 0) + 1
            for code, count in sorted(counts.items()):
                print(f'ERROR {code}: {count}')
            print('Details hidden by spoiler-safe mode. Use --reveal for editorial debugging.')
        return 1
    print('OK visual asset handoff is structurally valid')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
