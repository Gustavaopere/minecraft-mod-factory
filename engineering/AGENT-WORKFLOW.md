# Agent Workflow — Minecraft Mod Factory

Status: canonical working contract for reusable mod-production infrastructure.

## Target platform

- Minecraft `1.21.1`
- NeoForge physical baseline `21.1.248`
- Java `21`
- NeoGradle/UserDev and Gradle versions must be resolved from the target runtime repository or a validated Factory template; do not infer them from another project.

## Required entrypoints

Before relevant work read, in order: `../STATUS.md`, both plans under `../plans/`, `REPO-ROUTING.md`, `../skills/VERSION-AUTHORITY.md`, the latest physical modlist evidence, and current GitHub state.

Use `../migration/MIGRATION-MATRIX-F1-M3.md` while the historical transfer remains active. Do not duplicate work already classified and proven there.

## Permanent workflow invariants

1. Never invent API signatures, registry IDs, provider versions, paths, branch/PR state or test evidence.
2. The actual repository tree wins over conceptual plan paths.
3. Runtime authority remains in each mod repository; the Factory prepares and validates delivery.
4. `engineering/` and `art/` share a repository but retain separate authority boundaries.
5. Preserve native authoring formats, especially `.bbmodel`; conversions are explicit and source-preserving.
6. Version-sensitive behavior is verified against Minecraft 1.21.1 / NeoForge 21.1.248-compatible evidence before support is claimed.
7. Prefer fail-closed schemas, validators and provider adapters when evidence is incomplete.
8. Use regression-first/TDD where practical. A capability is not complete until its applicable automated or runtime/visual gate passes.
9. Compile success cannot be promoted to runtime, multiplayer, save, visual, compatibility or release success.
10. Recheck `main`, open PRs and concurrent branches immediately before merge-relevant actions.
11. Historical infrastructure is migrated/reconciled/revalidated rather than rewritten from scratch.
12. Never delete historical RPG infrastructure until an equivalent Factory capability is proven GREEN and the migration plan authorizes cleanup.

## Manual-user protocol

When a required operation cannot be executed by the agent, follow `../skills/USER-GUIDED-WORKFLOW.md`: one atomic manual step at a time, then wait for evidence before issuing another.

## Change workflow

Characterize the gap; verify version/authority facts; add a failing regression when practical; implement the smallest change; run deterministic validators/tests; run generated sample build or runtime/visual gates when applicable; resynchronize with current `main`; review the exact diff; open a PR; validate the exact PR head; and only mark the milestone complete with evidence.
