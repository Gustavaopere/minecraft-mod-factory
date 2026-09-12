# Construction C9 Agent/MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the already-proven Construction C2-C8 capabilities through a deterministic local stdio MCP server with nine bounded tools, immutable process-scoped artifacts, and no shell/filesystem/network/provider authority.

**Architecture:** Add a one-way `construction/mcp/` façade over C2-C8, first consolidating C4 composed-registry validation so C7 and C9 share one registry authority. The MCP server uses the official Python MCP SDK over stdio only, returns JSON authority results inline, publishes SVG/manifest/Sponge bytes through a content-addressed in-memory ArtifactStore, and introduces only one new Construction behavior: bounded `set_block`/`remove_block` editing followed by C2 recanonicalization.

**Tech Stack:** CPython 3.11, official `mcp==2.2.0` Python SDK, Pydantic supplied by the pinned SDK dependency graph, Python standard library (`hashlib`, `json`, `dataclasses`, `logging`, `unittest`), existing C2-C8 Construction contracts, MCP stdio transport, GitHub Actions on `ubuntu-24.04`, Java 21/Gradle only for inherited C4 NeoForge runtime-probe regression.

**Spec:** `docs/superpowers/specs/2026-09-11-construction-c9-agent-mcp-design.md`

## Global Constraints

- Target remains Minecraft Java Edition `1.21.1`, NeoForge `21.1.248`, Java `21` where the inherited runtime registry probe is exercised.
- Construction frontier entering implementation is `C8_COMPLETE_POSTMERGE_VALIDATED`.
- MCP SDK production baseline is exactly `mcp==2.2.0`.
- MCP transport is stdio only; the production server must not expose HTTP, SSE, Streamable HTTP, WebSocket, REST, OAuth, ports, hosts, or network clients.
- Server semantic version is exactly `c9-mcp-v1`.
- Exact advertised tool order is `registry_search`, `palette_resolve`, `build_canonicalize`, `build_validate`, `build_edit`, `qa_structural`, `preview_render`, `qa_visual`, `export_sponge_v3`.
- C2 remains canonical Build IR authority; C4 remains registry authority; C5 remains palette authority; C6 remains Sponge v3 authority; C7 remains structural QA authority; C8 remains preview/visual QA authority.
- C9 must add `validate_modpack_registry(registry) -> list[str]` to C4 and refactor C7 to consume it without changing valid C7 report bytes/hashes or invalid-registry rejection semantics.
- `minecraft-builder-mcp` remains `ENGINE_REFERENCE`; do not vendor or promote it as runtime authority.
- No free-form prompt planner, generic generation, C10 external provider, provider credential, C12 live-runtime acceptance, or C13 skill/router behavior enters C9.
- No arbitrary shell/code/process/filesystem/network/install/import tool may be advertised.
- Production C9 code must not call `subprocess`, open sockets, issue HTTP requests, traverse caller-selected filesystem paths, or persist artifacts to disk.
- Artifact URI is exactly `construction://artifact/sha256/<64-lowercase-hex>`.
- Artifact limits are exactly 64 MiB per artifact, 256 MiB total unique bytes per process, 512 unique records, no eviction.
- Existing `construction/upstream/harness/schematica-test-lock.txt` is not widened for MCP; C9 uses a separate hash-pinned additions lock.
- Do not advance `construction/STATUS.md` in the implementation PR; status closeout is a separate post-merge PR after exact-main validation.

---

### Task 1: Freeze C9 dependency and executable RED contract

**Files:**
- Create: `construction/upstream/harness/c9-mcp-lock.txt`
- Create: `construction/tests/test_c9_agent_mcp.py`
- Create: `.github/workflows/factory-construction-c9-agent-mcp.yml`

**Interfaces:**
- Consumes: existing Construction lock, C2-C8 public functions, official MCP SDK `2.2.0`.
- Produces: hash-pinned MCP test/runtime environment, executable C9 contract, and C9 CI gate before production C9 modules exist.

- [ ] **Step 1: Resolve and freeze the MCP additions lock without mutating the existing Construction lock**

Use an isolated temporary environment to resolve `mcp==2.2.0` against the already-pinned Construction environment, then freeze exact versions and hashes only for packages not already supplied compatibly by `schematica-test-lock.txt`:

```bash
python3 -m venv /tmp/c9-lock-venv
/tmp/c9-lock-venv/bin/python -m pip install --upgrade pip
/tmp/c9-lock-venv/bin/python -m pip install --require-hashes --no-deps -r construction/upstream/harness/schematica-test-lock.txt
/tmp/c9-lock-venv/bin/python -m pip install 'mcp==2.2.0'
/tmp/c9-lock-venv/bin/python -m pip check
/tmp/c9-lock-venv/bin/python -m pip freeze --all | sort > /tmp/c9-freeze.txt
```

