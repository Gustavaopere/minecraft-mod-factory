# Construction C10 External Providers Design

Date: 2026-09-12
Status: design approved in chat; written specification awaiting human review
Repository: `Gustavaopere/minecraft-mod-factory`
Construction frontier entering this design: `C9_COMPLETE_POSTMERGE_VALIDATED`
Canonical base at design start: `6ef8d9427b5c3f005616d9f7ebf3f8ace04cb198`

## 1. Purpose

C10 establishes the Construction-domain boundary for external structure-generation providers without promoting unverified web products, undocumented endpoints, browser automation, scraping, or provider-owned output into Factory authority.

The baseline providers already registered by C0 are:

- `objtoschematic`;
- `structmatic`;
- `schematic-helper`;
- `blockgpt`.

Their canonical starting state is `integration_policy=EXTERNAL_PROVIDER` and `api_state=UNVERIFIED_API` in `construction/upstream/registry.json`.

C10 is file-handoff-first. A provider with no proven public API may become operational only through an evidence-backed manual file handoff. Automated API integration is permitted only after an official callable API contract has been independently verified and Factory tests prove the adapter against that exact contract.

## 2. Authority baseline

C10 must preserve the existing authority graph.

- Engineering I2 remains authority for the physical modlist, physical provider identity/version, JAR topology, and physical hashes.
- C4 `construction/core/modpack_registry.py` remains authority for installed block/state existence and runtime-backed registry evidence.
- C5 remains semantic palette authority.
- C2 remains Canonical Build IR authority.
- C6 remains canonical Sponge Schematic v3 export/validation authority.
- C7 remains structural Architecture QA authority.
- C8 remains deterministic offline preview and Visual QA authority.
- C9 remains the exact nine-tool, stdio-only MCP façade over C2/C4/C5/C6/C7/C8.
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

C10 does not add:

- arbitrary browser automation or scraping;
- reverse-engineered/private HTTP endpoints;
- generic web-form automation;
- shell, arbitrary Python/code execution, subprocess, or package-install capabilities;
- arbitrary filesystem access;
- live Minecraft placement;
- full-modpack boot acceptance;
- runtime visual fidelity;
- worldgen integration;
- a natural-language architectural planner;
- a generic `generate_from_prompt` MCP tool;
- new C9 MCP tools or transports;
- silent format conversion among `.schem`, `.litematic`, vanilla structure NBT, mesh formats, or provider-private formats;
- direct promotion of provider output to C2/C6/C7/C8 authority;
- versioned credentials;
- treating an external service as an installed NeoForge provider.

C11 owns the first complex modded Golden using a proven C10 path. C12 owns runtime/in-game acceptance. C13 owns Skill/Router integration.

## 6. Selected architecture

