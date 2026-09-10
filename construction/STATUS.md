# STATUS — Construction

UPDATED_AT=2026-09-10
PHASE=C1_SCHEMATICA_PRESERVATION_SONAR_FIX_PENDING_GREEN
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
C1_GREEN_HEAD=868f0de33607eb4cad6112b4a37f2bdcb35b1a0d
C1_GREEN_RUN=34522954895
C1_GREEN_UPSTREAM_TESTS=498_PASS_0_FAIL
C1_PR_HEAD_BEFORE_SONAR_FIX=ae342148de25a45fa14e94450f1d0102bc53a339
C1_PR_C0_REGRESSION=PASS
C1_PR_GOVERNANCE=PASS
C1_PR_C1_GATE=PASS
C1_PR_SONARCLOUD=FAIL_SECURITY_RATING_C
HEAD_SHA=RESOLVE_FROM_GIT
OPEN_PR=20
TARGET_MINECRAFT=1.21.1
TARGET_LOADER=NeoForge
CANONICAL_OUTPUT=SPONGE_SCHEMATIC_V3
LATEST_MODLIST_SNAPSHOT=2026-09-09_595_TOP_LEVEL
MANUAL_ACTION_REQUIRED=NO
BLOCKERS=SONARCLOUD_SECURITY_RATING_PENDING_REVALIDATION
NEXT_ACTION=REVALIDATE_FIXED_LITERAL_GITLINK_GATE_ON_FINAL_PR_HEAD

## C1A target

Preserve Schematica exactly as audited upstream source using a Git submodule/gitlink. The Factory superproject must not contain an editable copied Schematica payload.

UPSTREAM_REPOSITORY=tester2024/schematica
UPSTREAM_URL=https://github.com/tester2024/schematica.git
UPSTREAM_PIN=0c88770005e7bbd7246997c81e810ba935c8e4cf
UPSTREAM_PATH=construction/upstream/snapshots/schematica
UPSTREAM_POLICY=IMMUTABLE_SNAPSHOT
UPSTREAM_LICENSE_DECLARATION=MIT
TEST_HARNESS_PYTHON=3.11
TEST_HARNESS_SCIPY=1.17.1

## Sonar remediation

The Python preservation contract no longer constructs or executes Git subprocess arguments. Gitlink mode/SHA verification remains a required CI gate using a fixed literal Git command and exact expected index row. No Sonar exclusion is added and no upstream Schematica source is modified.

## C1A acceptance

- [x] upstream commit independently resolves on GitHub
- [x] upstream package metadata declares MIT
- [x] preservation contract test authored
- [x] dedicated C1 workflow authored
- [x] expected RED obtained before gitlink exists
- [x] `.gitmodules` declares exact upstream URL and path
- [x] gitlink mode is `160000`
- [x] gitlink SHA equals audited upstream pin
- [x] Factory-owned missing-SciPy test supplement is outside the submodule
- [x] upstream native tests pass unchanged: 498/498
- [x] prior final-head C0 regression passed
- [x] prior final-head C1 gate passed
- [x] prior final-head Governance passed
- [ ] fixed-head C0 regression passes
- [ ] fixed-head C1 gate passes
- [ ] fixed-head Governance passes
- [ ] fixed-head SonarCloud passes
