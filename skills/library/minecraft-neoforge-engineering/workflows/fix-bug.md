# Workflow: fix a bug or crash

1. Reproduce or obtain trustworthy failure evidence.
2. Capture first causal error, environment, side, branch/HEAD, and versions.
3. Reduce to the smallest distinguishing reproduction/check.
4. Form a falsifiable root-cause hypothesis.
5. When feasible, encode the bug as a failing regression test before the fix.
6. Change the root cause, not just the observed symptom.
7. Reproduce original scenario after fix.
8. Run focused regression plus adjacent tests.
9. Check that logs do not reveal a new masked failure.
10. Report root cause, fix, and exact verification evidence.
