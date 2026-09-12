# Construction C10 External Providers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed, evidence-bound Construction C10 external-provider boundary that supports deterministic provider profiles, manual handoff requests/receipts, one real ObjToSchematic manual smoke, and no undocumented provider automation.

**Architecture:** C10 adds a small stdlib-only `construction/providers/` package. C0 remains the coarse provider registry, Engineering I2/C4 remain physical-modpack authorities, C9 remains the exact nine-tool MCP boundary, and C10 owns only external-provider profiles plus handoff provenance/trust-state contracts. The initial operational path is manual and network-free; an API adapter is not implemented unless a future independently verified API contract satisfies the spec promotion gate.

**Tech Stack:** Python 3.11 stdlib, JSON Schema draft 2020-12 documents, existing `nbtlib`/C6 only for optional Sponge v3 validation, GitHub Actions on Ubuntu 24.04, Java 21/NeoForge only for inherited C4 regression, existing C9 MCP 2.2.0 lock for inherited C9 regression.

**Spec:** `docs/superpowers/specs/2026-09-12-construction-c10-external-providers-design.md`

## Global Constraints

- Target remains Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`.
- Latest supplied physical-modlist SHA-256 is `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`; implementation must re-audit before binding any smoke request.
- Engineering I2 remains physical mod/provider identity/version authority.
- C4 remains installed block/state authority; C5 remains palette authority; C2 remains Build IR authority; C6 remains Sponge v3 authority; C7/C8 remain QA authorities.
- C9 v1 must still advertise exactly nine tools and must not gain provider/browser/network/filesystem/credential capabilities.
- Baseline C10 performs no outbound network calls at runtime and contains no generic HTTP client.
- No undocumented endpoint, UI scraping, browser automation, shell, arbitrary code execution, package install, or versioned secret.
- Every provider artifact is untrusted until its explicit Factory validation state advances.
- JSON contracts are closed and fail on unknown fields.
- C10 canonical JSON uses UTF-8, lexically sorted keys, compact separators, `ensure_ascii=False`, one final newline, and SHA-256 lowercase hex.
- Provider proof and API proof are independent state machines.
- Manual user actions are issued one at a time.
- Preserve `.bbmodel` and other native authoring formats; C10 does not silently convert provider formats.
- Do not update `construction/STATUS.md` in the implementation PR. Status advances only in a separate postmerge closeout PR after exact-main validation.
- Before every implementation/merge boundary, re-audit `main`, open PRs, and overlapping files. Current known concurrent PR #89 is in the `art/` domain and must be rechecked rather than assumed harmless.

---

## File Structure

Create these focused units unless the implementation-time tree proves a less duplicative placement:

- `construction/providers/__init__.py` — public C10 exports only.
- `construction/providers/common.py` — canonical JSON, digest helpers, shared vocabularies, deterministic ordering helpers.
- `construction/providers/errors.py` — stable C10 error codes and sanitized `C10Error`.
- `construction/providers/profiles.py` — profile loading, profile validation, upstream reconciliation, profile fingerprinting/catalog ordering.
- `construction/providers/handoff.py` — request/receipt builders, validators, profile/physical drift binding, trust-state transition validation.
- `construction/providers/staging.py` — workspace/fixture path safety and byte descriptor/hash/limit checks; no provider network logic.
- `construction/providers/profiles/objtoschematic.json`
- `construction/providers/profiles/structmatic.json`
- `construction/providers/profiles/schematic-helper.json`
- `construction/providers/profiles/blockgpt.json`
- `construction/schemas/external-provider-profile.schema.json`
- `construction/schemas/provider-handoff-request.schema.json`
- `construction/schemas/provider-handoff-receipt.schema.json`
- `construction/scripts/validate_c10.py` — repository-level C10 validator entrypoint.
- `construction/fixtures/c10/objtoschematic-smoke/input.obj` — deterministic Factory-owned mesh fixture.
- `construction/fixtures/c10/objtoschematic-smoke/request.json` — added only after ObjToSchematic reaches EP1.
- `construction/fixtures/c10/objtoschematic-smoke/provider-output.schem` — added only after the user returns exact smoke bytes and only if the artifact is small enough for repository evidence.
- `construction/fixtures/c10/objtoschematic-smoke/receipt.json` — added after exact returned bytes are available.
- `construction/fixtures/c10/objtoschematic-smoke/validation.json` — records C6 PASS/FAIL without altering C6.
- `construction/tests/test_c10_provider_profiles.py`
- `construction/tests/test_c10_handoff_request.py`
- `construction/tests/test_c10_handoff_receipt.py`
- `construction/tests/test_c10_security.py`
- `construction/tests/test_c10_workflow_contract.py`
- `.github/workflows/factory-construction-c10-external-providers.yml`
- `construction/README.md` and `construction/docs/ARCHITECTURE.md` — C10 boundary documentation after behavior is proven.

Do not create an API adapter package in baseline C10.

---

### Task 1: Establish the RED contract for C10 provider profiles

**Files:**
- Create: `construction/tests/test_c10_provider_profiles.py`
- Read-only authority inputs: `construction/upstream/registry.json`, `construction/tests/test_c0_foundation.py`, `engineering/tooling/import-physical-modlist.py`

**Interfaces:**
- Consumes: C0 `external_providers` entries and the C10 design spec.
- Produces: failing executable requirements for `construction.providers.profiles` and the four profile JSON files.

- [ ] **Step 1: Re-audit repository state before branching**

Run through GitHub/API or local git:

```bash
git fetch origin
git rev-parse origin/main
git status --short
git branch --show-current
```

Also enumerate open PRs and compare their changed filenames with every file listed in this plan. Do not start implementation if a concurrent PR overlaps C10 paths without reconciliation.

- [ ] **Step 2: Create implementation branch from the exact audited main SHA**

Use branch:

```text
feat/construction-c10-external-providers
```

Record the exact base SHA in execution notes.

- [ ] **Step 3: Write the failing provider-profile contract test**

Create `construction/tests/test_c10_provider_profiles.py` with tests that require:

```python
from pathlib import Path
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = ROOT / "construction" / "providers"
PROFILE_MODULE = PROVIDERS / "profiles.py"
PROFILE_DIR = PROVIDERS / "profiles"
UPSTREAM = ROOT / "construction" / "upstream" / "registry.json"
PROFILE_SCHEMA = ROOT / "construction" / "schemas" / "external-provider-profile.schema.json"
EXPECTED_IDS = ["blockgpt", "objtoschematic", "schematic-helper", "structmatic"]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ConstructionC10ProviderProfileTest(unittest.TestCase):
    def test_required_profile_files_exist(self):
        required = [PROFILE_MODULE, PROFILE_SCHEMA]
        required += [PROFILE_DIR / f"{provider_id}.json" for provider_id in EXPECTED_IDS]
        self.assertEqual([], [str(path.relative_to(ROOT)) for path in required if not path.is_file()])

    def test_profile_schema_is_closed(self):
        schema = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])

    def test_catalog_reconciles_with_c0_and_is_deterministic(self):
        module = load_module(PROFILE_MODULE, "construction_c10_profiles")
        upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))
        catalog = module.load_profile_catalog(PROFILE_DIR, upstream)
        self.assertEqual(EXPECTED_IDS, list(catalog))
        for provider_id, profile in catalog.items():
            self.assertEqual(provider_id, profile["provider_id"])
            self.assertEqual("EXTERNAL_PROVIDER", profile["integration_policy"])
            self.assertRegex(profile["profile_sha256"], r"^[0-9a-f]{64}$")

    def test_baseline_api_state_is_unverified(self):
        module = load_module(PROFILE_MODULE, "construction_c10_api_baseline")
        upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))
        catalog = module.load_profile_catalog(PROFILE_DIR, upstream)
        for profile in catalog.values():
            self.assertEqual("UNVERIFIED_API", profile["api"]["state"])
            self.assertIsNone(profile["api"]["official_contract"])
