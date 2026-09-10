# Minecraft Mod Factory Asset Toolkit for Blockbench

Internal project plugin: `asset_toolkit.js` (plugin ID matches filename).

## Scope

Structural/contract QA plus fail-closed provider/extension capability resolution for project-owned Minecraft assets, with narrowly bounded local Blockbench mutations where an audited contract exists. Mutation support is intentionally incremental: it does not authorize arbitrary geometry, UV, texture, pivot or animation rewrites, and it does not install or invoke arbitrary extensions.

The current PR4 slices include deterministic one-texture UV pack preview/apply for per-face cube UVs, bounded internal texture creation and locally approved texture import, deterministic bounded non-uniform texture painting inside an explicit rectangular region, bounded painting through an explicitly selected per-face UV island mask, and deterministic read-only palette sampling paired with bounded palette replacement. These are local desktop operations, not a generic UV/texture rewrite surface and not a Live Bridge/MCP write surface.

## Architecture

Canonical source lives in modular CommonJS files under `core/` and `blockbench-plugin/`. `build_toolkit_bundle.js` generates the standalone `asset_toolkit.js` consumed by Blockbench. CI requires the committed standalone bundle to match the modular source byte-for-byte.

Core modules include:

- `project-model` — safe model predicates and bounds;
- `validator` — structural/contract validation;
- `contract-profile` — profile JSON parsing;
- `report` — deterministic read-only reports;
- `extension-registry` — exact extension identity/version/compatibility/MCP authorization;
- `provider-profile` — physical provider snapshot plus fail-closed profile resolution;
- `uv-texture/uv_texture_engine` — bounded declarative UV/texture mutation contract and pixel budget;
- `uv-texture/uv_pack` — bounded revision-bound UV pack preview/apply contract;
- `blockbench-plugin/uv_texture_adapter.js` — Blockbench UV/texture inspection and bounded transactional mutation adapter;
- `blockbench-plugin/plugin_adapter.js` — verified UI integration.

Canonical policy documents:

- `../../../standards/BLOCKBENCH-EXTENSION-POLICY.md`;
- `../../../standards/ASSET-PROVIDER-PROFILES.md`.

## Verified Blockbench API surface

- `Plugin.register(...)`;
- `Action`;
- `MenuBar.menus.tools.addAction(...)`;
- `Blockbench.Project`;
- `Blockbench.showMessageBox(...)`;
- `Blockbench.textPrompt(...)`;
- `Texture.fromDataURL(...)`;
- `Texture.fromFile(...)`;
- `Texture.add(...)`.

The bounded UV/texture adapter additionally uses the project texture/cube state, texture canvas `getImageData(...)` / `putImageData(...)`, and Blockbench Undo transaction surface behind the adapter boundary. Tests exercise begin/finish/cancel transaction behavior and bitmap/UV/texture mutation semantics without exposing those mutations through Live Bridge/MCP.

A separate Toolkit file-picker action is not part of the declarative `texture_import_approved` contract and is not claimed as a current PR4 requirement. Approved local file data remains behind the opaque desktop-adapter approval boundary; declarative payloads do not carry filesystem paths.

References: https://blockbench.net/wiki/docs/plugin/ · https://blockbench.net/wiki/docs/ui/ · https://web.blockbench.net/docs/

## Provider/extension rules

Installed is not equivalent to compatible, trusted or MCP-authorized. Required extensions must match the audited exact plugin version, pass the Blockbench compatibility gate and be explicitly session-allowlisted. Blocked/human-only/audit-required paths fail closed. Cross-profile conversion is denied unless a later audited adapter exists.

The executable snapshot follows the current physical modlist authority: GeckoLib 4.9.2, AzureLib 3.1.11 and Entity Model Features 3.3.5 are represented as provider requirements where applicable; current Blockbench catalog pins are maintained separately in the extension registry.

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
- Advanced V2 semantic UV masks, palette operations, procedural brushes, arbitrary global painting and remote Live Bridge/MCP writes are outside this slice.

## Deterministic palette tools

The PR4 palette-tool boundary pairs the existing bounded `texture_replace_palette` mutation with read-only `texture.sample_palette` behavior exposed by the local UV/texture adapter as `samplePalette(...)`:

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

With deterministic palette sampling paired with the already-integrated bounded palette replacement, the canonical PR4 `PALETTE_TOOLS` capability is covered. PR4 itself remains incomplete until the final round-trip, visual-diff, Undo and texture-validation/texture-path acceptance gates are proven.

## Deliberate non-automation

Exact texel density is not guessed from incomplete project data. The Toolkit reports texture dimensions/bounds and validates UV completeness; contract + Visual Style Bible govern density decisions. Screenshot/aesthetic approval remains `minecraft-visual-qa` work.

Mutation capabilities remain explicit and bounded. There is no arbitrary JavaScript/shell execution, provider exporter, automatic plugin installation, gameplay authority, generic animation mutation, arbitrary global UV repack, arbitrary global texture painting or new Live Bridge/MCP write surface in this PR4 slice.

## Tests

```bash
node --check asset_toolkit.js
node --test asset_toolkit.uv_pack.test.js
node --test asset_toolkit.texture_create_import.test.js
node --test asset_toolkit.texture_create_import_adapter.test.js
node --test asset_toolkit.texture_paint_region.test.js
node --test asset_toolkit.uv_island_masks.test.js
node --test asset_toolkit.palette_sampling.test.js
node --test asset_toolkit.bundle_live_bridge.test.js
node --test asset_toolkit.test.js
node build_toolkit_bundle.js --check
```

Tests use Node's built-in runner and no third-party npm dependency. Coverage includes structural QA, Locator semantics, extension authorization, physical-provider authority, provider resolution, fail-closed conversion, schemas, generated-bundle reproducibility, deterministic UV-pack preview, exact confirmation/revision binding, Blockbench Undo behavior, overlap-safe source-pixel buffering, bounded texture creation, opaque approved import, dry-run approval preservation, collision/budget rejection, deterministic non-uniform bounded paint with exact RGBA/alpha preservation, bounded per-face UV-island mask derivation with gap preservation and fail-closed connectivity/alignment checks, deterministic bounded palette sampling with exact alpha-aware RGBA histograms and truncation metadata, and standalone bundle loading without introducing a remote write surface.
