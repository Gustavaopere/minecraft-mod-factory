# Construction Architecture

## 1. Authority

`construction/` owns reusable offline structure-generation infrastructure. It does not own gameplay runtime for individual mods and does not require structures to be generated inside Minecraft.

## 2. Architectural rule

Preserve proven upstream behavior first. Third-party engines are pinned and treated as immutable inputs. Factory-owned adapters normalize them behind construction contracts. This avoids rewriting a working engine merely to fit repository conventions.

## 3. Canonical flow

```text
Construction Brief
  → BuildSpec
  → Planner
  → Palette Resolver
  → Engine Adapter
  → Canonical Build IR
  → Structural QA
  → Modded Registry QA
  → Preview
  → Revision
  → Sponge v3 Export
```

## 4. BuildSpec and Canonical Build IR

`BuildSpec` is the engine-independent request contract. It expresses identity and deterministic seed, Minecraft target and modpack snapshot, size/bounds and terrain assumptions, architectural brief and required spaces, palette constraints, requested outputs and QA requirements.

C2 introduces the executable Canonical Build IR as the normalized voxel result contract between an engine adapter and later Construction stages.

The IR is intentionally smaller than a provider runtime object:

- sparse non-air placements only;
- palette entries represented as namespaced block IDs plus block-state properties;
- palette index referenced by each occupied `x/y/z` coordinate;
- explicit bounds inherited from `BuildSpec.geometry.max_size`;
- fixed coordinate system: axes `x/y/z`, `y` up, `min_corner` origin and block units;
- source `BuildSpec` SHA-256 fingerprint;
- canonical content SHA-256 fingerprint;
- producer identity and producer version.

The C2 normalization layer sorts block-state properties, palette entries and block coordinates deterministically. Duplicate coordinates, negative/out-of-bounds coordinates, malformed resource locations, malformed state properties and explicit air placements fail closed instead of being clipped, dropped or silently overwritten.

C2 accepts syntactically valid namespaced modded states but does not claim those states exist in the installed modpack. Physical registry existence and safety classification remain C4/C5 responsibilities.

BlockEntity payloads, entities, provider-specific serialization and output-format fields are excluded from the C2 IR. Controlled payload support belongs to later registry/export contracts where the exact runtime semantics can be proven.

## 5. Upstream integration classes

### IMMUTABLE_SNAPSHOT

Redistributable source is pinned at an exact commit in C1 and never edited in place. Schematica is the primary engine in this class.

### ENGINE_REFERENCE

A project may be preserved as a reference while only selected concepts or adapters are used by Factory. MineBench and Minecraft Builder MCP initially fit this class.

### LIBRARY_SNAPSHOT

A lower-level library can be preserved for compatibility/export paths. `mcschematic` initially fits this class.

### REFERENCE_ONLY

Source may be studied but not redistributed under the audited terms. Promptcraft is currently in this class.

### EXTERNAL_PROVIDER

A hosted service is integrated only through a documented API or explicit manual/file handoff. C0 places ObjToSchematic, Structmatic, Schematic Helper and BlockGPT here until an API is independently verified.

## 6. Modded block authority

A vanilla block database is insufficient for this modpack. Planned C4 authority is two-layered:

1. static JAR indexing for discoverable assets, blockstates, models, textures and metadata;
2. runtime NeoForge registry export for the exact installed environment.

When they disagree, the runtime registry snapshot wins for block/state existence.

Each catalogued block will eventually carry safety metadata distinguishing ordinary static blocks from stateful blocks, connected/multipart blocks, copycat/material-bearing blocks, BlockEntities, dynamic renderers and functional machine blocks.

## 7. Schematic authority

The target canonical exchange artifact is Sponge Schematic v3. The Factory exporter must preserve namespaced block IDs, states, required-mod metadata and controlled BlockEntity payloads. Existing upstream exporters may continue to produce their native formats; the Factory adapter is responsible for canonical conversion and validation.

C2 does not serialize that artifact. C6 owns the first canonical Sponge v3 exporter/validator gate.

## 8. Determinism

Any stochastic generation must receive an explicit seed. A repeated run with identical BuildSpec, engine version, upstream pins and modpack registry snapshot should produce identical canonical voxel output unless a provider is explicitly marked nondeterministic.

Within C2, canonicalization is independent of incoming placement order and block-state property-map order. The canonical content fingerprint therefore changes only when semantic IR content or its provenance changes.

## 9. QA layers

C7 and C8 will separate structural correctness from visual quality.

Structural QA includes bounds, enclosure, circulation, head clearance, floor continuity, vertical access, unsupported placements where meaningful and state validity.

Visual QA includes silhouette, proportion, material hierarchy, repetition, facade readability, interior density and canonical rendered views.

## 10. MCP boundary

C9 will expose narrow construction operations rather than arbitrary shell/code execution. Intended capabilities include registry search, palette resolution, build generation, bounded edits, preview, validation and export.

Credentials or service-specific configuration are never required in C0-C2. Manual setup is deferred until the first provider that actually needs it.

## 11. Runtime/worldgen boundary

Construction may produce reusable structure assets, references and canonical voxel data. Runtime placement, structure sets, biome tags, spacing/separation, processor rules, loot and spawn behavior remain owned by the individual mod runtime and its Mod Engineering worldgen gates.

The visual pipeline may consume structures as reference material, including `.nbt` analysis, without turning a complete build into a runtime entity model by default.

## 12. Current non-goals

The current Construction foundation does not scrape mod JARs, claim modded block compatibility, install MCP servers, request provider API keys, serialize canonical Sponge v3, or claim in-game/worldgen compatibility. Those claims require their later roadmap gates.
