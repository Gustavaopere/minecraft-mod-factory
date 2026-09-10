# Workflow: implement a feature

1. Bootstrap repository and read relevant architecture.
2. Write/confirm observable acceptance criteria.
3. Define server/client authority, state ownership/lifetime, lifecycle/cleanup, persistence, synchronization, performance bounds, and integrations where applicable.
4. Verify exact APIs and analogous repository patterns.
5. Select the smallest testable slice.
6. RED: add a failing test/reproduction when a meaningful seam exists and run it.
7. GREEN: implement minimal coherent behavior.
8. Run focused verification immediately.
9. Repeat slices until acceptance criteria are covered.
10. Refactor while tests remain green.
11. Run adjacent regressions, server/client/runtime checks as applicable.
12. Inspect diff/status and complete the evidence report.

Use `assets/FEATURE_SPEC_TEMPLATE.md` and `assets/IMPLEMENTATION_PLAN_TEMPLATE.md` for major systems.