```text
construction/upstream/registry.json
        |
        | coarse provider registry
        v
C10 External Provider Profiles
        |
        +--> evidence/proof state
        +--> declared capabilities
        +--> integration mode
        +--> input/output contracts
        +--> API/auth posture
        +--> deterministic limits
        |
        v
Provider Handoff Request
        |
        +--> one manual step, or
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

- `construction/providers/` — C10 provider-profile and handoff logic;
- `construction/providers/profiles/` — versioned provider profiles;
- `construction/schemas/external-provider-profile.schema.json`;
- `construction/schemas/provider-handoff-request.schema.json`;
- `construction/schemas/provider-handoff-receipt.schema.json`;
- `construction/tests/` — C10 contract/security/regression tests;
- `.github/workflows/factory-construction-c10-external-providers.yml` — dedicated C10 gate.

If the implementation-time tree shows a better non-duplicative location, the plan must adapt to the real tree.

## 8. Canonical JSON and fingerprints

All C10 JSON fingerprints use the same deterministic rule:

- UTF-8;
- object keys sorted lexically;
- compact separators `,` and `:`;
- `ensure_ascii=false` semantics;
- exactly one final newline;
- SHA-256 lowercase hexadecimal.

A document fingerprint excludes only its own fingerprint field. Timestamps or audit dates remain part of a fingerprint when they are fields in the fingerprinted document; no hidden wall-clock value is introduced during canonicalization.

## 9. External Provider Profile contract

Each operational profile is a closed JSON document. Unknown fields fail validation.

Logical fields are exactly:

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

Empty arrays and `UNKNOWN`/`null` values are valid when evidence is absent. Invented defaults are not.

### 9.1 Provider identity

`provider_id` is stable and lowercase. It must match an entry in `construction/upstream/registry.json` with `integration_policy=EXTERNAL_PROVIDER`, unless that same change adds the newly audited provider to the upstream registry.

### 9.2 Capability vocabulary

Initial capability values are limited to:

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

A capability appears only when evidence supports that exact claim. Capability presence never implies API availability.

### 9.3 Integration modes

Allowed values:

- `RESEARCH_ONLY`;
- `MANUAL_FILE_HANDOFF`;
- `API_ADAPTER`.

Rules:

- `RESEARCH_ONLY` is valid at any proof level and is mandatory at `EP0_DISCOVERED` when no usable handoff is proven;
- `MANUAL_FILE_HANDOFF` requires at least `EP1_HANDOFF_VERIFIED` and does not require any API state beyond `UNVERIFIED_API`;
- `API_ADAPTER` requires `api.state=CONTRACT_PROVEN_API` or `SMOKE_PROVEN_API`.

A visible download button or observed web UI is not enough to promote a profile to `MANUAL_FILE_HANDOFF`; the actual file handoff must be evidenced.

## 10. Provider proof levels

The provider proof ladder is independent from API proof so manual providers can advance without pretending to have an API.

- `EP0_DISCOVERED` — provider identity exists; no usable handoff is proven.
- `EP1_HANDOFF_VERIFIED` — an evidence-backed input/output handoff contract is known for the declared mode.
- `EP2_EXECUTION_PROVEN` — one real handoff completed successfully and exact returned artifact bytes were receipt-bound.
- `EP3_FORMAT_VALIDATED` — the returned artifact passed an applicable Factory format validator.
- `EP4_FACTORY_INTEGRATION_VALIDATED` — the validated artifact was successfully consumed or normalized by an explicitly approved Factory boundary without authority invention.
- `EP5_GOLDEN_VALIDATED` — a deterministic/evidence-bound Golden proves the intended end-to-end provider path.

The ladder is monotonic only while all evidence supporting the current and lower levels remains valid. Provider drift may demote the profile.

A provider can legitimately stop at EP2 when no approved parser/validator exists for its output format.

## 11. API proof state

API proof is a separate state machine:

- `UNVERIFIED_API` — no authoritative callable API contract is proven;
- `VERIFIED_API` — official docs/source prove endpoint/protocol shape and authentication posture;
- `CONTRACT_PROVEN_API` — Factory adapter contract tests prove request construction, bounded response parsing, errors, limits, and auth injection against the verified contract;
- `SMOKE_PROVEN_API` — a real authorized provider call succeeds against the exact contract and records a receipt.

`VERIFIED_API` alone does not permit `integration_mode=API_ADAPTER`; `CONTRACT_PROVEN_API` is the minimum automation gate.

Profiles never contain secret values. `api.auth` describes only the mechanism: `NONE`, `API_KEY`, `OAUTH`, `SESSION`, or `UNKNOWN`.

A browser/session-only workflow without a documented callable contract remains non-automated.

## 12. Evidence contract

Each profile contains an ordered evidence array. Every evidence record is closed and contains:

- `kind`: `OFFICIAL_SITE`, `OFFICIAL_DOCS`, `OFFICIAL_SOURCE`, `MANUAL_SMOKE`, or `FACTORY_TEST`;
- `locator`: non-secret URL, repository/ref, or Factory evidence locator;
- `observed_at`: explicit date or timestamp;
- `supports`: non-empty ordered array of exact claims supported by the evidence;
- optional `sha256` only when exact evidence bytes are under Factory control.

Claim examples include:

- `capability:MESH_TO_STRUCTURE`;
- `handoff:SPONGE_SCHEMATIC`;
- `proof:EP1_HANDOFF_VERIFIED`;
- `api:VERIFIED_API`.

`OFFICIAL_SITE` may establish identity or advertised capability but cannot by itself establish `VERIFIED_API`. API verification requires official docs/source defining a callable contract.

C10 does not archive third-party pages by default. URLs are provenance locators, not immutable evidence bytes.

## 13. C0 registry reconciliation

C10 profiles extend `construction/upstream/registry.json`; they do not replace it.

The validator must enforce:

1. every profile id exists in the upstream registry or is added there in the same audited change;
2. the upstream entry is `EXTERNAL_PROVIDER`;
3. duplicate profile ids fail;
4. profile `api.state=UNVERIFIED_API` is compatible with upstream `api_state=UNVERIFIED_API`;
5. any promotion above `UNVERIFIED_API` requires the upstream registry to be reconciled atomically with the same proof;
6. aggregate profile output sorts by `provider_id`.

This preserves one coarse discovery registry and one operational C10 profile authority.

## 14. Provider Handoff Request

A handoff request is a deterministic intent manifest, not executable browser automation.

Logical fields are exactly:

```json
{
  "schema_version": 1,
  "request_id": "<64 lowercase hex>",
  "provider_id": "objtoschematic",
  "provider_profile_sha256": "<64 lowercase hex>",
  "mode": "MANUAL_FILE_HANDOFF",
  "operation": "MESH_TO_STRUCTURE",
  "input_artifacts": [
    {
      "kind": "MESH",
      "sha256": "<64 lowercase hex>",
      "byte_length": 123,
      "media_type": "application/octet-stream"
    }
  ],
  "expected_output_kinds": ["SCHEMATIC_FILE"],
  "target": {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "physical_modlist_sha256": "<64 lowercase hex>"
  },
  "manual_step": {
    "required": true,
    "step_id": "submit-input",
    "instruction": "<single bounded action>",
    "expected_result": "<single artifact or confirmation>"
  }
}
```

`request_id` is the C10 canonical SHA-256 of the request excluding `request_id`.

Conditional rules:

- `RESEARCH_ONLY` cannot create an operational handoff request;
- `MANUAL_FILE_HANDOFF` requires `manual_step` to be the closed object above and describes exactly one manual action;
- `API_ADAPTER` requires `manual_step=null` and is legal only when the profile API state permits automation.

Requests contain no credentials, arbitrary local paths, cookies, browser sessions, executable code, or guessed endpoints.

## 15. Provider Handoff Receipt

A receipt records what actually returned from the external boundary.

Logical fields are exactly:

```json
{
  "schema_version": 1,
  "request_id": "<64 lowercase hex>",
  "provider_id": "objtoschematic",
  "provider_profile_sha256": "<64 lowercase hex>",
  "mode": "MANUAL_FILE_HANDOFF",
  "received_artifacts": [
    {
      "kind": "SCHEMATIC_FILE",
      "sha256": "<64 lowercase hex>",
      "byte_length": 456,
      "media_type": "application/octet-stream"
    }
  ],
  "provider_metadata": {},
  "factory_validation": {
    "state": "UNVALIDATED",
    "validators": []
  },
  "receipt_sha256": "<64 lowercase hex>"
}
```

`receipt_sha256` is the C10 canonical SHA-256 excluding `receipt_sha256`.

For C10 v1, `provider_metadata` is exactly an empty object. Provider-specific metadata is not accepted until a later explicit schema extension defines it.

Receipt creation proves provenance and byte identity only. It does not prove format validity, safety, canonicality, modpack compatibility, visual acceptance, or runtime compatibility.

`factory_validation.state` is one of:

- `UNVALIDATED`;
- `FORMAT_VALIDATED`;
- `FACTORY_NORMALIZED`;
- `GOLDEN_ACCEPTED`.

State may advance only when the named Factory validator/normalizer/Golden evidence is recorded in `validators`.

## 16. Artifact trust boundary

Every provider artifact enters as untrusted bytes.

C10 enforces, where applicable:

- explicit artifact kind;
- media type;
- exact byte length;
- SHA-256;
- configured size limits before deep parsing;
- no archive extraction to arbitrary paths;
- no execution of embedded code or binaries;
- no trust in provider-supplied filenames;
- no network dereference from artifact content;
- fail-closed parsing.

Format-specific authority remains elsewhere. A Sponge v3 candidate may be submitted to C6 when it matches the target contract. A file with no approved Factory parser remains `UNVALIDATED`. A valid external schematic is still not C2 Build IR unless a separately approved importer proves semantic conversion.

## 17. Manual file handoff

Manual handoff is the primary operational mode for a provider without a proven API.

```text
Factory creates request
→ one manual provider action
→ user returns one expected artifact/confirmation
→ Factory records receipt
→ Factory validates/hash-binds result
→ next manual action is generated only if needed
```

C10 may provide Factory-side request/receipt helpers but must not automate the provider UI.

Manual smoke evidence binds the exact provider profile fingerprint, request fingerprint, and returned artifact hashes. Screenshots may be supplementary evidence but cannot substitute for artifact byte identity.

## 18. API adapter promotion

An API adapter may be implemented only when:

1. official docs/source prove a callable contract;
2. profile API state is promoted to `VERIFIED_API` with evidence;
3. exact origin/protocol and auth mechanism are known;
4. a RED contract test is written first;
5. request/response schemas are bounded;
6. payload and timeout limits are explicit;
7. redirect/origin policy is explicit;
8. credentials are runtime-injected and never versioned/logged;
9. errors are sanitized;
10. Factory tests promote the state to `CONTRACT_PROVEN_API` before `API_ADAPTER` mode is allowed;
11. a real provider smoke is required for `SMOKE_PROVEN_API` and `EP2_EXECUTION_PROVEN`.

If no baseline provider reaches this gate, C10 does not ship an unused generic HTTP framework. YAGNI wins.

## 19. Network and credential security

The default C10 runtime is network-free.

Profile validation, request generation, receipt validation, and artifact hashing require no outbound network.

A future proven API adapter must enforce:

- evidence-bound allowlisted origin;
- no caller-supplied arbitrary URL;
- no redirect to an unallowlisted origin;
- TLS verification;
- explicit connect/read/total timeouts;
- request/response size limits;
- credentials only from approved runtime secret injection;
- no secrets in manifests, receipts, logs, hashes, or exception text;
- untrusted-response parsing.

No versioned C10 file may contain API keys, tokens, cookies, passwords, OAuth refresh tokens, or session material.

## 20. Filesystem security

C10 core contracts operate on bytes and JSON, not arbitrary absolute paths.

Any CLI wrapper for manual handoff may resolve only paths inside the Factory workspace or an explicitly configured staging root and must reject:

- traversal;
- workspace root as an artifact file;
- device/special files;
- symlink escape;
- implicit recursive directory ingestion;
- output overwrite without explicit contract.

Provider filenames are labels only. Factory-owned destinations are derived independently.

## 21. Determinism

Provider-side determinism is recorded separately from Factory determinism.

`handoff.determinism` is `YES`, `NO`, or `UNKNOWN`.

Regardless of provider behavior, Factory operations are deterministic for identical inputs:

- profile canonicalization/fingerprint;
- request fingerprint;
- receipt fingerprint;
- artifact hashes;
- validation ordering;
- error ordering;
- catalog ordering.

## 22. Error model

Stable fail-closed categories include:

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

Errors crossing a CLI/agent boundary expose no secrets, arbitrary provider response bodies, machine-local paths, or stack traces.

## 23. Drift and re-audit

A profile requires re-audit when any contract-relevant provider behavior changes, including:

- provider identity/URL;
- manual handoff flow;
- accepted inputs;
- exported artifact kind/version;
- API version/endpoint;
- authentication;
- contract-relevant usage limits;
- output behavior that breaks an established validator/Golden.

Drift may demote proof level, API state, or integration mode. Demotion is the expected fail-closed behavior when evidence becomes stale.

## 24. Interaction with the physical modpack

Provider claims about modded blocks are not physical authority.

Any artifact intended for the current pack must ultimately be checked against exact current I2/C4 evidence before the Factory may call it modpack-compatible.

Handoff requests carry the physical-modlist fingerprint. If the modlist changes, earlier artifacts may still exist, but their compatibility claim becomes stale until revalidated.

C10 profiles never copy the full physical modlist.

## 25. Interaction with C9 MCP

C9 v1 remains unchanged through C10 and continues to advertise exactly:

1. `registry_search`
2. `palette_resolve`
3. `build_canonicalize`
4. `build_validate`
5. `build_edit`
6. `qa_structural`
7. `preview_render`
8. `qa_visual`
9. `export_sponge_v3`

C10 adds no provider/browser/network/filesystem/credential MCP tool. Any future agent-facing provider surface requires a separately versioned MCP design; C13 remains the planned routing/orchestration frontier.

## 26. Initial provider posture

At the written-spec baseline:

- `objtoschematic`: `EP0_DISCOVERED`, `RESEARCH_ONLY`, `UNVERIFIED_API`;
- `structmatic`: `EP0_DISCOVERED`, `RESEARCH_ONLY`, `UNVERIFIED_API`;
- `schematic-helper`: `EP0_DISCOVERED`, `RESEARCH_ONLY`, `UNVERIFIED_API`;
- `blockgpt`: `EP0_DISCOVERED`, `RESEARCH_ONLY`, `UNVERIFIED_API`.

This is deliberately conservative. The implementation may promote a provider to `EP1_HANDOFF_VERIFIED` and `MANUAL_FILE_HANDOFF` only after repository-recorded evidence proves the actual file handoff.

## 27. Testing strategy

C10 follows `RED → minimum GREEN → refactor → integration smoke`.

The dedicated suite must prove at least:

1. required C10 files/schemas exist;
2. schemas are closed;
3. baseline provider ids reconcile with `construction/upstream/registry.json`;
4. unknown/duplicate providers fail;
5. profile fingerprinting is deterministic;
6. `MANUAL_FILE_HANDOFF` fails below EP1;
7. `API_ADAPTER` fails below `CONTRACT_PROVEN_API`;
8. upstream/profile API state cannot drift silently;
9. unsupported capability claims fail;
10. request fingerprints are deterministic;
11. `RESEARCH_ONLY` cannot create operational requests;
12. manual requests contain exactly one manual step;
13. API requests require `manual_step=null`;
14. receipts bind exact request/profile fingerprints;
15. hash-mismatched artifacts fail;
16. size limits fail before deep parsing;
17. provider filenames cannot escape staging boundaries in any CLI wrapper;
18. no fixture contains credentials/secrets;
19. validation state cannot advance without named evidence;
20. C9 still exposes exactly nine tools;
21. all inherited C0-C9 regression gates remain green.

Any future API adapter gets additional RED/GREEN coverage for allowlisted origin, auth injection, timeouts, size limits, response validation, sanitization, and real smoke.

## 28. CI gate

The dedicated C10 workflow runs on relevant pull requests and `main`.

The initial gate includes:

- C10 tests;
- C0 registry validation;
- relevant C4/C5/C6/C7/C8/C9 regressions;
- Engineering I2 contract where physical-target linkage is exercised;
- whitespace;
- governance/security;
- inherited Sonar/CodeQL gates when repository policy triggers them.

Initial profile/manual-handoff validation requires no provider credentials and no outbound network.

A green offline CI result is not evidence of a real provider smoke unless that provider path actually ran with authorized evidence.

## 29. Acceptance criteria

C10 baseline is complete only when all of the following are proven on the exact merged main revision:

1. provider profile schema/validator exist;
2. all current external providers have explicit profiles or an explicit exclusion reason;
3. profiles reconcile with C0 without duplicating I2/C4 physical authority;
4. EP0-EP5 promotion/demotion rules are enforced;
5. API-state promotion rules are enforced;
6. request and receipt contracts are deterministic and fail closed;
7. artifact trust states and hash binding are enforced;
8. no undocumented provider network call, scraping, or browser automation exists;
9. no versioned secret exists;
10. C9 still advertises exactly nine tools and C9 stdio acceptance is green;
11. triggered inherited Construction/Governance/Sonar/CodeQL gates required by repository policy pass;
12. at least one baseline provider reaches `EP2_EXECUTION_PROVEN` through a controlled manual file-handoff smoke, unless all four are independently evidenced as unavailable for such a handoff—in that exceptional case C10 closes blocked rather than inventing success;
13. exact PR head, merge SHA, run ids, provider proof states, and postmerge evidence are recorded;
14. `construction/STATUS.md` advances only after postmerge validation.

## 30. Expected closeout state

After successful C10 implementation and postmerge validation:

```text
PHASE=C10_COMPLETE_POSTMERGE_VALIDATED
NEXT_ACTION=BEGIN_C11_COMPLEX_MODDED_GOLDEN
MANUAL_ACTION_REQUIRED=NO
```

`MANUAL_ACTION_REQUIRED=NO` means no unresolved setup action blocks C10 closeout. A provider may still legitimately require manual file handoff during ordinary operation.

## 31. Decision summary

C10 adopts the approved file-handoff-first architecture:

- external provider evidence is explicit and versioned;
- C0 remains coarse registry; C10 profiles become operational external-provider authority;
- Engineering I2/C4 remain physical modpack authorities;
- manual handoff requires evidence before promotion;
- API automation requires official contract proof, RED/GREEN tests, and smoke evidence;
- external artifacts remain untrusted until Factory validation advances their state;
- C9 v1 is unchanged;
- C11 consumes the first complex proven provider path;
- C12 owns runtime acceptance;
- C13 owns Skill/Router integration.
