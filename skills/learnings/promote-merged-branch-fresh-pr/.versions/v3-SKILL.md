---
name: auto/promote-merged-branch-fresh-pr
description: Reconstruye una rama <HU>-to-master limpia desde master con solo los commits de una HU, sin arrastrar trabajo ajeno del CHANGELOG/archivos compartidos
triggers: promote to stage, PR merged orphaned push, cherry-pick to new branch, fresh branch from origin, verify not merged before commit, develop to stage promotion, pase HU a master, rama aislada, cherry-pick commits HU, consolidar un solo commit, promover develop stage master, no arrastrar compañeros
source: auto
session_key: dashboard:chat-15-1793029684
created_at: 2026-10-27T00:53:00+00:00
version: 3
---

## When to use
When you must push a fix to a branch whose PR may already be merged, OR promote already-merged commits from one environment branch to another (e.g. develop → stage), OR isolate a SINGLE HU to master as one clean commit without dragging in teammates' work that coexists in the develop/stage delta. This includes the case where the `<HU>-to-master` branch got **contaminated** — e.g. resolving a PR conflict in the GitHub web editor with the WRONG target, so the branch absorbed the environment merge and ballooned to hundreds of foreign commits/files. Pushing to a merged PR's branch leaves orphaned commits that never reach the target. This procedure guarantees the commits land in a live PR (or an isolated branch) with a clean, scoped diff. Also use it to prepare the isolated branch for the first time.

NOT for when the agreed model is a release cut from the tip of stage (that drags all of stage and is decided by LT/DevOps). Ask that question EARLY, in parallel — not at the end.

## The root cause that almost always appears
A branch cut from `origin/master` merges CLEAN against master but CONFLICTS against develop/stage, because those environments carry hundreds of foreign commits master doesn't know. The conflict lands on magnet files (CHANGELOG.md, enums, Constants). The typical user mistake is opening the `-to-master` branch's PR against develop: GitHub then asks to reconcile, and resolving in the web editor contaminates the branch. The fix is NOT to regenerate the branch infinitely — it is to set the PR BASE to master. But if the repo flow requires the branch to travel develop→stage→master and rejects a direct PR to master, then the HU reaches master via the release cut (LT/DevOps decides) and the isolated branch stays as evidence of the delta. Ask the user which model applies; do not insist on a PR to master if the user says the flow forbids it.

## Steps
1. **Check merge state FIRST** (before any commit/push to an existing PR branch):
   `gh pr view <num> --json number,state,mergedAt,headRefName,baseRefName,url`
   - If `state == MERGED`, any push to that head branch is orphaned → you need a NEW PR from a fresh branch.
2. **Measure contamination** (when reusing an existing `<HU>-to-master`): `git fetch origin`, then `git rev-list --count origin/master..origin/<HU>-to-master` and `git diff --name-only origin/master..origin/<HU>-to-master | wc -l`. Hundreds = contaminated → recreate from scratch (step 5/5b).
3. **Confirm the commit is orphaned** (not already in the target):
   `git fetch origin <target> --quiet`
   `git branch -r --contains <sha> | grep 'origin/<target>$'` → empty means orphaned.
4. **Stash a dirty working tree** before cutting the new branch (avoids dragging local WIP/workarounds):
   `git stash push -u -m "wip-pre-<target>"`
5. **Locate the HU's real commits** standing on develop, and confirm they already reached stage BY CONTENT (not by SHA — cherry-pick/rebase generate new SHAs):
   `git log --reverse --format="%H %s" --no-merges origin/<target>..origin/<source> | grep "<HU>"`
   `git diff --quiet origin/develop origin/stage -- <code-file>` per code file of the HU.
   `git diff origin/<target>..origin/<source> --stat`
   - If only your files appear, no selective cherry-pick needed. If foreign files appear, bring only your specific commits/files (exclude the rest).
