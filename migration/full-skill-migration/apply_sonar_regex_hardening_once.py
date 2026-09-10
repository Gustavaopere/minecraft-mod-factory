#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_exact(path: str, old: str, new: str, *, count: int = 1) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"{path}: expected {count} exact occurrence(s), found {actual}: {old!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


replace_exact(
    "skills/scripts/validate_skill_repository.py",
    "import re\n",
    "",
)
replace_exact(
    "skills/scripts/validate_skill_repository.py",
    '''def validate_names(root):\n    for path in root.glob("*/SKILL.md"):\n        match = re.search(r"^name:\\s*([^\\n]+)$", path.read_text(encoding="utf-8"), re.MULTILINE)\n        if not match or match.group(1).strip() != path.parent.name:\n            raise SystemExit(f"invalid skill name metadata: {path}")\n''',
    '''def validate_names(root):\n    for path in root.glob("*/SKILL.md"):\n        declared_name = None\n        for line in path.read_text(encoding="utf-8").splitlines():\n            if line.startswith("name:"):\n                declared_name = line.partition(":")[2].strip()\n                break\n        if declared_name != path.parent.name:\n            raise SystemExit(f"invalid skill name metadata: {path}")\n''',
)

replace_exact(
    "art/tooling/blockbench/asset-toolkit/build_toolkit_bundle.js",
    "return source.replace(/\\r\\n/g, '\\n').replace(/\\s+$/, '').split('\\n').map((line) => line.trim().length === 0 ? '' : `${prefix}${line}`).join('\\n');",
    "return source.replace(/\\r\\n/g, '\\n').trimEnd().split('\\n').map((line) => line.trim().length === 0 ? '' : `${prefix}${line}`).join('\\n');",
)

strip_helper = '''function stripSimpleMarkdownLinks(value) {\n  const source = String(value || '');\n  let output = '';\n  let index = 0;\n  while (index < source.length) {\n    const image = source[index] === '!' && source[index + 1] === '[';\n    const open = image ? index + 1 : index;\n    if (source[open] !== '[') {\n      output += source[index];\n      index += 1;\n      continue;\n    }\n    const textEnd = source.indexOf(']', open + 1);\n    if (textEnd <= open + 1) {\n      output += source[index];\n      index += 1;\n      continue;\n    }\n    const suffix = source[textEnd + 1];\n    if (suffix === '(') {\n      const targetEnd = source.indexOf(')', textEnd + 2);\n      if (targetEnd > textEnd + 2) {\n        output += source.slice(open + 1, textEnd);\n        index = targetEnd + 1;\n        continue;\n      }\n    } else if (suffix === '[') {\n      const labelEnd = source.indexOf(']', textEnd + 2);\n      if (labelEnd >= textEnd + 2) {\n        output += source.slice(open + 1, textEnd);\n        index = labelEnd + 1;\n        continue;\n      }\n    }\n    output += source[index];\n    index += 1;\n  }\n  return output;\n}\n\n'''

