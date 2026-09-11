# Minecraft Mod Factory Asset Toolkit for Blockbench

Standalone project plugin: `asset_toolkit.js` (plugin ID `rpg_asset_toolkit`).

## Scope

Structural/contract QA plus fail-closed provider/extension capability resolution for project-owned Minecraft assets, with narrowly bounded local Blockbench mutations where an audited contract exists. Mutation support is intentionally incremental: it does not authorize arbitrary geometry, UV, texture, pivot or provider-specific animation rewrites, and it does not install or invoke arbitrary extensions.

The Toolkit currently includes the bounded PR3 modeling/rig surface, the PR4 UV/texture surface, and the PR5 Generic Animation Core. PR5 adds provider-neutral animation and keyframe CRUD, loop/easing/duration controls, abstract effect-marker contracts, preview, pose inspection, deterministic capture, loop-seam validation, and foot-slide diagnostics when measurable. Provider-specific animation serialization/export remains outside the generic core.

All mutation capabilities are local desktop operations. They do not add a Live Bridge/MCP write surface.

## Architecture

Canonical source lives in modular CommonJS files under `core/` and `blockbench-plugin/`. `build_toolkit_bundle.js` generates the standalone `asset_toolkit.js` consumed by Blockbench. CI requires the committed standalone bundle to match the modular source byte-for-byte.

Core modules include:

- `project-model` — safe model predicates and bounds;
- `mutations/mutation_engine` — bounded modeling/rig mutation contract;
- `animation/animation_engine` — provider-neutral animation contract, diagnostics, preview/pose/capture adapter boundary;
- `validator` — structural/contract validation;
- `contract-profile` — profile JSON parsing;
- `report` — deterministic read-only reports;
- `extension-registry` — exact extension identity/version/compatibility/MCP authorization;
- `provider-profile` — physical provider snapshot plus fail-closed profile resolution;
- `uv-texture/uv_texture_engine` — bounded declarative UV/texture mutation contract and pixel budget;
- `uv-texture/uv_pack` — bounded revision-bound UV pack preview/apply contract;
- `blockbench-plugin/modeling_adapter.js` — Blockbench modeling/rig transactional adapter;
- `blockbench-plugin/uv_texture_adapter.js` — Blockbench UV/texture inspection and bounded transactional mutation adapter;
- `blockbench-plugin/animation_adapter.js` — desktop-local generic animation/keyframe adapter with provider-bound effect-marker serialization rejected fail-closed;
- `blockbench-plugin/plugin_adapter.js` — verified UI integration.

Canonical policy documents:

- `../../../standards/BLOCKBENCH-EXTENSION-POLICY.md`;
- `../../../standards/ASSET-PROVIDER-PROFILES.md`.

## Source-audited Blockbench API surface

The Toolkit code and tests are aligned to the following Blockbench surfaces that were verified against upstream source/type declarations during PR5 development:

- `Plugin.register(...)`;
- `Action`;
- `MenuBar.menus.tools.addAction(...)`;
- `Blockbench.Project`;
- `Blockbench.showMessageBox(...)`;
- `Blockbench.textPrompt(...)`;
- `Texture.fromDataURL(...)`;
- `Texture.fromFile(...)`;
- `Texture.add(...)`;
- `Animation` construction plus `add`, `remove`, `setLength`, `setLoop`, `select`, `getBoneAnimator`, and playback state;
- bone animator `addKeyframe(...)` plus keyframe removal;
- `Animator.preview(...)` and default-pose reset;
- `Preview.selected.loadAnglePreset(...)` with `DefaultCameraPresets`;
- `Screencam.screenshotPreview(...)`;
- Undo aspects for `animations` and `keyframes`.

The bounded UV/texture adapter additionally uses the project texture/cube state, texture canvas `getImageData(...)` / `putImageData(...)`, and Blockbench Undo transaction surface behind the adapter boundary. Tests exercise begin/finish/cancel transaction behavior and bitmap/UV/texture mutation semantics without exposing those mutations through Live Bridge/MCP.

PR5 tests exercise the same transaction boundary for animations/keyframes using a controlled Blockbench test double. This is not a claim that a physical installed Blockbench instance has completed a real animation/edit/capture smoke in this PR.

A separate Toolkit file-picker action is not part of the declarative `texture_import_approved` contract and is not claimed as a current PR4 requirement. Approved local file data remains behind the opaque desktop-adapter approval boundary; declarative payloads do not carry filesystem paths.

