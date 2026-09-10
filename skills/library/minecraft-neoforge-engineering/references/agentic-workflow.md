# Agentic workflow

Use this reference for multi-step implementation, cross-cutting systems, or work likely to require several edit/verify cycles.

## Discovery

Establish current truth before planning. Inspect the repository, current branch/HEAD/worktree, build system, target versions, project instructions, existing contracts, tests, and relevant upstream dependencies.

Do not use a conversation summary as a substitute when the repository can be inspected.

## Planning

Plan at the level necessary to eliminate architectural uncertainty, not at the level of narrating every line. A good plan identifies causal ordering, state ownership, public contracts, synchronization, persistence, cleanup, performance budgets, compatibility boundaries, verification, and unresolved dependencies.

Do not ask for approval merely because a plan exists if the user already authorized implementation. Plan mode is a reasoning step, not an excuse to stop.

## Execution

Implement in small coherent slices. Prefer a failing test/reproduction first. Verify each high-risk boundary soon after creating it rather than accumulating untested architecture.

## Tool use

Use deterministic tools for deterministic work: compiler, Gradle, tests, source search, parsers, Git status/diff, and scripts. Use web/docs/source retrieval for version-sensitive external facts. Do not replace an available authoritative lookup with memory.

## Review

Check behavioral acceptance, not just source aesthetics. Re-evaluate side safety, persistence/reload, cleanup, boundedness, optional-mod absence, and compatibility when applicable.

## Reporting

Report evidence, not confidence. Distinguish implemented from verified. Exact commands/CI/run IDs should be stated only when observed.