rendered_path = "art/tooling/validators/validate_golden_reference_rendered_edges.js"
replace_exact(
    rendered_path,
    "function normalizeRenderedText(value) {\n",
    strip_helper + "function normalizeRenderedText(value) {\n",
)
replace_exact(
    rendered_path,
    '''function normalizeRenderedText(value) {\n  return decodeBasicHtmlEntities(value)\n    .replace(/\\\\([!"#$%&'()*+,\\-.\\/:;<=>?@\\[\\]\\\\^_`{|}~])/g, '$1')\n    .replace(/!?\\[([^\\]]+)\\]\\([^)]+\\)/g, '$1')\n    .replace(/!?\\[([^\\]]+)\\]\\[[^\\]]*\\]/g, '$1')\n    .replace(/<\\/?[A-Za-z][^>]*>/g, '')\n    .replace(/(^|[\\s([{:;>\\-])_{1,3}(?=\\S)/g, '$1')\n    .replace(/(\\S)_{1,3}(?=$|[\\s)\\]}:;,.!?\\-])/g, '$1')\n    .replace(/[*`]/g, '')\n    .trim();\n}\n''',
    '''function normalizeRenderedText(value) {\n  const unescaped = decodeBasicHtmlEntities(value)\n    .replace(/\\\\([!"#$%&'()*+,\\-.\\/:;<=>?@\\[\\]\\\\^_`{|}~])/g, '$1');\n  return stripSimpleMarkdownLinks(unescaped)\n    .replace(/<\\/?[A-Za-z][^>]*>/g, '')\n    .replace(/(^|[\\s([{:;>\\-])_{1,3}(?=\\S)/g, '$1')\n    .replace(/(\\S)_{1,3}(?=$|[\\s)\\]}:;,.!?\\-])/g, '$1')\n    .replace(/[*`]/g, '')\n    .trim();\n}\n''',
)
replace_exact(
    rendered_path,
    '''function parseFenceOpening(line) {\n  const match = String(line || '').match(/^ {0,3}(`{3,}|~{3,})(.*)$/);\n  if (!match) return null;\n  const character = match[1][0];\n  if (character === '`' && match[2].includes('`')) return null;\n  return {character, length: match[1].length};\n}\n''',
    '''function parseFenceOpening(line) {\n  const source = String(line || '');\n  let offset = 0;\n  while (offset < source.length && offset < 3 && source[offset] === ' ') offset += 1;\n  const character = source[offset];\n  if (character !== '`' && character !== '~') return null;\n  let end = offset;\n  while (end < source.length && source[end] === character) end += 1;\n  const length = end - offset;\n  if (length < 3) return null;\n  const info = source.slice(end);\n  if (character === '`' && info.includes('`')) return null;\n  return {character, length};\n}\n''',
)
reference_helpers = '''function isSourceWhitespace(character) {\n  return character === ' ' || character === '\\t' || character === '\\r' || character === '\\n' || character === '\\f' || character === '\\v';\n}\n\nfunction skipSourceWhitespace(source, start) {\n  let index = start;\n  while (index < source.length && isSourceWhitespace(source[index])) index += 1;\n  return index;\n}\n\nfunction consumeListMarker(source, start) {\n  let markerEnd = start;\n  if (source[start] === '-' || source[start] === '+' || source[start] === '*') {\n    markerEnd = start + 1;\n  } else {\n    let digitEnd = start;\n    while (digitEnd < source.length && source[digitEnd] >= '0' && source[digitEnd] <= '9') digitEnd += 1;\n    if (digitEnd > start && (source[digitEnd] === '.' || source[digitEnd] === ')')) markerEnd = digitEnd + 1;\n  }\n  if (markerEnd === start || !isSourceWhitespace(source[markerEnd])) return null;\n  return skipSourceWhitespace(source, markerEnd);\n}\n\nfunction hasReferenceDefinition(value) {\n  const source = String(value || '');\n  for (let start = 0; start < source.length; start += 1) {\n    if (start !== 0 && source[start - 1] !== '\\n') continue;\n    let index = skipSourceWhitespace(source, start);\n    while (index < source.length) {\n      const next = consumeListMarker(source, index);\n      if (next === null) break;\n      index = next;\n    }\n    if (source[index] !== '[') continue;\n    let close = index + 1;\n    while (close < source.length && source[close] !== ']' && close - index - 1 <= 999) close += 1;\n    const labelLength = close - index - 1;\n    if (labelLength >= 1 && labelLength <= 999 && source[close] === ']' && source[close + 1] === ':') return true;\n  }\n  return false;\n}\n\n'''
replace_exact(
    rendered_path,
    "function validateRoot(root) {\n",
    reference_helpers + "function validateRoot(root) {\n",
)
replace_exact(
    rendered_path,
    "  const referenceDefinition = /^\\s*(?:(?:[-+*]|\\d+[.)])\\s+)*\\[[^\\]]{1,999}\\]:/m;\n",
    "",
)
replace_exact(
    rendered_path,
    "    if (referenceDefinition.test(source)) fail(`${relative} uses a Markdown reference definition; reference definitions are forbidden in the reference-only corpus because they can activate shortcut links that alter guarded evidence or acceptance text after local normalization`);",
    "    if (hasReferenceDefinition(source)) fail(`${relative} uses a Markdown reference definition; reference definitions are forbidden in the reference-only corpus because they can activate shortcut links that alter guarded evidence or acceptance text after local normalization`);",
)
replace_exact(
    rendered_path,
    "if (process.argv.includes('--self-test')) runSelfTest();\nelse {",
    "module.exports = {stripSimpleMarkdownLinks};\n\nif (process.argv.includes('--self-test')) runSelfTest();\nelse {",
)

golden_path = "art/golden-samples/validate_reference_evidence.js"
replace_exact(
    golden_path,
    "require('../tooling/validators/validate_golden_reference_rendered_edges.js');",
    "const {stripSimpleMarkdownLinks} = require('../tooling/validators/validate_golden_reference_rendered_edges.js');",
)
replace_exact(
    golden_path,
    '''function normalizeRenderedText(value) {\n  return decodeHtmlEntities(value)\n    .replace(/\\\\([!"#$%&'()*+,\\-.\\/:;<=>?@\\[\\]\\\\^_`{|}~])/g, '$1')\n    .replace(/!?\\[([^\\]]+)\\]\\([^)]+\\)/g, '$1')\n    .replace(/!?\\[([^\\]]+)\\]\\[[^\\]]*\\]/g, '$1')\n    .replace(/<\\/?[A-Za-z][^>]*>/g, '')\n    .replace(/(^|[\\s([{:;>\\-])_{1,3}(?=\\S)/g, '$1')\n    .replace(/(\\S)_{1,3}(?=$|[\\s)\\]}:;,.!?\\-])/g, '$1')\n    .replace(/[*`]/g, '')\n    .trim();\n}\n''',
    '''function normalizeRenderedText(value) {\n  const unescaped = decodeHtmlEntities(value)\n    .replace(/\\\\([!"#$%&'()*+,\\-.\\/:;<=>?@\\[\\]\\\\^_`{|}~])/g, '$1');\n  return stripSimpleMarkdownLinks(unescaped)\n    .replace(/<\\/?[A-Za-z][^>]*>/g, '')\n    .replace(/(^|[\\s([{:;>\\-])_{1,3}(?=\\S)/g, '$1')\n    .replace(/(\\S)_{1,3}(?=$|[\\s)\\]}:;,.!?\\-])/g, '$1')\n    .replace(/[*`]/g, '')\n    .trim();\n}\n''',
)
replace_exact(
    golden_path,
    "function isSeparatorRow(cells) { return cells.every((cell) => /^:?-{3,}:?$/.test(cell)); }",
    '''function isSeparatorCell(cell) {\n  let start = 0;\n  let end = cell.length;\n  if (cell[start] === ':') start += 1;\n  if (end > start && cell[end - 1] === ':') end -= 1;\n  if (end - start < 3) return false;\n  for (let index = start; index < end; index += 1) {\n    if (cell[index] !== '-') return false;\n  }\n  return true;\n}\n\nfunction isSeparatorRow(cells) { return cells.every(isSeparatorCell); }''',
)

print("OK: applied guarded Sonar slow-regex hardening to 4 canonical files")
