# Construction C10 External Providers Design

Date: 2026-09-12
Status: design approved by delegated human review
Repository: `Gustavaopere/minecraft-mod-factory`
Construction frontier entering this design: `C9_COMPLETE_POSTMERGE_VALIDATED`
Canonical base at design start: `6ef8d9427b5c3f005616d9f7ebf3f8ace04cb198`

## 1. Purpose

C10 establishes the Construction-domain boundary for external structure-generation providers without promoting unverified web products, undocumented endpoints, browser automation, scraping, or provider-owned output into Factory authority.

The baseline providers already registered by C0 are `objtoschematic`, `structmatic`, `schematic-helper`, and `blockgpt`. Their canonical starting state is `integration_policy=EXTERNAL_PROVIDER` and `api_state=UNVERIFIED_API` in `construction/upstream/registry.json`.

C10 is handoff-first. A provider with no proven public API may become operational only through an evidence-backed manual handoff. Automated API integration is allowed only after an official callable contract is independently verified and Factory tests prove the adapter against that exact contract.

## 2. Authority baseline

C10 preserves the existing authority graph.

- Engineering I2 remains authority for the physical modlist, physical provider identity/version, JAR topology, and physical hashes.
- C4 `construction/core/modpack_registry.py` remains authority for installed block/state existence and runtime-backed registry evidence.
- C5 remains semantic palette authority.
- C2 remains Canonical Build IR authority.
- C6 remains canonical Sponge Schematic v3 export/validation authority.
- C7 remains structural Architecture QA authority.
- C8 remains deterministic offline preview and Visual QA authority.
- C9 remains the exact nine-tool, stdio-only MCP facade over C2/C4/C5/C6/C7/C8.
- `construction/upstream/registry.json` remains the coarse discovery/policy registry for known external providers.

C10 introduces a separate **Construction External Provider Profile** authority. It is not the Engineering provider catalog. A physical NeoForge dependency is an Engineering/I2 provider; a hosted structure-generation service is a Construction external provider. The two domains may reference one another by fingerprint but may not substitute for one another.

## 3. Physical target baseline

The design was revalidated against the latest supplied physical modlist snapshot:

- top-level mods: `595`;
- Minecraft: `1.21.1`;
- NeoForge: `21.1.248`;
- source SHA-256: `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`.

C10 does not duplicate this snapshot. Claims about modpack compatibility reference authoritative I2/C4 fingerprints.

## 4. Design principles

1. **Evidence before capability.** A capability is supported only when evidence records the exact claim.
2. **Manual before invented automation.** No proven public API means no API automation.
3. **External output is untrusted input.** Provider output has no Factory authority merely because it was generated successfully.
4. **No silent repair.** Invalid or unresolved external artifacts are rejected or deferred, never silently rewritten into apparent authority.
5. **Exact-source provenance.** Promotion decisions retain source/evidence locators and audit dates.
6. **No hidden network surface.** No undocumented endpoint, scraping, or browser automation substitutes for an API contract.
7. **No C9 scope creep.** C10 does not alter the C9 v1 tool catalog.
8. **Deterministic Factory boundary.** Provider nondeterminism may be recorded; Factory manifests, hashes, validation decisions, and state transitions remain deterministic.

## 5. Explicit non-goals

C10 does not add arbitrary browser automation, scraping, reverse-engineered/private HTTP endpoints, generic web-form automation, shell/code execution, arbitrary subprocess/package-install capability, arbitrary filesystem access, live Minecraft placement, full-modpack boot acceptance, runtime visual fidelity, worldgen integration, a natural-language architectural planner, a generic `generate_from_prompt` MCP tool, new C9 MCP tools/transports, silent format conversion, direct promotion of provider output to C2/C6/C7/C8 authority, versioned credentials, or any claim that an external service is an installed NeoForge provider.

C11 owns the first complex modded Golden using a proven C10 path. C12 owns runtime/in-game acceptance. C13 owns Skill/Router integration.

## 6. Selected architecture

