---
name: minecraft-blockbench-geckolib
description: Use when creating, editing, exporting, or reviewing Blockbench models, UVs, rigs, animations, or GeckoLib-backed Minecraft assets for the NeoForge 1.21.1 project.
source: project-authored-2026-09-07
project_status: preferred
---
# Minecraft Blockbench + GeckoLib

## Target authority

This project targets Minecraft 1.21.1, NeoForge 21.1.x, and Java 21. Confirm the exact installed GeckoLib version from the current physical modlist/build before implementation. For Minecraft 1.21.1, use the GeckoLib 4 API family; do not transplant GeckoLib 5 patterns from 1.21.5+.

Blockbench with the GeckoLib plugin is the canonical authoring path for GeckoLib model and animation JSON. Keep the `.bbmodel` source under project control whenever the asset is project-owned.

## Production flow

1. Read `minecraft-asset-art-direction`, the Visual Style Bible and the applicable model/animation briefs first.
2. Create or convert a `GeckoLib Animated Model` project only when GeckoLib is actually the chosen renderer.
3. Establish hierarchy before animation: stable bone names, intentional parenting, correct pivots, and attachment points required by held items/VFX.
4. UV and texture deliberately. Preserve consistent texel density derived from project evidence; do not stretch a concept image over geometry or invent a global density constant.
5. Create animations from named gameplay states/poses. Decide whether each animation is `once`, `hold`, or `loop` intentionally.
6. Preserve the `.bbmodel`; export provider-appropriate model/animation resources and textures.
7. Run `../../tooling/blockbench/asset-toolkit/asset_toolkit.js` inside Blockbench for structural checks.
8. When the asset contract defines required bones/animations or maximum bounds, use the Toolkit contract-profile action.
9. Perform in-game visual QA with `minecraft-visual-qa`; Toolkit PASS is not proof of visual quality.

## Structural checks

Treat these as release blockers when applicable:

- duplicate/empty bone names;
- parent cycles;
- malformed pivots or bounds;
- enabled faces with unresolved textures or malformed UVs;
- invalid export paths;
- missing required attachment bones;
- missing contract-required animations;
- animations with wrong loop semantics;
- clipping that affects intended gameplay poses;
- client rendering code referenced from dedicated-server paths.

Warnings that require review rather than blind rejection include non-power-of-two textures, zero-thickness geometry, unusual bone naming, unusually large texture budgets, or intentionally unconventional pivots.

## GeckoLib integration rule

Verify actual GeckoLib 4 classes/methods/signatures against the installed dependency or source before writing Java. The normal resource responsibilities are model geometry, texture, and animation resources, but exact code must follow the version in this repository. GeckoLib animation keyframes can participate in sound/particle/custom-effect timing, but do not invent handler signatures: inspect the current API first.

## QA evidence

A completed model task should identify:

- source `.bbmodel`;
- exported resource paths;
- texture dimensions and texel-density evidence;
- bone/attachment contract;
- animation names and loop policy;
- Toolkit result/profile used;
- in-game screenshots or explicit PENDING visual review;
- dedicated-server/client separation when Java integration changed.

If the user must click through Blockbench, follow `../../USER-GUIDED-WORKFLOW.md` and provide one manual action at a time.