Download the exact resolved MCP-side wheels, calculate hashes, and write a lock whose entries use `package==version --hash=sha256:<digest>`. The finished lock must install with:

```bash
python3 -m pip install --require-hashes --no-deps -r construction/upstream/harness/schematica-test-lock.txt
python3 -m pip install --require-hashes --no-deps -r construction/upstream/harness/c9-mcp-lock.txt
python3 -m pip check
python3 -c 'import mcp; from importlib.metadata import version; assert version("mcp") == "2.2.0"'
```

Reject the task if the two locks require incompatible versions; do not solve a conflict by loosening an existing pin.

- [ ] **Step 2: Create the RED-first C9 contract test module**

Start with exact production path gates:

```python
ROOT = Path(__file__).resolve().parents[2]
MCP_DIR = ROOT / "construction" / "mcp"
SERVER_PATH = MCP_DIR / "server.py"
FACADE_PATH = MCP_DIR / "facade.py"
ARTIFACTS_PATH = MCP_DIR / "artifacts.py"
ERRORS_PATH = MCP_DIR / "errors.py"
IMPLEMENTATION_READY = all(path.is_file() for path in (SERVER_PATH, FACADE_PATH, ARTIFACTS_PATH, ERRORS_PATH))

class C9ContractTests(unittest.TestCase):
    def test_c9_modules_exist(self):
        self.assertTrue(SERVER_PATH.is_file(), "C9 MCP server is not implemented")
        self.assertTrue(FACADE_PATH.is_file(), "C9 facade is not implemented")
        self.assertTrue(ARTIFACTS_PATH.is_file(), "C9 artifact store is not implemented")
        self.assertTrue(ERRORS_PATH.is_file(), "C9 error boundary is not implemented")
```

Keep dependency/workflow/spec checks unguarded. Guard behavior classes with `@unittest.skipUnless(IMPLEMENTATION_READY, "C9 production modules not implemented yet")`.

Freeze these required test names in the file so later tasks fill them rather than inventing new acceptance semantics:

```text
test_mcp_dependency_is_exact_2_2_0
test_exact_nine_tool_catalog
test_no_forbidden_tool_surface
test_tool_schemas_are_closed
test_c4_public_validator_parity
test_registry_search_filters_and_order
test_palette_resolve_matches_c5
test_build_canonicalize_matches_c2
test_build_validate_mirrors_c2_errors
test_build_edit_add_replace_remove
test_build_edit_rejects_duplicate_touch_absent_remove_and_bounds
test_build_edit_requires_matching_build_spec_fingerprint
test_qa_structural_matches_c7
test_preview_render_matches_c8_and_is_deterministic
test_preview_bundle_manifest_is_canonical_and_bound
test_qa_visual_matches_c8
test_qa_visual_rejects_forged_stale_or_wrong_ir_bundle
test_export_sponge_v3_matches_c6_and_revalidates
test_artifact_store_deduplicates_and_is_immutable
test_artifact_store_enforces_all_limits
test_errors_are_stable_and_sanitized
test_real_stdio_discovery_and_tool_call
test_real_stdio_resource_read
test_real_stdio_golden_flow
test_stdio_server_terminates_cleanly
```

- [ ] **Step 3: Create the final C9 workflow before production modules exist**

Workflow name: `Factory Construction C9 Agent MCP`. Trigger on `main`, `feat/construction-c9-agent-mcp`, and PRs to `main` for C9 plus shared C2-C8/Engineering paths. Reuse exact Actions pins already used by C8:

```yaml
- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
  with:
    fetch-depth: 2
    submodules: recursive
- uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
  with:
    python-version: '3.11'
- uses: actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3
  with:
    distribution: temurin
    java-version: '21'
```

Run in this exact order:

```bash
python3 -m pip install --require-hashes --no-deps -r construction/upstream/harness/schematica-test-lock.txt
python3 -m pip install --require-hashes --no-deps -r construction/upstream/harness/c9-mcp-lock.txt
python3 -m pip check
python3 -m unittest engineering/tests/test_i2_modlist_catalog.py engineering/tests/test_i2_security_review.py -v
python3 -m unittest construction/tests/test_c9_agent_mcp.py -v
python3 -m unittest construction/tests/test_c7_architecture_qa.py construction/tests/test_c7_registry_authority.py -v
python3 -m unittest construction/tests/test_c8_visual_qa.py construction/tests/test_c8_palette_resolution_contract.py -v
python3 -m unittest construction/tests/test_c6_sponge_v3.py -v
python3 -m unittest construction/tests/test_c5_modded_palette.py -v
python3 -m unittest construction/tests/test_c4_modpack_registry.py construction/tests/test_c4_runtime_registry_probe.py -v
python3 construction/scripts/prepare_neoforge_registry_probe.py --output .factory-ci/c9/runtime-probe
chmod +x .factory-ci/c9/runtime-probe/gradlew
cd .factory-ci/c9/runtime-probe
GRADLE_USER_HOME="$GITHUB_WORKSPACE/.factory-ci/c9/gradle-home" ./gradlew test build --no-daemon
cd "$GITHUB_WORKSPACE"
python3 -m unittest construction/tests/test_c3_vanilla_golden.py -v
python3 -m unittest construction/tests/test_c2_build_ir.py -v
python3 -m unittest construction/tests/test_c0_foundation.py -v
python3 construction/scripts/validate_c0.py
```

