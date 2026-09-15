# Narrative Auxiliary Document Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in structural and typed-reference validation for auxiliary narrative Markdown documents without turning them into entity declarations.

**Architecture:** Extend `NarrativeProfile` with generic path-selected auxiliary document contracts. `validate_story.py` precomputes contract matches with `Path.glob`, refuses matches resolving outside `story_root`, and reuses the existing section/reference validators while remapping issue codes to auxiliary-specific fatal codes. Entity declaration detection remains authoritative and takes precedence over auxiliary matching.

**Tech Stack:** Python 3.11+, stdlib `pathlib`, `dataclasses`, `unittest`, JSON profiles, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-15-narrative-auxiliary-document-contracts-design.md`

## Global Constraints

- No campaign-specific paths, IDs, lore or policies in Factory production code.
- No paid dependency.
- Profiles omitting `auxiliary_document_contracts` preserve existing behavior.
- Auxiliary files never create stable-ID declarations.
- True H1 entity declarations always keep entity semantics even when a glob matches.
- Glob patterns are relative to `story_root`; absolute patterns and `..` segments are rejected.
- Matched files resolving outside `story_root` fail closed.
- Missing/empty required sections suppress duplicate reference-cardinality errors.
- Validation remains syntactic/structural; no lore truth, causality or knowledge inference.

---

### Task 1: RED tests for profile and validation behavior

**Files:**
- Create: `narrative/tests/test_auxiliary_document_contracts.py`

**Interfaces:**
- Consumes: `profile.load_profile(path, workspace_root)`, `validate_story.validate(root, profile)`, `validate_story.exit_code(issues)`.
- Produces: executable behavioral contract for `NarrativeProfile.auxiliary_document_contracts` and auxiliary issue codes.

- [ ] **Step 1: Write failing profile tests**
  - Valid contract loads `include`, required section aliases and typed reference rules.
  - Omitted field yields `{}`.
  - Reject non-object root, blank names, empty definitions, invalid/unsafe include patterns, empty required sections, undeclared reference-rule keys, unknown entity types and invalid minimums.

- [ ] **Step 2: Write failing validator tests**
  - Matching auxiliary docs emit `missing-auxiliary-required-section` / `empty-auxiliary-required-section`.
  - Typed rules emit `missing-auxiliary-section-reference` / `invalid-auxiliary-reference-type` and count distinct IDs.
  - Structural errors suppress reference-cardinality duplicates.
  - Unmatched docs remain unaffected.
  - An auxiliary H1 reference remains a reference, not a declaration.
  - A true `# TYPE-####` entity matched by the same glob is not auxiliary-validated.
  - A symlinked match resolving outside `story_root` raises `ValueError`.

- [ ] **Step 3: Push tests only and verify RED in CI**
  - Expected: focused tests fail because the profile field/parser and validator behavior do not exist.
  - Confirm failures are assertions about missing capability, not import/syntax errors.

- [ ] **Step 4: Commit**
  - Commit message: `test(narrative): specify auxiliary document contracts`

### Task 2: GREEN profile model and parser

**Files:**
- Modify: `narrative/tooling/profile.py`
- Test: `narrative/tests/test_auxiliary_document_contracts.py`

**Interfaces:**
- Produces:
  - `AuxiliaryReferenceRule(allowed_types: tuple[str, ...], min_references: int)`
  - `AuxiliaryDocumentContract(include: tuple[str, ...], required_sections: dict[str, tuple[str, ...]], reference_rules: dict[str, AuxiliaryReferenceRule])`
  - `NarrativeProfile.auxiliary_document_contracts: dict[str, AuxiliaryDocumentContract]`

- [ ] **Step 1: Add dataclasses and field to `NarrativeProfile`.**
- [ ] **Step 2: Add parser helpers** validating object shape, non-empty names/sections, `include`, relative `/`-style patterns, no `..` segments, allowed entity types and non-negative integer minima.
- [ ] **Step 3: Wire parser into `load_profile`.**
- [ ] **Step 4: Run profile-focused tests and verify GREEN.**
- [ ] **Step 5: Commit** with `feat(narrative): parse auxiliary document contracts`.

### Task 3: GREEN story validator

