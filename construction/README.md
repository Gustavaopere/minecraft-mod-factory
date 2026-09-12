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

## C7 scope

C7 establishes deterministic offline Architecture QA at `construction/core/structural_qa.py` without creating a second voxel, palette or runtime authority. It consumes the current `BuildSpec`, a C2-valid Canonical Build IR and optional C4 runtime-registry evidence, then emits the versioned machine-readable contract `construction/schemas/structural-qa-report.schema.json`.

The conservative C7 evidence layer provides:

- C2-backed bounds and canonical Build IR integrity checks;
- exact runtime block/state validation against C4 `runtime_confirmed` evidence when a registry is supplied;
- geometric two-block head-clearance metrics;
- a deterministic conservative walkable-surface graph;
- connected-component analysis without inventing semantic room mappings;
- conservative one-block vertical-step connectivity;
- deterministic report fingerprints, findings, metrics and ordering;
- explicit `PASS`, `FAIL`, `DEFERRED` and `NOT_APPLICABLE` check states, with required unresolved evidence preventing an overall `PASS`.

C7 deliberately does not guess semantics that the current contracts cannot prove. Enclosure remains `DEFERRED` when the BuildSpec does not identify intentional openings or interior volumes; semantic floor continuity remains `DEFERRED` because named spaces are not mapped to voxel regions; provider-aware unsupported-placement checks remain `DEFERRED` until authoritative support/gravity/attachment metadata exists. These states are visible evidence gaps, not silent passes.

C7 also does not score silhouette, proportion, materials, facade readability or other visual qualities, and it does not prove full modpack boot, live-world placement or worldgen compatibility. Those remain C8 Visual QA and C12 Runtime Acceptance responsibilities.

## C8 scope

C8 establishes deterministic offline Visual QA without promoting diagnostic previews into Minecraft runtime appearance authority.

`construction/qa/preview_renderer.py` renders the C2-valid Canonical Build IR through the fixed `c8-svg-v1` contract into seven canonical SVG artifacts: `front`, `back`, `left`, `right`, `top`, `isometric` and `layers`. The renderer uses integer geometry, deterministic C2-state pseudo-colors, fixed occlusion/painter ordering, no external resources and embedded Build IR/renderer fingerprints. Re-rendering identical authoritative input produces byte-identical SVGs.

`construction/core/visual_qa.py` validates those artifacts and emits `construction/schemas/visual-qa-report.schema.json`. Its objective evidence includes occupancy, projection, palette-distribution, repetition, facade-depth and layer-density metrics. C7 structural reports and C5 palette resolutions may be supplied only as fingerprinted provenance/context; they cannot resolve visual acceptance by themselves.

The six required subjective checks are `silhouette_readability`, `proportion`, `material_hierarchy`, `repetition`, `facade_readability` and `interior_density`. They remain `DEFERRED` unless explicit review evidence is bound to the exact BuildSpec, Build IR, renderer version and all seven current view hashes. Matching human or agent review may resolve only those checks to `PASS` or `FAIL`. It cannot resolve `runtime_visual_fidelity`, which is deliberately non-required and always `DEFERRED` to C12.

The C3 pavilion is extended under `construction/fixtures/vanilla-golden/c8/` with all seven canonical SVGs, bound review evidence and an expected Visual QA report. That Golden proves deterministic offline rendering/reporting and exact review-evidence binding; it does not prove Minecraft textures, CTM, tint, transparency, emissives, shaders, lighting, full-modpack boot or live-world appearance.

## C9 scope

C9 implements the capability-limited Agent/MCP boundary under `construction/mcp/` using the exact hash-pinned official MCP SDK `2.2.0`. The production server supports stdio only and advertises exactly nine tools: `registry_search`, `palette_resolve`, `build_canonicalize`, `build_validate`, `build_edit`, `qa_structural`, `preview_render`, `qa_visual` and `export_sponge_v3`.

The C9 boundary is deliberately narrow:

- every tool has a closed request schema and delegates authoritative validation/semantics to C2, C4, C5, C6, C7 or C8 rather than duplicating those authorities;
- C4 now owns the public `validate_modpack_registry` contract consumed directly by C7 and C9;
- bounded edits are re-canonicalized by C2 and cannot carry arbitrary BlockEntity/entity payloads;
- preview SVGs, preview bundles and Sponge v3 payloads are immutable process-scoped artifacts addressed only by `construction://artifact/sha256/<sha256>` URIs;
- one MCP resource template exposes those exact stored bytes without caller-selected filesystem paths or URLs;
- the artifact store is content-addressed, deduplicating and capacity-limited, and process restart is its only clearing mechanism;
- anticipated failures use stable sanitized C9 error codes while unexpected failures surface only as `INTERNAL_ERROR`;
- real stdio acceptance proves exact nine-tool discovery, malformed-input rejection, byte-exact C8 resource reads, the checked-in Golden flow, C6-valid export and clean process teardown.

C9 does not add a prompt/planning authority, external-provider integration, provider credentials, arbitrary shell/code execution, filesystem access, network access, package installation, HTTP transport or C12 runtime/in-game acceptance. C10 remains the authority frontier for external providers, C12 for runtime acceptance and C13 for Skill/Router integration.

## C10 scope

C10 defines the external-provider evidence and handoff boundary without expanding the C9 runtime capability surface.

- C10 external-provider profiles are separate from Engineering I2 physical providers. I2 remains authority for physically present mod/JAR identities and versions; a C10 profile describes an external service/tool handoff contract and does not imply physical-mod presence.
- The baseline C10 runtime is network-free and credential-free. Provider execution remains manual unless a later adapter is backed by a verified contract and explicit proof; C9 continues to advertise exactly its existing nine tools.
- Provider proof and API proof are independent. C10 uses `EP0_DISCOVERED`, `EP1_HANDOFF_VERIFIED`, `EP2_EXECUTION_PROVEN`, `EP3_FORMAT_VALIDATED`, `EP4_FACTORY_INTEGRATION_VALIDATED` and `EP5_GOLDEN_VALIDATED`, while API state separately progresses from `UNVERIFIED_API` only when corresponding evidence exists.
- All bytes crossing an external-provider boundary are untrusted input. Requests, receipts, artifact sizes/hashes, path safety and downstream Factory contracts must be revalidated rather than accepted by provider provenance.
- ObjToSchematic remains only a candidate manual smoke path until the required fresh official evidence and manual handoff evidence are captured. Discovery alone is not execution proof.
- C11 remains the complex-modded Golden frontier, C12 remains live/full-modpack runtime acceptance and C13 remains Skill/Router integration. C10 does not pre-empt those authorities.

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

- `core/` — Factory-owned canonical Construction runtime contracts, including Build IR, modpack registry composition, structural QA and visual QA
- `docs/` — architecture and provider decisions
- `fixtures/` — checked-in deterministic Construction Golden Samples and their generation inputs
- `qa/` — deterministic offline preview/rendering helpers used by Construction QA contracts
- `mcp/` — capability-limited stdio MCP server, façade, sanitized errors and process-scoped artifact store
- `runtime/` — Factory-owned runtime probes materialized through shared Engineering scaffolding
- `schemas/` — machine-readable contracts
- `upstream/` — pinned provenance and immutable permitted snapshots/references
- `scripts/` — Factory-owned validators and tooling
- `tests/` — construction-domain regression tests

Future directories such as `engines/`, `catalog/` and `registry/` are created only when their implementation starts. `providers/` exists from C10 onward for external-provider profiles and bounded handoff helpers; it is not an alternate Engineering I2 mod/provider catalog.

## Roadmap

`C0 Foundation → C1 Upstream Preservation → C2 Canonical Build IR → C3 Vanilla Golden → C4 Modpack Registry → C5 Modded Palette Engine → C6 Sponge v3 → C7 Architecture QA → C8 Visual QA → C9 Agent/MCP → C10 External Providers → C11 Complex Modded Golden → C12 Runtime Acceptance → C13 Skill/Router Integration`
