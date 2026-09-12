# Construction C9 Agent/MCP Design

Date: 2026-09-11
Status: design approved in chat; written specification pending final human review
Repository: `Gustavaopere/minecraft-mod-factory`
Construction frontier entering this design: `C8_COMPLETE_POSTMERGE_VALIDATED`

## 1. Purpose

C9 adds the first supported agent-facing control surface for the Construction domain. It exposes the capabilities already proven through C2-C8 as a narrow local Model Context Protocol (MCP) server without creating a second voxel, registry, palette, QA, schematic, runtime, filesystem, shell, provider, or planner authority.

The server exists to let an MCP-capable agent compose deterministic Construction operations safely. It does not turn Construction into a general remote execution environment and it does not claim that free-form architectural planning or live Minecraft placement has been solved.

## 2. Authority and dependency baseline

C9 must preserve the existing Construction authorities:

- C2 `construction/core/build_ir.py` remains the canonical Build IR authority.
- C4 `construction/core/modpack_registry.py` remains the modpack block/state evidence authority.
- C5 `construction/core/modded_palette.py` remains the semantic palette resolver.
- C6 `construction/core/sponge_v3.py` remains the Sponge Schematic v3 exporter/validator.
- C7 `construction/core/structural_qa.py` remains structural QA authority.
- C8 `construction/qa/preview_renderer.py` and `construction/core/visual_qa.py` remain preview and Visual QA authorities.
- The physical modlist and Engineering I2 remain authoritative for physical mod presence/version.
- `construction/upstream/registry.json` keeps `minecraft-builder-mcp` as an `ENGINE_REFERENCE`; C9 may study it but does not promote it to Factory runtime authority.

The official MCP Python SDK is the implementation dependency. The implementation baseline is `mcp==2.2.0`, verified against the official `modelcontextprotocol/python-sdk` stable GitHub release published 2026-09-07. C9 uses the SDK v2 line and MCP revision support supplied by that exact release. The implementation must pin the exact package and all required transitive packages with hashes in a C9-specific hash-pinned additions lock. Existing C0-C8 dependency locks must not be widened merely to support C9.

## 3. Scope

C9 owns:

1. one local MCP server transported only over stdio;
2. strict MCP tool schemas for bounded Construction operations;
3. a thin Factory-owned façade over C2-C8 authorities;
4. a process-scoped, in-memory, content-addressed artifact store for binary/large outputs;
5. MCP resource reads for artifacts produced by the current process;
6. deterministic bounded Build IR edits as the only new domain behavior introduced by C9;
7. normalized fail-closed tool errors that preserve the underlying authority result;
8. direct and real stdio integration tests proving parity with C2-C8.

## 4. Explicit non-goals

C9 does not add:

- arbitrary shell execution;
- arbitrary Python/code execution;
- subprocess execution as a tool capability;
- arbitrary filesystem read/write or caller-provided paths;
- HTTP, SSE, Streamable HTTP, WebSocket, REST, OAuth, API keys or remote hosting;
- outbound network access;
- external providers such as ObjToSchematic, Structmatic, Schematic Helper or BlockGPT;
- provider credentials or provider-specific setup;
- a free-form natural-language architectural planner;
- a generic `generate_from_prompt` tool;
- live Minecraft placement;
- worldgen integration;
- full-modpack boot acceptance;
- runtime visual fidelity claims;
- arbitrary BlockEntity/entity mutation;
- a generic NBT authoring API;
- skill/router orchestration.

Those boundaries remain owned by later phases: C10 external providers, C12 runtime acceptance and C13 skill/router integration.

## 5. Selected architecture

C9 uses a local stdio MCP server with a thin deterministic façade and an in-memory content-addressed artifact store.

```text
MCP host / agent
      |
      | stdio only
      v
Construction C9 MCP Server
      |
      +--> strict tool schema validation
      |
      +--> C9 facade
      |      +--> C2 Build IR
      |      +--> C4 registry evidence
      |      +--> C5 palette resolver
      |      +--> C6 Sponge v3
      |      +--> C7 structural QA
      |      +--> C8 preview + visual QA
      |
      +--> process-scoped ArtifactStore
             +--> SVG resources
             +--> preview bundle manifest
             +--> Sponge v3 bytes
```

