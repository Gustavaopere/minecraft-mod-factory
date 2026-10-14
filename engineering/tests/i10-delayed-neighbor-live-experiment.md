# I10 delayed-neighbor live experiment — preregistered

TRIAL_CLASS=EXPLORATORY
VERDICT=NOT_YET_OBSERVED
SOURCE_BRANCH=engineering/i10-multiblock-foundation-reference
EXACT_FIXTURE=Minecraft_1.21.1_NeoForge_21.1.250_Java_21
PHYSICAL_MODLIST_VERSION=NeoForge_21.1.248
PHYSICAL_MODLIST_SHA256=7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00

## Frozen question

Can the existing, unchanged `run_i10_delayed_neighbor_diagnostic.py` produce a real controller/port loaded, casing chunk unavailable interval by staged vanilla `forceload` tickets after a full-footprint persistent save/unload, followed by autonomous same-revision recovery without a capability query?

## Hypotheses and falsifiers

- H1: Staged tickets keep controller/port loaded while a casing chunk is genuinely unavailable. Confirmation requires read-only `i10probe peek` to report `UNAVAILABLE / PENDING_REVALIDATION`, `port_bound=true`, revision unchanged and false formed visuals over at least five game ticks. Falsifier: no such state within the configured poll deadline.
- H2: After adding casing tickets, the 20-tick scheduled retry restores the original formation revision, port binding, and formed visuals without a capability query. Confirmation requires observed H1 first, a subsequent passive `FORMED` marker at least 20 game ticks later, and only afterwards valid capability/sentinel. A failed H1 leaves H2 **not tested**, not false.

## Prespecified method, stop rule, and boundaries

Experiment E1: run the existing opt-in harness **once** on a fresh generated dedicated-server world in GitHub Actions, using 21.1.250 and Java 21. Preserve the exact workflow source commit, console output, per-phase server logs and diagnostic `summary.json`.

Exit 2, absence of H1 or a timeout means **PENDING_UNREPRODUCED**, not PASS. Exit 0 means **OBSERVED_EXPLORATORY_ONLY**, not a validated retry regression. An unexpected execution error remains **EXECUTION_INCOMPLETE**. Stop after the single trial and inspect logs. Do not repeat until an evidence-based revised hypothesis exists.

The retry-disabled negative control, independent P2 review, physically matching modpack 21.1.248, and exact-current-head two-real-client manual acceptance are all **separate gates**. No result from this workflow can mark them PASS or authorize merging PR #106.

## Provenance

The historical partial `forceload` approach previously failed to unload neighbor chunks while controller/port chunks were ticketed. Current experiment isolates its possible reproduction on a newly restarted server and fails closed if the missing-chunk condition is not observed.