6. **Verify cross dependencies BEFORE cherry-pick**: `git show --name-only <sha>` per commit. Confirm the touched files belong to the feature and don't depend on foreign work you are NOT bringing (otherwise cherry-pick conflicts or leaves inconsistent code).
7. **Create fresh branch from the live target** (NEVER from a tag or from stage when targeting master). To replace a contaminated branch: `git checkout -q origin/master`; `git branch -D <HU>-to-master`; `git checkout -q -b <HU>-to-master origin/master`.
8. **Bring in ONLY the HU**:
   - **Option A — cherry-pick** (when the commits don't drag a contaminated CHANGELOG): `git cherry-pick <sha1> <sha2> ...` in chronological order.
   - **Option B — code files only** (when the commit's CHANGELOG drags another HU's entries): do NOT cherry-pick the whole commit; bring only the CODE files with `git checkout <sha-tip> -- <file1> <file2>` and rebuild the CHANGELOG by hand ON TOP of master's, adding only THIS HU's entries.
9. **(Optional) Consolidate into a single commit** when the team wants clean history on master:
   `git reset --soft origin/<target>` then `git commit -F -` (heredoc body). The tree stays identical; only the history collapses to 1 commit.
10. **Scope-check / verify nothing foreign leaked**:
    `git diff origin/<target> --stat` (only intended files)
    `git diff --name-only origin/<target> | grep -ivE "<feature-file-patterns>"` (must be empty)
    `git diff origin/<target> -- CHANGELOG.md | grep '^+' | grep -v '^+++' | grep -icE '<OTHER-HU>|<foreign-keyword>'` must be 0. NOTE: mentions of other HUs appearing as CONTEXT (lines with a leading space, not `+`) are pre-existing in master's CHANGELOG, NOT contamination your branch adds — count only `+` lines.
    `git diff origin/<source> HEAD -- <files>` (empty = identical, no re-validation needed — only valid if you did NOT squash)
    `grep -rnE '^(<<<<<<<|=======|>>>>>>>)' <src dir>` (0 conflict markers)
    `git log --format='%an' --no-merges origin/<target>..origin/<branch> | sort -u` (only your user — a stray 'contributor' GitHub shows is usually the BASE/HEAD of master, not your work).
11. **Confirm clean merge against master BEFORE the PR**:
    `git merge-tree $(git merge-base origin/master <branch>) origin/master <branch> | grep -cE '^<<<<<<<|^>>>>>>>'` must be 0.
12. **Build + run affected tests locally** on the isolated branch with the project's real config (not just specs) — must pass cleanly against the live target.
13. **Push with explicit branch name** (never let shell expansion into the push target):
    - New branch: `git push -u origin <HU>-to-master`
    - Replace a contaminated remote: get the literal remote SHA first (`git rev-parse origin/<HU>-to-master`), then as an ISOLATED command: `git push --force-with-lease=<HU>-to-master:<REMOTE-SHA-LITERAL> origin <HU>-to-master`.
    Then open the PR with the correct base:
    `gh pr create --base <target> --head <HU>-to-master --title ... --body ...`
14. `gh pr view <newnum> --json number,state,baseRefName,headRefName,url` to confirm.
15. **Restore the stash** on the original branch: `git checkout <original-branch>` + `git stash pop`.

## Gotchas
- **force-with-lease with a LITERAL SHA, no inline substitution.** The git-publish-floor safety policy BLOCKS the push if the target comes from `$(cat ...)`, a variable, a loop, or if you chain `commit && ... && push` on one line (it can't verify the destination). The tool result lies saying 'User denied'. Fix: get the remote SHA beforehand with `git rev-parse origin/<branch>`, then emit the push as an ISOLATED command with the SHA written literally and the branch named explicitly. Never abbreviate the SHA in the lease (it's rejected).
- **Verify by CONTENT, not by SHA.** `git merge-base --is-ancestor <sha> origin/<env>` returns false even when the change is there, because cherry-pick/rebase create new SHAs. The real proof the HU already traveled environments is the byte-identical diff of the code files vs develop/stage.
- **Orphaned push is silent**: `git push` to a merged branch succeeds (exit 0) but the commit never enters the target. Always verify merge state before trusting a push to an existing PR branch. OPEN PR = same branch (push adds to the PR); MERGED = push is orphaned, cut a fresh branch + new PR.
- **Do NOT resolve the conflict in the GitHub web editor if the PR points to the wrong environment** — that drags the whole merge and re-contaminates the branch. Change the PR target or recreate the branch.
- **The isolated branch is prepared ALWAYS**, independent of the tag-to-master model. The release model (isolated HU vs stage cut) is decided by LT/DevOps and that question is asked EARLY, in parallel, not at the end.
- **Squash creates NEW SHAs** distinct from develop/stage. If you later route the squashed branch back through develop/stage, you inject a content-duplicate of the HU into environments that already have it under other SHAs. For a direct pass to master that's fine.
- **Change-control validator (DOFI) validates by SHA and GENEALOGY, not by content**: a tag from an isolated branch whose SHAs are not in stage can be rejected. Confirm with LT/DevOps before creating the tag.
- **Byte-identical content skips re-validation**: if `git diff origin/<source> HEAD` is empty for the promoted files (no squash applied), the already-run build/tests on source still hold — don't recompile. After a squash this check no longer applies; re-run build/tests on the isolated branch.
- **Git push safety policy / braces**: never chain `git add && commit && push` when the commit message contains `{...}` braces (e.g. `@Builder(...)`) — shell brace-expansion fuses into the push target and the push is blocked. Separate into a commit step (use `git commit -F -` with a heredoc) and an isolated `git push origin <explicit-branch>`.
- **Scope creep**: a working tree may carry unrelated modified files from other HUs. Stash or exclude them; stage only the specific files (`git add <explicit paths>`, then grep the diff for foreign directories to confirm none leaked).
- **Shared-lib property renames** (e.g. a TypeScript common-lib) are breaking changes that fail at COMPILE time (TS2339), not silently at runtime: the consumer's CI catches them. Verify no other consumer still uses the old name.
- **When the user gets frustrated and asks for micro-steps** ('list the commits', 'pull develop', 'cut from master'), switch to DATA mode and obey literally without re-explaining the PR-target theory.
