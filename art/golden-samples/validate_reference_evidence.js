'use strict';

const fs = require('node:fs');
const path = require('node:path');
require('../tooling/validators/validate_golden_reference_rendered_edges.js');

const ROOT = __dirname;
const UNRESOLVED = 'UNRESOLVED';
const PENDING = 'PENDING';
const CANONICAL_STATUS = 'REFERENCE-ONLY — not a runtime registration and not evidence of shipped gameplay.';
const EXPECTED_FILES = new Set([
  'README.md',
  'validate_golden_samples.js',
  'validate_reference_evidence.js',
  'model-asset/ANIMATION-BRIEF.md',
  'model-asset/ASSET-BRIEF.md',
  'model-asset/MODEL-CONTRACT.md',
  'model-asset/TOOLKIT-PROFILE.json',
  'model-asset/validator-project-fixture.json',
  'spell/AUDIO-CUE-SHEET.md',
  'spell/AUDIO-QA.md',
  'spell/SPELL-BRIEF.md',
  'spell/SPELL-PRESENTATION.md',
  'spell/VFX-BRIEF.md',
  'spell/VFX-QA.md',
  'spell/VISUAL-QA.md',
]);
const NAMED_HTML_ENTITIES = Object.freeze({amp: '&', apos: "'", gt: '>', lt: '<', nbsp: ' ', quot: '"'});

function fail(message) { throw new Error(`Golden Samples evidence validation failed: ${message}`); }

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

function relativePath(file) { return path.relative(ROOT, file).split(path.sep).join('/'); }

function decodeHtmlEntities(value) {
  return String(value || '').replace(/&(#x[0-9a-f]+|#\d+|[a-z][a-z0-9]+);/gi, (entity, body) => {
    if (body[0] === '#') {
      const hex = body[1] && body[1].toLowerCase() === 'x';
      const digits = hex ? body.slice(2) : body.slice(1);
      const codePoint = Number.parseInt(digits, hex ? 16 : 10);
      if (!Number.isInteger(codePoint) || codePoint < 0 || codePoint > 0x10ffff) fail(`invalid HTML numeric entity ${entity}`);
      return String.fromCodePoint(codePoint);
    }
    const decoded = NAMED_HTML_ENTITIES[body.toLowerCase()];
    if (decoded === undefined) fail(`unsupported HTML named entity ${entity}; reference-only evidence must use unambiguous text`);
    return decoded;
  });
}

