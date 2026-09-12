# Construction C10 External Providers Design

Date: 2026-09-12
Status: design approved in chat; written specification awaiting human review
Repository: `Gustavaopere/minecraft-mod-factory`
Construction frontier entering this design: `C9_COMPLETE_POSTMERGE_VALIDATED`
Canonical base at design start: `6ef8d9427b5c3f005616d9f7ebf3f8ace04cb198`

## 1. Purpose

C10 establishes the Construction-domain boundary for external structure-generation providers without promoting unverified web products, undocumented endpoints, browser automation, scraping, or provider-owned output into Factory authority.

The phase exists because Construction already has deterministic internal authorities for Build IR, registry evidence, palette resolution, Sponge v3 export, structural QA, Visual QA, and a capability-limited MCP façade, while several useful generation services are currently known only as external providers. C10 turns that ambiguous edge into an auditable contract.

The baseline providers already registered by C0 are:

- `objtoschematic`;
- `structmatic`;
- `schematic-helper`;
- `blockgpt`.

Their canonical C0 state at the start of C10 is `EXTERNAL_PROVIDER` with `api_state=UNVERIFIED_API`. C10 must preserve that state unless new evidence justifies promotion.

C10 is file-handoff-first. A provider with no proven public API may participate only through an evidence-backed manual file handoff. A provider may gain automated API integration only after the official API contract has been independently verified and Factory tests prove the adapter against that exact contract.

## 2. Authority baseline

C10 must preserve the existing Construction authority graph.

- Engineering I2 remains authority for the physical modlist, physical mod identity, physical version, JAR topology, and physical hashes.
- C4 `construction/core/modpack_registry.py` remains authority for installed block/state existence and runtime-backed registry evidence.
- C5 remains authority for semantic palette resolution against C4 evidence.
- C2 remains authority for Canonical Build IR.
- C6 remains authority for Factory-owned canonical Sponge Schematic v3 export/validation.
- C7 remains structural Architecture QA authority.
- C8 remains deterministic offline preview and Visual QA authority.
- C9 remains the exact nine-tool, stdio-only agent-facing façade over C2/C4/C5/C6/C7/C8.
- `construction/upstream/registry.json` remains the coarse discovery/policy registry for known external providers.

C10 introduces a separate Construction External Provider Profile authority. It must not be confused with the Engineering provider catalog for installed mods. A mod such as a physical NeoForge dependency is an Engineering/I2 provider. A web or hosted structure-generation service is a Construction external provider. The two catalogs may reference one another when useful, but they cannot substitute for one another.

## 3. Physical target baseline

The design was revalidated against the latest supplied physical modlist snapshot:

- top-level mods: `595`;
- Minecraft target: `1.21.1`;
- loader: NeoForge `21.1.248`;
- source SHA-256: `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`.

C10 does not duplicate this snapshot. Provider profiles that claim modpack-aware behavior must reference the authoritative physical/registry evidence by fingerprint rather than embedding a second copy of mod presence/version data.

## 4. Design principles

C10 follows these rules.

1. **Evidence before capability.** A provider capability is not supported because a marketing page or observed UI suggests it exists. The profile records only evidence-backed capability claims.
2. **Manual before invented automation.** If no public API is proven, the maximum operational mode is manual file handoff.
3. **External output is untrusted input.** A generated `.schem`, `.litematic`, `.nbt`, ZIP, JSON, image, mesh, or other artifact has no Factory authority merely because a provider produced it.
4. **No silent repair.** C10 may reject, quarantine, or defer an artifact; it must not silently rewrite an invalid provider result into something that appears authoritative.
5. **Exact-source provenance.** Promotion decisions cite the exact provider evidence used: official docs/source when available, manual smoke evidence when required, and audit date.
6. **No hidden network surface.** No C10 executable may call an undocumented endpoint, scrape a UI, or automate a browser as a substitute for an API contract.
7. **No C9 scope creep.** C10 does not add tools to the C9 v1 MCP server. Agent routing and higher-level orchestration remain a later phase.
8. **Deterministic Factory boundary.** Provider nondeterminism is allowed only when explicitly recorded; Factory manifests, hashes, validation decisions, and handoff state transitions remain deterministic.

## 5. Explicit non-goals

C10 does not implement:

- arbitrary browser automation;
- scraping provider web applications;
- reverse-engineered/private HTTP endpoints;
- generic web form automation;
- arbitrary shell, Python, subprocess, package-install, or filesystem capability;
- live Minecraft placement;
- full-modpack boot acceptance;
- runtime visual fidelity;
- worldgen integration;
- a natural-language architectural planner;
- a generic `generate_from_prompt` MCP tool;
- new C9 MCP tools or transport changes;
- automatic conversion among `.schem`, `.litematic`, vanilla structure NBT, mesh formats, or provider-private formats unless a later explicit conversion contract is approved;
- promotion of provider output directly to C2/C6/C7/C8 authority without validation;
- embedding third-party credentials in versioned files;
- treating an external provider as equivalent to an installed NeoForge mod/provider.

C11 owns the first complex modded Golden that may consume proven C10 handoff behavior. C12 owns runtime/in-game acceptance. C13 owns Skill/Router integration.

## 6. Selected architecture

C10 uses a data-driven external-provider catalog with evidence-bound profiles and deterministic handoff manifests.

```text
construction/upstream/registry.json
        |
        | coarse known-provider registry
        v
Construction C10 External Provider Profiles
        |
        +--> evidence/proof state
        +--> declared capabilities
        +--> integration mode
        +--> input/output artifact contracts
        +--> auth/network posture
        +--> determinism/manual-action posture
        |
        v
Provider Handoff Request
        |
        +--> RESEARCH_ONLY
        +--> MANUAL_FILE_HANDOFF
        +--> API_ADAPTER only after proof gate
        |
        v
Provider Handoff Receipt
        |
        +--> exact artifact hashes
        +--> provider/profile fingerprint
        +--> request fingerprint
        +--> provenance/evidence
        +--> validation state
        |
        v
Factory validators / later C11 consumers
```

C10 therefore owns the boundary contract and evidence lifecycle, not provider-generated voxel semantics.

## 7. Repository layout

The implementation is expected to add only the structure justified by the real repository tree at implementation time. The planned boundary is:

- `construction/providers/` — Factory-owned C10 provider-profile and handoff logic;
- `construction/providers/profiles/` — versioned provider profile documents;
- `construction/schemas/external-provider-profile.schema.json`;
- `construction/schemas/provider-handoff-request.schema.json`;
- `construction/schemas/provider-handoff-receipt.schema.json`;
- `construction/tests/` — C10 contract, evidence, handoff, and security tests;
- `.github/workflows/factory-construction-c10-external-providers.yml` — dedicated C10 gate.

The tree is not prescriptive beyond these logical responsibilities. If the current repository layout demonstrates a better non-duplicative placement during implementation, the implementation plan must adapt to the real tree.

## 8. External Provider Profile contract

Each operational C10 provider profile is a closed JSON document. Unknown fields fail validation.

