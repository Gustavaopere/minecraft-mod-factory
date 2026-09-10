---
name: minecraft-visual-qa
description: Use when accepting, rejecting, comparing, or regression-testing Minecraft models, textures, animations, VFX, spells, UI, icons, emissives, or other visual presentation in real game contexts.
source: project-authored-2026-09-08
project_status: preferred
---
# Minecraft Visual QA

## Core principle

Build success and editor preview are not visual acceptance. Validate the asset/system in the real Minecraft contexts where players will see it and keep structural, aesthetic, causal and performance evidence separate.

## Required sources

- `../../../../docs/art/VISUAL-STYLE-BIBLE.md` for project visual language;
- `../../standards/VISUAL-QA.md` for model/texture/animation baseline;
- `../../standards/VFX-QA.md` for VFX lifecycle/multiplayer/performance;
- `../../standards/AUDIO-QA.md` when sound is part of the presentation;
- `../../templates/VISUAL-QA.md` for evidence capture.

## Model/texture acceptance

Review applicable contexts:

- front/back/left/right/three-quarter;
- real in-game scale;
- bright and dark lighting;
- first- and third-person;
- GUI/ground/frame/held contexts;
- neighboring canonical assets;
- shader-on and a non-shader/degraded context when shader dependency would hide readability problems.

## Animation acceptance

Check silhouette, anticipation, timing, impact alignment, clipping, loop seams, first-/third-person behavior and coexistence with installed animation systems. A visually late/early hit is a defect even if the underlying server damage is correct, because presentation is misleading.

## VFX acceptance

Check near/far, hit/miss/cancel, multiple simultaneous instances, multiplayer viewers, interruption/cleanup, low-effects path when supported, dark/day scenes and performance under expected concurrency.

## Result vocabulary

- **PASS** — required evidence exists and no release-blocking issue remains;
- **FAIL** — known acceptance gate violated;
- **PENDING** — evidence cannot yet be produced (for example, in-game screenshot/manual Blockbench step still required).

Never convert PENDING into PASS by assumption.

## Manual workflow

When the user must operate Blockbench/Minecraft/another GUI, apply `../../USER-GUIDED-WORKFLOW.md`: one manual action, verify the result, then advance.