```text
construction/upstream/registry.json
        |
        v
C10 External Provider Profiles
        |
        +--> evidence / proof state
        +--> declared capabilities
        +--> integration mode
        +--> input/output contracts
        +--> API/auth posture
        +--> Factory-enforced limits
        |
        v
Provider Handoff Request
        |
        +--> one manual action, or
        +--> proven API adapter
        |
        v
Provider Handoff Receipt
        |
        +--> exact artifact hashes
        +--> profile/request fingerprints
        +--> validation state
        |
        v
Factory validators / later C11 consumers
```

C10 owns the boundary contract and evidence lifecycle, not provider-generated voxel semantics.

## 7. Planned repository boundary

The implementation is expected to add only the structure justified by the real tree at implementation time:

- `construction/providers/` — C10 Factory-owned contracts and helpers;
- `construction/providers/profiles/` — versioned provider profiles;
- `construction/schemas/external-provider-profile.schema.json`;
- `construction/schemas/provider-handoff-request.schema.json`;
- `construction/schemas/provider-handoff-receipt.schema.json`;
- `construction/fixtures/c10/` — Factory-owned deterministic handoff fixtures and, when legally/operationally appropriate, exact smoke evidence;
- `construction/tests/` — C10 contract/security/regression tests;
- `.github/workflows/factory-construction-c10-external-providers.yml` — dedicated C10 gate.

If the implementation-time tree shows a better non-duplicative location, the plan must adapt to the real tree.

## 8. Canonical JSON and fingerprints

All C10 JSON fingerprints use:

- UTF-8;
- object keys sorted lexically;
- compact separators `,` and `:`;
- `ensure_ascii=false` semantics;
- exactly one final newline;
- SHA-256 lowercase hexadecimal.

A document fingerprint excludes only its own fingerprint field. No hidden wall-clock value is introduced during canonicalization.

## 9. Shared vocabularies

### 9.1 Capability values

The closed capability vocabulary is:

- `PROMPT_TO_STRUCTURE`;
- `IMAGE_TO_STRUCTURE`;
- `MESH_TO_STRUCTURE`;
- `STRUCTURE_EDITING`;
- `SCHEMATIC_IMPORT`;
- `SCHEMATIC_EXPORT`;
- `LITEMATIC_IMPORT`;
- `LITEMATIC_EXPORT`;
- `VANILLA_STRUCTURE_IMPORT`;
- `VANILLA_STRUCTURE_EXPORT`.

Capability presence never implies API availability or operational handoff proof.

### 9.2 Operational request values

The C10 v1 request `operation` values are only:

- `PROMPT_TO_STRUCTURE`;
- `IMAGE_TO_STRUCTURE`;
- `MESH_TO_STRUCTURE`;
- `STRUCTURE_EDITING`.

Import/export capability labels describe provider support but are not standalone v1 request operations.

### 9.3 Artifact kinds

The closed C10 v1 artifact-kind vocabulary is:

- `IMAGE`;
- `MESH`;
- `SCHEMATIC_FILE`;
- `LITEMATIC_FILE`;
- `VANILLA_STRUCTURE_NBT`;
- `BEDROCK_MCSTRUCTURE`;
- `WORLD_ZIP`.

A file artifact descriptor contains exactly:

```json
{
  "kind": "MESH",
  "sha256": "<64 lowercase hex>",
  "byte_length": 123,
  "media_type": "application/octet-stream",
  "repo_relpath": "construction/fixtures/c10/example/input.obj"
}
```

`repo_relpath` is either `null` or a normalized repository-relative path under `construction/fixtures/c10/`. It may not be absolute, contain `..`, traverse through symlinks, or name a directory. An external provider filename never becomes authority for this field.

## 10. External Provider Profile contract

Each operational profile is a closed JSON document with exactly:

