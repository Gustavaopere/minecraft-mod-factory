# Construction C11 — Complex Modded Golden Design

Date: 2026-09-12

Status: approved design; implementation not started

Design baseline: `main@e768a73cfd810ee533d4d7f4c266b99bc1f9fabc`

## 1. Purpose

C11 establishes the first complex, deterministic, modpack-aware Construction Golden Sample that exercises the existing Construction authorities together on real modded block evidence.

The phase proves an offline evidence chain:

```text
physical modpack evidence
  -> C4 canonical modpack registry
  -> C5 palette resolution
  -> fixture-specific deterministic geometry
  -> C2 Canonical Build IR
  -> C7 Architecture QA
  -> C8 canonical previews + Visual QA
  -> C6 Sponge Schematic v3
  -> C11 manifest binding all exact artifacts
```

C11 is deliberately not runtime acceptance. Full-modpack boot, live-world placement, in-game texture fidelity, CTM, tint, emissive/shader behavior, machine behavior and worldgen/runtime compatibility remain C12 responsibilities.

## 2. Existing authorities remain authoritative

C11 composes the current Construction contracts; it does not replace them.

- Engineering I2 remains the only authority for the physical modlist and physical mod/JAR identities.
- C4 remains the authority for modpack block/state existence and safety evidence.
- C5 remains the authority for deterministic semantic palette selection.
- C2 remains the authority for Canonical Build IR validation and fingerprinting.
- C7 remains the authority for offline structural QA.
- C8 remains the authority for deterministic offline previews and Visual QA evidence.
- C6 remains the authority for canonical Sponge Schematic v3 serialization and validation.
- C10 remains the external-provider evidence boundary; providers are not required for C11 acceptance.
- C12 remains the full-modpack/live-world/runtime-visual acceptance boundary.
- C13 remains Skill/Router integration.

C11 must not add a parallel modlist parser, registry implementation, palette resolver, renderer, schematic exporter, MCP tool, provider adapter or runtime acceptance path.

## 3. Scope decision

The approved baseline is an industrial/tech architectural Golden of medium size using only block states that C4 proves are `runtime_confirmed` and whose C4 safety class is compatible with ordinary offline placement.

The baseline excludes functional machines and BlockEntities. A selected block with safety `block_entity`, `functional_machine`, `dynamic_renderer`, `connected_or_multipart`, `material_bearing`, `stateful`, `unknown`, or any future safety class not explicitly permitted by the approved C11 test must fail the baseline rather than being silently accepted.

The C11 baseline therefore targets ordinary decorative/architectural modded states, not functional runtime semantics.

## 4. Critical prerequisite: real C4 registry evidence

### 4.1 Current repository gap

At the design baseline, C4 provides the canonical registry contract, runtime probe, static JAR indexing and validator, and CI proves that the real Java 21 / NeoForge 21.1.248 probe compiles. C4 and C5 contract tests use synthetic runtime snapshots for deterministic unit coverage.

The repository does not yet contain a checked-in canonical C4 registry snapshot captured from the complete physical modpack.

C11 must not invent modded block IDs or promote physical mod presence into block/state existence. Therefore C11 implementation cannot select real modded Golden materials until this evidence exists.

### 4.2 Required evidence capture

The first C11 implementation gate is to obtain the canonical C4 composed registry for the exact physical modpack and version it as:

`construction/fixtures/complex-modded-golden/registry.json`

That file must be produced through the existing C4 authority, not hand-authored. It must satisfy the current `construction/schemas/modpack-registry.schema.json` and `construction.core.modpack_registry.validate_modpack_registry` contract.

The captured registry must bind:

- the exact Engineering I2 physical snapshot SHA-256;
- Minecraft `1.21.1`;
- loader `neoforge`;
- NeoForge `21.1.248`;
- the exact C4 `content_sha256` of the composed registry;
- the runtime block/state evidence and C4 safety classifications used by downstream C5/C11.

The checked-in C11 registry is immutable Golden input. CI validates and consumes it; CI is not allowed to pretend it can recapture the full physical modpack when the physical JAR set is not present in the runner.

If the actual canonical registry artifact is impractically large for the normal repository policy, implementation stops and the design is revised explicitly. C11 must not silently switch to a lossy subset, fabricated registry, compression convention, Git LFS contract or alternate evidence format.