Finish with `git diff --check HEAD^ --` over C9 workflow, lock, MCP package, C4/C7 touched files/tests, C9 tests, spec, plan, README, ARCHITECTURE, and STATUS.

- [ ] **Step 4: Commit RED1 and prove it on the exact SHA**

```bash
git add construction/upstream/harness/c9-mcp-lock.txt construction/tests/test_c9_agent_mcp.py .github/workflows/factory-construction-c9-agent-mcp.yml
git commit -m "test(construction): define C9 agent MCP contract"
```

Expected Actions result: dependency/workflow/spec checks pass, `test_c9_modules_exist` fails, C9 behavioral tests skip, inherited pre-C9 regressions remain green. Do not create production `construction/mcp/` files before this RED is captured.

---

### Task 2: Consolidate C4 registry validation and prove C7 parity

**Files:**
- Modify: `construction/core/modpack_registry.py`
- Modify: `construction/core/structural_qa.py`
- Modify: `construction/tests/test_c4_modpack_registry.py`
- Modify: `construction/tests/test_c7_registry_authority.py`
- Modify: `construction/tests/test_c9_agent_mcp.py`

**Interfaces:**
- Produces: `validate_modpack_registry(registry: object) -> list[str]` as the single public composed-registry validator.
- Consumes: existing C4 canonical JSON/fingerprint rules and C7 accepted/rejected fixture matrix.

- [ ] **Step 1: Add failing C4/C7 parity tests before implementation**

Add direct validator assertions:

```python
errors = modpack_registry.validate_modpack_registry(valid_registry)
self.assertEqual(errors, [])

tampered = copy.deepcopy(valid_registry)
tampered["blocks"][0]["authority"] = "invented"
self.assertTrue(any("authority" in error for error in modpack_registry.validate_modpack_registry(tampered)))
```

In C7 tests, freeze the valid report before the refactor and assert the refactored `run_structural_qa(...)` returns exactly the same dict. Preserve each existing invalid-registry case and assert it remains rejected.

- [ ] **Step 2: Run the focused RED**

```bash
python3 -m unittest construction/tests/test_c4_modpack_registry.py construction/tests/test_c7_registry_authority.py construction/tests/test_c9_agent_mcp.py -v
```

Expected: failures only because `validate_modpack_registry` does not exist yet and C9 module gates remain red/skipped.

- [ ] **Step 3: Implement the public C4 validator using existing C4 constants/helpers**

The function returns ordered strings rather than raising for validation failure:

```python
def validate_modpack_registry(registry: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(registry, dict):
        return ["registry must be an object"]
    if set(registry) != {"schema_version", "physical", "runtime", "static_index", "blocks", "content_sha256"}:
        errors.append("registry top-level fields do not match the C4 contract")
    physical = registry.get("physical")
    runtime = registry.get("runtime")
    static_index = registry.get("static_index")
    blocks = registry.get("blocks")
    if not isinstance(physical, dict):
        errors.append("registry.physical must be an object")
    if not isinstance(runtime, dict):
        errors.append("registry.runtime must be an object")
    if not isinstance(static_index, dict):
        errors.append("registry.static_index must be an object")
    if not isinstance(blocks, list):
        errors.append("registry.blocks must be an array")
    # The implementation then performs every exact C4 linkage, block/state,
    # canonical-order, and content_sha256 check enumerated below in this step.
    return errors
```

Do not change `build_modpack_registry(...)` output shape or schema version.

- [ ] **Step 4: Refactor C7 registry validation to delegate to C4**

