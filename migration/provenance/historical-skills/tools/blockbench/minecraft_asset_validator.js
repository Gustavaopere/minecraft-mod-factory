(() => {
  'use strict';

  let auditAction = null;

  function addIssue(issues, severity, code, message) {
    issues.push({ severity, code, message });
  }

  function finiteVector3(value) {
    return Array.isArray(value)
      && value.length >= 3
      && value.slice(0, 3).every(Number.isFinite);
  }

  function isPowerOfTwo(value) {
    return Number.isInteger(value) && value > 0 && (value & (value - 1)) === 0;
  }

  function validateProject(project) {
    const issues = [];
    if (!project || typeof project !== 'object') {
      addIssue(issues, 'error', 'NO_PROJECT', 'No Blockbench model project is open.');
      return issues;
    }

    const groups = Array.isArray(project.groups) ? project.groups : [];
    const elements = Array.isArray(project.elements) ? project.elements : [];
    const textures = Array.isArray(project.textures) ? project.textures : [];
    const animations = Array.isArray(project.animations) ? project.animations : [];

    if (elements.length > 0 && groups.length === 0) {
      addIssue(issues, 'warning', 'NO_GROUPS',
        'Model has elements but no groups/bones. Animated GeckoLib assets should have an intentional hierarchy.');
    }

    const groupNames = new Map();
    for (const group of groups) {
      const name = typeof group?.name === 'string' ? group.name.trim() : '';
      if (!name) {
        addIssue(issues, 'error', 'EMPTY_BONE_NAME', 'A group/bone has no name.');
      } else {
        const canonical = name.toLowerCase();
        if (groupNames.has(canonical)) {
          addIssue(issues, 'error', 'DUPLICATE_BONE_NAME',
            `Duplicate group/bone name: "${name}".`);
        } else {
          groupNames.set(canonical, group);
        }
        if (!/^[a-z0-9_]+$/.test(name)) {
          addIssue(issues, 'warning', 'BONE_NAME_STYLE',
            `Bone "${name}" is not lower_snake_case. Project convention prefers stable lower_snake_case names.`);
        }
      }

      if (!finiteVector3(group?.origin)) {
        addIssue(issues, 'error', 'INVALID_BONE_PIVOT',
          `Bone "${name || '<unnamed>'}" has a non-finite or malformed origin/pivot.`);
      }
    }

    for (const element of elements) {
      if (!element || !Array.isArray(element.from) || !Array.isArray(element.to)) {
        continue;
      }
      if (!finiteVector3(element.from) || !finiteVector3(element.to)) {
        addIssue(issues, 'error', 'INVALID_ELEMENT_BOUNDS',
          `Element "${element.name || '<unnamed>'}" has malformed from/to bounds.`);
        continue;
      }
      const size = [0, 1, 2].map((axis) => element.to[axis] - element.from[axis]);
      if (size.some((value) => value < 0)) {
        addIssue(issues, 'error', 'NEGATIVE_ELEMENT_SIZE',
          `Element "${element.name || '<unnamed>'}" has negative size on at least one axis.`);
      } else if (size.some((value) => value === 0)) {
        addIssue(issues, 'warning', 'ZERO_ELEMENT_SIZE',
          `Element "${element.name || '<unnamed>'}" has zero thickness on at least one axis.`);
      }
    }

    if (elements.length > 0 && textures.length === 0) {
      addIssue(issues, 'error', 'NO_TEXTURES',
        'Model has renderable elements but no project texture.');
    }

    for (const texture of textures) {
      const name = typeof texture?.name === 'string' && texture.name.trim()
        ? texture.name.trim()
        : '<unnamed>';
      const width = texture?.width;
      const height = texture?.height;

      if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
        addIssue(issues, 'error', 'INVALID_TEXTURE_SIZE',
          `Texture "${name}" has invalid dimensions.`);
        continue;
      }
      if (!isPowerOfTwo(width) || !isPowerOfTwo(height)) {
        addIssue(issues, 'warning', 'NON_POWER_OF_TWO_TEXTURE',
          `Texture "${name}" is ${width}x${height}. Power-of-two dimensions are the project default unless a provider requires otherwise.`);
      }
    }

    for (const animation of animations) {
      const name = typeof animation?.name === 'string' ? animation.name.trim() : '';
      if (!name) {
        addIssue(issues, 'error', 'EMPTY_ANIMATION_NAME', 'An animation has no name.');
      }
      if (!Number.isFinite(animation?.length) || animation.length <= 0) {
        addIssue(issues, 'warning', 'INVALID_ANIMATION_LENGTH',
          `Animation "${name || '<unnamed>'}" has zero, negative, or non-finite length.`);
      }
      if (!['once', 'hold', 'loop'].includes(animation?.loop)) {
        addIssue(issues, 'warning', 'UNKNOWN_LOOP_MODE',
          `Animation "${name || '<unnamed>'}" has unexpected loop mode "${animation?.loop}".`);
      }
    }

    return issues;
  }

  function formatReport(issues) {
    if (issues.length === 0) {
      return 'PASS — no structural issues detected by the project validator. Visual QA is still required in-game.';
    }

    const errors = issues.filter((item) => item.severity === 'error').length;
    const warnings = issues.length - errors;
    const lines = issues.slice(0, 40).map(
      (item) => `[${item.severity.toUpperCase()}] ${item.code}: ${item.message}`
    );
    if (issues.length > 40) {
      lines.push(`... ${issues.length - 40} additional issue(s) omitted.`);
    }

    return `Structural QA found ${errors} error(s) and ${warnings} warning(s).\n\n${lines.join('\n')}\n\nThis validator does not replace visual/in-game review.`;
  }

  Plugin.register('minecraft_asset_validator', {
    title: 'Minecraft Asset Validator',
    author: 'Gustavaopere',
    description: 'Read-only structural QA for Minecraft and GeckoLib Blockbench projects.',
    icon: 'fact_check',
    version: '0.1.0',
    variant: 'both',
    onload() {
      auditAction = new Action('minecraft_asset_validator_run', {
        name: 'Validate Minecraft Asset',
        description: 'Run project structural checks without modifying the model.',
        icon: 'fact_check',
        click() {
          const issues = validateProject(Blockbench.Project);
          const hasErrors = issues.some((item) => item.severity === 'error');
          Blockbench.showMessageBox({
            title: 'Minecraft Asset Validator',
            icon: hasErrors ? 'error' : 'check_circle',
            message: formatReport(issues),
            buttons: ['OK']
          });
        }
      });
      MenuBar.menus.tools.addAction(auditAction);
    },
    onunload() {
      if (auditAction) {
        auditAction.delete();
        auditAction = null;
      }
    }
  });
})();