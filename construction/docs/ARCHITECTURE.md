# Construction Architecture — C0 Baseline

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
  → Voxel IR
  → Structural QA
  → Modded Registry QA
  → Preview
  → Revision
  → Sponge v3 Export
```

## 4. Canonical BuildSpec

`BuildSpec` is the engine-independent request contract. C0 defines only its first schema. C2 will implement the executable IR and transformation layer.

The contract must be able to express:

- identity and deterministic seed;
- Minecraft target and modpack snapshot;
- size/bounds and terrain assumptions;
- architectural brief and required spaces;
- palette constraints and modded-block policy;
- output formats;
- QA requirements.

## 5. Upstream integration classes

### IMMUTABLE_SNAPSHOT

Redistributable source is copied at an exact commit in C1 and never edited in place. Schematica is the primary planned engine in this class.

### ENGINE_REFERENCE

A project may be preserved as a snapshot/reference while only selected concepts or adapters are used by the Factory. MineBench and Minecraft Builder MCP initially fit this class.

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

## 8. Determinism

Any stochastic generation must receive an explicit seed. A repeated run with identical BuildSpec, engine version, upstream pins and modpack registry snapshot should produce identical canonical voxel output unless a provider is explicitly marked nondeterministic.

## 9. QA layers

C7 and C8 will separate structural correctness from visual quality.

Structural QA includes bounds, enclosure, circulation, head clearance, floor continuity, vertical access, unsupported placements where meaningful and state validity.

Visual QA includes silhouette, proportion, material hierarchy, repetition, facade readability, interior density and canonical rendered views.

## 10. MCP boundary

C9 will expose narrow construction operations rather than arbitrary shell/code execution. Intended capabilities include registry search, palette resolution, build generation, bounded edits, preview, validation and export.

Credentials or service-specific configuration are never required in C0. Manual setup is deferred until the first provider that actually needs it.

## 11. C0 non-goals

C0 does not vendor third-party engines, scrape mod JARs, generate a schematic, install MCP servers, request API keys or claim in-game compatibility. Those claims require their later gates.
