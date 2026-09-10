# STATUS — Construction

UPDATED_AT=2026-09-10
PHASE=C1_MINEBENCH_REFERENCE_PR_GREEN_PENDING_STATUS_REVALIDATION
REPOSITORY=Gustavaopere/minecraft-mod-factory
BRANCH=feat/construction-c1-minebench-reference
BASE_SHA=c3d66068474f18622e864ff28de63c393544e787
C0_PR=19
C0_MERGE_SHA=a850627e1a9e012221e4fbabeeb50c22880af51f
C1A_PR=20
C1A_MERGE_SHA=ef991e103f65f0d81967bb0cc1c2592f8c85ccc5
C1A_FINAL_PR_HEAD=3937c63b4146945bc253f0cafdea81d9fe8a3011
C1A_FINAL_PR_RUN=34534056579
C1A_FINAL_PR_UPSTREAM_TESTS=498_PASS_0_FAIL
C1A_POSTMERGE_RUN=34534279311
C1A_POSTMERGE_UPSTREAM_TESTS=498_PASS_0_FAIL
C1A_POSTMERGE_C0_CHECK=103062132492
C1A_POSTMERGE_C0=PASS
C1A_POSTMERGE_GOVERNANCE_RUN=34534279229
C1A_POSTMERGE_GOVERNANCE=PASS
C1A_POSTMERGE_SONARCLOUD=GLOBAL_FAIL_EXTERNAL_TO_CONSTRUCTION_AT_THAT_TIME
HISTORICAL_GLOBAL_SONAR_RELIABILITY_REMEDIATION=PR_21_MERGED
HISTORICAL_GLOBAL_SONAR_SUPERSEDED_PR=22
HISTORICAL_GLOBAL_SONAR_SECURITY_REMEDIATION=PR_23_MERGED
C1B_PR=25
C1B_RED_HEAD=d0da47fe28b8b3748bc9aa290a67632ce332d49e
C1B_RED_RUN=34535088204
C1B_RED_RESULT=2_PASS_1_FAIL_EXPECTED_MISSING_GITMODULE
C1B_GREEN_HEAD=870950966b89d8010d9611cdb68c4b6dd213f32b
C1B_GREEN_RUN=34535272307
C1B_GREEN_CONTRACT=3_PASS_0_FAIL
C1B_GREEN_REGRESSION_TEST_FILES=149_PASS
C1B_GREEN_INTEGRATION_TEST_FILES=18_PASS
C1B_GREEN_LINT=PASS
C1B_GREEN_BUILD=PASS
C1B_GREEN_C0=PASS
C1B_GREEN_WHITESPACE=PASS
C1B_STATUS_REVALIDATION_HEAD=491d793ec69250381b9bfbb652bac46e12ce6807
C1B_STATUS_REVALIDATION_RUN=34535646398
C1B_STATUS_REVALIDATION=PASS
C1B_POSTGRES_PASSWORD_RED_HEAD=3df4cadf73319fac98828064140b5c93faf46c69
C1B_POSTGRES_PASSWORD_RED_RUN=34536772495
C1B_POSTGRES_PASSWORD_RED=4_TESTS_3_PASS_1_FAIL_EXPECTED_LITERAL_PASSWORD
C1B_MAIN_PUSH_RED_HEAD=b61086c78ed2c5162da3c71b198f3c0df627a635
C1B_MAIN_PUSH_RED_RUN=34537041302
C1B_MAIN_PUSH_RED=5_TESTS_4_PASS_1_FAIL_EXPECTED_MISSING_MAIN_TRIGGER
C1B_RECONCILED_MAIN_SHA=c3d66068474f18622e864ff28de63c393544e787
C1B_GATED_PR_HEAD=187f97c0a4a6be910aa2d7736527ee47c931f7aa
C1B_GATED_PR_MERGE_REF=c20c4c776357aa9310b84aa87ebde53723c3eba1
C1B_FINAL_PR_RUN=34538625449
C1B_FINAL_PR_CONTRACT=5_PASS_0_FAIL
C1B_FINAL_PR_REGRESSION_TEST_FILES=149_PASS
C1B_FINAL_PR_INTEGRATION_TEST_FILES=18_PASS
C1B_FINAL_PR_LINT=PASS
C1B_FINAL_PR_BUILD=PASS
C1B_FINAL_PR_C0=PASS
C1B_FINAL_PR_WHITESPACE=PASS
C1B_FINAL_PR_C1A_RUN=34538625347
C1B_FINAL_PR_C1A_CONTRACT=6_PASS_0_FAIL
C1B_FINAL_PR_SCHEMATICA_TESTS=498_PASS_0_FAIL
C1B_FINAL_PR_GOVERNANCE_RUN=34538625343
C1B_FINAL_PR_GOVERNANCE=PASS
C1B_FINAL_PR_SONARCLOUD_CHECK=103076225918
C1B_FINAL_PR_SONARCLOUD=PASS_0_NEW_ISSUES_0_ACCEPTED_0_HOTSPOTS
C1B_REVIEW_THREAD=PRRT_kwDOUUL3Ts6hRAPG
C1B_REVIEW_THREAD_STATUS=RESOLVED
HEAD_SHA=RESOLVE_FROM_GIT
OPEN_PR=25
TARGET_MINECRAFT=1.21.1
TARGET_LOADER=NeoForge
TARGET_NEOFORGE=21.1.248
CANONICAL_OUTPUT=SPONGE_SCHEMATIC_V3
LATEST_MODLIST_SNAPSHOT=2026-09-09_595_TOP_LEVEL
MANUAL_ACTION_REQUIRED=NO
BLOCKERS=NONE_IN_CONSTRUCTION
NEXT_ACTION=REVALIDATE_STATUS_ONLY_HEAD_THEN_MERGE_PR_25