```json
{
  "schema_version": 1,
  "provider_id": "objtoschematic",
  "display_name": "ObjToSchematic",
  "integration_policy": "EXTERNAL_PROVIDER",
  "proof_level": "EP0_DISCOVERED",
  "integration_mode": "RESEARCH_ONLY",
  "capabilities": [],
  "audit": {
    "audited_at": "2026-09-12",
    "evidence": []
  },
  "api": {
    "state": "UNVERIFIED_API",
    "auth": "UNKNOWN",
    "official_contract": null
  },
  "handoff": {
    "accepted_input_kinds": [],
    "output_artifact_kinds": [],
    "manual_action_required": true,
    "determinism": "UNKNOWN"
  },
  "limits": {
    "max_input_bytes": null,
    "max_output_bytes": null,
    "timeout_seconds": null
  },
  "profile_sha256": "<64 lowercase hex>"
}
```

Unknown fields fail. Empty arrays and `UNKNOWN`/`null` values are valid when evidence is absent. Invented provider claims are not.

`provider_id` must match a provider in `construction/upstream/registry.json` with `integration_policy=EXTERNAL_PROVIDER`, unless that same audited change adds the provider.

Capabilities are unique and lexically sorted. `accepted_input_kinds` and `output_artifact_kinds` use only the artifact-kind vocabulary, are unique, and are lexically sorted.

`handoff.determinism` is `YES`, `NO`, or `UNKNOWN`.

The three `limits` values are Factory-enforced limits, not claims about provider service limits. Null is allowed while `integration_mode=RESEARCH_ONLY`. `MANUAL_FILE_HANDOFF` requires positive `max_input_bytes` and `max_output_bytes`; `timeout_seconds` remains null. `API_ADAPTER` requires all three values to be positive integers.

## 11. Evidence contract

Every evidence record is closed and contains exactly:

```json
{
  "kind": "OFFICIAL_SITE",
  "locator": "https://example.invalid/",
  "observed_at": "2026-09-12",
  "supports": ["capability:MESH_TO_STRUCTURE"],
  "sha256": null
}
```

`kind` is one of `OFFICIAL_SITE`, `OFFICIAL_DOCS`, `OFFICIAL_SOURCE`, `MANUAL_SMOKE`, or `FACTORY_TEST`.

`locator` is a non-secret HTTPS URL, an exact `owner/repo@<40-hex-commit>` source locator, or a normalized `repo://construction/...` Factory evidence locator.

`supports` is non-empty, unique, and lexically sorted. `sha256` is null unless exact evidence bytes are under Factory control.

`OFFICIAL_SITE` may establish identity or advertised capability but cannot establish a callable API contract. API verification requires `OFFICIAL_DOCS` or `OFFICIAL_SOURCE` that defines the callable contract.

C10 does not archive third-party pages by default. URLs are provenance locators, not immutable evidence bytes.

## 12. Provider proof levels

Provider proof is independent from API proof.

- `EP0_DISCOVERED` — provider identity exists; no usable handoff is proven.
- `EP1_HANDOFF_VERIFIED` — an evidence-backed input/output handoff contract is known for the declared mode.
- `EP2_EXECUTION_PROVEN` — one real handoff completed successfully and exact returned artifact bytes were receipt-bound.
- `EP3_FORMAT_VALIDATED` — the returned artifact passed an applicable existing Factory format validator.
- `EP4_FACTORY_INTEGRATION_VALIDATED` — the validated artifact was consumed or normalized by an explicitly approved Factory boundary without authority invention.
- `EP5_GOLDEN_VALIDATED` — a deterministic/evidence-bound Golden proves the intended end-to-end provider path.

A provider may legitimately stop at EP2 when no approved validator accepts its exact output. Provider drift may demote the profile.

## 13. API proof state

API proof is a separate state machine:

- `UNVERIFIED_API`;
- `VERIFIED_API`;
- `CONTRACT_PROVEN_API`;
- `SMOKE_PROVEN_API`.

`api.auth` is one of `NONE`, `API_KEY`, `OAUTH`, `SESSION`, or `UNKNOWN`.

When `api.state=UNVERIFIED_API`, `official_contract` must be null.

When state is `VERIFIED_API` or above, `official_contract` is required and is a closed object containing exactly:

```json
{
  "kind": "REST",
  "locator": "https://provider.example/docs/api",
  "version": "v1",
  "origin": "https://api.provider.example",
  "protocol": "HTTPS"
}
```

`kind` is `REST`, `GRAPHQL`, `SDK`, or `OTHER`; `locator` and `origin` must be HTTPS; `version` is a non-empty stable provider version string or `UNVERSIONED`; `protocol` is `HTTPS` for a network adapter.

`VERIFIED_API` alone does not permit `API_ADAPTER`. `CONTRACT_PROVEN_API` is the minimum automation gate. Profiles never contain secret values.

## 14. Integration modes

Allowed values are `RESEARCH_ONLY`, `MANUAL_FILE_HANDOFF`, and `API_ADAPTER`.

- `RESEARCH_ONLY` is valid at any proof level and mandatory at EP0 when no handoff is proven.
- `MANUAL_FILE_HANDOFF` requires at least EP1 and may retain `UNVERIFIED_API`.
- `API_ADAPTER` requires `CONTRACT_PROVEN_API` or `SMOKE_PROVEN_API`.

A visible download button or observed web UI is not sufficient to promote a profile to `MANUAL_FILE_HANDOFF`; the actual handoff must be evidenced.

## 15. C0 registry reconciliation

C10 profiles extend `construction/upstream/registry.json`; they do not replace it.

The validator enforces:

1. every profile id exists upstream or is added in the same audited change;
2. the upstream entry is `EXTERNAL_PROVIDER`;
3. duplicate profile ids fail;
4. profile `UNVERIFIED_API` is compatible with upstream `UNVERIFIED_API`;
5. promotion above `UNVERIFIED_API` requires atomic reconciliation of the upstream registry with the same proof;
6. aggregate profile output is ordered by `provider_id`.

## 16. Provider Handoff Request

A handoff request is deterministic intent, not browser automation. It contains exactly:

```json
{
  "schema_version": 1,
  "request_id": "<64 lowercase hex>",
  "provider_id": "objtoschematic",
  "provider_profile_sha256": "<64 lowercase hex>",
  "mode": "MANUAL_FILE_HANDOFF",
  "operation": "MESH_TO_STRUCTURE",
  "text_input": null,
  "input_artifacts": [],
  "expected_output_kinds": ["SCHEMATIC_FILE"],
  "target": {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "physical_modlist_sha256": "<64 lowercase hex>"
  },
  "manual_step": {
    "required": true,
    "step_id": "submit-input",
    "instruction": "Upload the Factory-owned mesh fixture to the provider editor.",
    "expected_result": "The provider shows a generated block preview."
  }
}
```

`request_id` is the C10 canonical SHA-256 of the request excluding `request_id`.

Conditional input rules are exact:

- `PROMPT_TO_STRUCTURE`: `text_input` is non-empty UTF-8 text of at most 4000 characters and `input_artifacts=[]`;
- `IMAGE_TO_STRUCTURE`: exactly one `IMAGE` artifact; `text_input` is null or non-empty text of at most 4000 characters;
- `MESH_TO_STRUCTURE`: exactly one `MESH` artifact and `text_input=null`;
- `STRUCTURE_EDITING`: exactly one structure artifact (`SCHEMATIC_FILE`, `LITEMATIC_FILE`, or `VANILLA_STRUCTURE_NBT`) and non-empty `text_input` of at most 4000 characters describing the requested edit.

The operation must appear in the profile capability list and its input/output kinds must be compatible with the profile handoff lists.

`RESEARCH_ONLY` cannot create an operational request.

`MANUAL_FILE_HANDOFF` requires the closed `manual_step` object and describes exactly one human action. `API_ADAPTER` requires `manual_step=null` and a profile API state that permits automation.

Requests contain no credentials, arbitrary absolute paths, cookies, browser sessions, executable code, or guessed endpoints.

## 17. Provider Handoff Receipt

A receipt contains exactly:

```json
{
  "schema_version": 1,
  "request_id": "<64 lowercase hex>",
  "provider_id": "objtoschematic",
  "provider_profile_sha256": "<64 lowercase hex>",
  "mode": "MANUAL_FILE_HANDOFF",
  "received_artifacts": [],
  "provider_metadata": {},
  "factory_validation": {
    "state": "UNVALIDATED",
    "validators": []
  },
  "receipt_sha256": "<64 lowercase hex>"
}
```

Each received artifact uses the descriptor from section 9.3. `receipt_sha256` is the C10 canonical SHA-256 excluding `receipt_sha256`.

For C10 v1, `provider_metadata` is exactly `{}`.

`factory_validation.state` is `UNVALIDATED`, `FORMAT_VALIDATED`, `FACTORY_NORMALIZED`, or `GOLDEN_ACCEPTED`.

Each validator record is closed and contains exactly:

```json
{
  "stage": "FORMAT",
  "authority": "construction.core.sponge_v3.validate_sponge_v3",
  "artifact_sha256": "<64 lowercase hex>",
  "result": "PASS",
  "evidence_ref": "repo://construction/fixtures/c10/example/validation.json"
}
```

`stage` is `FORMAT`, `NORMALIZE`, or `GOLDEN`; `result` is `PASS` or `FAIL`; `evidence_ref` is a normalized `repo://construction/...` locator.

State advancement rules are fail-closed:

- `FORMAT_VALIDATED` requires at least one `FORMAT/PASS` record bound to every artifact claimed as format-validated;
- `FACTORY_NORMALIZED` additionally requires at least one `NORMALIZE/PASS` record;
- `GOLDEN_ACCEPTED` additionally requires at least one `GOLDEN/PASS` record;
- state may not skip a lower state;
- a FAIL record cannot be used to advance state.

Receipt creation proves provenance and byte identity only.

## 18. Artifact trust boundary

Every provider artifact enters as untrusted bytes. C10 enforces artifact kind, media type, exact byte length, SHA-256, configured size limits before deep parsing, no arbitrary archive extraction, no execution, no trust in provider filenames, no network dereference from artifact content, and fail-closed parsing.

Format-specific authority remains elsewhere. A Sponge v3 candidate may be submitted to C6. C6 may reject a provider `.schem` that does not match the strict Factory Sponge v3 contract; that rejection leaves the provider at EP2 rather than inventing EP3 success. A valid external schematic is not C2 Build IR unless a separately approved importer proves semantic conversion.

## 19. Manual handoff lifecycle

```text
Factory creates request
→ exactly one manual provider action
→ user reports the expected result or returns one artifact
→ Factory records/validates that result
→ Factory emits the next single manual action only if required
```

Manual smoke evidence binds the exact provider profile fingerprint, request fingerprint, and returned artifact hashes. Screenshots may supplement but cannot replace byte identity when an artifact is expected.

## 20. Initial controlled smoke target

The preferred initial manual smoke is ObjToSchematic because current official evidence advertises direct mesh upload and schematic export without requiring C10 to invent a generation engine.

The smoke uses a tiny Factory-owned deterministic OBJ fixture committed under `construction/fixtures/c10/objtoschematic-smoke/`. The sequence is deliberately split into separate manual actions:

1. upload the exact fixture and confirm the provider produces a block preview;
2. only after that evidence is recorded, export a `.schem` and return the exact file to the Factory;
3. Factory hashes/stages the returned bytes and creates the receipt;
4. Factory attempts C6 validation without weakening C6. Passing may promote to EP3; failing leaves the provider legitimately at EP2.

If the current provider cannot complete this flow, C10 records the failure and audits the next baseline provider rather than automating the UI.

## 21. API adapter promotion

An API adapter may be implemented only when official docs/source prove a callable contract, the profile is at least `VERIFIED_API`, origin/protocol/auth are known, a RED contract test exists first, request/response schemas are bounded, all limits are explicit, redirect/origin policy is explicit, credentials are runtime-injected and never versioned/logged, errors are sanitized, contract tests promote to `CONTRACT_PROVEN_API`, and a real authorized smoke is required for `SMOKE_PROVEN_API`.

If no baseline provider reaches this gate, C10 ships no generic HTTP framework.

