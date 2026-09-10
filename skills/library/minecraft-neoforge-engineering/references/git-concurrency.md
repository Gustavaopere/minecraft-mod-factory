# Git and concurrent branches

Git state is evidence. Verify it instead of relying on remembered conversation state.

Before editing: record branch and HEAD. If parallel agents/branches exist, identify ownership/overlap and base SHA when project rules require it.

Safe defaults:

- fetch remote refs non-destructively when fresh state matters;
- inspect diffs before and after edits;
- preserve unrelated local changes;
- do not reset/rebase/merge/cherry-pick/force-push/commit unless authorized by the task/project policy;
- do not mark preparatory branches as canonical completion;
- do not fabricate APIs expected from unfinished parallel stages.

When integration becomes possible, inspect the actual producer branch/interface and adapt against it, then rerun cross-stage tests.
