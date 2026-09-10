# Blockbench tools

## Preferred — Minecraft Mod Factory Asset Toolkit

Use `asset-toolkit/asset_toolkit.js` for new project-owned model work. It adds parent-cycle detection, face/UV validation and optional asset-contract profiles (`requiredBones`, `requiredAnimations`, `maxSpan`) while remaining read-only. Its pure validation logic has Node regression tests executed by the repository skill validator.

See `asset-toolkit/README.md`.

## Legacy — Minecraft Asset Validator

`minecraft_asset_validator.js` is retained as the first-generation internal, read-only Blockbench structural QA plugin. It does not generate models, rewrite UVs, fix pivots, or decide whether an asset looks good.

### Verified API surface

The implementation intentionally uses a small Blockbench API surface documented by the official Blockbench wiki/reference:

- `Plugin.register(...)` for plugin lifecycle;
- `Action` for the validation command;
- `MenuBar.menus.tools.addAction(...)` to expose the command;
- `Blockbench.Project` as the current model project;
- `Blockbench.showMessageBox(...)` for the report.

Project data inspected is limited to documented model-project fields such as groups, elements, textures and animations.

### Legacy checks

Errors:

- no open project;
- empty or duplicate bone/group names;
- malformed/non-finite bone pivots;
- malformed or negative element bounds;
- renderable geometry without a texture;
- invalid texture dimensions;
- unnamed animations.

Warnings:

- model elements without an intentional group/bone hierarchy;
- bone names outside project `lower_snake_case` convention;
- zero-thickness geometry;
- non-power-of-two textures;
- zero/non-finite animation length;
- unexpected animation loop mode.

Warnings are review items, not automatic rejection. Provider-specific formats may justify exceptions.

## Manual use

Do not dump a multi-step installation tutorial on the user. Apply `../../USER-GUIDED-WORKFLOW.md`.

When installation is actually needed, the first action is only: open Blockbench's plugin interface so the local plugin can be side-loaded. Ask for the visible result before giving the next action.

## Validation boundary

A PASS from either plugin means only that its listed structural checks passed. Final acceptance still requires `../../library/minecraft-visual-qa/SKILL.md`, the relevant standards, and in-game evidence.

## Upstream references checked 2026-09-08

- Blockbench plugin guide: https://blockbench.net/wiki/docs/plugin/
- Blockbench generated API reference: https://web.blockbench.net/docs/
- Blockbench UI API: https://blockbench.net/wiki/docs/ui/
- GeckoLib Blockbench model guide: https://github.com/bernie-g/geckolib/wiki/Making-Your-Models-%28Blockbench%29
- GeckoLib 4 documentation: https://wiki.geckolib.com/docs/geckolib4/
