# Minecraft Construction Factory

`construction/` is the dedicated authority for offline Minecraft structure generation, analysis, validation, preview and schematic export.

The goal is to let an agent receive a construction brief, plan the architecture, resolve a palette from the real modpack, generate voxels, validate the result and export a reproducible structure without requiring in-game building tools.

## Target

- Minecraft Java Edition 1.21.1
- NeoForge modpack-aware palettes
- canonical schematic output: Sponge Schematic v3 (`.schem`)
- optional outputs: Litematica (`.litematic`) and vanilla structure NBT when a proven adapter exists

## Source preservation policy

Third-party source code that may be incorporated is pinned to an exact upstream commit and preserved unchanged under `construction/upstream/` when its license permits redistribution. Factory-specific behavior must live in adapters, wrappers or derived modules outside immutable upstream snapshots.

A source snapshot is never modified silently. If an upstream limitation requires a fork, the fork must be explicit and covered by regression tests against the pinned original.

Services without redistributable source or a verified API are treated as external providers. They may have documented handoff/adapters, but are not represented as locally integrated code.

## C0 scope

C0 establishes only the construction control plane:

- authority and architecture documentation;
- status and roadmap;
- pinned upstream source registry;
- initial schemas for `BuildSpec` and upstream provenance;
- C0 validator and contract tests;
- dedicated GitHub Actions gate.

No generation engine is vendored in C0. Upstream preservation begins in C1.

## C2 scope

C2 establishes the executable, engine-independent canonical Build IR used between generation adapters and later validation/export stages.

The C2 contract provides:

- sparse non-air block placement rather than a provider-specific dense runtime object;
- a canonical palette of namespaced block IDs plus sorted block-state properties;
- fixed `x/y/z` coordinates with `y` up, block units and a minimum-corner origin;
- deterministic ordering independent of input placement or property-map order;
- fail-closed duplicate-coordinate, out-of-bounds, explicit-air and malformed-state handling;
- SHA-256 linkage back to the source `BuildSpec` and a canonical content fingerprint;
- producer identity/version metadata without provider-specific serialization.

C2 deliberately does not claim that a namespaced block exists in the physical modpack, does not carry arbitrary BlockEntity/entity payloads, does not export a schematic format and does not own runtime worldgen placement. Those gates belong to later Construction phases.

## C3 scope

C3 adds the first executable end-to-end Golden Sample across the preserved engine and the canonical C2 boundary.

`construction/fixtures/vanilla-golden/` contains a deterministic vanilla-only 7×5×7 pavilion. The checked-in `BuildSpec` is executed against the exact preserved Schematica pin, converted from the resulting voxel session into sparse placements, normalized by the Factory-owned C2 canonicalizer, and compared byte-for-data against the checked-in expected Build IR.

The Golden intentionally stays narrow:

- 110 occupied blocks with a fixed three-state vanilla palette;
- no modded namespace or physical modpack-registry claim;
- no Sponge/Litematica/NBT artifact committed or exported by C3;
- no BlockEntity/entity payload authority;
- no structural-quality, visual-quality or runtime/worldgen acceptance claim;
- deterministic reruns must reproduce the exact canonical Build IR and fingerprints.

C3 therefore proves the integration seam `BuildSpec → preserved Schematica → Canonical Build IR` without stealing responsibilities from C4–C8.

## C4 scope

C4 establishes the modpack-aware block registry without creating a second modlist authority.

The shared Engineering I2 importer remains the physical-modlist authority. Construction consumes that normalized evidence, including top-level and nested JarJar artifacts. A physical entry with an empty `mod_id` remains valid evidence but is not promoted to a provider identity; malformed non-empty identifiers still fail closed.

C4 then combines two evidence layers:

- static JAR indexing discovers NeoForge metadata, blockstate JSON, block models, block textures and nested JARs without extracting or mutating the source artifacts;
- a Factory-owned NeoForge runtime probe enumerates the post-registry `BuiltInRegistries.BLOCK` contents and every possible block state for the exact Minecraft 1.21.1 / NeoForge 21.1.248 environment.

Static discovery is evidence only. When static assets and runtime data disagree about whether a block/state exists, the exact runtime registry snapshot wins. Runtime snapshots are bound to the physical snapshot SHA-256 and the exact target before they may be merged into the Construction registry.