The MCP layer must not duplicate C2-C8 validation logic. It validates only its own closed request envelope and then delegates to the existing authority. When an authority rejects an input, C9 returns an error; it never repairs, guesses, downgrades or silently coerces that input.

## 6. Server and package boundary

Implementation starts a new `construction/mcp/` package because that directory does not exist before C9 and the repository roadmap explicitly reserved it for the phase that implements MCP.

The package is split by responsibility:

- `server.py`: MCP server construction, tool/resource registration and stdio entrypoint;
- `facade.py`: strict adapters calling C2-C8 and C9 bounded-edit logic;
- `artifacts.py`: in-memory content-addressed artifact store;
- `errors.py`: normalized internal error type and MCP error conversion.

No C2-C8 module may import `construction/mcp/`; dependency direction is one-way from C9 into established Construction authorities.

The C9 server semantic version constant is `c9-mcp-v1`. It is independent from the MCP SDK package version and appears in server metadata, bounded-edit producer metadata and tests.

## 7. Transport and lifecycle

The only supported C9 transport is stdio.

- The server does not bind a TCP port.
- The server does not start HTTP/SSE/Streamable HTTP listeners.
- The server does not read provider credentials.
- The server does not persist state to disk.
- Process restart clears all C9 artifacts.
- The only mutable process state is the artifact store.
- Tool behavior does not depend on wall-clock time, random values, machine paths, environment-specific identifiers or network state.

A C9 process is single logical artifact namespace. Concurrent requests may be served only if the implementation preserves deterministic artifact insertion and immutable resource reads.

## 8. Exact MCP tool catalog

The wire tool names are fixed for C9 v1 and are the only tools the server may advertise:

1. `registry_search`
2. `palette_resolve`
3. `build_canonicalize`
4. `build_validate`
5. `build_edit`
6. `qa_structural`
7. `preview_render`
8. `qa_visual`
9. `export_sponge_v3`

The server must not advertise shell, filesystem, network, install, process, generic code execution or generic file-conversion tools.

Every tool input schema is closed: unknown top-level or nested fields fail validation. JSON booleans are not accepted where integers are required. All Construction documents are passed as JSON objects, not as filesystem paths or URLs.

### 8.1 `registry_search`

Purpose: deterministic inspection of a caller-supplied C4 registry document.

Input:

- `registry`: complete C4 registry object;
- `query`: optional lowercase substring applied only to canonical block IDs;
- `namespace`: optional exact namespace;
- `authority`: optional exact `runtime_confirmed` or `static_only_unconfirmed`;
- `safety`: optional non-empty list of exact C4 safety classes;
- `limit`: integer 1-100, default 25.

Behavior:

- validate the complete C4 registry using the C4 contract before search;
- no fuzzy search, embeddings, semantic ranking or inferred tags;
- filters are conjunctive;
- results sort by canonical block ID ascending;
- truncate only after deterministic sorting;
- preserve C4 `available`, `authority` and `safety` values without promotion.

Output per match contains only block ID, namespace, availability, authority, safety and runtime state count. C9 does not reinterpret static-only evidence as runtime availability.

### 8.2 `palette_resolve`

Purpose: expose C5 palette resolution without changing C5 semantics.

Input:

- `build_spec`;
- `registry`;
- `request`.

Behavior: call C5 `resolve_palette` directly after C9 envelope validation.

Output: the exact C5 resolution document. C9 must not reorder, complete or choose ambiguous states beyond C5 behavior.

### 8.3 `build_canonicalize`

Purpose: create canonical C2 Build IR from explicit placements supplied by the caller.

Input:

- `build_spec`;
- `placements`: explicit C2 placement objects containing only `x`, `y`, `z`, `block_state`.

Behavior: call C2 `canonicalize_build_ir` with producer `construction-c9-mcp` and producer version `c9-mcp-v1`.

This is canonicalization, not architectural generation. C9 never derives placements from prose.

Output: exact valid C2 Build IR.

### 8.4 `build_validate`

Purpose: expose C2 validation.

Input: `build_ir`.

Output:

```json
{
  "valid": true,
  "errors": []
}
```

`errors` is exactly the ordered C2 validation error list. Validation failures are data, not MCP transport failures, because validation is the purpose of this tool.

### 8.5 `build_edit`

Purpose: perform deterministic bounded edits to an existing C2 Build IR without exposing a generic code/voxel engine.

Input:

- `build_spec`;
- `build_ir`;
- `operations`: ordered non-empty array of edit operations.

