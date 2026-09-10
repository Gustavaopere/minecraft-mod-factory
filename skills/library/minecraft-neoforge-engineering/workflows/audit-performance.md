# Workflow: performance audit

1. Identify workload and performance complaint/risk; do not optimize blindly.
2. Locate hot paths: ticks, entity AI, world scans, queues, pathfinding, networking, rendering, allocations, serialization.
3. Quantify algorithmic bounds from code.
4. Search for unbounded collections and missing unload/retirement paths.
5. Capture runtime evidence when performance is materially claimed.
6. Prioritize architectural reductions: event-driven work, indexes, amortization, budgets, caching with invalidation.
7. Add tests for bounds/invariants where feasible.
8. Re-measure under the same workload.
9. Report before/after evidence and remaining bottlenecks.
