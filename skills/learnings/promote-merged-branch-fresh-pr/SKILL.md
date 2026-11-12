---
name: auto/promote-merged-branch-fresh-pr
description: Promote only a feature's new commits to a higher environment branch without duplicating content already promoted under different SHAs
triggers: promote to stage, PR merged orphaned push, cherry-pick to new branch, fresh branch from origin, verify not merged before commit, develop to stage promotion, pase HU a master, rama aislada, cherry-pick commits HU, consolidar un solo commit, promover develop stage master, no arrastrar compañeros
source: auto
session_key: dashboard:chat-3-1792441022
created_at: 2026-10-27T00:53:00+00:00
version: 5
---

## When to use
Promote one or more HUs (Jira stories) or a feature's commits from one long-lived environment branch to another (`develop` → `stage`, `stage` → `master`) WITHOUT dragging other developers' commits into the target, AND without re-applying content that is already present on the target under DIFFERENT SHAs (previously cherry-picked rather than merged). Use a dedicated branch cut from the target and cherry-pick only the commits that genuinely belong to the HU and are genuinely new.

## Steps
1. `git fetch origin -q`. List candidates: `git log --reverse --no-merges --format='%h %an | %s' origin/<target>..origin/develop`.
2. Filter by HU key in the subject and by author. Also list the excluded commits (other authors or other HUs) so you can state clearly what is NOT included.
3. Detect what is NOT yet on the target by patch-id (content), NOT by SHA ancestry: `git cherry origin/<target> origin/<source>` — lines starting with `+` are commits whose content is absent from the target. Filter to the feature (grep the ticket id / keywords). This correctly ignores commits already promoted under a different SHA. For specific HU files also confirm with `git diff --quiet origin/<target> origin/develop -- <files of that HU>`; if the files are identical, it is already there.
4. Create a fresh branch/worktree FROM the target, not from source: `git worktree add -b <HU>-to-<target> "$SCRATCH/promo" origin/<target>` (or `git checkout -b <feature>-to-<target> origin/<target>`).
5. Cherry-pick only the identified new commits in chronological order, using `-x` so the original SHAs stay referenced. Stop at the first conflict and report the file.
6. Verify no foreign drag — pass `HEAD` explicitly: `git diff --name-only origin/<target> HEAD` (a bare `git diff --name-only origin/<target>` also shows uncommitted working-tree changes and will mislead you). Confirm every file belongs to the feature. If a stray file appears, check whether it is in your commit with `git show --stat --name-only HEAD` and `git diff --name-only HEAD~1 HEAD`; files not in those ranges are uncommitted local work, not part of the promotion — leave them untouched. Confirm touched files are byte-identical to the source: `git diff origin/develop --stat -- <touched files>` must be empty.
7. Check that dependent bases (shared libs) are included. Symlink node_modules into the worktree, then run the library build, the app build with the target environment configuration, `tsc --noEmit`, and the relevant jest suites with coverage. Run the local quality/security gate against `--base origin/<target>`.
8. Remove the symlink and `dist`. Verify a clean merge BEFORE opening the PR: `git merge-tree --write-tree origin/<target> HEAD >/dev/null 2>&1; echo "merge_clean_exit=$?"` and expect exit 0.
9. Run `git push -u origin <branch>` as an isolated command (do not chain it with `2>&1` or `&`).
10. Show the delta and wait for the user's OK before `gh pr create --base <target>` (set the base explicitly — never rely on the default). Use the repo PR template, marking [x] only the change types that apply. Then `gh pr view` to confirm it is OPEN and mergeable.
11. Remove the worktree.

## Gotchas
- `git merge-base --is-ancestor` and SHA-equality checks FAIL to detect content promoted under a different SHA (cherry-picks get new SHAs). Always use `git cherry` (patch-id based) for de-dup decisions.
- `git diff --name-only origin/<target>` without `HEAD` mixes in uncommitted working-tree changes — a stray file is usually unrelated local work, not something your cherry-pick introduced. Always re-run with `HEAD` and with a clean `git status --short` before concluding.
- Branch the promotion FROM the target branch, so the diff reflects only what you are adding.
- Before pushing a fix to an existing PR branch, check `gh pr view <n> --json state`. If it is MERGED, cut a new branch from origin/<base> and cherry-pick, because a push to a merged branch is orphaned.
- Never run `git push` in parallel with the commit in the same call; it can go out before the commit exists. Keep `git push` isolated so destination-verification policies are not bypassed.
- Verify by content (patch-id and files), not by SHA, that another HU is already in the target.
- Set the PR base explicitly to the environment branch; GitHub defaults to develop.
- Do not push or open the PR without explicit user authorization.
- Always include the PR template section for user stories (Jira links) and change types.