Allowed operation forms are exactly:

```json
{"op":"set_block","x":0,"y":0,"z":0,"block_state":{"name":"minecraft:stone","properties":{}}}
```

and

```json
{"op":"remove_block","x":0,"y":0,"z":0}
```

Rules:

- validate `build_ir` with C2 before editing;
- require `C2.build_spec_fingerprint(build_spec)` to equal `build_ir.metadata.build_spec_sha256`;
- every operation coordinate must be within BuildSpec/C2 bounds;
- one request may touch a coordinate at most once;
- `set_block` adds or replaces exactly one coordinate;
- `remove_block` requires an occupied coordinate and fails if it is already absent;
- explicit air is never accepted as `set_block` state;
- no BlockEntity/entity payload is accepted;
- after applying operations, reconstruct explicit placements and call C2 `canonicalize_build_ir` with producer `construction-c9-edit` and producer version `c9-mcp-v1`;
- therefore palette ordering, block ordering, BuildSpec fingerprint and content fingerprint are all re-derived by C2.

Output: the new valid C2 Build IR.

### 8.6 `qa_structural`

Purpose: expose C7 structural QA.

Input:

- `build_spec`;
- `build_ir`;
- optional `registry`.

Behavior: call C7 `run_structural_qa` directly.

Output: exact C7 report. `DEFERRED` remains `DEFERRED`; C9 cannot promote unresolved structural evidence.

### 8.7 `preview_render`

Purpose: render the seven canonical C8 SVG views and make them available as MCP resources without returning large binary/text payloads inline.

Input: `build_ir`.

Behavior:

1. call C8 `render_canonical_views`;
2. require exactly the seven canonical view IDs and canonical order;
3. store each SVG byte sequence in ArtifactStore;
4. create a canonical JSON preview-bundle manifest containing renderer version, Build IR SHA-256 and the seven artifact descriptors;
5. store that manifest as an ArtifactStore resource.

Output:

- `renderer_version`;
- `build_ir_sha256`;
- `bundle_uri`;
- seven ordered view descriptors containing `id`, `uri`, `media_type`, `sha256`, `byte_length`.

The SVG bytes are read through MCP resources using the returned URI.

### 8.8 `qa_visual`

Purpose: expose C8 Visual QA while proving that the views came from the current C9 process and match the exact Build IR.

Input:

- `build_spec`;
- `build_ir`;
- `preview_bundle_uri`;
- optional `structural_report`;
- optional `palette_resolution`;
- optional `review_evidence`.

Behavior:

- `preview_bundle_uri` must resolve to a C9-created preview manifest currently present in ArtifactStore;
- the manifest must reference exactly seven current C9 artifacts in canonical view order;
- manifest Build IR SHA-256 must equal the current Build IR fingerprint;
- retrieve exact SVG bytes from ArtifactStore;
- call C8 `run_visual_qa` with those bytes and supplied optional provenance/review documents.

Output: exact C8 report. `runtime_visual_fidelity` remains non-required `DEFERRED` exactly as C8 requires.

### 8.9 `export_sponge_v3`

Purpose: expose deterministic C6 export as a binary MCP resource.

Input:

- `build_ir`;
- optional `required_mods`: unique namespace strings in ascending lexical order.

C9 v1 deliberately does not expose C6 BlockEntity input because MCP/JSON currently has no approved typed-NBT authoring contract in Construction.

Behavior:

1. call C6 `export_sponge_v3(build_ir, required_mods=..., block_entities=())`;
2. immediately call C6 `validate_sponge_v3` on the generated bytes;
3. fail closed if the validator returns any error;
4. store the exact `.schem` bytes in ArtifactStore.

Output contains `uri`, media type `application/x-sponge-schematic`, SHA-256 and byte length.

## 9. ArtifactStore contract

ArtifactStore is process-scoped and immutable.

Each artifact record contains:

- exact bytes;
- media type;
- SHA-256 of exact bytes;
- byte length;
- creation kind (`preview_svg`, `preview_bundle`, `sponge_v3`).

Canonical URI format:

`construction://artifact/sha256/<64-lowercase-hex>`

The SHA-256 is the resource identity. Inserting identical bytes reuses the existing record and URI. A hash collision with different bytes is a fatal internal error.

C9 v1 limits:

