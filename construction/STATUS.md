# STATUS — Construction

UPDATED_AT=2026-09-10
PHASE=C1_MINEBENCH_REFERENCE_GREEN_PENDING_PR_GATES
REPOSITORY=Gustavaopere/minecraft-mod-factory
BRANCH=feat/construction-c1-minebench-reference
BASE_SHA=ef991e103f65f0d81967bb0cc1c2592f8c85ccc5
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
C1A_POSTMERGE_SONARCLOUD=GLOBAL_FAIL_EXTERNAL_TO_CONSTRUCTION
GLOBAL_SONAR_SECURITY_REMEDIATION_PR=23
GLOBAL_SONAR_RELIABILITY_REMEDIATION_PR=22
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
HEAD_SHA=RESOLVE_FROM_GIT
OPEN_PR=NONE
TARGET_MINECRAFT=1.21.1
TARGET_LOADER=NeoForge
TARGET_NEOFORGE=21.1.248
CANONICAL_OUTPUT=SPONGE_SCHEMATIC_V3
LATEST_MODLIST_SNAPSHOT=2026-09-09_595_TOP_LEVEL
MANUAL_ACTION_REQUIRED=NO
BLOCKERS=NONE_IN_CONSTRUCTION
NEXT_ACTION=REVALIDATE_STATUS_ONLY_HEAD_THEN_OPEN_C1B_PR

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

The PR head passed C0, C1, Governance and SonarCloud. On merged `main`, C1, 498/498 upstream tests, standalone C0 and Governance passed again. The later branch-level Sonar failure is global repository debt outside `construction/`; current remediation is already owned by concurrent PRs #22 and #23 and is not duplicated here.

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
- [x] global post-merge Sonar debt classified as outside Construction and delegated to existing PRs #22/#23

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

The upstream repository defines native quality gates for lint, regression tests, PostgreSQL-backed integration tests and production build. C1B reproduces only those gates with local CI dependencies and no provider credentials. All Factory-owned GitHub Actions dependencies are commit-pinned.

The first GREEN run reproduced the pinned source with a recursive checkout, installed 487 resolved packages from the frozen lockfile, passed lint, passed 149 regression/config/UI/unit test files, passed 18 PostgreSQL integration test files, and passed the Next.js production build. Upstream voxel export tests exercised Sponge `.schem` export on both a 424-block fixture and a 100,000-block case. C0 and whitespace gates also passed on the same head.

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
- [ ] STATUS-only head revalidation passes
- [ ] Schematica C1 regression passes on PR head
- [ ] Governance passes on PR head
- [ ] Sonar introduces no new Construction-owned issue
- [ ] C1B PR merged
- [ ] post-merge `main` revalidation passes