function normalizeRenderedText(value) {
  return decodeHtmlEntities(value)
    .replace(/\\([!"#$%&'()*+,\-.\/:;<=>?@\[\]\\^_`{|}~])/g, '$1')
    .replace(/!?\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/!?\[([^\]]+)\]\[[^\]]*\]/g, '$1')
    .replace(/<\/?[A-Za-z][^>]*>/g, '')
    .replace(/(^|[\s([{:;>\-])_{1,3}(?=\S)/g, '$1')
    .replace(/(\S)_{1,3}(?=$|[\s)\]}:;,.!?\-])/g, '$1')
    .replace(/[*`]/g, '')
    .trim();
}

function normalizeBlockDeclarationText(value) {
  let normalized = normalizeRenderedText(value);
  let previous = null;
  while (normalized !== previous) {
    previous = normalized;
    normalized = normalized.replace(/^#{1,6}(?:\s+|$)/, '').replace(/^(?:[-+]|\d+[.)]|\[[ xX]\])\s+/, '').trimStart();
  }
  return normalized;
}

function collectStatusDeclarations(source) {
  return String(source || '').split(/\r?\n/).map((line, index) => ({normalized: normalizeBlockDeclarationText(line.trim()), lineNumber: index + 1})).filter((entry) => /^Status\s*:/i.test(entry.normalized));
}

function collectPrefixedMatches(source, prefix) {
  const normalizedPrefix = normalizeBlockDeclarationText(prefix);
  const matches = String(source || '').split(/\r?\n/).map((line, index) => ({normalized: normalizeBlockDeclarationText(line.trim()), lineNumber: index + 1})).filter((entry) => entry.normalized.startsWith(normalizedPrefix));
  return {normalizedPrefix, matches};
}

function runStatusDeclarationRegressionSelfTest() {
  const contradictory = collectStatusDeclarations(`Status: ${CANONICAL_STATUS}\n- Status: PRODUCTION READY — runtime registration and shipped gameplay.\n`);
  if (contradictory.length !== 2) fail(`internal Status regression self-test expected 2 declarations for canonical plus list-contained contradiction; found ${contradictory.length}`);
  const nested = collectStatusDeclarations('  - 1. Status: PRODUCTION READY — nested list declaration.\n');
  if (nested.length !== 1 || !/^Status\s*:/i.test(nested[0].normalized)) fail('internal Status regression self-test failed to recognize a declaration inside nested list containers');
  const taskLists = collectStatusDeclarations('- [ ] Status: PRODUCTION READY — unchecked task list declaration.\n1. [x] Status: PRODUCTION READY — checked task list declaration.\n');
  if (taskLists.length !== 2) fail(`internal Status regression self-test expected 2 task-list declarations; found ${taskLists.length}`);
  const escapedGuard = collectPrefixedMatches('- Runtime consumer/class: `UNRESOLVED`\n- Runtime consumer/class\\: com.example.FabricatedRenderer\n', '- Runtime consumer/class:');
  if (escapedGuard.matches.length !== 2) fail(`internal guarded-prefix regression self-test expected escaped punctuation to produce a duplicate rendered field; found ${escapedGuard.matches.length}`);
  const headingGuard = collectPrefixedMatches('- Runtime consumer/class: `UNRESOLVED`\n## Runtime consumer/class: com.example.FabricatedRenderer\n', '- Runtime consumer/class:');
  if (headingGuard.matches.length !== 2) fail(`internal guarded-prefix regression self-test expected an ATX-heading declaration to count as a duplicate rendered field; found ${headingGuard.matches.length}`);

  const bareTableRow = parseTableRow('`root` | duplicate runtime root | fabricated pivot | com.example.FabricatedRenderer');
  if (!bareTableRow || bareTableRow.length !== 4 || bareTableRow[0] !== 'root' || bareTableRow[3] !== 'com.example.FabricatedRenderer') fail('internal table-row regression self-test expected a valid GFM row without outer pipes to be parseable');

  const tableBlock = extractGfmTableRows(['Bone | Purpose | Pivot rule | Runtime dependency','--- | --- | --- | ---','root | duplicate runtime root | fabricated pivot | com.example.FabricatedRenderer','','root | is a conventional name in examples and this is ordinary prose.'].join('\n'));
  if (tableBlock.length !== 2 || tableBlock[0].cells[0] !== 'Bone' || tableBlock[1].cells[0] !== 'root') fail(`internal table-boundary regression self-test expected exactly header + one bare GFM data row; found ${tableBlock.length}`);

  const shortRowTable = extractGfmTableRows(['Bone | Purpose | Pivot rule | Runtime dependency','--- | --- | --- | ---','root | canonical runtime root | canonical pivot | UNRESOLVED','| spacer |','root | fabricated duplicate | fabricated pivot | com.example.FabricatedRenderer'].join('\n'));
  if (shortRowTable.length !== 4 || shortRowTable[2].cells.length !== 4 || shortRowTable[2].cells[0] !== 'spacer' || shortRowTable[3].cells[0] !== 'root') fail(`internal short-table-row regression self-test expected a padded short body row without terminating the table; found ${shortRowTable.length} row(s)`);

  const codeExampleRows = extractGfmTableRows(['```text','Bone | Purpose | Pivot rule | Runtime dependency','--- | --- | --- | ---','root | fenced example | example pivot | com.example.FabricatedRenderer','```','','    Bone | Purpose | Pivot rule | Runtime dependency','    --- | --- | --- | ---','    root | indented example | example pivot | com.example.FabricatedRenderer'].join('\n'));
  if (codeExampleRows.length !== 0) fail(`internal code-block table regression self-test expected fenced and four-space-indented examples to be ignored; found ${codeExampleRows.length} row(s)`);
}

function normalizeToken(value) { return normalizeRenderedText(value); }

function parseTableRow(line, allowSingleCell = false) {
  const trimmed = line.trim();
  if (!trimmed.includes('|')) return null;
  let body = trimmed;
  if (body.startsWith('|')) body = body.slice(1);
  if (body.endsWith('|')) body = body.slice(0, -1);
  const cells = body.split('|').map(normalizeToken);
  return cells.length >= (allowSingleCell ? 1 : 2) ? cells : null;
}

function isSeparatorRow(cells) { return cells.every((cell) => /^:?-{3,}:?$/.test(cell)); }

function parseFenceOpening(line) {
  const match = String(line || '').match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
  if (!match) return null;
  const character = match[1][0];
  if (character === '`' && match[2].includes('`')) return null;
  return {character, length: match[1].length};
}

function isFenceClosing(line, fence) {
  if (!fence) return false;
  const match = String(line || '').match(/^ {0,3}(`+|~+)\s*$/);
  return Boolean(match && match[1][0] === fence.character && match[1].length >= fence.length);
}

function expandTabs(line) {
  let column = 0;
  let expanded = '';
  for (const character of String(line || '')) {
    if (character === '\t') {
      const width = 4 - (column % 4);
      expanded += ' '.repeat(width);
      column += width;
    } else {
      expanded += character;
      column += 1;
    }
  }
  return expanded;
}

function leadingSpaceCount(line) {
  const match = String(line || '').match(/^ */);
  return match ? match[0].length : 0;
}

function parseListItemMarker(line, containerIndent = 0) {
  const source = String(line || '');
  const containerPrefix = ' '.repeat(containerIndent);
  if (!source.startsWith(containerPrefix)) return null;
  const relative = source.slice(containerIndent);
  const match = relative.match(/^( {0,3})([-+*]|\d{1,9}[.)])( {1,4})(?=\S|$)/);
  if (!match) return null;
  return {markerIndent: containerIndent + match[1].length, contentIndent: containerIndent + match[1].length + match[2].length + match[3].length};
}

