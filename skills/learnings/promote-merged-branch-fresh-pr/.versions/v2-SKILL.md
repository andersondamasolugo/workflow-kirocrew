---
name: auto/promote-merged-branch-fresh-pr
description: Aislar una HU a una rama limpia desde master con un solo commit (cherry-pick + squash) para pase manual por ambientes sin arrastrar trabajo ajeno
triggers: promote to stage, PR merged orphaned push, cherry-pick to new branch, fresh branch from origin, verify not merged before commit, develop to stage promotion, pase HU a master, rama aislada, cherry-pick commits HU, consolidar un solo commit, promover develop stage master, no arrastrar compañeros
source: auto
session_key: dashboard:chat-3-1792441022
created_at: 2026-10-27T00:53:00+00:00
version: 2
---

## When to use
When you must push a fix to a branch whose PR may already be merged, OR promote already-merged commits from one environment branch to another (e.g. develop → stage), OR isolate a SINGLE HU to master as one clean commit without dragging in teammates' work that coexists in the develop/stage delta. Pushing to a merged PR's branch leaves orphaned commits that never reach the target. This procedure guarantees the commits land in a live PR (or an isolated branch) with a clean, scoped diff.

NOT for when the agreed model is a release cut from the tip of stage (that drags all of stage and is decided by LT/DevOps). Ask that question EARLY, in parallel — not at the end.

## Steps
1. **Check merge state FIRST** (before any commit/push to an existing PR branch):
   `gh pr view <num> --json number,state,mergedAt,headRefName,baseRefName,url`
   - If `state == MERGED`, any push to that head branch is orphaned → you need a NEW PR from a fresh branch.
2. **Confirm the commit is orphaned** (not already in the target):
   `git fetch origin <target> --quiet`
   `git branch -r --contains <sha> | grep 'origin/<target>$'` → empty means orphaned.
3. **Stash a dirty working tree** before cutting the new branch (avoids dragging local WIP/workarounds):
   `git stash push -u -m "wip-pre-<target>"`
4. **Scope-check the diff** — ensure only intended work is being promoted, no foreign HUs/teammates' changes:
   `git log --reverse --format="%H %s" --no-merges origin/<target>..origin/<source> | grep "<HU>"` (list the HU's commits in chronological order)
   `git diff origin/<target>..origin/<source> --stat`
   - If only your files appear, no selective cherry-pick needed. If foreign files appear, cherry-pick only your specific commits (exclude the rest).
5. **Create fresh branch from the live target** (NEVER from a tag or from stage when targeting master):
   `git checkout -b <slug>-<target> origin/<target>`
6. **Verify cross dependencies BEFORE cherry-pick**: `git show --name-only <sha>` per commit. Confirm the touched files belong to the feature and don't depend on foreign work you are NOT bringing (otherwise cherry-pick conflicts or leaves inconsistent code).
7. **Cherry-pick your commit(s) in chronological order**:
   `git cherry-pick <sha1> <sha2> <sha3>`
8. **(Optional) Consolidate into a single commit** when the team wants clean history on master:
   `git reset --soft origin/<target>` then `git commit -F -` (heredoc body). The tree stays identical; only the history collapses to 1 commit.
9. **Verify the result**: diff vs target shows ONLY intended files; diff vs source is empty when you did NOT squash (byte-identical to what was already validated):
   `git diff origin/<target> --stat`
   `git diff --name-only origin/<target> | grep -ivE "<feature-file-patterns>"` (must be empty = nothing foreign leaked)
   `git diff origin/<source> HEAD -- <files>` (empty = identical, no re-validation needed — only valid if you did NOT squash)
   `grep -rnE '^(<<<<<<<|=======|>>>>>>>)' <src dir>` (0 conflict markers)
10. **Build + run affected tests locally** on the isolated branch with the project's real config (not just specs) — must pass cleanly against the live target.
11. **Push with explicit branch name** (never let shell expansion into the push target) and open the PR:
    - New branch: `git push -u origin <slug>-<target>`
    - If you pushed before squashing: `git rev-parse origin/<slug>-<target>` then `git push --force-with-lease=<slug>-<target>:<remote-sha> origin <slug>-<target>` (SHA-pinned, safe on your own review-less branch).
    `gh pr create --base <target> --head <slug>-<target> --title ... --body ...`
12. `gh pr view <newnum> --json number,state,baseRefName,headRefName,url` to confirm.
13. **Restore the stash** on the original branch: `git checkout <original-branch>` + `git stash pop`.

## Gotchas
- **Orphaned push is silent**: `git push` to a merged branch succeeds (exit 0) but the commit never enters the target. Always verify merge state before trusting a push to an existing PR branch. OPEN PR = same branch (push adds to the PR); MERGED = push is orphaned, cut a fresh branch + new PR.
- **The isolated branch is prepared ALWAYS**, independent of the tag-to-master model. The release model (isolated HU vs stage cut) is decided by LT/DevOps and that question is asked EARLY, in parallel, not at the end.
- **Squash creates NEW SHAs** distinct from develop/stage. If you later route the squashed branch back through develop/stage, you inject a content-duplicate of the HU into environments that already have it under other SHAs. For a direct pass to master that's fine.
- **Change-control validator (DOFI) validates by SHA and GENEALOGY, not by content**: a tag from an isolated branch whose SHAs are not in stage can be rejected. Confirm with LT/DevOps before creating the tag.
- **Byte-identical content skips re-validation**: if `git diff origin/<source> HEAD` is empty for the promoted files (no squash applied), the already-run build/tests on source still hold — don't recompile. After a squash this check no longer applies; re-run build/tests on the isolated branch.
- **Git push safety policy**: never chain `git add && commit && push` when the commit message contains `{...}` braces (e.g. `@Builder(...)`) — shell brace-expansion fuses into the push target and the push is blocked. Separate into a commit step (use `git commit -F -` with a heredoc) and an isolated `git push origin <explicit-branch>`.
- **Scope creep**: a working tree may carry unrelated modified files from other HUs. Stash or exclude them; stage only the specific files (`git add <explicit paths>`, then grep the diff for foreign directories to confirm none leaked).
- **Shared-lib property renames** (e.g. a TypeScript common-lib) are breaking changes that fail at COMPILE time (TS2339), not silently at runtime: the consumer's CI catches them. Verify no other consumer still uses the old name.
