# Mixins and reflection

Treat mixins/reflection as compatibility debt, not automatically forbidden tools.

Before using them:

- demonstrate that a stable public API/event/data path is insufficient;
- identify the exact upstream symbol/version assumption;
- minimize injection/access scope;
- define behavior if the target changes or optional mod is absent;
- test target presence and startup on supported environments;
- document why the hook exists.

Avoid broad ordinal-based or fragile bytecode assumptions when a more semantic target exists. For reflection, cache resolved handles where appropriate, validate types/signatures, and fail with actionable diagnostics rather than silently corrupting state.
