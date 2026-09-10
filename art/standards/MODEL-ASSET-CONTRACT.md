# Canonical Model Asset Contract

Use this before producing a final project-owned visual asset. Unknown fields remain `UNRESOLVED`; do not invent them.

## Identity

- Asset ID:
- Gameplay role:
- Owning mod/system:
- Provider-native or project-owned:
- Intended render contexts:
- Typical viewing distance:

## Visual language

- Canonical neighboring assets/references:
- Silhouette description:
- Proportion rules:
- World/player scale:
- Primary palette:
- Secondary/accent palette:
- Materials/surface treatment:
- Contrast/readability hierarchy:
- Wear, damage, age, dirt, magical/technical motifs:
- Forbidden visual motifs:

## Texture contract

- Texture dimensions:
- Target texel density:
- UV mode/constraints:
- Alpha/translucency:
- Emissive regions:
- Animated texture regions:
- Tileability/seams requirements:

## Model contract

- Authoring format (`.bbmodel` unless provider requires otherwise):
- Runtime model format:
- Required hierarchy/bones:
- Required attachment points:
- Pivot requirements:
- Geometry/complexity budget:
- Collision/hitbox relationship, if applicable:

## Animation contract

For every animation record:

- name;
- gameplay purpose;
- start/readable/end pose;
- duration target;
- `once` / `hold` / `loop` intent;
- cancel/interruption behavior;
- VFX/SFX timing markers, if any;
- locomotion or held-item constraints.

## Integration and acceptance

- Runtime/provider version verified from:
- Expected resource paths:
- Client/server constraints:
- Required VFX anchors:
- Required screenshots: front / side / back / 3/4 / in-game scale.
- Required animation clips for review:
- Performance acceptance:
- Known unresolved items:

An asset is not approved because it exports. Approval requires structural validation plus the visual checks in `VISUAL-QA.md`.