function buildListContainerIndents(lines) {
  const containerIndents = new Array(lines.length).fill(0);
  const stack = [];
  let blankRun = 0;
  for (let index = 0; index < lines.length; index += 1) {
    const line = String(lines[index] || '');
    if (!line.trim()) {
      blankRun += 1;
      containerIndents[index] = stack.length ? stack[stack.length - 1].contentIndent : 0;
      if (blankRun >= 2) stack.length = 0;
      continue;
    }
    blankRun = 0;
    const leading = leadingSpaceCount(line);
    while (stack.length && leading < stack[stack.length - 1].contentIndent) stack.pop();
    const parentIndent = stack.length ? stack[stack.length - 1].contentIndent : 0;
    const marker = parseListItemMarker(line, parentIndent);
    containerIndents[index] = parentIndent;
    if (marker) stack.push(marker);
  }
  return containerIndents;
}

function lineForBlockParsing(lines, containerIndents, index) {
  const source = String(lines[index] || '');
  const containerIndent = containerIndents[index] || 0;
  const marker = parseListItemMarker(source, containerIndent);
  if (marker) return source.slice(marker.contentIndent);
  const containerPrefix = ' '.repeat(containerIndent);
  if (containerIndent && source.startsWith(containerPrefix)) return source.slice(containerIndent);
  return source;
}

function isIndentedCodeLine(line) { return /^(?:\t| {4})/.test(String(line || '')); }

function isTableTerminatingBlockConstruct(line) {
  const value = String(line || '');
  return /^ {0,3}#{1,6}(?:[ \t]+|$)/.test(value)
    || /^ {0,3}>/.test(value)
    || /^ {0,3}(?:[-+*]|\d{1,9}[.)])(?:[ \t]+|$)/.test(value);
}

function normalizeBodyCells(cells, width) {
  const normalized = cells.slice(0, width);
  while (normalized.length < width) normalized.push('');
  return normalized;
}

