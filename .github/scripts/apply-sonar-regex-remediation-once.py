#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(relative: str, old: str, new: str) -> None:
    target = ROOT / relative
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one replacement in {relative}, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


helper = ROOT / "art/tooling/validators/rendered_markdown_linear.js"
if helper.exists():
    raise SystemExit(f"refusing to overwrite existing helper: {helper}")
helper.write_text(
    """'use strict';

function stripMarkdownLinks(value) {
  const source = String(value || '');
  const output = [];
  let index = 0;
  while (index < source.length) {
    const image = source[index] === '!' && source[index + 1] === '[';
    if (!image && source[index] !== '[') {
      output.push(source[index]);
      index += 1;
      continue;
    }

    const open = image ? index + 1 : index;
    const close = source.indexOf(']', open + 1);
    if (close < 0) {
      output.push(source.slice(index));
      break;
    }
    const label = source.slice(open + 1, close);
    const delimiter = source[close + 1];
    if (delimiter === '(') {
      const targetEnd = source.indexOf(')', close + 2);
      if (targetEnd < 0) {
        output.push(source.slice(index));
        break;
      }
      if (targetEnd > close + 2) {
        output.push(label);
        index = targetEnd + 1;
        continue;
      }
    } else if (delimiter === '[') {
      const referenceEnd = source.indexOf(']', close + 2);
      if (referenceEnd < 0) {
        output.push(source.slice(index));
        break;
      }
      output.push(label);
      index = referenceEnd + 1;
      continue;
    }

    output.push(source.slice(index, close + 1));
    index = close + 1;
  }
  return output.join('');
}

function parseFenceOpening(line) {
  const source = String(line || '');
  let index = 0;
  while (index < 3 && source[index] === ' ') index += 1;
  const character = source[index];
  if (character !== '`' && character !== '~') return null;
  let end = index;
  while (source[end] === character) end += 1;
  const length = end - index;
  if (length < 3) return null;
  if (character === '`' && source.slice(end).includes('`')) return null;
  return {character, length};
}

function isHorizontalWhitespace(character) {
  return character === ' ' || character === '\\t' || character === '\\r' || character === '\\f' || character === '\\v';
}

function consumeListMarker(source, start, lineEnd) {
  let cursor = start;
  const first = source[cursor];
  if (first === '-' || first === '+' || first === '*') {
    cursor += 1;
  } else {
    let digits = 0;
    while (cursor < lineEnd && digits < 9 && source[cursor] >= '0' && source[cursor] <= '9') {
      cursor += 1;
      digits += 1;
    }
    if (!digits || (source[cursor] !== '.' && source[cursor] !== ')')) return null;
    cursor += 1;
  }
  const whitespaceStart = cursor;
  while (cursor < lineEnd && isHorizontalWhitespace(source[cursor])) cursor += 1;
  return cursor > whitespaceStart ? cursor : null;
}

function hasMarkdownReferenceDefinition(value) {
  const source = String(value || '');
  let lineStart = 0;
  while (lineStart <= source.length) {
    const newline = source.indexOf('\\n', lineStart);
    const lineEnd = newline < 0 ? source.length : newline;
    let cursor = lineStart;
    while (cursor < lineEnd && isHorizontalWhitespace(source[cursor])) cursor += 1;

    while (cursor < lineEnd) {
      const afterMarker = consumeListMarker(source, cursor, lineEnd);
      if (afterMarker === null) break;
      cursor = afterMarker;
      while (cursor < lineEnd && isHorizontalWhitespace(source[cursor])) cursor += 1;
    }

    if (source[cursor] === '[') {
      let close = cursor + 1;
      let labelLength = 0;
      while (close < source.length && source[close] !== ']' && labelLength <= 999) {
        close += 1;
        labelLength += 1;
      }
      if (labelLength >= 1 && labelLength <= 999 && source[close] === ']' && source[close + 1] === ':') return true;
    }

    if (newline < 0) break;
    lineStart = newline + 1;
  }
  return false;
}

module.exports = {stripMarkdownLinks, parseFenceOpening, hasMarkdownReferenceDefinition};
""",
    encoding="utf-8",
)

