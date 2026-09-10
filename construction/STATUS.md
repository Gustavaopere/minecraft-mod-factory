# STATUS — Construction

UPDATED_AT=2026-09-10
PHASE=C1_SCHEMATICA_PRESERVATION_READY_FOR_FINAL_STATUS_REVALIDATION
REPOSITORY=Gustavaopere/minecraft-mod-factory
BRANCH=feat/construction-c1-schematica-upstream
BASE_SHA=8e65289223d4b8a5728fa735a6d72b30a5e4b52e
C0_PR=19
C0_MERGE_SHA=a850627e1a9e012221e4fbabeeb50c22880af51f
C0_PR_GATE=PASS
C0_GOVERNANCE=PASS
C0_SONARCLOUD=PASS
C1_RED_HEAD=860bfac3150586629a478d4403842b2392915565
C1_RED_RUN=34522613247
C1_FIRST_INTEGRATION_HEAD=658afa45b6d223a68474073f86e39e4b440c787d
C1_FIRST_INTEGRATION_RUN=34522703336
C1_FIRST_INTEGRATION_RESULT=492_PASS_6_FAIL_MISSING_SCIPY
C1_FIRST_GREEN_HEAD=868f0de33607eb4cad6112b4a37f2bdcb35b1a0d
C1_FIRST_GREEN_RUN=34522954895
C1_FIRST_GREEN_UPSTREAM_TESTS=498_PASS_0_FAIL
C1_VERIFIED_HEAD=d2dfda928c781edf538244464652de6285b72448
C1_VERIFIED_RUN=34533871548
C1_VERIFIED_UPSTREAM_TESTS=498_PASS_0_FAIL
C1_VERIFIED_C0_RUN=34533871577
C1_VERIFIED_C0=PASS
C1_VERIFIED_GOVERNANCE_RUN=34533871496
C1_VERIFIED_GOVERNANCE=PASS
C1_VERIFIED_SONARCLOUD_CHECK=103060979745
C1_VERIFIED_SONARCLOUD=PASS_0_NEW_ISSUES_0_HOTSPOTS
C1_REVIEW_THREAD=PRRT_kwDOUUL3Ts6hOZca
C1_REVIEW_THREAD_STATE=RESOLVED
HEAD_SHA=RESOLVE_FROM_GIT
OPEN_PR=20
TARGET_MINECRAFT=1.21.1
TARGET_LOADER=NeoForge
CANONICAL_OUTPUT=SPONGE_SCHEMATIC_V3
LATEST_MODLIST_SNAPSHOT=2026-09-09_595_TOP_LEVEL
MANUAL_ACTION_REQUIRED=NO
BLOCKERS=NONE
NEXT_ACTION=REVALIDATE_STATUS_ONLY_HEAD_THEN_MERGE_PR_20_IF_ALL_GATES_PASS

## C1A target

Preserve Schematica exactly as audited upstream source using a Git submodule/gitlink. The Factory superproject must not contain an editable copied Schematica payload.

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

## C1A hardening

The Factory-owned C1 harness installs a fully resolved 33-package test environment from exact versions with SHA-256 hashes using `pip --require-hashes --no-deps`. Schematica itself is not installed editable and is executed directly from the immutable snapshot through `PYTHONPATH`.

The two Sonar findings were proven to belong to the Factory-owned workflow dependency installation commands, not to the upstream Schematica source. The unlocked install commands were removed rather than excluded from analysis. SonarCloud subsequently passed with zero new issues and zero security hotspots.

C0 snapshot validation is submodule-aware: initialized materializable Git submodules are allowed, while copied/vendor payloads and symlink escapes remain rejected. C0 is executed after recursive submodule checkout both in its own workflow and inside the C1 gate.

## C1A acceptance

- [x] upstream commit independently resolves on GitHub
- [x] upstream package metadata declares MIT
- [x] expected RED obtained before gitlink exists
- [x] `.gitmodules` declares exact upstream URL and path
- [x] gitlink mode is `160000`
- [x] gitlink SHA equals audited upstream pin
- [x] Factory superproject tracks no editable Schematica payload
- [x] C0 accepts initialized materializable submodules and rejects copied payloads
- [x] C0 workflow initializes submodules recursively
- [x] C1 executes C0 regression after Schematica initialization
- [x] test environment is fully version-pinned and SHA-256 hashed
- [x] workflow uses `pip --require-hashes --no-deps`
- [x] Schematica is executed from immutable source through `PYTHONPATH`
- [x] upstream native tests pass unchanged: 498/498
- [x] C0 regression passes on verified head
- [x] C1 gate passes on verified head
- [x] Governance passes on verified head
- [x] SonarCloud passes on verified head with 0 new issues and 0 hotspots
- [x] review thread about masked C0 regression is resolved with evidence
- [ ] STATUS-only final head revalidation passes
- [ ] PR #20 merged
- [ ] post-merge `main` revalidation passes