function extractGfmTableRows(source) {
  const rawLines = String(source || '').split(/\r?\n/);
  const lines = rawLines.map(expandTabs);
  const containerIndents = buildListContainerIndents(lines);
  const rows = [];
  let fence = null;
  for (let index = 0; index < lines.length - 1; index += 1) {
    const rawLine = rawLines[index];
    const line = lineForBlockParsing(lines, containerIndents, index);
    if (fence) { if (isFenceClosing(line, fence)) fence = null; continue; }
    const openingFence = parseFenceOpening(line);
    if (openingFence) { fence = openingFence; continue; }
    if (isIndentedCodeLine(line)) continue;

    const delimiterLine = lineForBlockParsing(lines, containerIndents, index + 1);
    if (parseFenceOpening(delimiterLine) || isIndentedCodeLine(delimiterLine)) continue;
    const header = parseTableRow(line);
    const delimiter = parseTableRow(delimiterLine);
    if (!header || !delimiter || header.length !== delimiter.length || !isSeparatorRow(delimiter)) continue;
    rows.push({line: rawLine, lineNumber: index + 1, cells: header});
    index += 1;
    while (index + 1 < lines.length) {
      const rawNextLine = rawLines[index + 1];
      const nextLine = lineForBlockParsing(lines, containerIndents, index + 1);
      if (!nextLine.trim() || parseFenceOpening(nextLine) || isIndentedCodeLine(nextLine) || isTableTerminatingBlockConstruct(nextLine)) break;
      const cells = parseTableRow(nextLine, true);
      if (!cells || isSeparatorRow(cells)) break;
      rows.push({line: rawNextLine, lineNumber: index + 2, cells: normalizeBodyCells(cells, header.length)});
      index += 1;
    }
  }
  return rows;
}

function tableRows(relative) {
  const file = path.join(ROOT, relative);
  if (!fs.existsSync(file)) fail(`missing guarded table file ${relative}`);
  return extractGfmTableRows(fs.readFileSync(file, 'utf8'));
}

function findPrefixedLine(relative, prefix) {
  const file = path.join(ROOT, relative);
  if (!fs.existsSync(file)) fail(`missing guarded file ${relative}`);
  const {normalizedPrefix, matches} = collectPrefixedMatches(fs.readFileSync(file, 'utf8'), prefix);
  if (!matches.length) fail(`${relative} missing guarded field ${prefix}`);
  if (matches.length !== 1) fail(`${relative} guarded field ${prefix} must appear exactly once after rendered-Markdown normalization; found ${matches.length}`);
  return {...matches[0], normalizedPrefix};
}

function requireValueStartsWith(relative, prefix, expected) {
  const {normalized, normalizedPrefix, lineNumber} = findPrefixedLine(relative, prefix);
  const value = normalizeRenderedText(normalized.slice(normalizedPrefix.length));
  if (!new RegExp(`^${expected}\\b`, 'i').test(value)) fail(`${relative}:${lineNumber} value after "${prefix}" must begin with ${expected}; got "${value || '<empty>'}"`);
}

function requireExactCell(relative, row, index, expected, label) {
  const actual = normalizeRenderedText(row.cells[index]);
  if (actual !== expected) fail(`${relative}:${row.lineNumber} ${label} must remain exactly ${expected}; got "${actual || '<empty>'}"`);
}

function requireUnresolvedCell(relative, row, index, label) {
  const actual = normalizeRenderedText(row.cells[index]);
  if (!new RegExp(`\\b${UNRESOLVED}\\b`).test(actual)) fail(`${relative}:${row.lineNumber} ${label} must remain explicitly ${UNRESOLVED}; got "${actual || '<empty>'}"`);
}