Load C4 through a fixed repository-relative module path, call `validate_modpack_registry`, raise `StructuralQAError("invalid C4 registry: " + "; ".join(errors))` on any returned error, then continue using the unchanged registry document. Delete duplicated C4 structural validation from C7 only after parity tests prove no drift.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c4_modpack_registry.py construction/tests/test_c7_registry_authority.py construction/tests/test_c7_architecture_qa.py -v
git add construction/core/modpack_registry.py construction/core/structural_qa.py construction/tests/test_c4_modpack_registry.py construction/tests/test_c7_registry_authority.py construction/tests/test_c9_agent_mcp.py
git commit -m "refactor(construction): centralize C4 registry validation"
```

Expected: all focused C4/C7 tests pass and every pre-existing valid C7 report fixture remains byte/hash equivalent.

---

### Task 3: Implement the immutable content-addressed ArtifactStore

**Files:**
- Create: `construction/mcp/__init__.py`
- Create: `construction/mcp/artifacts.py`
- Create: `construction/mcp/errors.py`
- Modify: `construction/tests/test_c9_agent_mcp.py`

**Interfaces:**
- Produces: `ArtifactStore`, `ArtifactRecord`, `C9Error` and stable C9 error payloads.
- Later tasks consume `ArtifactStore.put`, `ArtifactStore.get`, and `ArtifactStore.list_descriptors`.

- [ ] **Step 1: Write ArtifactStore/error RED tests**

Freeze these public signatures:

```python
store = ArtifactStore()
descriptor = store.put(b"abc", media_type="application/octet-stream", kind="sponge_v3")
record = store.get(descriptor["uri"])
self.assertEqual(record.data, b"abc")
self.assertEqual(store.put(b"abc", media_type="application/octet-stream", kind="sponge_v3"), descriptor)
```

Test exact URI/hash/length, immutable record reuse, sorted descriptor listing, invalid URI, 64 MiB single-artifact boundary, 256 MiB aggregate boundary, 512-record boundary, and collision fail-closed behavior via an injected digest helper in tests rather than trying to produce a real SHA collision.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py -v
```

Expected: ArtifactStore imports fail because C9 modules are not implemented.

- [ ] **Step 3: Implement stable errors**

Use:

```python
class C9Error(ValueError):
    def __init__(self, code: str, message: str, *, authority: str | None = None, details: object | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.authority = authority
        self.details = details

    def payload(self) -> dict[str, object]:
        result: dict[str, object] = {"code": self.code, "message": self.message}
        if self.authority is not None:
            result["authority"] = self.authority
        if self.details is not None:
            result["details"] = self.details
        return result
```

Only permit codes `INVALID_INPUT`, `AUTHORITY_REJECTED`, `ARTIFACT_NOT_FOUND`, `ARTIFACT_LIMIT`, `INTERNAL_ERROR` and authority values `C2`-`C8` where applicable.

- [ ] **Step 4: Implement ArtifactStore**

Use a frozen record:

```python
@dataclass(frozen=True)
class ArtifactRecord:
    uri: str
    data: bytes
    media_type: str
    sha256: str
    byte_length: int
    kind: str
```

`put(...)` computes SHA-256 from exact bytes, rejects unsupported kinds/media types, enforces all three capacity limits before mutation, deduplicates identical bytes, and returns a descriptor dict. `get(uri)` accepts only the exact canonical URI regex. `list_descriptors()` returns descriptors sorted by URI. No disk I/O.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py -v
git add construction/mcp/__init__.py construction/mcp/artifacts.py construction/mcp/errors.py construction/tests/test_c9_agent_mcp.py
git commit -m "feat(construction): add C9 artifact store"
```

---

### Task 4: Implement façade parity for registry, palette and C2 operations

**Files:**
- Create: `construction/mcp/facade.py`
- Modify: `construction/tests/test_c9_agent_mcp.py`

**Interfaces:**
- Produces: `ConstructionFacade(store: ArtifactStore)` with `registry_search`, `palette_resolve`, `build_canonicalize`, `build_validate`.
- Consumes: C2, C4 public validator, C5, ArtifactStore, C9Error.

- [ ] **Step 1: Write focused RED parity tests**

Expected signatures:

```python
facade = ConstructionFacade(ArtifactStore())
facade.registry_search(registry, query=None, namespace=None, authority=None, safety=None, limit=25)
facade.palette_resolve(build_spec, registry, request)
facade.build_canonicalize(build_spec, placements)
facade.build_validate(build_ir)
```

Assert C5/C2 results equal direct authority calls exactly, except C9 producer metadata for canonicalization. Assert search is sorted by block ID and preserves C4 authority/availability/safety.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py -v
```

Expected: `ConstructionFacade` missing.

- [ ] **Step 3: Implement authority loading and normalized rejection**

Use fixed repository-relative module imports only. Wrap known C2/C4/C5 validation exceptions into:

```python
raise C9Error("AUTHORITY_REJECTED", "C5 rejected palette resolution input", authority="C5", details=[str(exc)])
```

Do not include traceback, absolute path, `repr(exc)`, environment, or machine data.

- [ ] **Step 4: Implement the four façade methods**

