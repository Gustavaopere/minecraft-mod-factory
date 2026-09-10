# Workflow: continue existing work

1. Run repository bootstrap and obtain fresh branch/HEAD/worktree evidence.
2. Read project status/decisions/plans and the most recent relevant source/tests.
3. Compare documented status with real code; repository/code evidence wins when stale docs disagree, but update stale docs if authorized.
4. Identify the next causal unfinished task rather than restarting completed work.
5. If previous work claimed verification, re-use it only if evidence is accessible and still applies to the current HEAD; otherwise rerun relevant checks.
6. Preserve concurrent/unrelated changes.
7. Implement and verify from the current real HEAD.
8. Report new checkpoint identifiers only after querying Git/CI.