- maximum artifact size: 64 MiB;
- maximum total unique artifact bytes per process: 256 MiB;
- maximum unique artifact records: 512;
- no automatic eviction;
- exceeding a limit fails closed with `ARTIFACT_LIMIT`;
- restarting the server is the only supported way to clear the store.

MCP resource reads accept only exact ArtifactStore URIs. No file path, `file://`, HTTP(S), relative path or caller-selected URI is resolved. Resource listing, when requested, returns current artifact descriptors sorted by URI and never reads the filesystem.

## 10. Error contract

C9 normalizes errors at the MCP boundary but does not reinterpret authority semantics.

Stable C9 error codes:

- `INVALID_INPUT`: C9 request envelope/schema failure;
- `AUTHORITY_REJECTED`: C2-C8 authority rejected supplied content;
- `ARTIFACT_NOT_FOUND`: unknown or expired C9 artifact URI;
- `ARTIFACT_LIMIT`: ArtifactStore capacity violation;
- `INTERNAL_ERROR`: unexpected C9 implementation failure.

Error payload fields are exactly:

- `code`;
- `message`;
- optional `authority` for `AUTHORITY_REJECTED` (`C2`, `C4`, `C5`, `C6`, `C7`, `C8`);
- optional `details` containing only deterministic validation information safe for the caller.

C9 errors never include Python tracebacks, local absolute paths, environment variables, credentials or arbitrary exception representations. Unexpected exceptions are logged only to stderr in a sanitized form and surface to the MCP caller as `INTERNAL_ERROR`.

## 11. Determinism

C9 must preserve the deterministic properties of its authorities.

- `registry_search` sorts by canonical block ID.
- `palette_resolve` returns C5 output unchanged.
- `build_canonicalize` and `build_edit` delegate canonical ordering/fingerprints to C2.
- C7/C8 reports remain their authority outputs.
- C8 SVG bytes remain byte-identical for identical Build IR.
- C6 `.schem` bytes remain byte-identical for identical valid input and canonical `required_mods` order.
- Artifact URIs derive only from exact artifact bytes.
- No timestamp, random UUID, machine path or process identifier appears in tool result identity.

## 12. Security boundary

C9 is intentionally capability-limited.

The implementation must contain no tool that accepts a shell command, executable, Python snippet, filesystem path, URL, host, port, environment variable name, package name to install or arbitrary import target.

The production server must not call `subprocess`, create sockets, make HTTP requests, traverse caller-selected filesystem paths or write artifacts to disk. Normal Python imports of repository code and the SDK are allowed.

The stdio server may write protocol traffic to stdout only as required by the SDK. Diagnostics go to stderr and must not corrupt MCP framing.

Tests may spawn the server subprocess to exercise the real stdio transport; this test harness behavior is not a server capability.

## 13. C9 dependency policy

C9 must not mutate the existing `construction/upstream/harness/schematica-test-lock.txt` solely to add MCP.

Implementation creates a dedicated hash-pinned MCP additions lock under `construction/upstream/harness/`. It pins `mcp==2.2.0` and all transitive packages required beyond the existing Construction test environment, with `--hash` entries sufficient for CI installation using `pip install --require-hashes --no-deps`.

Before freezing that delta lock, implementation must test it together with the existing Schematica lock and resolve any version conflict explicitly. C9 CI installs the established lock first and the C9 additions lock second; dependency resolution is never left to an unpinned online solve.

## 14. Test architecture

C9 is implemented TDD-first.

### 14.1 Contract/unit tests

Tests must prove:

- exact nine-tool catalog and no extra tools;
- closed schemas reject unknown fields;
- `registry_search` validates C4 and sorts/filter deterministically;
- `palette_resolve` equals direct C5 output;
- `build_canonicalize` equals direct C2 canonicalization with C9 producer metadata;
- `build_validate` mirrors ordered C2 errors exactly;
- `build_edit` add/replace/remove behavior, duplicate-touch rejection, absent-remove rejection, out-of-bounds rejection and BuildSpec fingerprint linkage;
- `qa_structural` equals direct C7 output;
- `preview_render` bytes equal direct C8 renderer output and ArtifactStore hashes;
- `qa_visual` equals direct C8 output and rejects forged/stale/wrong-Build-IR bundles;
- `export_sponge_v3` bytes equal direct C6 output and pass C6 validation;
- ArtifactStore deduplication and all capacity limits;
- stable sanitized error codes;
- no arbitrary filesystem/network/shell tool surface.