```

Add mutation tests that fail closed for unknown fields, duplicate provider ids, unknown provider ids, unsorted/duplicate capability lists, invalid evidence kinds, invalid evidence locators, invalid profile digest, EP0 with an operational mode, manual mode below EP1, API adapter below `CONTRACT_PROVEN_API`, and non-null API contract at `UNVERIFIED_API`.

- [ ] **Step 4: Run RED and capture evidence**

Run:

```bash
python3 -m unittest construction/tests/test_c10_provider_profiles.py -v
```

Expected: FAIL because `construction/providers/profiles.py`, schema, and profiles do not exist. Preserve the run/log as C10 initial RED evidence.

- [ ] **Step 5: Commit RED only**

```bash
git add construction/tests/test_c10_provider_profiles.py
git commit -m "test(construction): define C10 provider profile contract"
```

---

### Task 2: Implement profile authority, schemas, and four conservative baseline profiles

**Files:**
- Create: `construction/providers/__init__.py`
- Create: `construction/providers/common.py`
- Create: `construction/providers/errors.py`
- Create: `construction/providers/profiles.py`
- Create: `construction/providers/profiles/*.json`
- Create: `construction/schemas/external-provider-profile.schema.json`
- Modify: `construction/tests/test_c10_provider_profiles.py`

**Interfaces:**
- Produces: `canonical_json_bytes`, `sha256_hex`, `profile_fingerprint`, `validate_profile`, `load_profile_catalog`, `C10Error`.
- Later tasks consume exact profile dictionaries returned by `load_profile_catalog`.

- [ ] **Step 1: Add shared constants and canonical digest helpers**

`construction/providers/common.py` must expose:

```python
from __future__ import annotations
import hashlib
import json
import re

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CAPABILITIES = (
    "IMAGE_TO_STRUCTURE",
    "LITEMATIC_EXPORT",
    "LITEMATIC_IMPORT",
    "MESH_TO_STRUCTURE",
    "PROMPT_TO_STRUCTURE",
    "SCHEMATIC_EXPORT",
    "SCHEMATIC_IMPORT",
    "STRUCTURE_EDITING",
    "VANILLA_STRUCTURE_EXPORT",
    "VANILLA_STRUCTURE_IMPORT",
)
ARTIFACT_KINDS = (
    "BEDROCK_MCSTRUCTURE",
    "IMAGE",
    "LITEMATIC_FILE",
    "MESH",
    "SCHEMATIC_FILE",
    "VANILLA_STRUCTURE_NBT",
    "WORLD_ZIP",
)
PROOF_LEVELS = (
    "EP0_DISCOVERED",
    "EP1_HANDOFF_VERIFIED",
    "EP2_EXECUTION_PROVEN",
    "EP3_FORMAT_VALIDATED",
    "EP4_FACTORY_INTEGRATION_VALIDATED",
    "EP5_GOLDEN_VALIDATED",
)
API_STATES = (
    "UNVERIFIED_API",
    "VERIFIED_API",
    "CONTRACT_PROVEN_API",
    "SMOKE_PROVEN_API",
)


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
```

- [ ] **Step 2: Add stable sanitized C10 error type**

`construction/providers/errors.py`:

```python
ERROR_CODES = frozenset({
    "INVALID_PROVIDER_PROFILE",
    "UNKNOWN_PROVIDER",
    "PROOF_LEVEL_INSUFFICIENT",
    "INTEGRATION_MODE_NOT_ALLOWED",
    "CAPABILITY_NOT_PROVEN",
    "UNVERIFIED_API",
    "INVALID_HANDOFF_REQUEST",
    "REQUEST_PROFILE_MISMATCH",
    "INVALID_HANDOFF_RECEIPT",
    "ARTIFACT_LIMIT_EXCEEDED",
    "ARTIFACT_HASH_MISMATCH",
    "ARTIFACT_KIND_UNSUPPORTED",
    "FORMAT_VALIDATION_FAILED",
    "MANUAL_ACTION_REQUIRED",
    "PROVIDER_DRIFT_DETECTED",
    "INTERNAL_ERROR",
})


class C10Error(ValueError):
    def __init__(self, code: str, message: str):
        if code not in ERROR_CODES:
            raise ValueError("unknown C10 error code")
        self.code = code
        super().__init__(message)
```

Messages must never embed secret material or absolute machine paths.

- [ ] **Step 3: Implement profile fingerprint and validation**

`construction/providers/profiles.py` must expose:

```python
def profile_fingerprint(profile: dict[str, object]) -> str:
    payload = dict(profile)
    payload.pop("profile_sha256", None)
    return sha256_hex(canonical_json_bytes(payload))


def validate_profile(profile: dict[str, object], upstream_registry: dict[str, object]) -> list[str]:
    ...


def load_profile_catalog(profile_dir: Path, upstream_registry: dict[str, object]) -> dict[str, dict[str, object]]:
    ...
```

Validation must manually enforce the closed contract from the spec, including exact top-level/nested field sets, ordered unique arrays, proof/mode/API conditional rules, evidence record shape, `profile_sha256` equality, and upstream reconciliation. Do not repair a malformed document.

`load_profile_catalog` loads only `*.json`, rejects duplicate ids, rejects any validation error, and returns a normal dict inserted in lexically sorted `provider_id` order.

- [ ] **Step 4: Create closed JSON Schema**

Create `construction/schemas/external-provider-profile.schema.json` using draft 2020-12 and `additionalProperties: false` at every object level. Mirror the spec vocabularies and conditional requirements. The Python validator remains runtime authority; the schema is the machine-readable public contract and must agree with it.

- [ ] **Step 5: Add the four baseline EP0 profiles**

All four start `EP0_DISCOVERED`, `RESEARCH_ONLY`, `UNVERIFIED_API`, empty operational handoff kinds, `manual_action_required=true`, `determinism=UNKNOWN`, and null limits.

Record official-site evidence observed on 2026-09-12 without claiming API support:

- ObjToSchematic: `https://objtoschematic.com/` and `https://objtoschematic.com/wiki`; advertised capabilities may include only claims directly supported by those pages.
- Structmatic: `https://structmatic.com/`.
- Schematic Helper: `https://schematichelper.com/` and `https://schematichelper.com/about/`.
- BlockGPT: `https://blockgpt.ai/` and `https://blockgpt.ai/blog/how-to-generate-minecraft-schematics-using-ai`.

Compute each `profile_sha256` from the exact canonical JSON excluding that field. Do not add API endpoint guesses.

- [ ] **Step 6: Run focused GREEN**

```bash
python3 -m unittest construction/tests/test_c10_provider_profiles.py -v
```

Expected: all PASS.

- [ ] **Step 7: Run inherited C0 regression immediately**

```bash
python3 -m unittest construction/tests/test_c0_foundation.py -v
python3 construction/scripts/validate_c0.py
```

Expected: PASS; C0 external-provider registry remains authoritative and unchanged.

- [ ] **Step 8: Commit**

```bash
git add construction/providers construction/schemas/external-provider-profile.schema.json construction/tests/test_c10_provider_profiles.py
git commit -m "feat(construction): add C10 provider profiles"
```

---

### Task 3: Add deterministic handoff-request contract by RED → GREEN

**Files:**
- Create: `construction/tests/test_c10_handoff_request.py`
- Create: `construction/providers/handoff.py`
- Create: `construction/schemas/provider-handoff-request.schema.json`
- Modify: `construction/providers/__init__.py`

**Interfaces:**
- Consumes: exact validated profile dict from Task 2.
- Produces: `build_handoff_request(...)`, `validate_handoff_request(...)`.

- [ ] **Step 1: Write request RED tests**

Require these exact operation rules:

```python
VALID_SHA = "a" * 64
PHYSICAL_SHA = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"

# PROMPT_TO_STRUCTURE: text only
# IMAGE_TO_STRUCTURE: exactly one IMAGE artifact, optional text
# MESH_TO_STRUCTURE: exactly one MESH artifact, text_input=None
# STRUCTURE_EDITING: exactly one structure artifact + non-empty text instruction
```

Tests must prove:

- request ids are deterministic and tamper-evident;
- `RESEARCH_ONLY` cannot build a request;
- operation must be in profile capabilities;
- artifact kinds must match profile handoff lists;
- expected output kinds must be non-empty and compatible with profile handoff outputs;
- prompt/edit text is at most 4000 characters;
- manual mode requires exactly one closed manual step;
- API mode requires `manual_step is None` and `CONTRACT_PROVEN_API` or higher;
- profile SHA mismatch returns/raises `PROVIDER_DRIFT_DETECTED`;
- target is exactly Minecraft 1.21.1/NeoForge plus a 64-hex physical-modlist digest;
- unknown fields fail.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c10_handoff_request.py -v
```

Expected: FAIL because handoff module/schema are absent.

- [ ] **Step 3: Implement minimal request builder/validator**

`construction/providers/handoff.py` public signatures:

```python
def validate_handoff_request(
    request: dict[str, object],
    profile: dict[str, object],
    *,
    current_physical_modlist_sha256: str | None = None,
) -> list[str]:
    ...


def build_handoff_request(
    profile: dict[str, object],
    *,
    operation: str,
    text_input: str | None,
    input_artifacts: list[dict[str, object]],
    expected_output_kinds: list[str],
    physical_modlist_sha256: str,
    manual_step: dict[str, object] | None,
) -> dict[str, object]:
    ...
```

The builder constructs all fields, computes `request_id`, then calls the validator and raises `C10Error("INVALID_HANDOFF_REQUEST", ...)` on any error. It never guesses missing fields.

If `current_physical_modlist_sha256` is supplied and differs from request target SHA, validation must report stale physical evidence rather than silently rebinding the request.

- [ ] **Step 4: Create request schema**

Mirror the exact request contract, closed nested objects, artifact descriptor shape, text length limit, and manual-step object. Python validation owns cross-field operation/mode semantics.

- [ ] **Step 5: Run GREEN plus profile regression**

```bash
python3 -m unittest \
  construction/tests/test_c10_provider_profiles.py \
  construction/tests/test_c10_handoff_request.py \
  -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add construction/providers/handoff.py construction/providers/__init__.py construction/schemas/provider-handoff-request.schema.json construction/tests/test_c10_handoff_request.py
git commit -m "feat(construction): add C10 handoff requests"
```

---

### Task 4: Add receipt and trust-state contract by RED → GREEN

**Files:**
- Create: `construction/tests/test_c10_handoff_receipt.py`
- Create: `construction/schemas/provider-handoff-receipt.schema.json`
- Modify: `construction/providers/handoff.py`

**Interfaces:**
- Produces: `build_handoff_receipt`, `validate_handoff_receipt`, `advance_validation_state`.

- [ ] **Step 1: Write receipt RED tests**

Tests must prove:

- receipt id is deterministic and tamper-evident;
- request id/provider id/mode/profile SHA must match the request/current profile;
- expected output kinds constrain returned artifacts;
- `provider_metadata` must be exactly `{}`;
- artifact SHA/length/media type/kind/optional repo path shape are validated;
- current profile SHA mismatch yields `PROVIDER_DRIFT_DETECTED`;
- `UNVALIDATED → FORMAT_VALIDATED → FACTORY_NORMALIZED → GOLDEN_ACCEPTED` is monotonic;
- `FORMAT_VALIDATED` requires FORMAT/PASS evidence for each claimed validated artifact;
- `FACTORY_NORMALIZED` requires NORMALIZE/PASS in addition to prior format evidence;
- `GOLDEN_ACCEPTED` requires GOLDEN/PASS in addition to prior states;
- FAIL evidence never advances state;
- skipping a state fails.

Representative assertion:

```python
with self.assertRaisesRegex(ValueError, "FORMAT"):
    module.advance_validation_state(receipt, "FORMAT_VALIDATED", [])
```

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c10_handoff_receipt.py -v
```

Expected: FAIL on missing receipt implementation/schema.

- [ ] **Step 3: Implement exact public functions**

```python
def validate_handoff_receipt(
    receipt: dict[str, object],
    request: dict[str, object],
    profile: dict[str, object],
) -> list[str]:
    ...


def build_handoff_receipt(
    request: dict[str, object],
    profile: dict[str, object],
    *,
    received_artifacts: list[dict[str, object]],
) -> dict[str, object]:
    ...


def advance_validation_state(
    receipt: dict[str, object],
    new_state: str,
    validators: list[dict[str, object]],
) -> dict[str, object]:
    ...
```

`advance_validation_state` returns a deep-copied receipt with deterministic validator ordering and a recomputed `receipt_sha256`; it never mutates the caller document in place.

- [ ] **Step 4: Create receipt schema**

Close all nested objects, including validator records. Schema must permit only the four trust states and three validation stages from the spec.

- [ ] **Step 5: Run GREEN**

```bash
python3 -m unittest \
  construction/tests/test_c10_provider_profiles.py \
  construction/tests/test_c10_handoff_request.py \
  construction/tests/test_c10_handoff_receipt.py \
  -v
```

- [ ] **Step 6: Commit**

```bash
git add construction/providers/handoff.py construction/schemas/provider-handoff-receipt.schema.json construction/tests/test_c10_handoff_receipt.py
git commit -m "feat(construction): add C10 handoff receipts"
```

---

### Task 5: Add artifact/path security and repository validator by RED → GREEN

**Files:**
- Create: `construction/tests/test_c10_security.py`
- Create: `construction/providers/staging.py`
- Create: `construction/scripts/validate_c10.py`
- Modify: `construction/providers/__init__.py`

**Interfaces:**
- Produces: `safe_repo_fixture_path`, `artifact_descriptor_from_bytes`, `artifact_descriptor_from_file`, repository `validate_c10.py`.

- [ ] **Step 1: Write security RED tests**

Cover:

- absolute paths rejected;
- `..` traversal rejected;
- only `construction/fixtures/c10/` repo paths accepted for versioned artifact descriptors;
- symlink escape rejected using a temporary directory fixture;
- directories/special files rejected;
- hash mismatch rejected;
- byte-length mismatch rejected;
- profile `max_input_bytes`/`max_output_bytes` enforced before any C6/deep parser call;
- provider-supplied filename is never used to derive a destination path;
- secret-pattern fixture scan rejects `api_key`, `token`, `password`, cookie/session-looking values in profile/request/receipt fixtures.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c10_security.py -v
```

Expected: FAIL because `staging.py`/validator are absent.

- [ ] **Step 3: Implement security helpers**

`construction/providers/staging.py` signatures:

```python
def safe_repo_fixture_path(root: Path, repo_relpath: str, *, must_exist: bool) -> Path:
    ...


def artifact_descriptor_from_bytes(
    data: bytes,
    *,
    kind: str,
    media_type: str,
    repo_relpath: str | None,
    max_bytes: int,
) -> dict[str, object]:
    ...


def artifact_descriptor_from_file(
    root: Path,
    repo_relpath: str,
    *,
    kind: str,
    media_type: str,
    max_bytes: int,
) -> dict[str, object]:
    ...
```

Reject over-limit bytes before format parsing. Keep all returned paths repository-relative; never include absolute paths in errors.

- [ ] **Step 4: Implement repository-level validator**

`construction/scripts/validate_c10.py` must:

1. load `construction/upstream/registry.json`;
2. load all profiles through `load_profile_catalog`;
3. verify the three C10 schemas are JSON objects and closed at top level;
4. validate any checked-in C10 request/receipt fixtures;
5. scan C10 versioned JSON/text fixtures for obvious secret keys without printing secret values;
6. exit nonzero with deterministic sorted errors.

- [ ] **Step 5: Run GREEN and C0 aggregate**

```bash
python3 -m unittest discover -s construction/tests -p 'test_c10_*.py' -v
python3 construction/scripts/validate_c10.py
python3 -m unittest construction/tests/test_c0_foundation.py -v
python3 construction/scripts/validate_c0.py
```

- [ ] **Step 6: Commit**

```bash
git add construction/providers/staging.py construction/providers/__init__.py construction/scripts/validate_c10.py construction/tests/test_c10_security.py
git commit -m "feat(construction): harden C10 handoff artifacts"
```

---

### Task 6: Add the dedicated C10 CI gate and prove inherited regressions

**Files:**
- Create: `construction/tests/test_c10_workflow_contract.py`
- Create: `.github/workflows/factory-construction-c10-external-providers.yml`

**Interfaces:**
- Produces: dedicated offline C10 workflow that proves C10 plus inherited authorities.

- [ ] **Step 1: Write workflow RED contract**

Test exact workflow properties:

```python
WORKFLOW = ROOT / ".github/workflows/factory-construction-c10-external-providers.yml"
text = WORKFLOW.read_text(encoding="utf-8")
self.assertIn("Factory Construction C10 External Providers", text)
self.assertIn("permissions:\n  contents: read", text)
self.assertIn("construction/tests/test_c10_provider_profiles.py", text)
self.assertIn("construction/scripts/validate_c10.py", text)
self.assertIn("construction/tests/test_c9_agent_mcp.py", text)
self.assertIn("construction/tests/test_c9_mcp_stdio.py", text)
self.assertNotIn("curl ", text)
self.assertNotIn("wget ", text)
self.assertNotIn("secrets.", text)
```

Also assert checkout/setup action pins match current repository pins rather than floating tags.

- [ ] **Step 2: Run RED**

```bash
python3 -m unittest construction/tests/test_c10_workflow_contract.py -v
```

Expected: FAIL because workflow is absent.

- [ ] **Step 3: Create C10 workflow**

Use exact existing repository action pins from C9:

- `actions/checkout@11d5960a326750d5838078e36cf38b85af677262`
- `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`
- `actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3`

Use Ubuntu 24.04, Python 3.11, Java 21, `permissions: contents: read`, recursive submodules, and the existing hash-pinned Construction locks only.

The workflow must run, in this order:

1. shared Engineering I2 tests;
2. all `test_c10_*.py` tests;
3. `construction/scripts/validate_c10.py`;
4. C9 direct and stdio tests;
5. C8, C7, C6, C5, C4 regressions;
6. materialize/build the C4 NeoForge registry probe exactly as C9 does;
7. C3, C2, C0 regressions and `validate_c0.py`;
8. `git diff --check` over C10 plus touched docs;
9. final enforcement step if any intentionally `continue-on-error` direct C10/C9 test step failed.

Do not add network calls or provider credentials.

PR path filters must include C10 provider files, C10 schemas/tests/fixtures, upstream registry, C0/C4-C9 authorities consumed by C10, the C10 spec/plan, README/ARCHITECTURE/STATUS, and the workflow itself.

- [ ] **Step 4: Run local contract GREEN**

```bash
python3 -m unittest construction/tests/test_c10_workflow_contract.py -v
python3 -m unittest discover -s construction/tests -p 'test_c10_*.py' -v
python3 construction/scripts/validate_c10.py
git diff --check
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/factory-construction-c10-external-providers.yml construction/tests/test_c10_workflow_contract.py
git commit -m "ci(construction): add C10 external provider gate"
```

---

### Task 7: Document the implemented boundary without touching STATUS

**Files:**
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Do not modify: `construction/STATUS.md`

**Interfaces:**
- Documents the exact behavior already proven by Tasks 1-6.

- [ ] **Step 1: Add C10 scope to README**

Document:

- external-provider profiles are separate from I2 physical providers;
- baseline runtime is network-free;
- EP0-EP5 and API proof are independent;
- external bytes are untrusted;
- C9 remains nine tools;
- ObjToSchematic is only a candidate smoke until manual evidence lands;
- C11/C12/C13 boundaries remain unchanged.

- [ ] **Step 2: Add C10 authority section to ARCHITECTURE**

Include the flow:

```text
C0 external provider registry
  -> C10 profile
  -> handoff request
  -> manual/proven API boundary
  -> receipt
  -> existing Factory validators
```

State explicitly that no provider output becomes C2/C6/C7/C8 authority by provenance alone.

- [ ] **Step 3: Run all offline C10 tests and whitespace**

```bash
python3 -m unittest discover -s construction/tests -p 'test_c10_*.py' -v
python3 construction/scripts/validate_c10.py
git diff --check
```

- [ ] **Step 4: Commit docs**

```bash
git add construction/README.md construction/docs/ARCHITECTURE.md
git commit -m "docs(construction): document C10 provider boundary"
```

---

### Task 8: Promote ObjToSchematic to EP1 and create the deterministic manual-smoke request

**Files:**
- Create: `construction/fixtures/c10/objtoschematic-smoke/input.obj`
- Create: `construction/fixtures/c10/objtoschematic-smoke/request.json`
- Modify: `construction/providers/profiles/objtoschematic.json`
- Modify: `construction/tests/test_c10_provider_profiles.py`
- Modify: `construction/tests/test_c10_handoff_request.py`

**Interfaces:**
- Consumes: official ObjToSchematic docs evidence and C10 profile/request builders.
- Produces: one EP1 manual provider path and a deterministic request ready for manual execution.

- [ ] **Step 1: Re-verify official ObjToSchematic evidence immediately before promotion**

Verify only official sources, at minimum:

```text
https://objtoschematic.com/
https://objtoschematic.com/wiki
```

Require evidence that a user can upload a 3D model and export a schematic file. Do not treat the editor's internal Lua API as a remote API. If this evidence no longer exists, do not promote; re-audit another provider and update the spec/plan before proceeding.

- [ ] **Step 2: Add RED test for EP1 profile and fixture request**

Require ObjToSchematic profile to have:

```text
proof_level=EP1_HANDOFF_VERIFIED
integration_mode=MANUAL_FILE_HANDOFF
api.state=UNVERIFIED_API
handoff.accepted_input_kinds=["MESH"]
handoff.output_artifact_kinds containing "SCHEMATIC_FILE"
limits.max_input_bytes > 0
limits.max_output_bytes > 0
limits.timeout_seconds = null
```

Require the checked-in request to validate against the exact profile fingerprint and the current physical-modlist SHA.

- [ ] **Step 3: Run RED**

```bash
python3 -m unittest \
  construction/tests/test_c10_provider_profiles.py \
  construction/tests/test_c10_handoff_request.py \
  -v
```

Expected: FAIL because profile/fixture/request are still EP0/absent.

- [ ] **Step 4: Create a deterministic tiny OBJ fixture**

Create an axis-aligned unit cube with eight vertices and twelve triangle faces; use no external material or texture file. Exact content:

```obj
# Factory C10 deterministic ObjToSchematic smoke fixture
o c10_unit_cube
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1
f 1 2 3
f 1 3 4
f 5 7 6
f 5 8 7
f 1 5 6
f 1 6 2
f 2 6 7
f 2 7 3
f 3 7 8
f 3 8 4
f 4 8 5
f 4 5 1
```

- [ ] **Step 5: Promote ObjToSchematic profile to EP1 only**

Add official-doc evidence supporting `capability:MESH_TO_STRUCTURE`, `capability:SCHEMATIC_EXPORT`, `handoff:MESH`, `handoff:SCHEMATIC_FILE`, and `proof:EP1_HANDOFF_VERIFIED`. Keep API state `UNVERIFIED_API` and `official_contract=null`.

Use conservative Factory-enforced limits suitable for the smoke, for example `max_input_bytes=16777216` and `max_output_bytes=67108864`. These are safety caps, not provider service-limit claims.

Recompute `profile_sha256`.

- [ ] **Step 6: Build and check in the request manifest**

Use `artifact_descriptor_from_file` on the committed OBJ and `build_handoff_request` with:

```text
operation=MESH_TO_STRUCTURE
text_input=null
expected_output_kinds=["SCHEMATIC_FILE"]
physical_modlist_sha256=<freshly revalidated current modlist SHA>
manual_step.step_id=upload-mesh
manual_step.instruction=Upload the exact Factory C10 input.obj fixture to ObjToSchematic using the documented model-upload workflow.
manual_step.expected_result=ObjToSchematic displays a generated block preview derived from the uploaded fixture.
```

Write canonical pretty JSON only for human readability if the repository convention permits; the request fingerprint must still use C10 canonical bytes.

- [ ] **Step 7: Run GREEN**

```bash
python3 -m unittest discover -s construction/tests -p 'test_c10_*.py' -v
python3 construction/scripts/validate_c10.py
```

- [ ] **Step 8: Commit EP1 + request**

```bash
git add construction/providers/profiles/objtoschematic.json construction/fixtures/c10/objtoschematic-smoke construction/tests/test_c10_provider_profiles.py construction/tests/test_c10_handoff_request.py
git commit -m "test(construction): prepare ObjToSchematic C10 handoff"
```

---

### Task 9: Execute the real ObjToSchematic manual smoke and record EP2 evidence

**Files:**
- Add after user returns bytes: `construction/fixtures/c10/objtoschematic-smoke/provider-output.schem`
- Create: `construction/fixtures/c10/objtoschematic-smoke/receipt.json`
- Create: `construction/fixtures/c10/objtoschematic-smoke/validation.json`
- Modify: `construction/providers/profiles/objtoschematic.json`
- Modify: tests as needed to pin the exact smoke evidence.

**Interfaces:**
- Produces: exact provider-output byte identity and EP2 evidence; EP3 only if C6 independently passes.

- [ ] **Step 1: Re-audit main/PR concurrency before requesting manual action**

Do not ask the user to act on stale fixture/profile/request evidence. Confirm branch still has a clean semantic merge path against current `main`; reconcile unrelated upstream changes if necessary and rerun C10 tests before continuing.

- [ ] **Step 2: Manual action 1 — upload only**

Give the user exactly one action: download/use the exact committed `input.obj`, open the official ObjToSchematic editor, upload that exact file, and report whether a block preview appears. Do not yet ask them to export.

If upload/preview fails, record evidence, do not promote to EP2, and audit the next provider rather than automating the UI.

- [ ] **Step 3: Manual action 2 — export only after step 2 passes**

Ask the user to export/download a `.schem` from that exact provider session and upload the exact downloaded file to the chat. Explicitly tell them not to rename/modify/recompress it before upload.

- [ ] **Step 4: Verify exact returned artifact before committing evidence**

For the uploaded bytes:

```python
descriptor = artifact_descriptor_from_bytes(
    data,
    kind="SCHEMATIC_FILE",
    media_type="application/octet-stream",
    repo_relpath="construction/fixtures/c10/objtoschematic-smoke/provider-output.schem",
    max_bytes=profile["limits"]["max_output_bytes"],
)
```

Reject if over limit or bytes are unavailable. Persist exact bytes only after the hash/length descriptor is known.

- [ ] **Step 5: Build receipt and promote to EP2**

Create receipt with `factory_validation.state=UNVALIDATED`. Add `MANUAL_SMOKE` evidence to the profile supporting `proof:EP2_EXECUTION_PROVEN` and the exact artifact hash. Set profile `proof_level=EP2_EXECUTION_PROVEN`; keep `MANUAL_FILE_HANDOFF` and `UNVERIFIED_API`.

Recompute profile fingerprint, then rebuild the receipt against the final EP2 profile SHA so request/profile drift is handled deliberately. Because the original request was bound to the EP1 profile, preserve the EP1 request as historical execution evidence and add a profile-promotion evidence record that explicitly links the request id and returned artifact hash. Do not mutate the historical request id.

The receipt validator must accept a `executed_profile_sha256`/promotion relationship only if the implementation contract explicitly supports it. If this becomes awkward, prefer the safer route: after EP1 is established, create the formal request before manual execution and do not change profile fingerprint until the receipt is recorded; only then create a second profile revision to EP2 while the receipt remains bound to the execution-time EP1 profile. Tests must prove that historical receipts remain valid against their execution-time profile bytes and that using them with the current profile requires explicit provenance rather than silent rebinding.

- [ ] **Step 6: Attempt C6 validation without changing C6**

Run existing C6 validator on the exact bytes:

```python
errors = sponge_v3.validate_sponge_v3(data)
```

Write `validation.json` with artifact SHA, validator identity, result, and exact ordered errors.

If `errors == []`, advance receipt to `FORMAT_VALIDATED` and profile to `EP3_FORMAT_VALIDATED` with FACTORY_TEST evidence.

If errors exist, leave receipt `UNVALIDATED` and profile `EP2_EXECUTION_PROVEN`; record the failed validation evidence. Do not change C6 or rewrite the provider artifact.

- [ ] **Step 7: Add smoke regression tests**

Pin:

- fixture input hash;
- returned artifact hash/length;
- request id;
- receipt hash;
- profile proof state;
- validation outcome;
- C6 errors if the provider output is not C6-valid.

- [ ] **Step 8: Run C10 + C6 + C9 regressions**

```bash
python3 -m unittest discover -s construction/tests -p 'test_c10_*.py' -v
python3 -m unittest construction/tests/test_c6_sponge_v3.py -v
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py -v
python3 construction/scripts/validate_c10.py
git diff --check
```

- [ ] **Step 9: Commit smoke evidence**

Use commit message:

```bash
git commit -m "test(construction): prove ObjToSchematic manual handoff"
```

Include only the exact smoke evidence/profile/tests required by this task.

---

### Task 10: Open and validate the C10 implementation PR

**Files:**
- No new production behavior unless a concrete review/gate defect is found.
- `construction/STATUS.md` remains untouched.

**Interfaces:**
- Produces: reviewable implementation PR with frozen validated head.

- [ ] **Step 1: Reconcile current main before PR**

Fetch/re-audit main and open PRs. If PR #89 or another branch has merged, merge current main into the feature branch rather than force-pushing/rebasing shared history. Resolve only semantic conflicts, then rerun all C10 tests.

- [ ] **Step 2: Run the complete local/CI-equivalent suite**

At minimum:

```bash
python3 -m unittest discover -s construction/tests -p 'test_*.py' -v
python3 construction/scripts/validate_c0.py
python3 construction/scripts/validate_c10.py
python3 -m unittest engineering/tests/test_i2_modlist_catalog.py engineering/tests/test_i2_security_review.py -v
git diff --check
```

Run the real C4 NeoForge materialized build exactly as the workflow does before claiming local parity.

- [ ] **Step 3: Audit diff and STATUS exclusion**

Require:

```text
construction/STATUS.md is absent from the implementation diff
no provider secret exists
no HTTP/browser/scraping implementation exists
C9 tool catalog remains exactly nine
```

- [ ] **Step 4: Open PR**

Title exactly:

```text
feat(construction): add C10 external provider boundary
```

PR body must state:

- C10 is manual-handoff-first;
- all four profiles and proof states;
- ObjToSchematic exact smoke proof state;
- whether C6 validation passed or failed;
- no API automation was added;
- STATUS intentionally unchanged pending postmerge validation.

- [ ] **Step 5: Require all PR gates green**

Require the dedicated C10 workflow plus all triggered inherited Construction, Governance, Sonar/CodeQL checks. Review threads must be resolved. Freeze the exact final PR head SHA before merge.

- [ ] **Step 6: Merge with expected head SHA**

Use GitHub merge with the exact frozen head. Record implementation PR number, final head, merge SHA, and all terminal run/check ids.

---

### Task 11: Validate the exact merged main revision

**Files:**
- No write unless a concrete postmerge defect is found.

**Interfaces:**
- Produces: exact-main evidence required for closeout.

- [ ] **Step 1: Confirm main equals implementation merge SHA**

Record signed/verified merge metadata and parents.

- [ ] **Step 2: Inventory every workflow triggered by the implementation merge**

Require successful completion of the C10 workflow and every triggered inherited Construction C0-C9, Governance, Sonar, CodeQL, Full Skill Migration, or repository policy gate applicable to that SHA.

- [ ] **Step 3: Re-run/inspect provider evidence against merged bytes**

Confirm exact current profiles, smoke artifact hash, request/receipt ids, proof level, API state, and C6 validation outcome on `main`.

- [ ] **Step 4: Re-audit open PRs before closeout**

If another PR has advanced `main`, do not write stale STATUS evidence. Rebase conceptually by validating the newer exact main SHA or wait for relevant gates.

---

### Task 12: Close C10 with a separate STATUS-only PR

**Files:**
- Modify only: `construction/STATUS.md`

**Interfaces:**
- Produces: canonical transition to C11 only after all postmerge evidence is green.

- [ ] **Step 1: Create status-only branch from the exact validated main SHA**

Use a descriptive branch such as:

```text
docs/construction-c10-closeout-status
```

- [ ] **Step 2: Update STATUS only**

Set exactly:

```text
PHASE=C10_COMPLETE_POSTMERGE_VALIDATED
NEXT_ACTION=BEGIN_C11_COMPLEX_MODDED_GOLDEN
MANUAL_ACTION_REQUIRED=NO
```

Record:

- C10 design/plan refs;
- implementation PR number/final head/merge SHA;
- initial RED runs;
- final C10 PR run;
- ObjToSchematic profile proof state and exact artifact/request/receipt hashes;
- C6 validation result without overstating it;
- postmerge C10 and inherited run/check ids;
- current exact main SHA used for closeout.

- [ ] **Step 3: Prove status-only diff**

Require exactly one changed file:

```text
construction/STATUS.md
```

Run `git diff --check` and all path-triggered PR gates.

- [ ] **Step 4: Open/validate closeout PR**

Title:

```text
docs(construction): close C10 postmerge validation
```

Require all triggered gates green and no unresolved review thread.

- [ ] **Step 5: Merge with expected head SHA and validate final main**

Confirm final `main` contains the C10 closeout state. If the status-only merge triggers Construction/Sonar/Governance workflows, require them green before declaring C10 officially complete.

---

## Plan Self-Review Checklist

Before executing Task 1, verify this plan against the spec:

- Profile schema/validator: Tasks 1-2.
- C0 reconciliation and four baseline providers: Task 2.
- Canonical fingerprints and closed vocabularies: Tasks 2-4.
- Request operation-specific shapes: Task 3.
- Receipt/trust states: Task 4.
- Artifact/path/secret security: Task 5.
- Dedicated offline CI/inherited regressions: Task 6.
- C9 unchanged: Tasks 6, 9, 10, 11.
- Documentation without premature STATUS: Task 7.
- ObjToSchematic EP1 evidence and deterministic fixture: Task 8.
- Single-action-at-a-time real handoff, EP2 proof, optional EP3: Task 9.
- PR freeze/merge: Task 10.
- Exact-main postmerge validation: Task 11.
- STATUS-only transition to C11: Task 12.
- No API adapter is created because no baseline provider currently has a verified callable API contract.

Execution choice for this conversation: **Inline Execution**, because the user explicitly delegated review/decision-making and instructed the assistant to proceed. Before implementation begins, load `superpowers:executing-plans` and execute this plan with verification checkpoints.