`registry_search` first calls `C4.validate_modpack_registry`; it rejects invalid registries, validates filter values, filters conjunctively, sorts by `id`, truncates after sort, and emits only `id`, `namespace`, `available`, `authority`, `safety`, `state_count`.

`palette_resolve` returns direct C5 output unchanged.

`build_canonicalize` calls:

```python
c2.canonicalize_build_ir(
    build_spec,
    placements,
    producer="construction-c9-mcp",
    producer_version="c9-mcp-v1",
)
```

`build_validate` returns exactly `{"valid": not errors, "errors": errors}` using C2's ordered list.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c5_modded_palette.py construction/tests/test_c2_build_ir.py -v
git add construction/mcp/facade.py construction/tests/test_c9_agent_mcp.py
git commit -m "feat(construction): expose C2 C4 C5 through C9 facade"
```

---

### Task 5: Implement bounded Build IR editing

**Files:**
- Modify: `construction/mcp/facade.py`
- Modify: `construction/tests/test_c9_agent_mcp.py`

**Interfaces:**
- Produces: `ConstructionFacade.build_edit(build_spec, build_ir, operations) -> dict`.
- Consumes: C2 `validate_build_ir`, `build_spec_fingerprint`, `canonical_block_state_string`, `canonicalize_build_ir`.

- [ ] **Step 1: Write RED tests for exact edit semantics**

Cover add, replace and remove plus all rejected cases:

```python
edited = facade.build_edit(
    build_spec,
    build_ir,
    [{"op": "set_block", "x": 1, "y": 1, "z": 1,
      "block_state": {"name": "minecraft:stone", "properties": {}}}],
)
self.assertEqual(c2.validate_build_ir(edited), [])
self.assertEqual(edited["metadata"]["producer"], "construction-c9-edit")
self.assertEqual(edited["metadata"]["producer_version"], "c9-mcp-v1")
```

Also assert duplicate coordinate touch in one request, absent remove, out of bounds, malformed op, explicit air, and mismatched BuildSpec fingerprint all fail as `INVALID_INPUT` or `AUTHORITY_REJECTED` according to the spec boundary.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py -v
```

- [ ] **Step 3: Implement minimal edit algorithm**

Validate C2 IR first. Expand current canonical blocks to a coordinate->state map using palette indices. Validate each operation in input order; reject touching the same coordinate twice. Apply `set_block` or `remove_block`. Reconstruct explicit placements sorted by coordinates and call C2 canonicalization with:

```python
producer="construction-c9-edit"
producer_version="c9-mcp-v1"
```

Never mutate the input dict in place.

- [ ] **Step 4: Run GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c2_build_ir.py -v
git add construction/mcp/facade.py construction/tests/test_c9_agent_mcp.py
git commit -m "feat(construction): add bounded C9 build edits"
```

---

### Task 6: Add C7 structural and C8 preview façade operations

**Files:**
- Modify: `construction/mcp/facade.py`
- Modify: `construction/tests/test_c9_agent_mcp.py`

**Interfaces:**
- Produces: `qa_structural`, `preview_render`, preview bundle manifest creation/validation helper.
- Consumes: C7 `run_structural_qa`, C8 `render_canonical_views`, C2 fingerprint, ArtifactStore.

- [ ] **Step 1: Write RED parity/determinism tests**

Assert:

```python
self.assertEqual(
    facade.qa_structural(build_spec, build_ir, registry),
    structural_qa.run_structural_qa(build_spec, build_ir, registry),
)
```

For preview, compare every resource's exact stored bytes to direct `render_canonical_views(build_ir)` bytes. Call twice and assert descriptors, bundle bytes and URIs are identical.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py -v
```

- [ ] **Step 3: Implement `qa_structural`**

Delegate directly to C7 and normalize only C7 rejection into `AUTHORITY_REJECTED` with `authority="C7"`.

- [ ] **Step 4: Implement `preview_render` and canonical manifest bytes**

Require renderer keys exactly in C8 canonical order. Put each SVG as `kind="preview_svg"`, `media_type="image/svg+xml"`. Build the exact schema-v1 manifest, encode with:

```python
def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
```

Store manifest as `kind="preview_bundle"`, `media_type="application/json"`.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c7_architecture_qa.py construction/tests/test_c8_visual_qa.py -v
git add construction/mcp/facade.py construction/tests/test_c9_agent_mcp.py
git commit -m "feat(construction): add C9 QA preview facade"
```

---

### Task 7: Add Visual QA bundle verification and Sponge export resources

**Files:**
- Modify: `construction/mcp/facade.py`
- Modify: `construction/tests/test_c9_agent_mcp.py`

**Interfaces:**
- Produces: `qa_visual`, `export_sponge_v3`.
- Consumes: C8 `run_visual_qa`, C6 `export_sponge_v3` + `validate_sponge_v3`, ArtifactStore.

- [ ] **Step 1: Write RED tests for bundle binding and C6 parity**

Prove matching bundles reproduce direct C8 output. Forge manifest bytes, remove a view artifact, alter a descriptor length/SHA, or pair a valid bundle with a different Build IR and assert fail-closed rejection. For Sponge export, assert stored bytes equal direct C6 bytes and C6 validator returns `[]`.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py -v
```

