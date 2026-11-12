---
name: auto/promote-merged-branch-fresh-pr
description: Promote already-merged commits to another target branch via fresh branch + cherry-pick, verifying merge status and no foreign work first
triggers: promote to stage, PR merged orphaned push, cherry-pick to new branch, fresh branch from origin, verify not merged before commit, develop to stage promotion
source: auto
session_key: dashboard:chat-15-1793029684
created_at: 2026-10-27T00:53:00+00:00
---

## When to use
When you must push a fix to a branch whose PR may already be merged, OR promote already-merged commits from one environment branch to another (e.g. develop → stage). Pushing to a merged PR's branch leaves orphaned commits that never reach the target. This procedure guarantees the commits land in a live PR with a clean, scoped diff.

## Steps
1. **Check merge state FIRST** (before any commit/push to an existing PR branch):
   `gh pr view <num> --json number,state,mergedAt,headRefName,baseRefName,url`
   - If `state == MERGED`, any push to that head branch is orphaned → you need a NEW PR from a fresh branch.
2. **Confirm the commit is orphaned** (not already in the target):
   `git fetch origin <target> --quiet`
   `git branch -r --contains <sha> | grep 'origin/<target>$'` → empty means orphaned.
3. **Scope-check the diff** — ensure only intended work is being promoted, no foreign HUs/teammates' changes:
   `git log origin/<target>..origin/<source> --oneline`
   `git diff origin/<target>..origin/<source> --stat`
   - If only your files appear, no selective cherry-pick needed. If foreign files appear, cherry-pick only your specific commits (exclude the rest).
4. **Create fresh branch from the live target**:
   `git checkout -b <slug>-<target> origin/<target>`
5. **Cherry-pick your commit(s) in chronological order**:
   `git cherry-pick <sha1> <sha2> <sha3>`
6. **Verify the result**: diff vs target shows ONLY intended files; diff vs source is empty (byte-identical to what was already validated):
   `git diff origin/<target> --stat`
   `git diff origin/<source> HEAD -- <files>` (empty = identical, no re-validation needed)
   `grep -rnE '^(<<<<<<<|=======|>>>>>>>)' <src dir>` (0 conflict markers)
7. **Push with explicit branch name** (never let shell expansion into the push target) and open the PR:
   `git push -u origin <slug>-<target>`
   `gh pr create --base <target> --head <slug>-<target> --title ... --body ...`
8. `gh pr view <newnum> --json number,state,baseRefName,headRefName,url` to confirm.

## Gotchas
- **Orphaned push is silent**: `git push` to a merged branch succeeds (exit 0) but the commit never enters the target. Always verify merge state before trusting a push to an existing PR branch.
- **Git push safety policy**: never chain `git add && commit && push` when the commit message contains `{...}` braces (e.g. `@Builder(...)`) — shell brace-expansion fuses into the push target and the push is blocked. Separate into a commit step (use `git commit -F -` with a heredoc to avoid brace issues in the command line) and an isolated `git push origin <explicit-branch>`.
- **Byte-identical content skips re-validation**: if `git diff origin/<source> HEAD` is empty for the promoted files, the already-run build/tests on source still hold — don't waste resources recompiling.
- **Scope creep**: a working tree may carry unrelated modified files from other HUs. Stash or exclude them; stage only the specific files for this change (`git add <explicit paths>`, then grep the diff for foreign directories to confirm none leaked).
