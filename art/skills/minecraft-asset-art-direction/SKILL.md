---
name: minecraft-asset-art-direction
description: Use when creating, redesigning, reviewing, or specifying Minecraft visual assets that must match the project's established style, including mobs, items, blocks, armor, spell constructs, icons, textures, and model concepts.
source: project-authored-2026-09-07
project_status: preferred
---
# Minecraft Asset Art Direction

## Core principle

Do not start final geometry or texture work from a vague prompt. Establish the visual contract first, then preserve it through modeling, texturing, animation, integration, and in-game review.

## Authority order

1. physical/current project assets and the latest physical modlist;
2. `docs/art/VISUAL-STYLE-BIBLE.md`, approved project art direction and nearby canonical assets;
3. provider-native visual language when an integration must visually belong to that provider;
4. concept references and generated images;
5. generic Minecraft conventions.

If these disagree, report the conflict. Do not average incompatible styles silently.

## Required asset contract

Before final production, record:

- gameplay role and viewing distance;
- silhouette and proportions;
- world/player scale;
- palette, materials, surface age and contrast hierarchy;
- texture resolution and intended texel density **with project/reference evidence**;
- emissive/translucent/animated regions, if any;
- model type and expected render contexts;
- required bones/attachment points when animation or VFX needs them;
- animation list with purpose, loop policy and readable poses;
- provider/style references that are allowed to influence the asset;
- performance constraints and LOD/complexity assumptions when relevant;
- acceptance views: front, side, back, three-quarter and in-game scale;
- provenance/licensing and unresolved visual compromises.

Use `standards/MODEL-ASSET-CONTRACT.md` as the canonical contract and the reusable `templates/ASSET-BRIEF.md`, `MODEL-BRIEF.md` and `ANIMATION-BRIEF.md` as appropriate.

## Workflow

1. Read `../../../../docs/art/VISUAL-STYLE-BIBLE.md` and `../../VISUAL-STYLE-SOURCES.md`.
2. Inspect existing project assets before inventing a new visual language.
3. Produce the asset contract/brief.
4. Use `minecraft-imagegen` only for concept/look-dev or reference sheets when useful; generated art is not automatically a final texture, UV, rig, or model.
5. Convert the approved visual intent into explicit model/texture requirements.
6. For Blockbench or GeckoLib work, use `minecraft-blockbench-geckolib`.
7. Run `art/tooling/blockbench/asset-toolkit/asset_toolkit.js` for structural/contract validation; preserve the legacy validator only for compatibility.
8. Perform in-game review with `minecraft-visual-qa` and `standards/VISUAL-QA.md`.
9. Record unresolved visual compromises instead of declaring the asset finished.

## Hard gates

- No final asset from concept art alone.
- No texture style chosen without checking the Visual Style Bible and neighboring canonical assets.
- No universal texture resolution or texel density invented without measured evidence.
- No emissive/glow used as a substitute for material definition.
- No animation accepted solely because it exports; silhouette, timing, clipping and gameplay readability must be reviewed.
- No provider-specific aesthetic copied into a project-owned asset without deciding whether the asset is actually meant to belong to that provider.
- No third-party visual copied without compatible provenance/licensing.

If the user must operate Blockbench or another GUI, follow `../../USER-GUIDED-WORKFLOW.md`: give exactly one manual action, ask for the visible result, then continue.