## 5. Golden fixture layout

The fixture root is:

`construction/fixtures/complex-modded-golden/`

The intended checked-in artifacts are:

```text
construction/fixtures/complex-modded-golden/
├── registry.json
├── build-spec.json
├── palette-request.json
├── expected-palette-resolution.json
├── generate.py
├── expected-build-ir.json
├── expected-structural-qa.json
├── c8/
│   ├── front.svg
│   ├── back.svg
│   ├── left.svg
│   ├── right.svg
│   ├── top.svg
│   ├── isometric.svg
│   ├── layers.svg
│   ├── review-evidence.json
│   └── expected-visual-qa.json
├── expected.schem
└── manifest.json
```

No provider-returned binary is part of the required Golden chain.

## 6. BuildSpec contract

`build-spec.json` remains BuildSpec schema version 1.

Required C11 characteristics:

- `target.minecraft_version = "1.21.1"`;
- `target.loader = "neoforge"`;
- `target.modpack_snapshot` identifies the exact physical snapshot bound by `registry.json`;
- `palette.allow_modded = true`;
- `palette.allowed_namespaces` is closed to the namespaces intentionally allowed by the final palette design;
- `outputs.formats` includes `sponge_v3`;
- deterministic seed is fixed;
- `geometry.terrain_policy = "flat"` for the baseline;
- `qa.require_determinism = true`.

The target envelope is approximately `32 × 14 × 32`. The final frozen dimensions may be smaller but must remain materially more complex than the C3 `7 × 5 × 7` pavilion. Exact frozen dimensions become Golden fixture constants, not universal Construction limits.

Architectural intent includes these required-space labels:

- `production_hall`;
- `maintenance_mezzanine`;
- `loading_bay`;
- `utility_annex`;
- `service_corridor`.

Those strings describe design intent only. C11 does not claim C7 has semantic voxel-region mappings for those spaces. Existing C7 semantic limitations remain visible as `DEFERRED` where appropriate.

## 7. Palette selection

### 7.1 Roles

`palette-request.json` defines exactly these baseline roles unless the implementation design is explicitly revised before the first GREEN fixture is frozen:

- `structural_frame`;
- `wall_cladding`;
- `flooring`;
- `roofing`;
- `accent_trim`;
- `window_or_grille`;
- `walkway`.

Each role must use the existing C5 request contract.

### 7.2 Safety policy

Every C11 role is constrained to `allowed_safety=["ordinary"]`.

C11 must not automatically fall back to `block_entity`, vanilla, another namespace or another safety class merely because the requested role cannot be resolved.

If any required role cannot be resolved under the approved constraints, C11 fails and the palette request is revised deliberately; the resolver is not bypassed.

### 7.3 Namespace requirement

The final Canonical Build IR must contain at least three namespaces in actual placements, with at least two non-`minecraft` namespaces.

Physical mod presence alone is insufficient. Every selected state must come from `registry.json`, have C4 authority `runtime_confirmed`, and satisfy the C11 ordinary-safety policy.

Candidate physically present decorative/architectural mods may inform the eventual C5 request, but no candidate mod name or block ID is a design-time acceptance fact until the captured C4 registry proves the exact block/state.

### 7.4 Resolution artifact

`expected-palette-resolution.json` is the exact deterministic C5 output for:

- the approved BuildSpec;
- the checked-in C4 registry;
- the approved palette request.

The resolution must preserve C5's bindings to:

- registry fingerprint;
- BuildSpec SHA-256;
- palette request SHA-256.

C11 additionally hashes the exact checked-in palette-resolution bytes in its fixture manifest. This does not replace the C5 schema or C5 validation contract.

## 8. Deterministic fixture geometry

`generate.py` is fixture-specific Golden-generation code. It is not a reusable planner authority.

Its responsibilities are narrow:

1. load and validate the checked-in BuildSpec;
2. load and validate the checked-in C4 registry;
3. reproduce the C5 palette resolution and require exact equality with `expected-palette-resolution.json`;
4. map the approved semantic roles onto deterministic fixture geometry;
5. emit placements using only the states selected by C5;
6. pass all placements through the existing C2 canonicalizer.

The generator does not contain a second list of modded block IDs. The selected state for a role comes from C5 resolution.

