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

C4 implements the modpack-aware registry as a layered authority rather than inventing a Construction-specific copy of the physical modlist.

The shared Engineering I2 importer is the physical-modlist authority. C4 consumes its normalized snapshot, including top-level and nested JarJar entries. Empty physical `mod_id` values are preserved as evidence but are excluded from provider identities; malformed non-empty identifiers remain invalid. This preserves the exact physical evidence while avoiding fabricated provider names.

Construction adds two registry evidence layers:

1. static JAR indexing discovers NeoForge metadata, blockstate JSON, block models, block textures and nested JAR topology without extracting or mutating the artifacts;
2. a Factory-owned NeoForge runtime probe enumerates the post-registry `BuiltInRegistries.BLOCK` contents and every `getPossibleStates()` state in the exact installed runtime.

Static evidence may identify a candidate blockstate that is not actually registered. Therefore static indexing never proves block/state availability. When static and runtime evidence disagree, the runtime NeoForge registry snapshot wins for block and state existence.

A runtime snapshot is accepted only when its `physical_snapshot_sha256` matches the exact Engineering I2 snapshot and its target is exactly Minecraft 1.21.1 / NeoForge 21.1.248. The merged registry is deterministically ordered and content-fingerprinted.

The runtime producer reuses the shared Engineering I3 scaffolder instead of maintaining another Gradle project. `construction/scripts/prepare_neoforge_registry_probe.py` materializes the Factory-owned Java probe into the canonical scaffold, inheriting the audited Gradle 8.14 wrapper, Java 21 toolchain and NeoForge 21.1.248 dependency. C4 CI compiles/tests that materialized probe through the same real NeoForge userdev path.

C4 currently classifies registered blocks conservatively as `block_entity` when the runtime block implements `EntityBlock`, otherwise `ordinary`. This is only the first safety boundary. Connected/multipart blocks, copycat/material-bearing blocks, dynamic renderers, functional machine semantics and other provider-specific placement constraints require separately proven C5/later metadata and must not be inferred from static assets alone.

## 7. Schematic authority

The target canonical exchange artifact is Sponge Schematic v3. The Factory exporter preserves namespaced block IDs and states, required-mod provenance and controlled BlockEntity payloads without modifying preserved upstream sources.

C6 implements the first canonical exporter/validator in `construction/core/sponge_v3.py`. The adapter consumes only a C2-valid Canonical Build IR and reuses the C2 validator as the input authority, including its canonical content fingerprint check. Invalid or tampered IR therefore fails before any output-format conversion occurs.

The C6 serialization contract is:

- deterministic big-endian NBT wrapped in GZip with a zero timestamp and empty root name;
- root `Schematic` compound with Sponge `Version=3`;
- Minecraft 1.21.1 `DataVersion=3955`;
- C2 `min_corner` coordinates mapped to Sponge `Offset=[0,0,0]`;
- `Width`, `Height` and `Length` encoded with the unsigned 16-bit Sponge dimension semantics over NBT `Short` bit patterns;
- explicit `minecraft:air` at local palette id `0`, followed by the C2 canonical palette without state invention;
- `Blocks.Data` encoded as unsigned VarInts in the Sponge index order `x + z*Width + y*Width*Length`;
- `Metadata.RequiredMods` retained as a Factory metadata convention, not misrepresented as a Sponge-standard field;
- controlled BlockEntities represented by namespaced `Id`, in-bounds `Pos` and typed `Data` compounds whose NBT tag types are preserved.

The paired validator independently decompresses and parses the binary artifact and rejects wrong Sponge/data versions, malformed dimensions or offset, non-contiguous palettes, unknown palette references, malformed VarInts, wrong dense-volume cardinality and malformed/out-of-bounds controlled BlockEntities.

Two preserved upstreams informed the implementation but are not silently promoted to canonical authority. MineBench's pinned exporter uses the v3 layout and VarInt/index mechanics, but the audited revision hardcodes an older Minecraft data version and time-dependent metadata. The pinned `mcschematic` library recognizes Minecraft 1.21.1 data version 3955, but its audited serializer emits Sponge version 2. Factory therefore owns the explicit v3 adapter while keeping both upstreams unchanged.

## 8. Determinism