## C1A — Schematica preservation

UPSTREAM_REPOSITORY=tester2024/schematica
UPSTREAM_URL=https://github.com/tester2024/schematica.git
UPSTREAM_PIN=0c88770005e7bbd7246997c81e810ba935c8e4cf
UPSTREAM_PATH=construction/upstream/snapshots/schematica
UPSTREAM_POLICY=IMMUTABLE_SNAPSHOT
UPSTREAM_LICENSE_DECLARATION=MIT
TEST_HARNESS_PYTHON=3.11
TEST_HARNESS_LOCK=construction/upstream/harness/schematica-test-lock.txt
TEST_HARNESS_LOCK_PACKAGES=33
TEST_HARNESS_PIP_REQUIRE_HASHES=YES
TEST_HARNESS_PIP_NO_DEPS=YES

C1A is merged. The Factory superproject tracks only the exact Schematica gitlink; the upstream source remains unchanged. C0 accepts initialized materializable submodules while continuing to reject copied payloads and symlink escapes. The C1 harness uses a fully resolved SHA-256 dependency lock and executes Schematica from the immutable source through `PYTHONPATH`.

The original C1A PR head passed C0, C1, Governance and SonarCloud, and merged `main` revalidated C1, 498/498 upstream tests, standalone C0 and Governance. Later Factory-wide Sonar debt and its remediations are historical context only here and are not used as a current global-Sonar claim. For C1B PR #25, the current reconciled merge ref independently re-ran the C1A contract as 6/6 and the unchanged Schematica upstream suite as 498/498 PASS.

### C1A acceptance

- [x] upstream commit resolves and declares MIT
- [x] exact `.gitmodules` path and canonical URL
- [x] gitlink mode `160000` and exact audited SHA
- [x] no editable Schematica payload in the Factory superproject
- [x] recursive C0 validation with initialized submodule
- [x] copied/vendor payload rejection preserved
- [x] fully pinned SHA-256 test dependency lock
- [x] `pip --require-hashes --no-deps`
- [x] unchanged upstream suite: 498/498
- [x] PR-head C0, C1, Governance and Sonar PASS
- [x] review thread resolved with regression evidence
- [x] PR #20 merged
- [x] post-merge C1 and 498/498 PASS
- [x] post-merge standalone C0 PASS
- [x] post-merge Governance PASS
- [x] post-merge gitlink remains exact
- [x] C1B PR merge ref revalidates C1A contract 6/6 and Schematica 498/498

## C1B — MineBench engine reference

C1B preserves the audited MineBench source as an immutable engine reference. It does not yet introduce a Factory adapter, canonical Build IR, model-provider configuration, API credentials, generation behavior or runtime integration.