References: https://blockbench.net/wiki/docs/plugin/ · https://blockbench.net/wiki/docs/ui/ · https://web.blockbench.net/docs/

## Provider/extension rules

Installed is not equivalent to compatible, trusted or MCP-authorized. Required extensions must match the audited exact plugin version, pass the Blockbench compatibility gate and be explicitly session-allowlisted. Blocked/human-only/audit-required paths fail closed. Cross-profile conversion is denied unless a later audited adapter exists.

The executable snapshot follows the current physical modlist authority: GeckoLib 4.9.2, AzureLib 3.1.11 and Entity Model Features 3.3.5 are represented as provider requirements where applicable; current Blockbench catalog pins are maintained separately in the extension registry.

Generic animation is deliberately provider-neutral. GeckoLib, AzureLib, EMF/CEM or another provider adapter is responsible for its own serialization/export contract. PR5 does not silently translate generic animation data into any provider format.

## Checks

Errors include no project; empty/duplicate bone names; malformed pivots; parent cycles; malformed/negative **cube** bounds; malformed Locator positions; enabled cube face with unresolved texture; malformed cube-face UV; invalid texture dimensions; empty/duplicate animation names; missing required contract bones/animations; and profile-specific `maxSpan` overflow.

Warnings include unsaved/non-`.bbmodel` source; naming deviations; zero-thickness cube geometry; ungrouped cubes/Locators; non-power-of-two textures; duplicate texture/element names; invalid animation length/loop mode; unknown animator target UUID.

### Cube x Locator semantics

Blockbench/GeckoLib Locators are attachment/VFX points, not renderable cubes. The Toolkit therefore applies cube bounds/face/UV/texture checks only to cube-like elements and validates Locator positions separately as `INVALID_LOCATOR_POSITION`.

## Contract profile

The Tools-menu contract action accepts JSON such as:

```json
{
  "requiredBones": ["root", "vfx_anchor"],
  "requiredAnimations": ["animation.example.idle", "animation.example.attack"],
  "maxSpan": [16, 32, 16]
}
```

`maxSpan` is **asset-specific contract data**, not a universal project budget.

## Bounded UV pack preview/apply

The initial PR4 pack contract is deliberately narrow:

- scope is one texture at a time (`scope: "texture"`);
- target faces must use per-face cube UVs; Box UV is rejected by this slice;
- preview is deterministic and mutation-free;
- preview is bound to `expectedRevision` and returns the before-revision, atlas plan, old/new UVs, source/destination pixel regions, copied-pixel count and a confirmation token;
- invalid confirmation fails before preflight or Undo;
- apply revalidates the revision-bound preview and requires its exact confirmation token;
- source bitmap regions are buffered before the first destination write, so overlapping source/destination moves preserve original pixels;
- apply uses one transaction and publishes the changed texture/UV state once;
- successful mutation must advance the project revision;
- face-count and copied-pixel budgets are bounded and fail closed;
- no resize, arbitrary global painting, generic global repack or remote Live Bridge/MCP write is introduced by this slice.

## Bounded texture create/import

The current create/import contract is also deliberately narrow:

- `texture_create` accepts only an explicit texture name plus positive integer width/height and creates an internal texture through Blockbench's native texture APIs;
- create operations are charged against the existing per-batch pixel budget;
- texture-name collisions fail closed case-insensitively during preflight;
- `texture_import_approved` accepts only an opaque approval id in the declarative mutation payload; filesystem paths are not accepted by the contract;
- local file data is registered inside the desktop adapter behind an ephemeral approval id whose value does not contain the selected path or filename;
- approved dimensions are validated against the pixel budget before the approval is issued;
- dry-run performs validation/preflight without creating textures, opening Undo or consuming the approval;
- successful import consumes the approval exactly once and uses Blockbench's native `Texture.fromFile(...).add(false, true)` path;
- create/import in one batch commit through one Undo transaction, and the finished Undo aspects contain the newly created/imported textures;
- rollback restores a consumed approval if the transaction fails;
- no arbitrary path is accepted from declarative JSON, Live Bridge or MCP;
- no separate picker action is claimed by this contract.

## Bounded texture paint region

The PR4 bounded-paint contract adds `texture_paint_region` as a deterministic exact-pixel patch rather than a brush engine:

- target is one explicit `textureId` and one explicit rectangular `region`;
- `pixels` is an exact row-major sequence of RGBA tuples;
- tuple count must equal `region.width * region.height` exactly;
- every channel must be an integer in `0..255`, including per-pixel alpha;
- the region area is charged against the existing `262144`-pixel per-batch budget;
- adapter preflight rejects out-of-bounds or layered targets before Undo;
- dry-run validates and preflights without writing bitmap state or opening Undo;
- committed apply performs one bounded `putImageData(...)`, publishes the changed texture once and remains inside the existing single Undo transaction;
- this operation itself does not derive UV-island masks, sample palettes, run procedural/random brushes, paint globally or expose a remote Live Bridge/MCP write.

## Bounded UV island masks

The PR4 UV-island-mask contract adds `texture_paint_uv_island` as a deterministic mask derived only from current per-face cube UV geometry selected explicitly by the caller:

- target is one explicit `textureId` plus a bounded list of explicit `{cubeId, face}` selectors;
- no material, part, provider or other semantic face inference is performed;
- every selected face must be enabled, use per-face UV and reference the target texture; Box UV fails closed;
- UV coordinates must map exactly to bitmap pixels using the current project UV dimensions and texture resolution;
- selected face rectangles must form one connected UV component through positive-area overlap or a shared edge segment; corner-only contact is not connectivity;
- the declared `region` must exactly equal the bounding rectangle derived from the selected UV mask;
- `pixels` remains an exact row-major RGBA sequence for the declared region and the conservative pixel budget is charged by the full region area;
- only pixels covered by the derived face-union mask are changed; holes/gaps inside the bounding rectangle and all pixels outside it are preserved;
- duplicate face selectors, disconnected selections, texture mismatch, non-pixel-aligned UVs, invalid bounds and layered textures fail during preflight before Undo;
- dry-run performs validation/preflight without bitmap mutation or Undo;
- committed apply writes the bounded region once, publishes the changed texture once and remains inside the existing single Undo transaction;
- Advanced V2 semantic UV masks, procedural brushes, arbitrary global painting and remote Live Bridge/MCP writes are outside this slice.

## Deterministic palette tools

The PR4 palette-tool boundary pairs the bounded `texture_replace_palette` mutation with read-only `texture.sample_palette` behavior exposed by the local UV/texture adapter as `samplePalette(...)`:

- sampling requires one explicit `textureId` and one explicit rectangular `region`;
- the region must use non-negative integer coordinates, positive integer dimensions and remain entirely inside the target texture;
- layered textures fail closed because this PR4 boundary has no layer selector;
- sampling reuses the existing `262144`-pixel bound and fails before reading bitmap data when that budget is exceeded;
- bitmap inspection uses one bounded `getImageData(...)` read and never calls `putImageData(...)`, opens Undo, publishes texture edits or changes the project revision;
- RGBA values are counted exactly, including alpha; transparent pixels are not normalized or collapsed by RGB value;
- the result reports `projectRevision`, `textureId`, `region`, `sampledPixels`, the full `uniqueColorCount`, `truncated`, and `colors[{rgba,count}]`;
- colors are ordered deterministically by count descending and then numeric RGBA lexicographic order;
- returned color entries are capped at the existing `256` palette-replacement bound while `uniqueColorCount` continues to report the full histogram cardinality and `truncated=true` records omitted entries;
- no quantization, clustering, harmonization, gradient generation, material inference or randomness is introduced;
- the sampled `projectRevision` can be used by callers as the stale-revision authority before constructing an existing bounded `texture_replace_palette` batch;
- Live Bridge/MCP remains read-only and this slice adds no remote write method.

The committed PR4 acceptance suite preserves round-trip, alpha-aware visual-diff, bitmap-aware Undo, and texture validation/path regressions while PR5 extends the Toolkit.

## Generic Animation Core

PR5 introduces a provider-neutral animation contract under `core/animation/animation_engine.js` and a desktop-local Blockbench adapter under `blockbench-plugin/animation_adapter.js`.

The generic mutation contract is bounded and revision-guarded:

- `animation_create`, `animation_update_settings`, and `animation_delete` manage generic animations;
- `animation_add_keyframe`, `animation_update_keyframe`, and `animation_delete_keyframe` manage transform keyframes;
- transform channels are limited to `position`, `rotation`, and `scale`;
- generic easing/interpolation is limited to the explicit allowlist `linear`, `bezier`, `catmullrom`, and `step`;
- loop modes are limited to the generic `once`, `loop`, and `hold` contract;
- operation count, identifiers, labels, duration/time values and vector payloads are bounded and validated before mutation;
- `expectedRevision` rejects stale batches before preflight/Undo;
- `dryRun` validates and preflights without opening an Undo transaction;
- committed batches use one animation/keyframe Undo transaction and roll back adapter failures;
- the desktop adapter composes its local revision authority from the canonical project snapshot plus deterministic keyframe state, without expanding the read-only Live Bridge protocol;
- duplicate IDs/names, missing animations/targets/keyframes and keyframes beyond animation duration fail closed during preflight.

