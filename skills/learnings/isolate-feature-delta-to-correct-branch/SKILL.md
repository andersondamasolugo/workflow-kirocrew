---
name: auto/isolate-feature-delta-to-correct-branch
description: Move uncommitted feature work off a wrong branch onto its own branch cut from the base, without contaminating either
triggers: wrong branch, isolate delta, stash selective, feature branch, contaminate other HU, move uncommitted changes, cut from develop
source: auto
session_key: dashboard:chat-29-1793811970
created_at: 2026-11-05T00:58:25+00:00
---

## When to use
When a subagent/writer or a prior session left uncommitted feature work sitting on top of the WRONG branch (another ticket's branch), and you must relocate only that feature's delta to its own branch cut from the base (e.g. origin/develop) without disturbing the other branch's work. Also applies when verifying a delta is safe to commit before committing.

## Steps
1. Confirm current branch and that it is NOT the target feature branch: `git -C <repo> rev-parse --abbrev-ref HEAD`.
2. Enumerate the exact delta with `git status --porcelain`. Identify which paths belong to THIS feature (new dirs = untracked, shared files = modified).
3. For any SHARED tracked file (e.g. a routing file), verify it is identical between the current wrong branch and the base so the block transplants cleanly: `git fetch origin <base> --quiet` then `git diff --stat HEAD origin/<base> -- <shared-file>`. Zero diff = safe to move.
4. Check whether the target feature branch already exists: `git branch -a | grep -i <ticket>`.
5. Selectively stash ONLY this feature's paths (include untracked with -u): `git stash push -u -m "<ticket> <desc>" -- <feature-dir> <shared-file>`.
6. Confirm the wrong branch is now clean: `git status --porcelain` (must be empty of the feature paths).
7. Switch to the feature branch: `git checkout <feature-branch>` (or `git checkout -b <feature-branch> origin/<base>` if it does not exist).
8. Reapply the delta: `git stash pop`. Confirm with `git status --porcelain`.
9. Before committing: verify git identity (`git config user.name/user.email`), stage ONLY the feature files with explicit paths (never `git add .`), confirm with `git diff --cached --stat`, and ensure work docs (SDD/README) are left OUT. Commit with a Conventional Commits message describing the result.

## Gotchas
- NEVER `git add .` — stage explicit paths so stray work docs or config don't leak into the commit.
- Step 3 is mandatory: if the shared file differs between the wrong branch and base, `stash pop` can conflict or carry the other branch's changes. Verify zero diff first.
- A plain `git stash -u` (no pathspec) grabs EVERYTHING including the other ticket's dirty work — always pass explicit `-- <paths>`.
- If you do a repo-wide `git stash -u` to switch branches, note it — a later `git stash pop` on the original branch is needed to restore that other work.
- The untracked feature directory travels with you across `checkout -b` only because it's untracked; a shared tracked file does not, hence the stash.
- Do not commit a working doc (SDD, PR body, scratch .md) with the code — keep it untracked.