UPSTREAM_REPOSITORY=Ammaar-Alam/minebench
UPSTREAM_URL=https://github.com/Ammaar-Alam/minebench.git
UPSTREAM_PIN=c96abbd4c4098aa9c264490c80a1c6544a64ba85
UPSTREAM_PATH=construction/upstream/references/minebench
UPSTREAM_POLICY=ENGINE_REFERENCE
UPSTREAM_LICENSE_DECLARATION=MIT
UPSTREAM_NODE=24
UPSTREAM_PACKAGE_MANAGER=pnpm@10.26.1
UPSTREAM_LOCKFILE=pnpm-lock.yaml
UPSTREAM_INSTALL=pnpm install --frozen-lockfile

The upstream repository defines native quality gates for lint, regression tests, PostgreSQL-backed integration tests and production build. C1B reproduces those gates with local CI dependencies and no model-provider credentials. All Factory-owned GitHub Actions dependencies are commit-pinned.

The first GREEN run reproduced the pinned source with a recursive checkout, installed 487 resolved packages from the frozen lockfile, passed lint, passed 149 regression/config/UI/unit test files, passed 18 PostgreSQL integration test files, and passed the Next.js production build. Upstream voxel export tests exercised Sponge `.schem` export on both a 424-block fixture and a 100,000-block case. C0 and whitespace gates also passed on the same head.

PR #25 then exposed two Factory-owned acceptance defects and both were fixed through explicit RED/GREEN cycles. Sonar first rejected a literal PostgreSQL CI password; the C1B contract now forbids that literal and the workflow derives an ephemeral database password from the GitHub run id and attempt. Review then identified that C1B would not revalidate on the resulting `main` push; a second regression test captured that RED, and the workflow now runs on pushes to both `main` and the feature branch.

After repeated reconciliation with concurrent Factory work, the gated PR head `187f97c0a4a6be910aa2d7736527ee47c931f7aa` is based on canonical `main@c3d66068474f18622e864ff28de63c393544e787` with `behind_by=0`. Its PR merge ref `c20c4c776357aa9310b84aa87ebde53723c3eba1` passed the C1B contract 5/5, exact MineBench gitlink checks, frozen installation, lint, 149 regression/config/UI/unit test files, 18 PostgreSQL integration test files, production build, C0 and whitespace. The same PR head passed the C1A contract 6/6 plus Schematica 498/498, Governance, and SonarCloud with 0 new issues, 0 accepted issues and 0 security hotspots. The only review thread was answered with regression evidence and resolved.

### C1B acceptance

- [x] pinned upstream commit independently resolves
- [x] upstream license independently confirmed MIT
- [x] upstream package manager and frozen lockfile identified
- [x] upstream native CI gates audited
- [x] path selected under `upstream/references/`, preserving the `ENGINE_REFERENCE` boundary
- [x] C1B preservation contract authored
- [x] C1B dedicated workflow authored
- [x] expected RED captured before MineBench gitlink exists
- [x] `.gitmodules` declares exact MineBench URL and path
- [x] MineBench gitlink mode is `160000`
- [x] MineBench gitlink SHA equals audited upstream pin
- [x] recursive checkout resolves exact upstream pin
- [x] frozen dependency installation passes
- [x] upstream lint passes
- [x] upstream regression/config/UI/unit suite passes: 149 test files
- [x] upstream PostgreSQL integration suite passes: 18 test files
- [x] upstream production build passes
- [x] upstream `.schem` export smoke passes, including 100,000-block case
- [x] C0 regression passes on GREEN head
- [x] C1B whitespace passes on GREEN head
- [x] STATUS-only historical revalidation passes
- [x] literal PostgreSQL password regression captured and fixed with ephemeral CI credential
- [x] C1B workflow revalidates on push to `main`
- [x] main-push regression RED captured before trigger fix
- [x] branch reconciled with `main@c3d66068474f18622e864ff28de63c393544e787`, `behind_by=0`
- [x] reconciled final PR head C1B gate passes: 5/5 + 149 + 18 + build + C0 + whitespace
- [x] Schematica C1 regression passes on PR merge ref: 6/6 + 498/498
- [x] Governance passes on PR head
- [x] Sonar introduces no new Construction-owned issue: 0 new issues / 0 accepted / 0 hotspots
- [x] PR review thread resolved with regression evidence
- [ ] final STATUS-only head revalidation passes
- [ ] C1B PR merged
- [ ] post-merge `main` C1B revalidation passes