Fixture-local geometry helpers may create boxes, walls, frames, slabs of occupied coordinates, openings and level transitions, but they must remain local to the Golden fixture. C11 does not introduce a new general-purpose engine API merely to express the test building.

The building should exercise at least:

- a large primary hall;
- a secondary annex;
- two or more occupied vertical levels;
- elevated walkway/mezzanine geometry;
- loading-bay/opening geometry;
- controlled facade repetition;
- structural frame versus cladding contrast;
- internal service circulation;
- more occupied placements and a materially larger envelope than C3.

Exact occupied-block count, palette size, bounds and per-role placement counts are frozen after evidence-backed palette selection and become fixture-specific regression constants.

## 9. Canonical Build IR acceptance

`expected-build-ir.json` is the canonical C2 output.

C11 requires:

- exact equality between regenerated and checked-in canonical IR;
- correct BuildSpec fingerprint;
- stable `content_sha256`;
- valid coordinates and bounds;
- no duplicate placements;
- no explicit air placements;
- canonical block-state property ordering;
- at least three actual namespaces, at least two modded;
- every modded state traceable to the validated C5 resolution and C4 runtime evidence.

Two consecutive regenerations in one checkout must yield the same canonical document and content fingerprint.

## 10. C7 structural QA

C11 runs the existing C7 structural QA against the exact:

- BuildSpec;
- Canonical Build IR;
- C4 registry evidence.

`expected-structural-qa.json` is the checked-in expected report.

C11 requires:

- exact deterministic report reproduction;
- zero C7 checks in `FAIL` state;
- the expected set of `DEFERRED` checks pinned explicitly by the C11 test;
- no newly introduced `DEFERRED` check may pass silently;
- runtime block/state validation must use the checked-in C4 registry.

C11 does not modify C7 simply to force an overall `PASS`. If the current C7 contract legitimately lacks semantic evidence for enclosure, named-space mapping, provider-aware support rules or other deferred semantics, that remains explicit evidence debt.

## 11. C8 preview and Visual QA

C11 uses the current `c8-svg-v1` renderer and the existing C8 Visual QA contract.

The fixture checks in all seven canonical views:

- `front`;
- `back`;
- `left`;
- `right`;
- `top`;
- `isometric`;
- `layers`.

The SVG files must regenerate byte-for-byte from the current Build IR and renderer version.

`review-evidence.json` is bound to the exact:

- BuildSpec;
- Build IR;
- renderer version;
- hashes of all seven views.

The six required subjective C8 checks remain:

- silhouette readability;
- proportion;
- material hierarchy;
- repetition;
- facade readability;
- interior density.

The checked-in review evidence may resolve those checks only under the existing C8 contract. C11 requires no subjective check to resolve to `FAIL`.

`runtime_visual_fidelity` remains `DEFERRED` and non-required. C11 must not claim offline SVG pseudo-color output proves Minecraft textures, CTM, tint, transparency, emissives, shaders or lighting.

## 12. C6 Sponge Schematic v3 artifact

`expected.schem` is produced exclusively by the existing C6 exporter from the valid C11 Build IR.

C11 requires:

- byte-for-byte deterministic re-export;
- successful C6 validation of the exact checked-in bytes;
- Minecraft 1.21.1 DataVersion and Sponge v3 semantics as defined by C6;
- preservation of the selected namespaced block IDs and states;
- no unapproved BlockEntity payloads;
- required-mod provenance only as supported by the current C6 Factory metadata convention.

Provider provenance does not make a schematic valid. The C6 validator is the format authority.

## 13. C11 manifest

`manifest.json` is a fixture-local evidence index, not a new shared Construction authority and not a new public schema in C11.

The C11 test treats the manifest as a closed object and rejects unknown fields.

The manifest records only deterministic evidence. It contains no current timestamp, machine path, username, random identifier or environment-derived value.

Required logical content:

- `schema_version = 1`;
- fixture identity `complex-modded-golden`;
- exact target Minecraft/loader/loader version;
- physical snapshot SHA-256;
- C4 registry `content_sha256`;
- exact file SHA-256 for `registry.json`;
- exact file SHA-256 for `build-spec.json`;
- exact file SHA-256 for `palette-request.json`;
- exact file SHA-256 for `expected-palette-resolution.json`;
- C2 Build IR `content_sha256`;
- exact file SHA-256 for `expected-build-ir.json`;
- exact file SHA-256 for `expected-structural-qa.json`;
- exact SHA-256 for each of the seven SVG views;
- exact file SHA-256 for review evidence;
- exact file SHA-256 for expected Visual QA;
- exact SHA-256 for `expected.schem`;
- relevant producer/version pins already owned by the underlying authorities.