golden = "art/golden-samples/validate_reference_evidence.js"
replace_once(
    golden,
    "require('../tooling/validators/validate_golden_reference_rendered_edges.js');\n",
    "require('../tooling/validators/validate_golden_reference_rendered_edges.js');\nconst {stripMarkdownLinks, parseFenceOpening} = require('../tooling/validators/rendered_markdown_linear.js');\n",
)
replace_once(
    golden,
    r"""function normalizeRenderedText(value) {
  return decodeHtmlEntities(value)
    .replace(/\\([!"#$%&'()*+,\-.\/:;<=>?@\[\]\\^_`{|}~])/g, '$1')
    .replace(/!?\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/!?\[([^\]]+)\]\[[^\]]*\]/g, '$1')
    .replace(/<\/?[A-Za-z][^>]*>/g, '')
    .replace(/(^|[\s([{:;>\-])_{1,3}(?=\S)/g, '$1')
    .replace(/(\S)_{1,3}(?=$|[\s)\]}:;,.!?\-])/g, '$1')
    .replace(/[*`]/g, '')
    .trim();
}""",
    r"""function normalizeRenderedText(value) {
  const unescaped = decodeHtmlEntities(value)
    .replace(/\\([!"#$%&'()*+,\-.\/:;<=>?@\[\]\\^_`{|}~])/g, '$1');
  return stripMarkdownLinks(unescaped)
    .replace(/<\/?[A-Za-z][^>]*>/g, '')
    .replace(/(^|[\s([{:;>\-])_{1,3}(?=\S)/g, '$1')
    .replace(/(\S)_{1,3}(?=$|[\s)\]}:;,.!?\-])/g, '$1')
    .replace(/[*`]/g, '')
    .trim();
}""",
)
replace_once(
    golden,
    r"""function parseFenceOpening(line) {
  const match = String(line || '').match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
  if (!match) return null;
  const character = match[1][0];
  if (character === '`' && match[2].includes('`')) return null;
  return {character, length: match[1].length};
}

""",
    "",
)

rendered = "art/tooling/validators/validate_golden_reference_rendered_edges.js"
replace_once(
    rendered,
    "const path = require('node:path');\n",
    "const path = require('node:path');\nconst {stripMarkdownLinks, parseFenceOpening, hasMarkdownReferenceDefinition} = require('./rendered_markdown_linear.js');\n",
)
replace_once(
    rendered,
    r"""function normalizeRenderedText(value) {
  return decodeBasicHtmlEntities(value)
    .replace(/\\([!"#$%&'()*+,\-.\/:;<=>?@\[\]\\^_`{|}~])/g, '$1')
    .replace(/!?\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/!?\[([^\]]+)\]\[[^\]]*\]/g, '$1')
    .replace(/<\/?[A-Za-z][^>]*>/g, '')
    .replace(/(^|[\s([{:;>\-])_{1,3}(?=\S)/g, '$1')
    .replace(/(\S)_{1,3}(?=$|[\s)\]}:;,.!?\-])/g, '$1')
    .replace(/[*`]/g, '')
    .trim();
}""",
    r"""function normalizeRenderedText(value) {
  const unescaped = decodeBasicHtmlEntities(value)
    .replace(/\\([!"#$%&'()*+,\-.\/:;<=>?@\[\]\\^_`{|}~])/g, '$1');
  return stripMarkdownLinks(unescaped)
    .replace(/<\/?[A-Za-z][^>]*>/g, '')
    .replace(/(^|[\s([{:;>\-])_{1,3}(?=\S)/g, '$1')
    .replace(/(\S)_{1,3}(?=$|[\s)\]}:;,.!?\-])/g, '$1')
    .replace(/[*`]/g, '')
    .trim();
}""",
)
replace_once(
    rendered,
    r"""function parseFenceOpening(line) {
  const match = String(line || '').match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
  if (!match) return null;
  const character = match[1][0];
  if (character === '`' && match[2].includes('`')) return null;
  return {character, length: match[1].length};
}

""",
    "",
)
replace_once(
    rendered,
    r"""  const referenceDefinition = /^\s*(?:(?:[-+*]|\d+[.)])\s+)*\[[^\]]{1,999}\]:/m;
""",
    "",
)
replace_once(
    rendered,
    "    if (referenceDefinition.test(source)) fail(`${relative} uses a Markdown reference definition; reference definitions are forbidden in the reference-only corpus because they can activate shortcut links that alter guarded evidence or acceptance text after local normalization`);",
    "    if (hasMarkdownReferenceDefinition(source)) fail(`${relative} uses a Markdown reference definition; reference definitions are forbidden in the reference-only corpus because they can activate shortcut links that alter guarded evidence or acceptance text after local normalization`);",
)

replace_once(
    "art/tooling/blockbench/asset-toolkit/build_toolkit_bundle.js",
    ".replace(/\\s+$/, '')",
    ".trimEnd()",
)

skills = "skills/scripts/validate_skill_repository.py"
replace_once(skills, "import re\n", "")
replace_once(
    skills,
    '''def validate_names(root):
    for path in root.glob("*/SKILL.md"):
        match = re.search(r"^name:\\s*([^\\n]+)$", path.read_text(encoding="utf-8"), re.MULTILINE)
        if not match or match.group(1).strip() != path.parent.name:
            raise SystemExit(f"invalid skill name metadata: {path}")
''',
    '''def validate_names(root):
    for path in root.glob("*/SKILL.md"):
        declared_name = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("name:"):
                value = line[len("name:"):].strip()
                declared_name = value or None
                break
        if declared_name != path.parent.name:
            raise SystemExit(f"invalid skill name metadata: {path}")
''',
)

print("Applied deterministic linear Sonar regex remediation")
