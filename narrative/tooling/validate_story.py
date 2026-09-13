from __future__ import annotations

import pathlib
import re
import sys
from typing import NamedTuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from profile import NarrativeProfile, load_profile


class Issue(NamedTuple):
    code: str
    ref: str
    path: pathlib.Path
    line: int


FATAL_CODES = {'duplicate-id', 'filename-id-mismatch', 'invalid-editorial-state', 'missing-editorial-state-value'}


def _patterns(profile: NarrativeProfile):
    types = '|'.join(re.escape(item) for item in profile.entity_types)
    return (
        re.compile(r'\b(?:' + types + r')-\d{4}\b'),
        re.compile(r'^#\s+((?:' + types + r')-\d{4})\b'),
        re.compile(r'^((?:' + types + r')-\d{4})(?:[-_.]|$)'),
    )


def _markdown_files(root: pathlib.Path):
    return sorted(path for path in pathlib.Path(root).rglob('*.md') if path.is_file())


def _editorial_state_issues(path: pathlib.Path, lines: list[str], headings: tuple[str, ...], prefixes: tuple[str, ...]) -> list[Issue]:
    issues: list[Issue] = []
    normalized_headings = {'## ' + heading.strip().casefold() for heading in headings}
    for index, line in enumerate(lines):
        if line.strip().casefold() not in normalized_headings:
            continue
        value_line = None
        value_no = index + 2
        for candidate_index in range(index + 1, len(lines)):
            stripped = lines[candidate_index].strip()
            if stripped.startswith('## '):
                break
            if stripped:
                value_line = stripped
                value_no = candidate_index + 1
                break
        if value_line is None:
            issues.append(Issue('missing-editorial-state-value', '', path, index + 1))
            continue
        folded = value_line.casefold()
        if not any(folded.startswith(prefix.casefold()) for prefix in prefixes):
            issues.append(Issue('invalid-editorial-state', value_line, path, value_no))
    return issues


def validate(root: pathlib.Path, profile: NarrativeProfile) -> list[Issue]:
    root = pathlib.Path(root)
    id_re, decl_re, filename_id_re = _patterns(profile)
    declarations: dict[str, list[tuple[pathlib.Path, int]]] = {}
    references: list[tuple[str, pathlib.Path, int]] = []
    issues: list[Issue] = []

    for path in _markdown_files(root):
        text = path.read_text(encoding='utf-8')
        lines = text.splitlines()
        issues.extend(_editorial_state_issues(path, lines, profile.editorial_state_headings, profile.editorial_state_prefixes))
        filename_match = filename_id_re.match(path.name)
        first_declared_id = None
        for line_no, line in enumerate(lines, start=1):
            decl = decl_re.match(line)
            if decl:
                ref = decl.group(1)
                declarations.setdefault(ref, []).append((path, line_no))
                if first_declared_id is None:
                    first_declared_id = ref
                    if filename_match and filename_match.group(1) != ref:
                        issues.append(Issue('filename-id-mismatch', ref, path, line_no))
            for ref in id_re.findall(line):
                references.append((ref, path, line_no))

    for ref, locations in sorted(declarations.items()):
        if len(locations) > 1:
            for path, line_no in locations[1:]:
                issues.append(Issue('duplicate-id', ref, path, line_no))

    declared_ids = set(declarations)
    seen_unresolved: set[tuple[str, pathlib.Path, int]] = set()
    for ref, path, line_no in references:
        key = (ref, path, line_no)
        if ref not in declared_ids and key not in seen_unresolved:
            seen_unresolved.add(key)
            issues.append(Issue('unresolved-ref', ref, path, line_no))

    return sorted(issues, key=lambda i: (str(i.path), i.line, i.code, i.ref))


def exit_code(issues: list[Issue], strict_references: bool = False) -> int:
    if any(issue.code in FATAL_CODES for issue in issues):
        return 1
    if strict_references and any(issue.code == 'unresolved-ref' for issue in issues):
        return 1
    return 0


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description='Validate profile-driven narrative Markdown records.')
    parser.add_argument('--profile', required=True, help='path to narrative project profile JSON')
    parser.add_argument('--root', help='story root override; defaults to profile story_root')
    parser.add_argument('--strict-references', action='store_true')
    parser.add_argument('--reveal', action='store_true', help='show IDs/paths/lines for editorial debugging')
    args = parser.parse_args(argv)

    profile = load_profile(args.profile)
    root = pathlib.Path(args.root or profile.story_root)
    issues = validate(root, profile)
    if issues:
        if args.reveal:
            for issue in issues:
                level = 'ERROR' if issue.code in FATAL_CODES or args.strict_references else 'WARN'
                try:
                    display = issue.path.relative_to(root)
                except ValueError:
                    display = issue.path
                print(f'{level} {issue.code} {issue.ref} {display}:{issue.line}')
        else:
            counts: dict[tuple[str, str], int] = {}
            for issue in issues:
                level = 'ERROR' if issue.code in FATAL_CODES or (args.strict_references and issue.code == 'unresolved-ref') else 'WARN'
                counts[(level, issue.code)] = counts.get((level, issue.code), 0) + 1
            for (level, code), count in sorted(counts.items()):
                print(f'{level} {code}: {count}')
            print('Details hidden by spoiler-safe mode. Use --reveal for editorial debugging.')
    else:
        print('OK no narrative ID/reference/state issues found')
    return exit_code(issues, strict_references=args.strict_references)


if __name__ == '__main__':
    raise SystemExit(main())
