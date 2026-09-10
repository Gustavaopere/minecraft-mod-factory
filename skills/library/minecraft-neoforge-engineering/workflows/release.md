# Workflow: release/hardening

1. Read repository release checklist/versioning/CI policy.
2. Freeze intended scope; distinguish known deferred issues.
3. Run clean build and full applicable automated suite.
4. Validate generated resources/data.
5. Run dedicated-server and client scenarios where relevant.
6. Test save/reload/upgrade and optional-mod matrix according to supported claims.
7. Review performance bounds and runtime warnings.
8. Inspect artifact metadata, dependency ranges, license/notices, version/changelog.
9. Inspect final diff/status and CI.
10. Release only with explicit authorization; otherwise report readiness and blockers.