function requireRowsByKey(relative, headerKey, contracts) {
  const rows = tableRows(relative);
  const normalizedHeader = normalizeRenderedText(headerKey);
  const dataRows = rows.filter((row) => normalizeRenderedText(row.cells[0]) !== normalizedHeader);
  for (const contract of contracts) {
    const normalizedKey = normalizeRenderedText(contract.key);
    const matches = dataRows.filter((candidate) => normalizeRenderedText(candidate.cells[0]) === normalizedKey);
    if (!matches.length) fail(`${relative} missing guarded row ${contract.key}`);
    if (matches.length !== 1) fail(`${relative} guarded row ${contract.key} must appear exactly once after rendered-Markdown normalization; found ${matches.length}`);
    const row = matches[0];
    for (const index of contract.exactUnresolved || []) requireExactCell(relative, row, index, UNRESOLVED, `${contract.key} cell ${index + 1}`);
    for (const index of contract.containsUnresolved || []) requireUnresolvedCell(relative, row, index, `${contract.key} cell ${index + 1}`);
    for (const [index, expected] of Object.entries(contract.exact || {})) requireExactCell(relative, row, Number(index), expected, `${contract.key} cell ${Number(index) + 1}`);
  }
}

function requireCanonicalReferenceStatus(file) {
  const relative = relativePath(file);
  const statusLines = collectStatusDeclarations(fs.readFileSync(file, 'utf8'));
  if (statusLines.length !== 1) fail(`${relative} must contain exactly one canonical Status declaration, including declarations nested in Markdown list/task-list/heading containers; found ${statusLines.length}`);
  const entry = statusLines[0];
  const value = entry.normalized.replace(/^Status\s*:\s*/i, '');
  if (value !== CANONICAL_STATUS) fail(`${relative}:${entry.lineNumber} Status must be exactly "${CANONICAL_STATUS}" after rendered-Markdown normalization; got "${value || '<empty>'}"`);
}

function runBacktickFenceInfoRegressionSelfTest() {
  const rows = extractGfmTableRows(['```text`not-a-fence','','Bone | Purpose | Pivot rule | Runtime dependency','--- | --- | --- | ---','root | live table after invalid opener | live pivot | com.example.FabricatedRenderer'].join('\n'));
  if (rows.length !== 2 || rows[0].cells[0] !== 'Bone' || rows[1].cells[0] !== 'root') fail(`internal invalid-backtick-fence regression self-test expected invalid info-string opener not to mask a live GFM table; found ${rows.length} row(s)`);
}

function runNestedListTableRegressionSelfTest() {
  const rows = extractGfmTableRows(['- nested live contract','','    Bone | Purpose | Pivot rule | Runtime dependency','    --- | --- | --- | ---','    root | nested live duplicate | nested pivot | com.example.FabricatedRenderer'].join('\n'));
  if (rows.length !== 2 || rows[0].cells[0] !== 'Bone' || rows[1].cells[0] !== 'root') fail(`internal nested-list table regression self-test expected a four-space-continued live GFM table to remain visible; found ${rows.length} row(s)`);

  const nestedCodeRows = extractGfmTableRows(['- nested code contract','','      Bone | Purpose | Pivot rule | Runtime dependency','      --- | --- | --- | ---','      root | nested code example | nested pivot | com.example.FabricatedRenderer'].join('\n'));
  if (nestedCodeRows.length !== 0) fail(`internal nested-list code regression self-test expected four spaces relative to list content to remain indented code; found ${nestedCodeRows.length} row(s)`);

  const orderedRows = extractGfmTableRows(['10. ordered live contract','','    Bone | Purpose | Pivot rule | Runtime dependency','    --- | --- | --- | ---','    root | ordered live duplicate | ordered pivot | com.example.FabricatedRenderer'].join('\n'));
  if (orderedRows.length !== 2 || orderedRows[1].cells[0] !== 'root') fail(`internal ordered-list table regression self-test expected W+N-relative indentation to remain visible; found ${orderedRows.length} row(s)`);

  const nestedListRows = extractGfmTableRows(['- outer contract','  - inner contract','','      Bone | Purpose | Pivot rule | Runtime dependency','      --- | --- | --- | ---','      root | deeply nested live duplicate | nested pivot | com.example.FabricatedRenderer'].join('\n'));
  if (nestedListRows.length !== 2 || nestedListRows[1].cells[0] !== 'root') fail(`internal nested-list stack regression self-test expected recursively relative indentation to remain visible; found ${nestedListRows.length} row(s)`);

  const terminatedListCodeRows = extractGfmTableRows(['- terminated list','','','    Bone | Purpose | Pivot rule | Runtime dependency','    --- | --- | --- | ---','    root | post-list code example | code pivot | com.example.FabricatedRenderer'].join('\n'));
  if (terminatedListCodeRows.length !== 0) fail(`internal terminated-list regression self-test expected two blank lines to clear list context before four-space-indented code; found ${terminatedListCodeRows.length} row(s)`);

  const sameLineListFenceRows = extractGfmTableRows(['- ```text','  Bone | Purpose | Pivot rule | Runtime dependency','  --- | --- | --- | ---','  root | list-fenced example | fenced pivot | com.example.FabricatedRenderer','  ```'].join('\n'));
  if (sameLineListFenceRows.length !== 0) fail(`internal same-line list fence regression self-test expected a fence opened on the list-item marker line to hide table-shaped code; found ${sameLineListFenceRows.length} row(s)`);
}

