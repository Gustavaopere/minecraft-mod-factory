# Narrative Auxiliary Document Contracts — Design

Date: 2026-09-15
Status: design approved in chat; implementation authorized

## Problem

The narrative Factory can validate entity declarations and dialogue records through profile-driven required sections and typed reference rules. It deliberately does not treat auxiliary documents as entity declarations.

Consumer campaigns already use auxiliary narrative documents such as quest lifecycle maps and NPC authoring sheets. These files may contain important editorial structure—availability/discovery/engagement/resolution, knowledge boundaries, causality, references, QA—but they currently receive only global story checks because they do not redeclare `TYPE-####` entities.

The gap is therefore structural validation for non-entity auxiliary documents without weakening the existing rule that only entity records declare stable IDs.

## Goals

Add a generic, opt-in profile contract that can validate auxiliary Markdown documents selected by path pattern.

The capability must:

- preserve the distinction between entity declarations and auxiliary documents;
- select auxiliary documents through consumer-owned relative glob patterns under `story_root`;
- require configured `##` sections and non-empty content;
- optionally constrain stable-ID reference types and minimum distinct reference counts per configured section;
- reuse the same case-insensitive heading/alias semantics already used by entity and dialogue contracts;
- remain purely syntactic/structural;
- preserve spoiler-safe reporting and existing unresolved-reference behavior;
- remain backward-compatible for profiles that omit the new field.

## Non-goals

This feature will not:

- infer truth, canon, authorship, causality, chronology, knowledge legitimacy or relationship semantics;
- parse lifecycle enums or validate transition logic;
- validate nested bullet fields such as `knows`, `believes` or provenance channels;
- detect causal or chronological graph cycles;
- create a new stable entity family for lifecycle/relation/authoring notes;
- hardcode Minecraft RPG Skill Tree paths, headings or policies into the Factory;
- rewrite consumer content to make a contract pass.

## Proposed profile contract

Add an optional top-level object:

```json
{
  "auxiliary_document_contracts": {
    "quest-lifecycle": {
      "include": ["04-quests/**/*-lifecycle.md"],
      "required_sections": {
        "availability": ["Availability"],
        "discovery": ["Discovery"],
        "engagement": ["Engagement"],
        "resolution": ["Resolution"]
      },
      "reference_rules": {
        "engagement": {
          "allowed_types": ["NPC", "FAC"],
          "min_references": 0
        }
      }
    }
  }
}
```

Names such as `quest-lifecycle` are logical contract identifiers only. They do not create entity types.

### `include`

- required non-empty list of non-empty relative glob strings;
- patterns are interpreted relative to `story_root` using the recursive glob semantics of `Path.glob`, so `**` is the recursive segment operator;
- profile patterns use `/` as the separator and are normalized for the host platform before matching;
- absolute paths and any pattern containing a `..` path segment are invalid;
- matched paths must resolve inside the trusted `story_root`; a path that resolves outside the root is rejected rather than validated;
- a document matching multiple contracts receives each matching contract independently.

### `required_sections`

- required non-empty object;
- logical section keys map to one or more accepted `##` heading aliases;
- heading comparison is case-insensitive after trimming;
- at least one matching alias occurrence must contain a non-empty line before the next `##` heading.

### `reference_rules`

- optional object;
- keys must name `required_sections` in the same auxiliary contract;
- `allowed_types` must be a non-empty list drawn from `entity_types`;
- `min_references` defaults to `0` and must be a non-negative integer;
- references are counted by distinct stable ID;
- when a required section is absent or empty, only the structural section error is emitted; reference cardinality does not duplicate it.

## Validation model

`validate_story.py` keeps the current entity declaration pass authoritative. Auxiliary validation is an additional pass over Markdown files under `story_root`, but only for files that do **not** contain an H1 entity declaration recognized by the existing declaration regex.

This means a true record such as `# QST-0001 — ...` remains an entity record even if an `include` glob also matches its path. A note such as `# Lifecycle editorial de QST-0001 — ...` remains auxiliary because the H1 does not declare `QST-0001` as the record identity.