The runtime probe does not duplicate the Engineering build stack. `construction/scripts/prepare_neoforge_registry_probe.py` materializes it through the canonical I3 scaffolder, inheriting the Factory-owned Gradle 8.14 wrapper, Java 21 toolchain and NeoForge 21.1.248 dependency contract. CI compiles and tests the materialized probe with `./gradlew test build --no-daemon`.

C4 does not select an optimal modded palette, claim advanced connected/copycat/dynamic-renderer semantics, serialize Sponge v3 or perform structural/visual/runtime acceptance. Those remain C5, C6, C7, C8 and C12 responsibilities.

## C6 scope

C6 establishes the first Factory-owned canonical Sponge Schematic v3 exporter and validator at `construction/core/sponge_v3.py`.

The exporter consumes only a C2-valid Canonical Build IR and fails closed when its target, coordinate, palette or content fingerprint contract is invalid. It serializes deterministic big-endian NBT inside GZip with a zero timestamp, an empty NBT root name and the required `Schematic` compound. The canonical target is fixed to Sponge `Version=3` and Minecraft 1.21.1 `DataVersion=3955`.

C6 preserves the Construction contract across the format boundary:

- sparse C2 cells become an explicit `minecraft:air` palette entry at local id `0` plus dense Sponge block data;
- namespaced block IDs and sorted block-state properties are preserved as canonical Sponge palette strings;
- `Blocks.Data` uses unsigned VarInt palette ids and the Sponge index order `x + z*Width + y*Width*Length`;
- dimensions are encoded as Sponge unsigned 16-bit dimensions through NBT `Short` bit patterns and `Offset` is fixed to `[0,0,0]` for the C2 minimum-corner origin;
- Factory-required mod provenance is preserved as `Metadata.RequiredMods` without claiming it is a Sponge-standard metadata key;
- controlled BlockEntities preserve typed NBT `Compound` payloads with explicit namespaced ids and in-bounds positions;
- the validator independently parses the emitted GZip/NBT payload and rejects wrong format/data versions, malformed dimensions, invalid palette/data references and malformed controlled BlockEntities.

The pinned MineBench exporter remains an engine reference: it demonstrates Sponge v3 layout/VarInt mechanics but its audited revision hardcodes an older `DataVersion` and time-dependent metadata. The pinned `mcschematic` library recognizes Minecraft 1.21.1 data version 3955 but its audited serializer emits Sponge version 2. Neither upstream is silently modified; C6 therefore owns the canonical v3 adapter in Factory code.

C6 does not claim structural or visual quality, advanced provider-specific placement semantics, MCP/provider integration, or in-game/worldgen compatibility. Those remain later Construction gates.

## Planned pipeline

```text
prompt / construction brief
        ↓
BuildSpec
        ↓
architectural planner
        ↓
modded palette resolver
        ↓
voxel engine
        ↓
Canonical Build IR
        ↓
structural + modded QA
        ↓
preview / critique loop
        ↓
Sponge Schematic v3 validator
        ↓
.schem + manifest
```

## Directory map

- `core/` — Factory-owned canonical Construction runtime contracts, including Build IR and modpack registry composition
- `docs/` — architecture and provider decisions
- `fixtures/` — checked-in deterministic Construction Golden Samples and their generation inputs
- `runtime/` — Factory-owned runtime probes materialized through shared Engineering scaffolding
- `schemas/` — machine-readable contracts
- `upstream/` — pinned provenance and immutable permitted snapshots/references
- `scripts/` — Factory-owned validators and tooling
- `tests/` — construction-domain regression tests

Future directories such as `engines/`, `catalog/`, `registry/`, `providers/`, `mcp/` and `qa/` are created only when their implementation starts.

## Roadmap

`C0 Foundation → C1 Upstream Preservation → C2 Canonical Build IR → C3 Vanilla Golden → C4 Modpack Registry → C5 Modded Palette Engine → C6 Sponge v3 → C7 Architecture QA → C8 Visual QA → C9 Agent/MCP → C10 External Providers → C11 Complex Modded Golden → C12 Runtime Acceptance → C13 Skill/Router Integration`