- [ ] **Step 3: Implement exact preview-bundle validation**

Resolve only ArtifactStore URIs, require `kind="preview_bundle"`, parse UTF-8 JSON, require exact fields, exact seven-view canonical order, descriptor/hash/byte-length equality to stored artifacts, and Build IR SHA equality to C2 fingerprint. Any mismatch is `INVALID_INPUT` or `ARTIFACT_NOT_FOUND`; do not silently rerender.

- [ ] **Step 4: Implement `qa_visual`**

Reconstruct `views: dict[str, bytes]` from verified artifacts and call C8 `run_visual_qa(...)` with all supplied provenance/review docs unchanged. Return direct C8 report.

- [ ] **Step 5: Implement `export_sponge_v3`**

Require `required_mods` to be unique and already sorted ascending. Call:

```python
payload = c6.export_sponge_v3(build_ir, required_mods=required_mods, block_entities=())
errors = c6.validate_sponge_v3(payload)
if errors:
    raise C9Error("AUTHORITY_REJECTED", "C6 rejected generated Sponge v3 bytes", authority="C6", details=errors)
```

Store exact bytes as `kind="sponge_v3"`, `media_type="application/octet-stream"`; output includes `artifact_kind="sponge_v3"`.

- [ ] **Step 6: Run GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c8_visual_qa.py construction/tests/test_c6_sponge_v3.py -v
git add construction/mcp/facade.py construction/tests/test_c9_agent_mcp.py
git commit -m "feat(construction): add C9 visual QA and Sponge export"
```

---

### Task 8: Implement the exact nine-tool MCP server and artifact resource template

**Files:**
- Create: `construction/mcp/server.py`
- Modify: `construction/tests/test_c9_agent_mcp.py`

**Interfaces:**
- Produces: module-level `mcp: MCPServer`, stdio entrypoint, nine tools, one artifact resource template.
- Consumes: `ConstructionFacade`, `ArtifactStore`, official MCP SDK v2.2.0.

- [ ] **Step 1: Write server-schema RED tests**

Import the server without running it. Use SDK server metadata/introspection APIs available in v2.2.0 to assert exact tool names and no prompts. Inspect each generated JSON Schema and assert `additionalProperties`/equivalent closure at the tool envelope and operation-object levels. Assert no tool parameter is named `path`, `url`, `host`, `port`, `command`, `code`, `package`, or `environment`.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py -v
```

- [ ] **Step 3: Define closed operation models and server singleton**

Use Pydantic models with `ConfigDict(extra="forbid")` for nested edit operations:

```python
class SetBlockOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["set_block"]
    x: int
    y: int
    z: int
    block_state: dict[str, object]

class RemoveBlockOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["remove_block"]
    x: int
    y: int
    z: int
```

Construct:

```python
STORE = ArtifactStore()
FACADE = ConstructionFacade(STORE)
mcp = MCPServer("Minecraft Construction Factory", version="c9-mcp-v1")
```

- [ ] **Step 4: Register exactly the nine tools**

Each `@mcp.tool()` function is a thin call into the matching façade method. It returns JSON-serializable dicts only. For anticipated `C9Error`, serialize `C9Error.payload()` with `json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` and raise `ToolError` with that canonical JSON string. MCP SDK v2.2.0 then returns `is_error=true` with textual content and `structured_content=None`; stdio tests must parse only the JSON suffix after the SDK's `Error executing tool <name>:` prefix. For an unexpected exception, log only `C9 internal tool failure` to stderr and raise `ToolError('{"code":"INTERNAL_ERROR","message":"internal C9 failure"}') from None`, never the exception text.

- [ ] **Step 5: Register the artifact resource template**

Use:

```python
@mcp.resource("construction://artifact/sha256/{digest}", mime_type="application/octet-stream")
def artifact(digest: str) -> bytes:
    uri = f"construction://artifact/sha256/{digest}"
    return STORE.get(uri).data
```

Because the SDK v2.2.0 resource contract converts `bytes` to `BlobResourceContents`, real client tests must verify exact decoded bytes. The descriptor returned by tools remains authoritative for the artifact's specific media type (`image/svg+xml`, `application/json`, or `application/octet-stream`); the template transport MIME remains generic because one template serves mixed binary kinds.

