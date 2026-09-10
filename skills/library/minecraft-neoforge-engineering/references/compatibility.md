# Third-party mod compatibility

Never invent another mod's API.

For each integration:

1. resolve exact mod/version used by the target pack/project;
2. inspect public source/API/docs for that exact version;
3. classify dependency: required, compile-only, runtime optional, or data-only;
4. design the smallest adapter boundary;
5. keep optional dependency types out of unconditional classloading;
6. define failure/fallback behavior;
7. test with dependency present;
8. if optional, test absent;
9. document supported versions/assumptions.

Preference order: stable documented API → public events/interfaces → tags/data/config → narrow adapter/accessor → reflection/mixin only when necessary.

For combat/magic/tech mods, identify who owns final damage, resource consumption, cooldown, cast/action success, capability/state, and animation. Integrate at a semantic success/commit point to avoid double-applying effects.

Use `assets/INTEGRATION_CONTRACT_TEMPLATE.md` for complex integrations.