Any stochastic generation must receive an explicit seed. A repeated run with identical BuildSpec, engine version, upstream pins and modpack registry snapshot should produce identical canonical voxel output unless a provider is explicitly marked nondeterministic.

Within C2, canonicalization is independent of incoming placement order and block-state property-map order. Within C4, physical evidence, static JAR indexes, runtime block/state data and final registry records are normalized before fingerprinting. Canonical content fingerprints therefore change only when semantic content or provenance changes.

Within C6, the canonical palette order comes from C2, sparse cells are expanded deterministically, NBT compound/list construction order is controlled by Factory code, and the GZip timestamp is fixed to zero. Re-exporting the same valid Build IR plus the same required-mod and BlockEntity inputs must therefore reproduce identical bytes.

Within C7, report fingerprints derive from the exact BuildSpec, C2 Build IR and supplied C4 registry evidence. Occupancy traversal, graph traversal, connected-component ordering, findings and metrics use deterministic ordering and the report contains no timestamps, random identifiers or machine-specific paths. Equivalent authoritative inputs therefore reproduce an equivalent structural QA report.

## 9. QA layers

C7 implements structural Architecture QA while C8 remains the later visual-quality layer.

`construction/core/structural_qa.py` consumes the current BuildSpec, a C2-valid Canonical Build IR and optional C4 runtime-registry evidence. The paired `construction/schemas/structural-qa-report.schema.json` records deterministic fingerprints, metrics, findings and check states.

C7 currently proves only evidence available from those authorities:

- canonical bounds and C2 Build IR integrity;
- exact block/state validity against C4 `runtime_confirmed` evidence when supplied;
- conservative geometric two-block head clearance;
- deterministic walkable-surface graph topology;
- connected-component measurements;
- conservative one-block vertical-step connectivity.

The report distinguishes `PASS`, `FAIL`, `DEFERRED` and `NOT_APPLICABLE`. A required unresolved check contributes `DEFERRED` to the overall result rather than being silently accepted. This is important where current intent/runtime contracts do not contain enough semantics to prove the architectural requirement.

C7 therefore keeps the following concepts explicit but deferred instead of guessing:

- enclosure, because BuildSpec v1 does not map interior volumes, entrances, windows or intentional openings;
- semantic floor continuity, because named required spaces are not mapped to voxel regions;
- provider-aware unsupported placement, because C4 does not yet carry authoritative support-face, gravity or attachment metadata.

Disconnected conservative walkable components are measurable, but C7 does not claim which component corresponds to a named room or intended circulation path without a spatial intent mapping. Likewise, ladders, elevators, scaffolding, trapdoors and modded traversal mechanisms are not inferred from block names.

C8 visual QA remains responsible for silhouette, proportion, material hierarchy, repetition, facade readability, interior density and canonical rendered views. Structural evidence is not used as a proxy for those visual properties.

## 10. MCP boundary

C9 will expose narrow construction operations rather than arbitrary shell/code execution. Intended capabilities include registry search, palette resolution, build generation, bounded edits, preview, validation and export.

Credentials or service-specific configuration are not introduced by C0-C7. Manual setup remains deferred until the first provider that actually needs it.

## 11. Runtime/worldgen boundary

Construction may produce reusable structure assets, references and canonical voxel data. Runtime placement, structure sets, biome tags, spacing/separation, processor rules, loot and spawn behavior remain owned by the individual mod runtime and its Mod Engineering worldgen gates.

The C4 NeoForge probe is evidence-gathering infrastructure only. Compiling that probe and defining the post-registry export contract does not by itself prove the complete physical modpack can boot, capture the snapshot or place a generated structure. C7 state evidence likewise does not promote offline structural QA into live-world acceptance. Full runtime acceptance remains C12.

The visual pipeline may consume structures as reference material, including `.nbt` analysis, without turning a complete build into a runtime entity model by default.

## 12. Current non-goals

Through C7, Construction now owns canonical Build IR validation, modpack registry evidence, semantic palette resolution, deterministic Sponge v3 serialization and conservative offline structural QA. It still does not infer provider-specific support/traversal semantics without explicit authority, perform C8 visual QA, install C9 MCP servers, request C10 external-provider credentials, or claim C12 full-modpack/in-game/worldgen compatibility.
