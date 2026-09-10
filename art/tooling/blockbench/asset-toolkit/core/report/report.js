'use strict';

function formatReport(result) {
  const lines = [`Structural QA: ${result.errors.length} error(s), ${result.warnings.length} warning(s).`];
  if (result.bounds) lines.push(`Bounds span: ${result.bounds.span.join(' x ')}.`);
  if (result.counts) lines.push(`Bones: ${result.counts.groupCount || 0}; elements: ${result.counts.elementCount || 0} (cubes: ${result.counts.cubeCount || 0}, locators: ${result.counts.locatorCount || 0}); textures: ${result.counts.textureCount || 0}; animations: ${result.counts.animationCount || 0}.`);
  const limited = result.issues.slice(0, 50);
  for (const item of limited) lines.push(`[${item.severity.toUpperCase()}] ${item.code}: ${item.message}`);
  if (result.issues.length > limited.length) lines.push(`... ${result.issues.length - limited.length} additional issue(s) omitted.`);
  lines.push('Texel-density/aesthetic approval still requires the asset contract and in-game visual QA.');
  return lines.join('\n');
}

module.exports = {formatReport};