function runTabIndentationRegressionSelfTest() {
  const rows = extractGfmTableRows(['-\tnested live contract','','\tBone | Purpose | Pivot rule | Runtime dependency','\t--- | --- | --- | ---','\troot | tab-indented live duplicate | nested pivot | com.example.FabricatedRenderer'].join('\n'));
  if (rows.length !== 2 || rows[0].cells[0] !== 'Bone' || rows[1].cells[0] !== 'root') fail(`internal tab-indentation regression self-test expected CommonMark tab expansion to preserve a live nested GFM table; found ${rows.length} row(s)`);

  const rootCodeRows = extractGfmTableRows(['\tBone | Purpose | Pivot rule | Runtime dependency','\t--- | --- | --- | ---','\troot | root-level tab-indented code | code pivot | com.example.FabricatedRenderer'].join('\n'));
  if (rootCodeRows.length !== 0) fail(`internal tab-indentation regression self-test expected a root-level tab to remain four-column indented code; found ${rootCodeRows.length} row(s)`);
}

function runTableBlockTerminationRegressionSelfTest() {
  const headingRows = extractGfmTableRows(['Check | Status | Evidence','--- | --- | ---','Geometry | PENDING | UNRESOLVED','## Follow-up |'].join('\n'));
  if (headingRows.length !== 2 || headingRows[0].cells[0] !== 'Check' || headingRows[1].cells[0] !== 'Geometry') fail(`internal table-termination regression self-test expected an ATX heading with a trailing pipe to terminate the live GFM table; found ${headingRows.length} row(s)`);
}

runStatusDeclarationRegressionSelfTest();
runBacktickFenceInfoRegressionSelfTest();
runNestedListTableRegressionSelfTest();
runTabIndentationRegressionSelfTest();
runTableBlockTerminationRegressionSelfTest();

const allFiles = walk(ROOT);
const actualFiles = allFiles.map(relativePath).sort();
const unexpectedFiles = actualFiles.filter((relative) => !EXPECTED_FILES.has(relative));
const missingFiles = [...EXPECTED_FILES].filter((relative) => !actualFiles.includes(relative)).sort();
if (unexpectedFiles.length) fail(`reference-only corpus contains unexpected file(s): ${unexpectedFiles.join(', ')}`);
if (missingFiles.length) fail(`reference-only corpus is missing allowlisted file(s): ${missingFiles.join(', ')}`);

const markdownFiles = allFiles.filter((file) => file.toLowerCase().endsWith('.md'));
if (!markdownFiles.length) fail('no Markdown files found in Golden Samples corpus');
for (const file of markdownFiles) requireCanonicalReferenceStatus(file);

