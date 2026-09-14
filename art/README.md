# Art production — Minecraft Mod Factory

This domain contains reusable visual-production capability for Minecraft projects.

## Ownership boundary

- **Factory**: art-direction skills, generic asset/model/VFX/audio standards, reusable templates, validators, Blockbench/tooling workflows and regression tests.
- **Consumer repository**: project-specific visual direction, provider/runtime evidence, per-entity briefs, manifest/configuration data and the actual project-owned assets.
- **Narrative consumer**: canon and appearance decisions approved by that campaign's own authorities.

Do not copy generic Factory validators or production contracts into a consumer campaign/story tree. If a reusable capability is missing, add it here and let the consumer pin/consume the Factory revision.

Conversely, do not move a consumer's NPC portraits, skins, lore-specific briefs, faction symbols or other campaign-owned assets into the Factory merely because Factory tooling validates them.

## NPC portraits and skins

Use:

- `standards/NPC-VISUAL-ASSET-CONTRACT.md` for the reusable ownership/provenance contract;
- `skills/minecraft-asset-art-direction/SKILL.md` for art-direction workflow;
- `tooling/validate_npc_visual_assets.py` to validate a consumer-owned manifest.

Example consumer invocation:

```bash
python3 .factory/art/tooling/validate_npc_visual_assets.py \
  --manifest path/to/consumer/npc-assets/manifest.json \
  --repo-root .
```

The consumer manifest supplies its own resolution/format policy. The Factory does not impose one campaign's portrait dimensions, provider, names or canon globally.

## Finality

Passing a structural validator proves only the checks implemented by that validator. It does not replace provider validation, in-game visual QA, licensing/provenance review or campaign approval.
