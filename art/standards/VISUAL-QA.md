# Visual QA — Minecraft Assets

Structural validity is necessary but insufficient. Review the rendered asset in the contexts where players will actually see it.

## 1. Silhouette and scale

- recognizable at intended gameplay distance;
- proportions match the asset contract;
- no accidental tiny/oversized details;
- relative scale checked against player, blocks, held items, mobs, or provider assets as applicable.

## 2. Texture and materials

- texel density is coherent across visible surfaces;
- UV seams do not create unintended discontinuities;
- materials read as different materials, not only different colors;
- highlights/shadows are not baked in a way that fights Minecraft lighting unless intentionally stylized;
- emissive/translucent regions remain subordinate to the intended focal hierarchy;
- palette fits nearby canonical assets.

## 3. Rig and animation

- hierarchy and pivots produce intended arcs;
- idle does not look frozen or excessively noisy;
- loop transitions do not visibly jump;
- attack/cast/tool-use poses have readable anticipation, action and recovery when applicable;
- limbs, armor, held items and attachments do not clip in expected poses;
- animation timing communicates gameplay before decorative motion is added.

## 4. VFX and attachment readiness

- required anchors/bones exist and remain stable;
- projectile, beam, trail, hand, weapon, head or ground anchors are semantically named;
- effects do not hide the model's key silhouette unless that is intentional;
- visual effect scale remains correct in first/third person and world space where applicable.

## 5. Render contexts

Check only contexts the asset actually supports:

- world/entity;
- inventory/GUI;
- dropped item;
- first person;
- third person;
- armor/body;
- block/entity renderer;
- multiplayer observation by another client.

## 6. Performance and robustness

- complexity matches expected on-screen count;
- texture budget is justified by viewing distance;
- animation/VFX do not create unbounded per-tick work;
- missing optional provider fails safely;
- no client-only asset integration is loaded on dedicated server.

## Acceptance evidence

Record validator output plus screenshots or captures sufficient to judge front, side, back, three-quarter and in-game scale. For animated assets, include the clips/poses that exercise the contract. If visual evidence is unavailable, status is `PENDING VISUAL QA`, not complete.