The dynamic artifact endpoint is a resource template and therefore appears in `resources/templates/list`, not as one concrete entry per artifact in `resources/list`. `ArtifactStore.list_descriptors()` is the deterministic current-artifact listing required by the C9 design; concrete resource reads still use the returned content-addressed URIs. Do not dynamically register per-artifact SDK resources merely to populate `resources/list`.

- [ ] **Step 6: Add stdio-only entrypoint and run unit GREEN**

```python
if __name__ == "__main__":
    mcp.run()
```

No transport argument means stdio in SDK v2.2.0. Do not import or call HTTP server helpers.

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py -v
git add construction/mcp/server.py construction/tests/test_c9_agent_mcp.py
git commit -m "feat(construction): add C9 stdio MCP server"
```

---

### Task 9: Prove real stdio protocol and Golden acceptance

**Files:**
- Create: `construction/tests/test_c9_mcp_stdio.py`
- Modify: `.github/workflows/factory-construction-c9-agent-mcp.yml`

**Interfaces:**
- Consumes: real `construction/mcp/server.py`, official `ClientSession`, `StdioServerParameters`, `stdio_client` from MCP SDK 2.2.0.
- Produces: protocol-level evidence independent of direct façade calls.

- [ ] **Step 1: Write the real stdio client helper**

Use the official v2.2.0 client API:

```python
params = StdioServerParameters(
    command=sys.executable,
    args=[str(ROOT / "construction" / "mcp" / "server.py")],
    cwd=str(ROOT),
)
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
```

Tests may spawn the subprocess; production server code may not expose subprocess capability.

- [ ] **Step 2: Add RED protocol tests**

Verify exact discovery order/set, one simple `build_validate` call through protocol serialization, malformed extra top-level input rejection, and clean teardown when the context exits.

- [ ] **Step 3: Add resource-read test**

Call `preview_render`, obtain `front` URI, call `session.read_resource(uri)`, assert the returned `BlobResourceContents.blob` decodes to exactly the checked-in C8 `front.svg` bytes.

- [ ] **Step 4: Add full Golden flow**

Through stdio only:

1. `build_validate` on checked-in C3 expected Build IR;
2. `preview_render` and read all seven resources;
3. `qa_visual` with the checked-in BuildSpec/review evidence and matching existing C8 context;
4. compare report to checked-in expected C8 report;
5. `export_sponge_v3`;
6. read exact `.schem` bytes and validate them through direct C6 validator in the test harness.

Do not invoke shell/filesystem tools because none exist.

- [ ] **Step 5: Run GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py -v
git add construction/tests/test_c9_mcp_stdio.py .github/workflows/factory-construction-c9-agent-mcp.yml
git commit -m "test(construction): prove C9 MCP stdio golden flow"
```

---

### Task 10: Harden the capability boundary and dependency contract

**Files:**
- Modify: `construction/tests/test_c9_agent_mcp.py`
- Modify: `construction/tests/test_c9_mcp_stdio.py`
- Modify: `.github/workflows/factory-construction-c9-agent-mcp.yml`

**Interfaces:**
- Produces: executable proof that the production C9 package stays local, stdio-only, deterministic and capability-limited.

- [ ] **Step 1: Add source-level security assertions**

Parse production C9 Python files with `ast` and fail if they import or call forbidden capability modules/functions:

```python
FORBIDDEN_IMPORT_ROOTS = {"subprocess", "socket", "requests", "httpx", "urllib", "ftplib", "paramiko"}
FORBIDDEN_CALL_NAMES = {"exec", "eval", "compile", "__import__"}
```

Also fail if server tool signatures contain caller filesystem/network/process parameter names from the spec.

- [ ] **Step 2: Add determinism/error sanitation tests**

Repeat identical direct and stdio calls and compare structured outputs, manifest bytes and artifact URIs. Force a known authority failure and assert no traceback marker, repository absolute path, environment variable dump or raw `repr` reaches the tool payload.

- [ ] **Step 3: Verify lock composition in CI**

Add:

```bash
python3 -m pip check
python3 -c 'from importlib.metadata import version; assert version("mcp") == "2.2.0"'
```

Ensure no unpinned `pip install mcp`, `pip install -U`, or dependency solve exists in the workflow.