const guardedUnresolvedPrefixes = {
  'model-asset/ASSET-BRIEF.md': ['- Gameplay owner:','- Runtime consumer/class:','- Registry/resource ID:','- Multiplayer authority impact: none in this reference; runtime ownership is','- Production dimensions/scale:','- Real texture file:','- Texel density:','- Exact exporter/plugin version:','- Runtime renderer/controller:','- Export destination:','- VFX provider/API for `spell_muzzle`:'],
  'model-asset/MODEL-CONTRACT.md': ['- Project-owned native `.bbmodel`:','- Real texture source:','- Exported GeckoLib geometry/animation resources:','- Exact provider consumer/API:','- Production cube count/topology:','- Production scale:','- Actual PNG asset:','- Final palette/material separation:','- Final texel density:','- Any future VFX attachment must consume a proven provider-native hook or project bridge; exact hook is','- Blockbench GeckoLib plugin/exporter version:','- Geometry export path:','- Animation export path:','- Renderer/model class:','- Client registration:','- Dedicated-server classloading boundary:'],
  'model-asset/ANIMATION-BRIEF.md': ['- Production amplitude/easing/keyframes:','- Player-hand synchronization:','- Exact keyframes/easing:','- Exact event marker/API linking release to gameplay:','- Animation controller class/API:','- Trigger/network synchronization:','- Client prediction policy:'],
  'spell/SPELL-BRIEF.md': ['- Gameplay owner/mod:','- Runtime spell/ability registry ID:','- Provider-native spell implementation:','- Cast legality:','- Resource/mana cost:','- Cooldown:','- Damage/effect:','- Targeting/range/velocity:','- Hit/miss/block resolution:','- Anti-abuse/deduplication key:','- Real model dependency:','- Real animation dependency:','- Real VFX assets/provider graphs:','- Real audio assets/SoundEvents:','- Selected provider and exact API/hook:'],
  'spell/SPELL-PRESENTATION.md': ['- exact prediction policy is','- exact event/network message/API is','- authoritative projectile/active-state owner is','- interpolation/snapshot policy is','- hit/miss/block/resist/damage owner is','- deduplication/causal event key is','- lifecycle cleanup hooks are','- anticipation cue asset/event:','- release cue asset/event:','- travel loop: optional,','- impact cue asset/event:','- decay tail: optional,','- camera shake: optional and','- crosshair/target lock integration:','- first-person obstruction budget:','- provider selection/API:','- particle count/lifetime/distance culling budgets:','- multiplayer concurrency target:','- fallback when optional provider is absent/incompatible:'],
  'spell/VFX-BRIEF.md': ['- Release/travel authoritative start condition:','- Impact must consume authoritative result evidence; exact event/hook is','- Deduplication token/event identity:','- particle/emitter budgets:','- max visible distance/culling:','- simultaneous caster stress target:','- fallback behavior:'],
  'spell/AUDIO-CUE-SHEET.md': ['- Variant count:','- Pitch randomization:','- Volume:','- Attenuation distance/model:','- Mono/stereo choice:','- Start/loop/end implementation for travel:','A future implementation must prevent duplicate release/impact cues from duplicate network/event delivery. The authoritative event identity and client deduplication mechanism are','Actual audio source/author/license:'],
};
for (const [relative, prefixes] of Object.entries(guardedUnresolvedPrefixes)) for (const prefix of prefixes) requireValueStartsWith(relative, prefix, UNRESOLVED);

const guardedPendingPrefixes = {
  'model-asset/ASSET-BRIEF.md': ['Final visual acceptance remains'],
  'model-asset/MODEL-CONTRACT.md': ['Structural fixture validation can PASS deterministically. Native editor, texture, first-person, third-person, animation playback, lighting, combat, and multiplayer visual acceptance remain'],
  'model-asset/ANIMATION-BRIEF.md': ['- Native Blockbench playback:','- First-person cast readability:','- Third-person cast readability:','- Multiplayer timing against server-confirmed release:'],
  'spell/SPELL-BRIEF.md': ['Structural/document completeness can be validated. In-game spell behavior, multiplayer causality, visual quality, audio mix, and performance remain'],
  'spell/SPELL-PRESENTATION.md': ['No in-game implementation exists in this sample. Editor screenshots, gameplay capture, multiplayer capture, profiler evidence, and audio mix evidence are all'],
  'spell/VFX-BRIEF.md': ['No provider graph/effect file, screenshot, capture, or profiler trace is supplied. Visual/performance acceptance remains'],
  'spell/AUDIO-CUE-SHEET.md': ['No waveform, OGG validation, in-game attenuation test, multiplayer mix test, or loudness evidence exists. Audio QA remains'],
  'spell/VISUAL-QA.md': ['Build success and structural validation are not visual acceptance. Because no real rendered asset/effect is supplied, every visual acceptance item remains'],
};
for (const [relative, prefixes] of Object.entries(guardedPendingPrefixes)) for (const prefix of prefixes) requireValueStartsWith(relative, prefix, PENDING);