## 22. Network and credential security

The baseline C10 runtime is network-free. Profile validation, request generation, receipt validation, artifact hashing, and manual smoke evidence processing require no outbound network.

A future proven API adapter must enforce an evidence-bound allowlisted origin, no caller-supplied arbitrary URL, no redirect to unallowlisted origin, TLS verification, explicit timeouts, request/response size limits, runtime-only secret injection, no secrets in manifests/receipts/logs/hashes/exceptions, and untrusted-response parsing.

No versioned C10 file may contain API keys, tokens, cookies, passwords, OAuth refresh tokens, or session material.

## 23. Filesystem security

C10 core contracts operate on bytes and JSON, not arbitrary absolute paths.

Any CLI wrapper may resolve only normalized paths inside the Factory workspace or an explicitly configured staging root and rejects traversal, workspace root as a file, device/special files, symlink escape, recursive directory ingestion, and overwrite without explicit contract.

Provider filenames are labels only. Factory-owned destinations are derived independently.

## 24. Drift and re-audit

C10 does not poll provider websites or APIs to detect drift.

Runtime drift detection is deterministic: any request or receipt whose `provider_profile_sha256` differs from the current exact profile fingerprint fails with `PROVIDER_DRIFT_DETECTED` until re-audited/reissued.

Human/evidence re-audit is required when identity/URL, manual handoff, accepted inputs, export artifact kind/version, API version/endpoint, auth, contract-relevant limits, or output behavior changes. Re-audit may demote proof level, API state, or integration mode.

A changed physical modlist likewise invalidates compatibility claims bound to an older `physical_modlist_sha256` until revalidated.

## 25. Error model

Stable fail-closed categories are:

- `INVALID_PROVIDER_PROFILE`;
- `UNKNOWN_PROVIDER`;
- `PROOF_LEVEL_INSUFFICIENT`;
- `INTEGRATION_MODE_NOT_ALLOWED`;
- `CAPABILITY_NOT_PROVEN`;
- `UNVERIFIED_API`;
- `INVALID_HANDOFF_REQUEST`;
- `REQUEST_PROFILE_MISMATCH`;
- `INVALID_HANDOFF_RECEIPT`;
- `ARTIFACT_LIMIT_EXCEEDED`;
- `ARTIFACT_HASH_MISMATCH`;
- `ARTIFACT_KIND_UNSUPPORTED`;
- `FORMAT_VALIDATION_FAILED`;
- `MANUAL_ACTION_REQUIRED`;
- `PROVIDER_DRIFT_DETECTED`;
- `INTERNAL_ERROR`.

Errors crossing a CLI/agent boundary expose no secret, provider response body, machine-local absolute path, or stack trace.

## 26. Interaction with C9 MCP

C9 v1 remains unchanged and advertises exactly:

1. `registry_search`
2. `palette_resolve`
3. `build_canonicalize`
4. `build_validate`
5. `build_edit`
6. `qa_structural`
7. `preview_render`
8. `qa_visual`
9. `export_sponge_v3`

C10 adds no provider/browser/network/filesystem/credential MCP tool. Any future agent-facing provider surface requires a separately versioned design; C13 remains the routing/orchestration frontier.

## 27. Initial provider posture

At the baseline before manual smoke:

- `objtoschematic`: `EP0_DISCOVERED`, `RESEARCH_ONLY`, `UNVERIFIED_API`;
- `structmatic`: `EP0_DISCOVERED`, `RESEARCH_ONLY`, `UNVERIFIED_API`;
- `schematic-helper`: `EP0_DISCOVERED`, `RESEARCH_ONLY`, `UNVERIFIED_API`;
- `blockgpt`: `EP0_DISCOVERED`, `RESEARCH_ONLY`, `UNVERIFIED_API`.

Official-site evidence may populate advertised `capabilities`; operational `handoff.accepted_input_kinds` and `output_artifact_kinds` stay empty until EP1 evidence exists.

## 28. Testing strategy

C10 follows `RED → minimum GREEN → refactor → integration smoke`.