Where an underlying authority exposes its own fingerprint, C11 records that authority fingerprint rather than inventing a competing semantic hash.

## 14. Fail-closed rules

C11 must reject at least the following mutations:

- BuildSpec physical snapshot mismatch;
- C4 registry physical-link mismatch;
- invalid C4 registry content fingerprint;
- wrong Minecraft/loader/NeoForge target;
- altered palette request fingerprint;
- altered C5 resolution;
- unresolved required palette role;
- selected state not `runtime_confirmed`;
- selected safety other than `ordinary`;
- selected block/state absent from C4 evidence;
- Build IR content fingerprint mismatch;
- duplicate or out-of-bounds placement;
- stale C7 input linkage;
- unexpected C7 `FAIL`;
- unexpected additional C7 `DEFERRED` check;
- stale C8 review evidence;
- replaced or altered SVG view;
- C8 required subjective `FAIL`;
- changed Sponge bytes;
- invalid Sponge v3 payload;
- incorrect manifest hash/fingerprint;
- unknown manifest field.

No fail-closed path may silently substitute vanilla content or a different modded namespace merely to make the Golden pass.

## 15. Determinism contract

C11 determinism is defined over checked-in evidence and pinned code, not over recapturing the complete external physical environment on every CI run.

After the real C4 registry is captured and frozen:

- identical BuildSpec + registry + palette request must reproduce identical C5 resolution;
- identical resolution + fixture generator must reproduce identical C2 IR;
- identical IR + C7 inputs must reproduce identical structural QA;
- identical IR + C8 renderer must reproduce identical SVG bytes;
- identical current C8 evidence must reproduce identical Visual QA;
- identical IR + C6 inputs must reproduce identical `.schem` bytes;
- the manifest must reproduce the exact expected hashes/fingerprints.

Any nondeterminism in required C11 artifacts is a C11 failure.

## 16. External providers

C10 remains a regression gate, not a C11 execution dependency.

C11 baseline performs:

- no external-provider network call;
- no credential lookup;
- no paid generation;
- no browser automation against providers;
- no requirement for EP2 or higher provider proof.

If a future provider reaches sufficient proof, it may be compared to the C11 Golden in a later change, but provider execution is not required for C11 acceptance.

## 17. Test strategy

The primary C11 contract test is:

`construction/tests/test_c11_complex_modded_golden.py`

The test must cover the positive Golden path and explicit fail-closed mutations.

At minimum, the positive path proves:

1. fixture files exist;
2. `registry.json` passes C4 validation;
3. registry target is Minecraft 1.21.1 / NeoForge 21.1.248;
4. BuildSpec is bound to the registry physical snapshot;
5. palette request is valid;
6. C5 recomputation equals `expected-palette-resolution.json`;
7. all seven roles resolve;
8. all selected states have authority `runtime_confirmed`;
9. all selections satisfy ordinary-safety policy;
10. C2 regeneration equals `expected-build-ir.json`;
11. actual Build IR uses at least three namespaces and at least two non-`minecraft` namespaces;
12. fixture complexity is materially above C3 through frozen fixture-specific metrics;
13. consecutive regeneration is deterministic;
14. C7 regeneration equals `expected-structural-qa.json`;
15. C7 contains zero `FAIL` checks and exactly the expected `DEFERRED` set;
16. all seven C8 SVGs regenerate byte-for-byte;
17. C8 review evidence binds to current artifact hashes;
18. C8 required subjective checks contain zero `FAIL`;
19. `runtime_visual_fidelity` remains `DEFERRED`;
20. C6 re-export equals `expected.schem` byte-for-byte;
21. C6 validates the exact checked-in `.schem`;
22. `manifest.json` is closed and every hash/fingerprint matches.

Mutation tests cover the fail-closed cases in section 14.

## 18. Dedicated CI workflow

C11 adds:

`.github/workflows/factory-construction-c11-complex-modded-golden.yml`

The workflow follows the established Construction pattern:

- pinned `actions/checkout`;
- pinned `actions/setup-python`;
- pinned `actions/setup-java`;
- Python 3.11;
- Java 21;
- hashed Construction dependency installation;
- read-only repository permissions.

The workflow runs:

1. shared Engineering I2 regressions;
2. C11 contract tests;
3. C10 contract tests and `validate_c10.py`;
4. C9 direct and real stdio regressions;
5. C8 regressions;
6. C7 regressions;
7. C6 regressions;
8. C5 regressions;
9. C4 regressions;
10. C4 runtime-probe materialization;
11. real `./gradlew test build --no-daemon` of the materialized C4 probe under Java 21 / NeoForge 21.1.248;
12. C3 regressions;
13. C2 regressions;
14. C0 tests and validator;
15. `git diff --check` over the C11 surface.

C11 does not run a complete physical-modpack boot. That remains C12.

The workflow must include path filters for the C11 fixture/test/workflow/spec/plan plus every consumed authority whose behavioral change could invalidate C11 evidence.

## 19. Sonar and governance

The normal repository Governance and Sonar gates remain applicable.

C11 implementation is not accepted merely because the dedicated C11 workflow is green. The implementation PR must reach terminal success for all applicable repository gates and have no unresolved review blocker before merge.

After merge, all workflows triggered on the exact merge SHA must be inventoried and reach the required terminal green state before Construction STATUS is advanced.

## 20. Acceptance criteria

C11 implementation is complete only when all of the following are proven:

- a real C4 registry captured from the exact physical modpack is checked in and validates canonically;
- C5 deterministically resolves all approved roles from that registry;
- every selected Golden state is `runtime_confirmed` and ordinary-safe;
- actual Build IR uses at least two modded namespaces and at least three namespaces total;
- C2 Golden output is byte/content stable;
- C7 output is deterministic, has no `FAIL`, and expected deferments are explicit;
- all seven C8 previews are byte-stable;
- current C8 review evidence is hash-bound and no required subjective check is `FAIL`;
- runtime visual fidelity remains deferred to C12;
- C6 emits byte-stable Sponge v3 accepted by its validator;
- manifest hashes/fingerprints all validate;
- required mutation tests fail closed;
- C0–C10 applicable regressions pass;
- the real C4 NeoForge probe builds in CI;
- whitespace, Governance and Sonar gates pass;
- no external-provider execution or payment is required;
- no C12 claim is made.

## 21. STATUS and closeout

`construction/STATUS.md` is not changed during the C11 implementation PR.

After the implementation merge is validated on `main`, a dedicated STATUS-only closeout records the exact implementation merge SHA and post-merge gate evidence and advances:

`PHASE=C11_COMPLETE_POSTMERGE_VALIDATED`

The next frontier becomes C12 Runtime Acceptance.

No STATUS advance occurs before exact post-merge evidence exists.

## 22. Expected implementation surface

The implementation plan may create or modify only the surfaces justified by this design, expected to include:

- `.github/workflows/factory-construction-c11-complex-modded-golden.yml`;
- `construction/fixtures/complex-modded-golden/**`;
- `construction/tests/test_c11_complex_modded_golden.py`;
- C11-specific fixture generation/validation helpers only if the fixture-local code cannot stay reasonably focused;
- `construction/README.md` and `construction/docs/ARCHITECTURE.md` for C11 scope documentation;
- the C11 spec and implementation plan.

Existing C2/C4/C5/C6/C7/C8/C9/C10 production modules should not be changed unless TDD exposes a genuine contract defect required by the approved C11 use case. Any such defect must be fixed in the owning authority with dedicated regression coverage rather than patched around in C11.

## 23. Implementation ordering constraint

The implementation plan must begin with evidence, not geometry:

1. re-audit `main`, open PRs, current STATUS and physical modlist;
2. establish the real C4 registry capture for the exact physical snapshot;
3. validate and freeze that registry evidence;
4. derive the C5 palette request and resolution from real C4 states;
5. only then freeze Golden geometry and downstream artifacts;
6. implement C11 tests/workflow through TDD;
7. run all gates;
8. merge only from a fully reconciled head;
9. validate all post-merge gates;
10. close out STATUS separately.

No exact modded block ID, final palette, placement count or artifact hash may be invented before the C4 evidence step proves it.