requireRowsByKey('model-asset/MODEL-CONTRACT.md', 'Bone', [{key:'root',exactUnresolved:[3]},{key:'cast_hand',exactUnresolved:[3]},{key:'vfx_anchor',exactUnresolved:[3]}]);
requireRowsByKey('spell/VFX-BRIEF.md', 'Candidate', [{key:'Photon 2.2.6.a',exactUnresolved:[2,3]},{key:'AAA Particles 2.2.3',exactUnresolved:[2,3]},{key:'AAA Particles World 2.0.0',exactUnresolved:[2,3]}]);
requireRowsByKey('spell/AUDIO-CUE-SHEET.md', 'Phase', [{key:'Anticipation',exactUnresolved:[3],containsUnresolved:[2,4],exact:{5:PENDING}},{key:'Release',exactUnresolved:[3],containsUnresolved:[4],exact:{5:PENDING}},{key:'Travel',exactUnresolved:[3],containsUnresolved:[4],exact:{5:PENDING}},{key:'Impact',exactUnresolved:[3],containsUnresolved:[4],exact:{5:PENDING}},{key:'Decay',exactUnresolved:[3],exact:{5:PENDING}}]);

for (const [relative, headerKey] of [['spell/VISUAL-QA.md','Check'],['spell/VFX-QA.md','Area'],['spell/AUDIO-QA.md','Check']]) {
  const rows = tableRows(relative).filter((row) => normalizeRenderedText(row.cells[0]) !== normalizeRenderedText(headerKey));
  if (!rows.length) fail(`${relative} has no guarded QA rows`);
  for (const row of rows) { requireExactCell(relative,row,1,PENDING,`${row.cells[0]} status`); requireUnresolvedCell(relative,row,2,`${row.cells[0]} evidence`); }
}

for (const file of markdownFiles) {
  const relative = relativePath(file);
  const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const lineNumber = index + 1;
    if (line.includes('~~')) fail(`${relative}:${lineNumber} uses Markdown strikethrough, which is forbidden in the reference-only corpus because it can visually replace guarded evidence sentinels`);
    const normalizedLine = normalizeRenderedText(line);
    const cells = parseTableRow(line);
    if (cells) for (const cell of cells) { const normalizedCell = normalizeRenderedText(cell); if (/^PASS\b/i.test(normalizedCell)) fail(`${relative}:${lineNumber} claims unsupported table status "${normalizedCell}"`); }
    const colonStatus = normalizedLine.match(/:\s*PASS\b[^\n]*/i); if (colonStatus) fail(`${relative}:${lineNumber} claims unsupported acceptance status "${colonStatus[0]}"`);
    const namedStatus = normalizedLine.match(/\b(?:status|state|result|resultado|acceptance|aceita(?:ç|c)[aã]o)\s*=\s*PASS\b[^\n]*/i); if (namedStatus) fail(`${relative}:${lineNumber} claims unsupported named status "${namedStatus[0]}"`);
    const proseAcceptance = normalizedLine.match(/\b(?:acceptance|aceita(?:ç|c)[aã]o|qa)\b(?:\s+\S+){0,6}\s+(?:(?:has|have|had)\s+been|remains?|remained|remain|is|are|was|were|permanece|continuam?|continuou|continuaram|fica|ficou|continua)\s+PASS\b/i); if (proseAcceptance) fail(`${relative}:${lineNumber} claims unsupported prose acceptance "${proseAcceptance[0]}"`);
  }
}

console.log(`OK: Golden Samples evidence gate scanned exactly ${actualFiles.length} allowlisted file(s), required one canonical REFERENCE-ONLY Status per Markdown document, normalized rendered block-container labels/statuses/entities/escapes, enforced unique scalar/table guards within actual non-code GFM table blocks (including CommonMark tab-expanded/list-relative indentation, padded short rows, and block-construct table termination), and found no unsupported PASS-form acceptance claim`);
