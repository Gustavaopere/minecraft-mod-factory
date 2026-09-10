# Release and hardening

Release readiness is stronger than code completion.

Check applicable areas:

## Build and metadata

Java 21, wrapper/plugin/dependency resolution, clean build, mod metadata/version ranges, generated resources, artifact naming, license/notices.

## Runtime

Dedicated server, client where relevant, representative new world and existing-world upgrade paths, registry/data reload, save/reload, reconnect/dimension transitions.

## Compatibility

Required dependencies declared correctly, optional dependencies genuinely optional, supported-version matrix, graceful absence/failure, no client-only leakage.

## Performance

No unbounded growth, no whole-world per-tick scans, explicit budgets for hot work, cache invalidation/retirement, no packet storms.

## Persistence

Missing/old data handling, codec/default compatibility, identifier stability, upgrade behavior, unload/reload.

## Hygiene

Diff/status clean of unrelated files, no secrets/local paths/debug artifacts, CI verified if present, changelog/release notes if project uses them.