The logical fields are exactly:

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
  }
}
```

Profile values must be evidence-backed. Empty arrays and `UNKNOWN`/`null` values are valid when evidence is absent; invented defaults are not.

### 8.1 `provider_id`

`provider_id` is a stable lowercase identifier and must match a provider present in `construction/upstream/registry.json` with `integration_policy=EXTERNAL_PROVIDER`, unless the same change explicitly adds a new audited provider to the upstream registry.

### 8.2 `capabilities`

C10 defines a narrow capability vocabulary so profiles cannot invent ad-hoc marketing labels. Initial values may include:

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

A capability appears in a profile only when the recorded evidence supports it. Capability presence never implies API availability.

### 8.3 API state

The C10 API state values are:

- `UNVERIFIED_API` — no authoritative public API contract is proven;
- `VERIFIED_API` — official documentation/source proves a concrete callable API contract.

`VERIFIED_API` is necessary but not sufficient for automated use. An executable adapter additionally requires `EP3_API_CONTRACT_PROVEN` or higher.

The profile must never contain secret values. `auth` may describe only the mechanism: `NONE`, `API_KEY`, `OAUTH`, `SESSION`, or `UNKNOWN`. A provider requiring a browser/session-only interaction without a documented programmatic contract remains non-automated.

### 8.4 Integration mode

The only C10 integration modes are:

- `RESEARCH_ONLY`;
- `MANUAL_FILE_HANDOFF`;
- `API_ADAPTER`.

Promotion is constrained by proof level:

- `RESEARCH_ONLY` is valid at any level and is mandatory at `EP0_DISCOVERED` when no usable handoff has been proven;
- `MANUAL_FILE_HANDOFF` requires at least `EP1_MANUAL_HANDOFF_VERIFIED`;
- `API_ADAPTER` requires at least `EP3_API_CONTRACT_PROVEN`.

A provider with no proven API must never be represented as `API_ADAPTER`. A provider with no proven file workflow must not be prematurely represented as `MANUAL_FILE_HANDOFF` merely because the website appears to have download controls.

## 9. Provider proof levels

C10 uses its own external-provider proof levels. They mirror the discipline of the Mod Engineering proof ladder without replacing Engineering provider proof levels.

- `EP0_DISCOVERED` — provider identity exists in the audited registry; no usable handoff is proven.
- `EP1_MANUAL_HANDOFF_VERIFIED` — a human-performed input/export path has been evidenced end-to-end and the exact output artifact kind is known.
- `EP2_API_DOC_VERIFIED` — an official API contract is independently verified, including endpoint/protocol shape and authentication posture.
- `EP3_API_CONTRACT_PROVEN` — Factory contract tests prove request/response behavior against the exact verified API contract without leaking credentials.
- `EP4_PROVIDER_SMOKE` — a real provider invocation or manual handoff completes successfully on a controlled fixture and records exact artifacts/provenance.
- `EP5_GOLDEN_VALIDATED` — provider output has entered the Factory through the C10 receipt boundary and the applicable downstream validators/Golden acceptance prove the intended integration path.

Promotion is monotonic only when all lower-level evidence remains valid. Evidence drift may demote a provider. A changed provider UI, API version, auth model, export format, or service behavior invalidates the affected proof layer until re-audited.

## 10. Evidence contract

Each profile contains an ordered evidence list. Each evidence record is closed and contains:

- `kind`: `OFFICIAL_SITE`, `OFFICIAL_DOCS`, `OFFICIAL_SOURCE`, `MANUAL_SMOKE`, or `FACTORY_TEST`;
- `locator`: a non-secret stable URL, repository/ref, or Factory evidence artifact locator;
- `observed_at`: explicit date/time or date;
- `supports`: the exact capability/proof claim supported by this evidence;
- optional `sha256` only when C10 stores or receives exact evidence bytes under Factory control.

C10 does not archive third-party pages by default. A URL is provenance, not proof of immutability. If a provider changes materially, its profile must be re-audited before promotion remains valid.

`OFFICIAL_SITE` evidence may establish identity and publicly advertised capability, but cannot by itself establish `VERIFIED_API`. `EP2_API_DOC_VERIFIED` requires official documentation or official source that defines a callable contract.

## 11. C0 registry reconciliation

`construction/upstream/registry.json` remains the coarse source registry. C10 profiles extend it; they do not replace it.

The C10 validator must enforce:

1. every profile `provider_id` exists in the upstream registry or is added there in the same audited change;
2. the upstream entry has `integration_policy=EXTERNAL_PROVIDER`;
3. profile `api.state=UNVERIFIED_API` is compatible with upstream `api_state=UNVERIFIED_API`;
4. a profile may not claim `VERIFIED_API` while the upstream registry still claims `UNVERIFIED_API`; both must be reconciled atomically with proof;
5. duplicate provider ids are rejected;
6. provider profiles sort deterministically by `provider_id` whenever an aggregate catalog is emitted.

This preserves one discovery registry and one operational profile authority rather than two conflicting provider catalogs.

## 12. Provider Handoff Request

A C10 handoff request is a deterministic intent manifest, not an executable browser script.

Logical fields are exactly:

```json
{
  "schema_version": 1,
  "request_id": "<sha256-derived-id>",
  "provider_id": "objtoschematic",
  "provider_profile_sha256": "<64 lowercase hex>",
  "mode": "MANUAL_FILE_HANDOFF",
  "operation": "MESH_TO_STRUCTURE",
  "input_artifacts": [
    {
      "kind": "MESH",
      "sha256": "<64 lowercase hex>",
      "byte_length": 123,
      "media_type": "model/obj"
    }
  ],
  "expected_output_kinds": ["SPONGE_SCHEMATIC"],
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

`request_id` is derived from canonical JSON of the request body excluding the id itself. No wall-clock value participates in the request fingerprint.

For manual flows, a request describes exactly one next manual action at a time. This aligns provider operation with the Factory execution rule that a user is never given an uncontrolled batch of manual steps.

A provider request does not contain credentials, arbitrary local paths, cookies, browser sessions, executable code, or provider-private endpoint guesses.

## 13. Provider Handoff Receipt

A provider handoff receipt records what actually came back from the external boundary.

Logical fields are exactly:

```json
{
  "schema_version": 1,
  "request_id": "<request fingerprint>",
  "provider_id": "objtoschematic",
  "provider_profile_sha256": "<64 lowercase hex>",
  "mode": "MANUAL_FILE_HANDOFF",
  "received_artifacts": [
    {
      "kind": "SPONGE_SCHEMATIC",
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

Provider metadata is a closed, provider-profile-approved object. C10 does not accept arbitrary nested metadata blobs by default.

The receipt fingerprint is computed over canonical JSON excluding `receipt_sha256`.

Receipt creation proves only provenance and byte identity. It does not prove that the artifact is valid, safe, canonical, modpack-compatible, visually acceptable, or runtime-compatible.

## 14. Artifact trust boundary

Every external provider artifact enters the Factory as untrusted bytes.

C10 must enforce, where applicable:

- explicit artifact kind;
- explicit media type;
- exact byte length;
- SHA-256 fingerprint;
- configured size limits before deep parsing;
- no automatic archive extraction into arbitrary paths;
- no execution of embedded scripts or binaries;
- no interpretation of provider filenames as trusted paths;
- no network dereference from inside an artifact;
- fail-closed parsing.

Format-specific authority remains elsewhere. Examples:

- a Sponge v3 artifact may be presented to the existing C6 validator when it meets the target contract;
- a provider-produced file that cannot yet be safely parsed by a Factory authority remains `UNVALIDATED` or `DEFERRED`;
- an external `.litematic` is not converted automatically simply because C10 recognizes the extension;
- an artifact with valid syntax is still not a C2 Build IR unless a separately approved importer proves that semantic conversion.

C10 must distinguish `RECEIVED`, `FORMAT_VALIDATED`, `FACTORY_NORMALIZED`, and `GOLDEN_ACCEPTED` instead of collapsing them into a single success boolean.

## 15. Manual file handoff

Manual file handoff is the primary C10 operational mode when a provider lacks a proven API.

A manual flow consists of deterministic Factory-side records around one human action:

```text
Factory creates handoff request
→ one manual provider action
→ user returns one expected artifact/confirmation
→ Factory records receipt
→ Factory validates/hash-binds the result
→ next manual action is generated only if needed
```

C10 may provide CLI/helpers that create or validate request/receipt manifests, but those helpers must not automate the provider UI.

Manual evidence must identify the provider profile fingerprint and the exact resulting artifact hashes. Screenshots may be attached as evidence in a later implementation if useful, but screenshots alone cannot prove artifact bytes.

## 16. API adapter promotion

C10 defines the promotion boundary for future API adapters but does not fabricate one for the initial four providers.

An API adapter may be implemented only when:

1. official documentation/source proves a callable contract;
2. `api.state` is promoted to `VERIFIED_API` with that evidence;
3. the exact base origin/protocol and authentication mechanism are known;
4. a RED contract test is written first;
5. request/response schemas are bounded;
6. payload and timeout limits are explicit;
7. redirect/origin policy is explicit;
8. credentials are obtained only from runtime secret injection and never versioned/logged;
9. provider errors are sanitized;
10. a real provider smoke is performed before claiming the adapter operational.

If these conditions are not met, the provider remains `RESEARCH_ONLY` or `MANUAL_FILE_HANDOFF`.

C10 baseline does not need to ship an executable network-adapter abstraction if no provider reaches this gate. The implementation plan should prefer YAGNI over an unused generic HTTP framework.

## 17. Network and credential security

The default C10 runtime is network-free.

Manual profile validation, request generation, receipt validation, and artifact hashing require no outbound network.

If a later C10 slice gains a verified API adapter:

- only an evidence-bound allowlisted origin may be contacted;
- no caller-supplied arbitrary URL is accepted;
- redirects to unallowlisted origins fail closed;
- TLS verification remains enabled;
- explicit connect/read/total timeouts are required;
- request and response size limits are required;
- credentials come from an environment/secret name declared by code, not from profile JSON values;
- secrets are never printed, hashed into manifests, written to receipts, or included in exception text;
- provider responses are treated as untrusted bytes/data.

No C10 profile may contain API keys, tokens, cookies, OAuth refresh tokens, passwords, or session material.

## 18. Filesystem security

C10 core contracts operate on bytes and JSON values, not arbitrary absolute paths.

Any CLI wrapper introduced for manual handoff may resolve only paths inside the current Factory workspace or an explicitly configured staging root. It must reject:

- path traversal;
- workspace root as an artifact file;
- device/special files;
- symlink escape;
- implicit recursive directory ingestion;
- output overwrite without explicit contract.

Provider-supplied filenames are labels only. Factory-owned artifact names and staging destinations are derived independently.

## 19. Determinism

C10 cannot require third-party services to be deterministic. Instead it separates provider determinism from Factory determinism.

The profile records `handoff.determinism` as:

- `YES` — repeated equivalent provider requests are proven byte/semantic stable under a defined contract;
- `NO` — provider output is known to vary;
- `UNKNOWN` — not proven.

Regardless of provider behavior, Factory-side operations must be deterministic:

- profile canonicalization;
- profile fingerprints;
- request fingerprints;
- receipt fingerprints;
- artifact SHA-256 values;
- validation ordering;
- error ordering;
- catalog ordering.

No timestamp participates in content fingerprints. Audit timestamps remain provenance fields and are excluded only where the relevant canonicalization contract explicitly defines that behavior.

## 20. Error model

C10 errors are fail-closed and stable. Planned categories include:

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

Errors crossing an agent/CLI boundary must not expose secrets, cookies, arbitrary provider response bodies, machine-local paths, or stack traces.

## 21. Drift and re-audit

External providers are expected to change independently of the Factory.

C10 must support explicit drift detection based on evidence fields rather than pretending a prior audit remains current forever.

A profile requires re-audit when any of these changes are observed:

- provider URL/identity changes;
- UI handoff changes materially;
- accepted input kind changes;
- exported artifact kind/version changes;
- API version or endpoint contract changes;
- authentication changes;
- usage limits change in a way that affects the contract;
- provider output stops satisfying an established validator/Golden.

Drift may demote proof level or integration mode. Demotion is not a failure of the Factory; it is the correct fail-closed response to lost evidence.

## 22. Interaction with the physical modpack

An external provider may claim or expose modded block selection, but C10 must not trust that claim as physical modpack authority.

Any provider output intended for the current pack must ultimately be checked against the exact current Engineering I2/C4 evidence before the Factory may call it modpack-compatible.

The current physical snapshot fingerprint is carried in handoff requests as provenance. If the modlist changes, previously generated artifacts are not automatically invalid, but their compatibility claim is stale until revalidated against the new authoritative snapshot.

C10 profiles do not copy 595 physical mod entries. They reference the physical snapshot fingerprint and, when relevant, a C4 registry fingerprint.

## 23. Interaction with C9 MCP

C9 v1 remains unchanged through C10.

The server must continue to advertise exactly these nine tools:

1. `registry_search`
2. `palette_resolve`
3. `build_canonicalize`
4. `build_validate`
5. `build_edit`
6. `qa_structural`
7. `preview_render`
8. `qa_visual`
9. `export_sponge_v3`

C10 must not silently add `provider_generate`, `provider_upload`, `provider_download`, browser, filesystem, credential, or network tools.

If a future provider capability must become agent-facing, it requires an explicitly versioned MCP design and acceptance surface. C13 remains the planned Skill/Router integration point.

## 24. Testing strategy

C10 implementation follows TDD: `RED → minimum GREEN → refactor → integration smoke`.

The dedicated C10 suite must cover at least:

1. required files and schemas exist;
2. profile schemas are closed;
3. baseline external provider ids reconcile exactly with `construction/upstream/registry.json`;
4. unknown/duplicate providers fail;
5. `MANUAL_FILE_HANDOFF` fails below `EP1_MANUAL_HANDOFF_VERIFIED`;
6. `API_ADAPTER` fails below `EP3_API_CONTRACT_PROVEN`;
7. `VERIFIED_API` cannot coexist with upstream `UNVERIFIED_API`;
8. capability claims require matching evidence support;
9. profile canonicalization/fingerprints are deterministic;
10. request fingerprints are deterministic;
11. requests reject unknown capability/mode combinations;
12. manual requests contain one bounded manual step only;
13. receipts bind the exact request/profile fingerprints;
14. receipts reject duplicate, malformed, or hash-mismatched artifacts;
15. artifact size limits fail before parser invocation;
16. provider filenames cannot escape staging boundaries in any CLI wrapper;
17. credentials/secrets are absent from all versioned profile/request/receipt fixtures;
18. external artifacts remain untrusted until explicit validator state advances;
19. C9 exact nine-tool contract remains unchanged;
20. existing C0-C9 Construction suites remain green.

If an API adapter is later added inside C10, it receives its own RED/GREEN tests for origin allowlisting, auth injection, timeout, size limits, response validation, sanitization, and real provider smoke.

## 25. CI gate

The C10 workflow must run on pull requests touching the C10 boundary and on `main`.

The initial gate should include:

- C10 unit/contract tests;
- C0 registry validation;
- C4/C5/C6/C7/C8/C9 regression coverage required by the touched authority graph;
- Engineering I2 physical-modlist contract where profile/target linkage is exercised;
- repository whitespace checks;
- governance/security checks;
- Sonar/CodeQL inherited gates where repository policy triggers them.

The workflow must use read-only repository permissions unless a concrete requirement proves otherwise. Initial C10 profile/manual-handoff validation does not require provider credentials or network access.

No CI green result may be interpreted as a real external-provider smoke unless the workflow actually executed that provider path with the required authorized credentials/evidence.

## 26. Initial provider posture

At design time the four baseline providers remain evidence-conservative:

- `objtoschematic` — C0 `UNVERIFIED_API`; C10 starts without automated integration;
- `structmatic` — C0 `UNVERIFIED_API`; C10 starts without automated integration;
- `schematic-helper` — C0 `UNVERIFIED_API`; C10 starts without automated integration;
- `blockgpt` — C0 `UNVERIFIED_API`; C10 starts without automated integration.

The implementation may promote any of them to `EP1_MANUAL_HANDOFF_VERIFIED` only after recording actual manual file-handoff evidence. It may not promote any of them to `VERIFIED_API` or `API_ADAPTER` without the API proof gates in this specification.

This intentionally separates the design's allowed maximum mode from the provider's current proven state.

## 27. Documentation

When C10 implementation starts, Construction documentation must explain:

- the difference between physical mod providers and external Construction providers;
- proof levels EP0-EP5;
- research-only vs manual-file vs API modes;
- artifact trust states;
- one-step manual handoff behavior;
- how provider drift causes re-audit/demotion;
- that C9 remains unchanged;
- that C11/C12/C13 retain their later authorities.

Documentation must not advertise a provider as integrated beyond its recorded proof level.

## 28. Acceptance criteria

C10 baseline is complete only when all of the following are proven on the exact merged main revision:

1. the C10 provider-profile schema and validators are implemented;
2. all current external providers in the upstream registry have explicit C10 profiles or an explicit documented exclusion reason;
3. profiles reconcile with C0 without duplicated physical-mod authority;
4. EP0-EP5 promotion/demotion rules are enforced;
5. manual request and receipt contracts are deterministic and fail closed;
6. artifact trust states and hash binding are enforced;
7. no undocumented provider network call, browser automation, or scraping exists;
8. no secret values exist in versioned provider artifacts;
9. C9 still advertises exactly nine tools and all C9 stdio acceptance remains green;
10. all triggered inherited Construction/Governance gates pass;
11. Sonar/CodeQL inherited gates required by repository policy pass;
12. at least one real external provider reaches `EP1_MANUAL_HANDOFF_VERIFIED` through a controlled manual file-handoff smoke, unless all four providers are independently proven unavailable for such a handoff—in that exceptional case C10 must close with explicit blocker evidence rather than fake a success;
13. C10 STATUS evidence records exact PR head, merge SHA, workflow runs, provider proof states, and postmerge validation;
14. `construction/STATUS.md` advances only after postmerge validation and sets the next frontier to C11.

## 29. Expected closeout state

After successful C10 implementation and postmerge validation, the intended Construction status is:

```text
PHASE=C10_COMPLETE_POSTMERGE_VALIDATED
NEXT_ACTION=BEGIN_C11_COMPLEX_MODDED_GOLDEN
MANUAL_ACTION_REQUIRED=NO
```

`MANUAL_ACTION_REQUIRED=NO` means no unresolved setup action is blocking the phase closeout. It does not mean external providers can operate without humans; a provider profile may legitimately remain `MANUAL_FILE_HANDOFF`.

## 30. Decision summary

C10 adopts the approved file-handoff-first approach.

- External provider evidence becomes explicit and versioned.
- C0 remains the coarse registry; C10 profiles are the operational provider authority.
- Engineering I2/C4 remain the physical modpack authorities.
- No provider gets an API adapter through inference.
- Manual handoff is permitted only after EP1 evidence.
- API automation requires official contract proof plus TDD and smoke evidence.
- External artifacts remain untrusted until Factory validators advance their state.
- C9 v1 is not expanded.
- C11 consumes the first complex proven provider path; C12 handles runtime acceptance; C13 handles agent/router integration.