**Files:**
- Modify: `narrative/tooling/validate_story.py`
- Test: `narrative/tests/test_auxiliary_document_contracts.py`

**Interfaces:**
- Consumes: `NarrativeProfile.auxiliary_document_contracts`.
- Produces fatal issue codes:
  - `missing-auxiliary-required-section`
  - `empty-auxiliary-required-section`
  - `missing-auxiliary-section-reference`
  - `invalid-auxiliary-reference-type`

- [ ] **Step 1: Add the four codes to `FATAL_CODES`.**
- [ ] **Step 2: Precompute lexical relative matches per contract with `root.glob(pattern)`; for each file match, resolve and require `resolved.relative_to(root.resolve(strict=True))` or raise `ValueError`.**
- [ ] **Step 3: Keep the existing declaration scan authoritative. Only when `first_declared_id is None`, apply matching auxiliary contracts.**
- [ ] **Step 4: Reuse `_required_section_issues` and `_entity_reference_issues`, remapping their codes and using `contract_name` as the structural record key.**
- [ ] **Step 5: Run focused tests and the full `narrative/tests` suite; all must pass.**
- [ ] **Step 6: Commit** with `feat(narrative): validate auxiliary documents`.

### Task 4: Documentation, example and roadmap completion

**Files:**
- Modify: `narrative/README.md`
- Modify: `narrative/profiles/example.json`
- Delete: `plans/narrative-authoring/11 - Auxiliary Document Contracts 🔄.md`
- Create: `plans/narrative-authoring/11 - Auxiliary Document Contracts ✅.md`
- Modify: `plans/narrative-authoring/README.md`

**Interfaces:**
- Documents the exact profile schema and keeps roadmap status synchronized with merged implementation evidence.

- [ ] **Step 1: Add a generic example contract to `example.json`.**
- [ ] **Step 2: Document selection, section rules, typed references, entity precedence, path safety and structural-only scope in `narrative/README.md`.**
- [ ] **Step 3: Rename milestone 11 from 🔄 to ✅ and record implementation/tests/PR evidence without claiming consumer integration before it occurs.**
- [ ] **Step 4: Run full narrative tests again.**
- [ ] **Step 5: Commit** with `docs(narrative): document auxiliary document contracts`.

### Task 5: PR verification and Factory release gate

**Files:** none beyond prior tasks.

- [ ] **Step 1: Review changed files and diff for consumer-specific leakage or accidental entity reclassification.**
- [ ] **Step 2: Verify no unresolved review threads and refetch PR head SHA.**
- [ ] **Step 3: Wait for all required PR checks on the exact head SHA to succeed.**
- [ ] **Step 4: Merge with `expected_head_sha` so a moved head cannot be merged accidentally.**
- [ ] **Step 5: Certify the exact merge SHA with post-merge CI before any consumer pins it.**

### Task 6: RPG consumer integration after certified Factory merge

**Files in `Gustavaopere/neoforge-rpg-skilltree`:**
- Modify: `.github/workflows/narrative-factory-consumer.yml`
- Modify: `historia/narrative-authoring-profile.json`

**Interfaces:**
- Pins the certified Factory merge SHA.
- Adds one quest-lifecycle auxiliary contract matching the real campaign path convention.

- [ ] **Step 1: Re-audit `QST-0001-lifecycle.md` and campaign quest policy; require only established lifecycle headings.**
- [ ] **Step 2: Update Factory pin directly from the current SHA to the newly certified merge SHA.**
- [ ] **Step 3: Add a `quest-lifecycle` contract for the actual lifecycle glob; configure typed reference rules only if the current corpus establishes a real invariant.**
- [ ] **Step 4: Run consumer CI and verify the real corpus passes without fabricated content changes.**
- [ ] **Step 5: Merge with exact head SHA and certify post-merge consumer CI.**

## Self-review

Spec coverage: all accepted design requirements map to Tasks 1–6, including path safety, entity precedence, backward compatibility and no duplicate reference errors.

Placeholder scan: no TBD/TODO or unspecified implementation steps remain.

Type consistency: the plan consistently uses `AuxiliaryReferenceRule`, `AuxiliaryDocumentContract` and `NarrativeProfile.auxiliary_document_contracts`; validator issue codes match the design spec exactly.