# NPC visual asset contract

## Scope

This standard defines reusable production and validation rules for NPC portraits, concept art and humanoid skins. It belongs to the Factory because it is workflow/tooling, not campaign canon.

Consumer repositories own:

- the NPC identity and lore;
- project-specific art direction;
- provider/runtime evidence;
- target portrait dimensions and formats;
- skin/model requirements;
- actual visual assets and their manifest data.

The Factory must not hard-code one consumer project's NPC names, repository paths, providers, resolutions or canon.

## Separation of artifacts

Portrait/concept and Minecraft skin are different artifacts.

- Portrait/concept communicates identity, face, silhouette, materials and art direction.
- Skin is a technical texture for a proven humanoid renderer/provider.
- A portrait must never be cropped/downscaled and treated as a final skin automatically.
- Generated concept art is look-dev until a consumer project explicitly approves it.

## Production states

Recommended state vocabulary:

1. `LOOK-DEV` — visual exploration; not approved.
2. `CANDIDATE` — versioned visual candidate under review.
3. `APPROVED MASTER` — approved portrait/concept master satisfying the consumer policy.
4. `SKIN CANDIDATE` — technical skin ready for provider/in-game QA.
5. `FINAL` — approved and validated in its actual render path.

A consumer may use a stricter subset, but validation must remain explicit and machine-readable.

## Consumer manifest

A consumer may keep a JSON manifest next to its project-owned assets. The reusable validator is:

`art/tooling/validate_npc_visual_assets.py`

The manifest owns project-specific policy. The validator owns only generic checks.

Recommended top-level shape:

```json
{
  "schema_version": 1,
  "asset_root": "path/to/project/assets/npcs",
  "policy": {
    "portrait_master": {
      "width": 2048,
      "height": 2048,
      "format": "PNG",
      "require_native_target_resolution": true
    },
    "humanoid_skin": {
      "width": 64,
      "height": 64,
      "format": "PNG"
    }
  },
  "assets": []
}
```

The numeric values above are examples, not Factory defaults. The consumer must derive them from its own visual/runtime requirements.

## Minimum asset record

Each entry should record enough provenance to prevent a preview or transformed derivative from being silently promoted:

- stable project entity ID when available;
- asset kind (`portrait`, `skin`, or another consumer-defined kind);
- production status;
- repository-relative path;
- measured width and height;
- actual format;
- SHA-256;
- whether the target resolution is native;
- relevant transformations such as crop, resize, upscale or lossy compression;
- whether the file is final;
- notes/limitations when useful.

## Generic validation gates

The Factory validator checks, when fields are present:

- schema version and basic manifest shape;
- path confinement beneath `asset_root`;
- file existence;
- SHA-256 equality;
- measured image dimensions and detected format;
- allowed production states;
- `final_asset=true` only with `status=FINAL`;
- approved/final portraits against the consumer's `policy.portrait_master`;
- skin candidates/finals against the consumer's `policy.humanoid_skin`.

The validator must not infer a portrait resolution, skin layout, provider or renderer when the consumer does not declare one.

## Canon boundary

Visual tooling does not create narrative facts.

A generated scar, symbol, species cue, costume element, age cue, magical effect or equipment choice remains look-dev until accepted by the consumer project's narrative authority. Likewise, a lore document cannot prove that a renderer supports emissive layers, custom geometry, outer-layer depth or animation.

## Provider boundary

Technical skin/model requirements come from the real render path and current provider evidence. Generic Factory examples are not proof that a consumer can use a feature.

If the provider changes, revalidate the technical asset contract before marking a skin/model final.

## Grimoire and external campaign tools

An external campaign tool may display project-owned art, but its image field is a presentation reference unless the consumer explicitly declares otherwise. It does not become authority for the technical skin/model by default.

## Repository ownership rule

- reusable standards, validators, templates and skills -> Factory;
- campaign lore, NPC-specific briefs, project-specific manifest data and actual campaign art -> consumer repository;
- runtime/provider-specific facts -> consumer repository or provider documentation according to that project's authority model.