- [ ] **Step 4: Run focused security GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py -v
git add construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py .github/workflows/factory-construction-c9-agent-mcp.yml
git commit -m "test(construction): harden C9 MCP capability boundary"
```

---

### Task 11: Run full inherited matrix and document the supported C9 boundary

**Files:**
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Modify: `.github/workflows/factory-construction-c9-agent-mcp.yml`

**Interfaces:**
- Produces: final documented C9 behavior and complete CI evidence before PR.

- [ ] **Step 1: Run the complete local/CI-equivalent C9 test matrix**

Run every command from the C9 workflow in order, including the real NeoForge runtime probe build. Do not mark this step complete until all commands pass on the exact branch head.

- [ ] **Step 2: Update README C9 scope**

Document exactly: stdio only, nine tools, content-addressed process-scoped artifacts, C4 public-validator consolidation, no prompt planner, no external providers, no runtime acceptance, no arbitrary shell/filesystem/network.

- [ ] **Step 3: Update ARCHITECTURE MCP boundary**

Replace the future-tense C9 section with the implemented authority flow:

```text
MCP host
  -> stdio C9 server
  -> closed tool schemas
  -> C9 facade
  -> C2/C4/C5/C6/C7/C8 authorities
  -> process-scoped content-addressed resources
```

Keep C10/C12/C13 boundaries explicit.

- [ ] **Step 4: Re-run docs-inclusive workflow and whitespace gate**

```bash
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py -v
git diff --check HEAD^ -- .github/workflows/factory-construction-c9-agent-mcp.yml construction/mcp construction/core/modpack_registry.py construction/core/structural_qa.py construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py construction/upstream/harness/c9-mcp-lock.txt docs/superpowers/specs/2026-09-11-construction-c9-agent-mcp-design.md docs/superpowers/plans/2026-09-11-construction-c9-agent-mcp.md construction/README.md construction/docs/ARCHITECTURE.md construction/STATUS.md
```

- [ ] **Step 5: Commit documentation**

```bash
git add construction/README.md construction/docs/ARCHITECTURE.md .github/workflows/factory-construction-c9-agent-mcp.yml
git commit -m "docs(construction): document C9 agent MCP boundary"
```

`construction/STATUS.md` must still be unchanged.

---

### Task 12: Review, PR, merge, exact-main validation, and status-only closeout

**Files:**
- No implementation-code changes unless review finds a concrete defect.
- Later, separate closeout branch modifies only `construction/STATUS.md`.

**Interfaces:**
- Produces: merged C9 implementation with exact-main evidence and C10 frontier only after post-merge validation.

- [ ] **Step 1: Perform implementation review against the approved spec**

Verify exact nine tools, no extra transport/capability, no C10/C12/C13 creep, C4/C7 authority consolidation, artifact limits, error sanitation, lock correctness, Golden parity, and that `construction/STATUS.md` is absent from implementation diff. Any finding gets its own RED test before a production fix.

- [ ] **Step 2: Reaudit `main`, open PRs and diff before opening the implementation PR**

If `main` advanced, compare files. If there is no overlap, synchronize the branch with current `main` and rerun applicable gates. If there is overlap, resolve minimally and rerun the full affected matrix.

- [ ] **Step 3: Open implementation PR**

Use title:

```text
feat(construction): add C9 agent MCP
```

PR body records RED runs, focused GREEN runs, final C9 run, exact MCP `2.2.0` pin, stdio Golden evidence, inherited C8-C0/runtime-probe evidence, C1A/C1B/Governance/Sonar state, and explicit C10/C12/C13 non-goals.

- [ ] **Step 4: Require all PR gates green and merge with frozen head SHA**

Do not merge on stale evidence. Immediately before merge, recheck current `main`, PR mergeability, checks, Sonar, reviews, comments and unresolved threads. Merge only with an exact expected head SHA.

- [ ] **Step 5: Validate exact merged `main`**

On the exact merge SHA, require C9 plus every triggered inherited Construction/C1/Governance/Sonar gate to complete successfully. Capture the C9 job log proving dependency lock, C4/C7 parity, C9 unit+stdio, C8-C0 regressions and NeoForge runtime probe.

- [ ] **Step 6: Create separate status-only closeout branch and PR**

Update only `construction/STATUS.md` with:

```text
PHASE=C9_COMPLETE_POSTMERGE_VALIDATED
NEXT_ACTION=BEGIN_C10_EXTERNAL_PROVIDERS
MANUAL_ACTION_REQUIRED=NO
```

Record implementation PR number, merge SHA, final PR head/run, exact post-merge C9 run and inherited gate evidence. Open a status-only PR, validate its triggered gates, merge with frozen head SHA, and validate the resulting `main` before declaring C9 complete.

---

## Plan Completion Gate

The implementation plan is complete only when:

- every spec section 1-19 maps to at least one task above;
- no task requires inventing an authority not defined by the spec or existing C2-C8 code;
- no placeholder such as `TODO`/`TBD` remains;
- exact public names are consistent across tasks;
- C9 implementation work begins only after this plan is committed and reviewed;
- execution uses TDD: RED evidence precedes each new behavior, and no `PASS` claim is made without the corresponding test/build/workflow evidence.
