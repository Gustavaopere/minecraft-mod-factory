# Workflow: integrate a third-party mod

1. Resolve exact target mod/version and dependency status.
2. Inspect exact public source/API/docs and repository's existing compat code.
3. Define semantic integration point and state ownership; avoid double-applying gameplay effects.
4. Choose stable API/event/tag/data boundary where possible.
5. Create a narrow adapter package/module.
6. If optional, isolate third-party types from unconditional classloading.
7. Add contract/adapter tests where possible.
8. Verify dependency present.
9. Verify dependency absent when optional.
10. Verify dedicated-server path if common/server code changed.
11. Document exact version assumptions and fallback behavior.