The dedicated suite proves at least:

1. required C10 files/schemas exist;
2. schemas are closed;
3. baseline provider ids reconcile with C0;
4. unknown/duplicate providers fail;
5. profile fingerprinting is deterministic;
6. capability/evidence vocabularies are closed and ordered;
7. `MANUAL_FILE_HANDOFF` fails below EP1;
8. `API_ADAPTER` fails below `CONTRACT_PROVEN_API`;
9. API official-contract conditional rules are enforced;
10. upstream/profile API state cannot drift silently;
11. request fingerprints are deterministic;
12. each operation enforces its exact input shape;
13. `RESEARCH_ONLY` cannot create operational requests;
14. manual requests contain exactly one manual step;
15. API requests require `manual_step=null`;
16. receipts bind exact request/profile fingerprints;
17. current-profile SHA mismatch yields provider drift;
18. hash-mismatched artifacts fail;
19. size limits fail before deep parsing;
20. repository/staging paths cannot escape allowed roots;
21. no fixture contains credentials/secrets;
22. validation state cannot advance without the required PASS evidence;
23. C9 still exposes exactly nine tools;
24. inherited C0-C9 regression gates remain green.

Future API adapters get additional RED/GREEN coverage for allowlisted origin, auth injection, timeouts, size limits, response validation, sanitization, and real smoke.

## 29. CI gate

The dedicated C10 workflow runs on relevant pull requests and `main` and includes C10 tests, C0 registry validation, relevant C4/C5/C6/C7/C8/C9 regressions, Engineering I2 where physical-target linkage is exercised, whitespace, governance/security, and inherited Sonar/CodeQL gates when repository policy triggers them.

Initial profile/manual-handoff validation requires no provider credentials and no outbound network. A green offline CI result is not evidence of a real provider smoke.

## 30. Acceptance criteria

C10 baseline is complete only when all of the following are proven on the exact merged main revision:

1. provider profile schema/validator exist;
2. all current external providers have explicit profiles or an explicit exclusion reason;
3. profiles reconcile with C0 without duplicating I2/C4 physical authority;
4. EP0-EP5 rules are enforced;
5. API-state promotion rules are enforced;
6. request/receipt contracts are deterministic and fail closed;
7. artifact trust states and hash binding are enforced;
8. no undocumented provider network call, scraping, or browser automation exists;
9. no versioned secret exists;
10. C9 still advertises exactly nine tools and C9 stdio acceptance is green;
11. triggered inherited Construction/Governance/Sonar/CodeQL gates required by repository policy pass;
12. at least one baseline provider reaches `EP2_EXECUTION_PROVEN` through a controlled manual handoff smoke, unless all four are independently evidenced as unavailable for such a handoff; in that exceptional case C10 closes blocked rather than inventing success;
13. exact PR head, merge SHA, run ids, provider proof states, and postmerge evidence are recorded;
14. `construction/STATUS.md` advances only after postmerge validation.

## 31. Expected closeout state

After successful implementation and postmerge validation:

```text
PHASE=C10_COMPLETE_POSTMERGE_VALIDATED
NEXT_ACTION=BEGIN_C11_COMPLEX_MODDED_GOLDEN
MANUAL_ACTION_REQUIRED=NO
```

`MANUAL_ACTION_REQUIRED=NO` means no unresolved setup action blocks C10 closeout. A provider may still require manual handoff during ordinary operation.

## 32. Decision summary

C10 adopts the approved handoff-first architecture:

- external-provider evidence is explicit and versioned;
- C0 remains coarse registry; C10 profiles become operational external-provider authority;
- Engineering I2/C4 remain physical modpack authorities;
- manual handoff requires evidence before promotion;
- API automation requires official contract proof, RED/GREEN tests, and smoke evidence;
- external artifacts remain untrusted until Factory validation advances their state;
- profile SHA and physical-modlist SHA provide deterministic drift boundaries;
- C9 v1 is unchanged;
- C11 consumes the first complex proven provider path;
- C12 owns runtime acceptance;
- C13 owns Skill/Router integration.