### Abstract effect markers and provider boundary

The core contract understands bounded abstract `particle`, `sound`, `timeline`, and `custom` effect markers so provider-neutral specifications can represent semantic timing. The generic Blockbench adapter deliberately rejects effect-marker serialization with `PROVIDER_ADAPTER_REQUIRED` before Undo.

This is intentional: provider adapters such as the later GeckoLib adapter decide how an abstract marker maps to a concrete provider representation. PR5 does not create GeckoLib/AzureLib/EMF codecs, exporter payloads, effect-keyframe serialization or cross-provider conversion.

### Preview, pose inspection and capture

PR5 exposes adapter-bound read operations:

- `playPreview(...)` and `stopPreview(...)` delegate playback to the active editor adapter;
- `inspectPose(...)` returns a provider-neutral pose snapshot for the requested animation/time;
- `capturePose(...)` delegates deterministic camera-preset selection and screenshot capture to the adapter;
- Blockbench capture uses an explicitly named available `DefaultCameraPresets` entry and `Screencam.screenshotPreview(...)`;
- invalid animation/time/camera inputs fail closed;
- preview, pose inspection and capture do not mutate the asset revision.

CI tests these contracts with deterministic Blockbench test doubles. A physical editor/runtime capture smoke is not claimed by this PR.

### Animation diagnostics

The core also provides provider-neutral diagnostic primitives:

- `validateLoopSeam(...)` compares sampled start/end poses deterministically against an explicit tolerance and reports per-target/channel deltas;
- `diagnoseFootSlide(...)` computes contact displacement only when sufficient measurable contact samples are supplied;
- insufficient contact evidence returns a fail-closed `NOT_MEASURABLE` diagnostic rather than inventing a foot-slide result.

These diagnostics do not make gameplay, provider export or aesthetic approval decisions.

## Deliberate non-automation

Exact texel density is not guessed from incomplete project data. The Toolkit reports texture dimensions/bounds and validates UV completeness; contract + Visual Style Bible govern density decisions. Screenshot/aesthetic approval remains `minecraft-visual-qa` work.

Mutation capabilities remain explicit and bounded. There is no arbitrary JavaScript/shell execution, provider exporter, automatic plugin installation, gameplay authority, provider-specific animation serialization, arbitrary global UV repack, arbitrary global texture painting or new Live Bridge/MCP write surface. Physical Blockbench runtime health and real runtime handoff remain separate evidence gates.

## Tests

```bash
node --check asset_toolkit.js
node --test asset_toolkit.animation_core.test.js
node --test asset_toolkit.animation_adapter.test.js
node --test asset_toolkit.bundle_live_bridge.test.js
node --test asset_toolkit.uv_pack.test.js
node --test asset_toolkit.texture_create_import.test.js
node --test asset_toolkit.texture_create_import_adapter.test.js
node --test asset_toolkit.texture_paint_region.test.js
node --test asset_toolkit.uv_island_masks.test.js
node --test asset_toolkit.palette_sampling.test.js
node --test asset_toolkit.texture_acceptance.test.js
node --test asset_toolkit.test.js
node build_toolkit_bundle.js --check
```

Tests use Node's built-in runner and no third-party npm dependency. Coverage includes structural QA, Locator semantics, extension authorization, physical-provider authority, provider resolution, fail-closed conversion, schemas, generated-bundle reproducibility, deterministic UV-pack preview, exact confirmation/revision binding, Blockbench Undo behavior, overlap-safe source-pixel buffering, bounded texture creation, opaque approved import, dry-run approval preservation, collision/budget rejection, deterministic non-uniform bounded paint with exact RGBA/alpha preservation, bounded per-face UV-island mask derivation with gap preservation and fail-closed connectivity/alignment checks, deterministic bounded palette sampling with exact alpha-aware RGBA histograms and truncation metadata, PR4 texture acceptance, provider-neutral animation/keyframe contracts, stale-revision and transaction rollback behavior, provider-bound marker rejection, deterministic loop-seam and foot-slide diagnostics, preview/pose/capture adapter delegation, and standalone bundle loading without introducing a remote write surface.