For each non-entity Markdown file:

1. derive its normalized path relative to `story_root`;
2. find matching auxiliary contracts from `include` patterns;
3. locate configured `##` headings using aliases;
4. emit structural issues for missing or empty required sections;
5. for populated configured sections, extract stable IDs with the existing profile ID regex;
6. apply per-section allowed-type and distinct minimum-reference rules;
7. leave global ID resolution to the existing story graph logic.

Auxiliary validation never creates declarations. An ID mentioned in an auxiliary H1 or body remains a reference unless separately declared by a true entity record.

## Issue codes

Introduce auxiliary-specific fatal issue codes so reports remain diagnosable and do not conflate entity contracts with auxiliary contracts:

- `missing-auxiliary-required-section`
- `empty-auxiliary-required-section`
- `missing-auxiliary-section-reference`
- `invalid-auxiliary-reference-type`

Issue refs should identify the logical contract and section, plus the offending stable ID where applicable, without changing spoiler-safe default output.

## Configuration validation

`profile.py` must reject malformed configuration, including:

- non-object `auxiliary_document_contracts`;
- blank contract names;
- non-object/empty contract definitions;
- missing or invalid `include` lists;
- absolute patterns or patterns containing a `..` path segment;
- missing/empty `required_sections`;
- blank section keys or empty alias lists;
- `reference_rules` keys not present in that contract's `required_sections`;
- unknown `allowed_types`;
- negative/non-integer `min_references`.

Profiles that omit `auxiliary_document_contracts` must preserve current behavior exactly.

## Implementation boundaries

Expected production files:

- `narrative/tooling/profile.py`
- `narrative/tooling/validate_story.py`

Expected support files:

- new focused tests under `narrative/tests/`;
- `narrative/profiles/example.json`;
- `narrative/README.md`.

No consumer-specific content belongs in this PR.

## TDD strategy

Create tests before production changes. RED must demonstrate:

- profile object/shape validation is missing;
- a matching auxiliary document can omit a required section without current detection;
- an empty section is not currently detected;
- invalid reference types and minimum distinct reference counts are not currently enforced;
- auxiliary files do not accidentally become declarations;
- a true entity record matched by the same glob remains governed only by entity semantics;
- unmatched auxiliary files remain unaffected;
- old profiles remain backward-compatible;
- unsafe absolute/traversal patterns are rejected.

GREEN will implement only the minimum parser/model and validator behavior required by those tests. Documentation/example changes follow after the minimal functional GREEN is observed.

## Consumer integration after Factory merge

The first consumer slice in `Gustavaopere/neoforge-rpg-skilltree` will:

- update `.github/workflows/narrative-factory-consumer.yml` directly from its current Factory pin to the newly certified Factory merge commit;
- add one `auxiliary_document_contracts` entry for quest lifecycle files matching the campaign's actual path convention;
- require only headings already present in the real `QST-0001-lifecycle.md` contract;
- use typed reference rules only where the current corpus supports a genuine invariant;
- avoid rewriting `QST-0001-lifecycle.md` merely to satisfy the validator.

NPC authoring sheets and relationship notes will be audited separately before activation. The generic Factory capability may support them, but this first consumer PR will not assume their invariants.

## Acceptance criteria

The Factory change is accepted when:

1. old profiles still load and validate unchanged;
2. malformed auxiliary contracts fail profile loading deterministically;
3. matching auxiliary documents are validated for required/non-empty sections;
4. configured typed references are validated per section;
5. unmatched documents are unaffected;
6. auxiliary documents never create entity declarations;
7. true entity records are not reclassified as auxiliary by path matching;
8. missing/empty sections do not produce duplicate reference-cardinality errors;
9. unsafe glob patterns or resolved matches outside `story_root` fail closed;
10. the full Narrative Authoring Toolkit test suite passes;
11. Factory repository checks pass on the final PR SHA;
12. the post-merge Factory SHA is certified before the RPG pins it.

The consumer integration is accepted when its real narrative corpus passes the pinned Factory validator without content fabrication or semantic weakening.