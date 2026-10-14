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

## E1 observed evidence — 2026-10-14 (append-only result)

- Exact trial source commit: `242f22f5e5b378805d791305ab739073f59f0810`.
- GitHub Actions experiment: [run 38602113387](https://github.com/Gustavaopere/minecraft-mod-factory/actions/runs/38602113387), successful as **operational execution only**; artifact `i10-delayed-neighbor-exploratory` ID `11914686164`, [artifact link](https://github.com/Gustavaopere/minecraft-mod-factory/actions/runs/38602113387/artifacts/11914686164).
- Evidence ZIP: five files, ZIP CRC passed, SHA-256 `f09579a737d8835f6fbe59bab5347069017de1bddd7367ebe1136933d73da909`.
- Return code `2`, manifest `verdict=PENDING_UNREPRODUCED`. The dedicated server ran against the exact experimental fixture `Minecraft 1.21.1 / NeoForge 21.1.250 / Java 21`, not the physical modlist loader `21.1.248`.
- Preparation server: `I10_PROBE setup VALID / FORMED / revision=1 / count=1 / capability=true`; after a 40-game-tick drain, the real full-four-chunk removal produced `I10_PEEK UNAVAILABLE / UNFORMED / revision=0` at tick 60.
- Staged restart: 50 passive `I10_PEEK` markers from tick 64 through 657, with **zero** `validation=UNAVAILABLE` observations. First marker was `VALID / PENDING_REVALIDATION / revision=1` at tick 64, with formed visuals still true; 49 subsequent markers were `VALID / FORMED / revision=1`, with formed visuals and port binding true. The test timed out awaiting an actual `UNAVAILABLE / PENDING_REVALIDATION` casing-gap observation.
- Verdict: **H1 not reproduced in E1**. H2 was **not tested**, because the required unavailable-neighbor precondition was never observed. The retry-disabled negative control was **not run**. No P2 closure and no physical multiplayer PASS are justified.
- Interpretation: ordinary chunk-ticket propagation is a plausible mechanism for adjacent casing availability, but E1 does not include internal ticket traces proving this mechanism. The recorded result is narrower: staged `forceload` did not produce the required observable unavailable state in this run.
- Next validation must use a confirmed version-matched isolation mechanism or an explicitly scoped alternative behavioral seam, followed by the negative control and independent review. **Do not repeat the same staged ticket experiment without a revised hypothesis.**