### 14.2 Real MCP stdio integration

A test client using the same pinned official MCP SDK must start the actual C9 server over stdio and prove:

- discovery exposes exactly the nine tools;
- tool calls work through protocol serialization rather than direct Python calls;
- resource reads return exact artifact bytes;
- an MCP host can execute the canonical Golden flow without shell/filesystem tools;
- malformed tool input fails at the MCP boundary;
- the server terminates cleanly when stdio closes.

### 14.3 Golden acceptance

The existing C3/C8 vanilla pavilion is reused; C9 does not create a new architectural Golden.

The C9 Golden acceptance path is:

1. `build_validate` accepts the checked-in C3 expected Build IR;
2. `preview_render` reproduces the seven checked-in C8 SVG bytes/hashes;
3. `qa_visual`, supplied with the checked-in BuildSpec, C7/C5 context when required by the fixture, and checked-in C8 review evidence, reproduces the expected C8 report;
4. `export_sponge_v3` produces a C6-valid deterministic schematic from the same Build IR;
5. resource reads reproduce exact generated bytes.

`build_canonicalize` parity is tested separately against a direct C2 call using the same C9 producer metadata, because producer metadata is part of the C2 fingerprint and therefore is intentionally different from the historical C3 producer metadata.

## 15. CI gate

Implementation adds `.github/workflows/factory-construction-c9-agent-mcp.yml` using the repository's existing pinned Actions identities, Python 3.11 and Java 21 where inherited runtime-registry regression requires it.

The workflow must run, in this order:

1. install existing hash-pinned Construction environment;
2. install the C9 hash-pinned MCP additions;
3. Engineering I2 regression;
4. C9 contract/unit tests;
5. C9 real stdio integration tests;
6. C8 regression;
7. C7 regression;
8. C6 regression;
9. C5 regression;
10. C4 regression plus materialized NeoForge runtime probe build;
11. C3 regression;
12. C2 regression;
13. C0 regression + validator;
14. `git diff --check` over C9 and documentation paths.

C1A/C1B and Governance remain independent repository workflows and must also be green in PR and post-merge validation when triggered.

## 16. Documentation and status policy

The implementation PR updates `construction/README.md` and `construction/docs/ARCHITECTURE.md` only after the C9 implementation is green, documenting the exact supported tool/resource boundary and non-goals.

`construction/STATUS.md` is not advanced in the implementation PR. As with prior Construction phases, C9 status becomes complete only after:

1. implementation PR gates are green;
2. implementation PR is merged;
3. post-merge C9 and inherited gates are green on the exact merge SHA;
4. a separate status-only closeout PR records the evidence and advances `NEXT_ACTION` to C10.

## 17. C9/C10/C12/C13 boundaries

### C10 External Providers

C10 owns any integration with hosted/external construction services, APIs, credentials, provider-specific network clients or manual provider handoff. C9 only supplies local deterministic Factory operations.

### C12 Runtime Acceptance

C12 owns full-modpack boot, live-world placement, worldgen compatibility and runtime visual fidelity. C9 does not convert offline C7/C8 evidence into runtime acceptance.

### C13 Skill/Router Integration

C13 owns natural-language routing/orchestration and decides how an agent turns a user brief into a sequence of C9 operations. C9 deliberately contains no free-form planner or prompt-to-build tool.

## 18. Acceptance criteria

C9 is acceptable only when all of the following are proven:

- official MCP Python SDK exactly pinned to `2.2.0` with hash-pinned transitive additions;
- server runs over stdio only;
- exact nine-tool catalog is exposed;
- no arbitrary shell, filesystem, code-execution, network or provider capability is exposed;
- all tool schemas are closed and fail closed;
- direct façade results are equivalent to their C2-C8 authorities;
- bounded edits always return a C2-valid, re-fingerprinted Build IR;
- ArtifactStore resources are immutable, content-addressed and process-scoped;
- C3/C8 Golden flows through real MCP stdio and resource reads;
- Sponge v3 outputs are independently revalidated by C6 before exposure;
- all C9 tests and C8-C0 regressions pass;
- C1A/C1B, Governance, Sonar and other applicable repository gates are green before merge;
- post-merge validation is green on the exact main SHA;
- no C10, C12 or C13 capability is silently promoted into C9.
