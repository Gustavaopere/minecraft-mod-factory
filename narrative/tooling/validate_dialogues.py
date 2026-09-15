from __future__ import annotations

import pathlib
import re
import sys
import unicodedata
from typing import NamedTuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from profile import NarrativeProfile, load_profile, resolve_workspace_path


CHECKBOX_RE = re.compile(r'(?m)^\s*-\s*\[[ xX]\]\s+')


class Issue(NamedTuple):
    code: str
    detail: str
    path: pathlib.Path
    line: int


def _normalize(value: str) -> str:
    value = unicodedata.normalize('NFKD', value)
    value = ''.join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r'\s+', ' ', value.casefold().strip())


def _patterns(profile: NarrativeProfile):
    dlg = re.escape(profile.dialogue_entity_type)
    types = '|'.join(re.escape(item) for item in profile.entity_types)
    return (
        re.compile(r'^' + dlg + r'-\d{4}.*\.md$', re.IGNORECASE),
        re.compile(r'^#\s+' + dlg + r'-\d{4}\b', re.IGNORECASE | re.MULTILINE),
        re.compile(r'\b(?:' + types + r')-####'),
        re.compile(r'\b(?:' + types + r')-\d{4}\b'),
    )


def _dialogue_files(root: pathlib.Path, profile: NarrativeProfile):
    file_re, _, _, _ = _patterns(profile)
    return sorted(path for path in pathlib.Path(root).rglob('*.md') if path.is_file() and file_re.match(path.name))


def _sections(text: str):
    lines = text.splitlines()
    found = []
    for index, line in enumerate(lines):
        if not line.startswith('## '):
            continue
        heading = line[3:].strip()
        end = len(lines)
        for next_index in range(index + 1, len(lines)):
            if lines[next_index].startswith('## '):
                end = next_index
                break
        found.append((_normalize(heading), '\n'.join(lines[index + 1:end]).strip(), index + 1))
    return found


def _find_section(sections, aliases):
    normalized = tuple(_normalize(alias) for alias in aliases)
    for heading, body, line in sections:
        if any(heading.startswith(alias) for alias in normalized):
            return body, line
    return None


def _reference_rule_issues(path: pathlib.Path, located, profile: NarrativeProfile, id_re) -> list[Issue]:
    issues: list[Issue] = []
    for detail, rule in profile.dialogue_reference_rules.items():
        result = located.get(detail)
        if result is None:
            continue
        body, line = result
        if not body:
            continue
        references = tuple(sorted(set(id_re.findall(body))))
        if len(references) < rule.min_references:
            issues.append(Issue('missing-section-reference', detail, path, line))
        for ref in references:
            entity_type = ref.split('-', 1)[0]
            if entity_type not in rule.allowed_types:
                issues.append(Issue('invalid-reference-type', f'{detail}:{ref}', path, line))
    return issues


def validate_dialogue(path: pathlib.Path, profile: NarrativeProfile) -> list[Issue]:
    text = path.read_text(encoding='utf-8')
    _, title_re, placeholder_re, id_re = _patterns(profile)
    issues: list[Issue] = []
    if not title_re.search(text):
        issues.append(Issue('missing-dialogue-title', profile.dialogue_entity_type, path, 1))
    placeholder = placeholder_re.search(text)
    if placeholder:
        issues.append(Issue('placeholder-id', placeholder.group(0), path, text[:placeholder.start()].count('\n') + 1))
    sections = _sections(text)
    located = {}
    for detail, aliases in profile.dialogue_required_sections.items():
        result = _find_section(sections, aliases)
        if result is None:
            issues.append(Issue('missing-section', detail, path, 1))
            continue
        body, line = result
        located[detail] = (body, line)
        if not body:
            issues.append(Issue('empty-section', detail, path, line))
    issues.extend(_reference_rule_issues(path, located, profile, id_re))
    qa = located.get('qa')
    if qa and qa[0] and not CHECKBOX_RE.search(qa[0]):
        issues.append(Issue('qa-without-checkbox', 'qa', path, qa[1]))
    return sorted(issues, key=lambda i: (str(i.path), i.line, i.code, i.detail))


def validate(root: pathlib.Path, profile: NarrativeProfile) -> list[Issue]:
    issues: list[Issue] = []
    for path in _dialogue_files(pathlib.Path(root), profile):
        issues.extend(validate_dialogue(path, profile))
    return sorted(issues, key=lambda i: (str(i.path), i.line, i.code, i.detail))


def main(argv=None, workspace_root=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description='Validate profile-driven dialogue Markdown structure.')
    parser.add_argument('--profile', required=True)
    parser.add_argument('--root', help='dialogue root override; defaults to profile dialogue_root')
    parser.add_argument('--reveal', action='store_true')
    args = parser.parse_args(argv)
    workspace = pathlib.Path(workspace_root or pathlib.Path.cwd()).resolve(strict=True)
    try:
        profile = load_profile(args.profile, workspace)
        root = resolve_workspace_path(args.root or profile.dialogue_root, workspace)
    except (OSError, ValueError):
        print('ERROR workspace-path: profile/root must resolve inside the trusted workspace')
        return 2
    issues = validate(root, profile)
    if issues and args.reveal:
        for issue in issues:
            try:
                display = issue.path.relative_to(root)
            except ValueError:
                display = issue.path
            print(f'ERROR {issue.code} {issue.detail} {display}:{issue.line}')
    elif issues:
        counts: dict[str, int] = {}
        for issue in issues:
            counts[issue.code] = counts.get(issue.code, 0) + 1
        for code, count in sorted(counts.items()):
            print(f'ERROR {code}: {count}')
        print('Details hidden by spoiler-safe mode. Use --reveal for editorial debugging.')
    else:
        print('OK no dialogue structure issues found')
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
