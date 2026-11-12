---
name: auto/promote-merged-branch-fresh-pr
description: Promote only your own HU commits from develop to stage via a cherry-pick branch, verified and opened as a PR
triggers: promote to stage, PR merged orphaned push, cherry-pick to new branch, fresh branch from origin, verify not merged before commit, develop to stage promotion, pase HU a master, rama aislada, cherry-pick commits HU, consolidar un solo commit, promover develop stage master, no arrastrar compañeros
source: auto
session_key: dashboard:chat-21-1793280258
created_at: 2026-10-27T00:53:00+00:00
version: 4
---

## When to use
Promote one or more HUs (Jira stories) from `develop` to `stage` (or stage to master) WITHOUT dragging other developers' commits into the target branch. Use a dedicated branch cut from the target and cherry-pick only the commits that belong to the HU.

## Steps
1. `git fetch origin`. List candidates: `git log --reverse --no-merges --format='%h %an | %s' origin/<target>..origin/develop`.
2. Filter by HU key in the subject and by author. Also list the excluded commits (other authors or other HUs) so you can state clearly what is NOT included.
3. Check whether another HU is already in the target by CONTENT, not by SHA (earlier cherry-picks change hashes): `git cherry origin/<target> origin/develop`, plus `git diff --quiet origin/<target> origin/develop -- <files of that HU>`. If the files are identical, it is already there.
4. Create an isolated worktree and branch from the target: `git worktree add -b <HU>-to-<target> "$SCRATCH/promo" origin/<target>`.
5. Cherry-pick in chronological order using `-x` so the original SHAs stay referenced. Stop at the first conflict and report the file.
6. Make sure nothing foreign got in: `git diff --name-only origin/<target>` must only list the expected projects. Confirm the touched files are byte-identical to develop: `git diff origin/develop --stat -- <touched files>` must be empty.
7. Check that dependent bases (shared libs) are included. Symlink node_modules into the worktree, then run the library build, the app build with the target environment configuration, `tsc --noEmit`, and the relevant jest suites.
8. Remove the symlink and `dist`. Run `git merge-tree --write-tree origin/<target> HEAD` and expect exit 0.
9. Run `git push -u origin <branch>` as an isolated command (do not chain it).
10. Show the delta and wait for the user's OK before `gh pr create --base <target>`. Use the repo PR template, marking [x] only the change types that apply. Then `gh pr view` to confirm it is OPEN and mergeable.
11. Remove the worktree.

## Gotchas
- Before pushing a fix to an existing PR branch, check `gh pr view <n> --json state`. If it is MERGED, cut a new branch from origin/<base> and cherry-pick, because a push to a merged branch is orphaned.
- Never run `git push` in parallel with the commit in the same call; it can go out before the commit exists.
- Verify by content (patch-id and files), not by SHA, that another HU is already in the target.
- Do not push or open the PR without explicit user authorization.
- Always include the PR template section for user stories (Jira links) and change types.
