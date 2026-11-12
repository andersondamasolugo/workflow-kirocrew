---
name: auto/promote-commits-develop-to-stage-by-patch-id
description: Promote only a feature's new commits from one branch to another without duplicating content already cherry-picked under different SHAs
triggers: promover a stage, develop to stage, cherry-pick selectivo, git cherry patch-id, no duplicar commits, promote branch, arrastre ajeno
source: auto
session_key: dashboard:chat-3-1792441022
created_at: 2026-11-05T13:50:16+00:00
---

## When to use
Promoting a feature's commits from one long-lived branch (e.g. `develop`) to another (e.g. `stage`) when some of the feature's work was already promoted earlier under DIFFERENT SHAs (prior cherry-picks). `git merge-base --is-ancestor` fails here because it only sees exact SHA ancestry, so it reports already-promoted commits as missing and you risk duplicating content.

## Steps
1. Sync: `git fetch origin -q`.
2. Identify what is genuinely NOT in the target by patch-id, not by SHA ancestry:
   `git cherry origin/<target> origin/<source>` → lines starting with `+` are commits whose patch content is absent from target. Filter to your feature (e.g. `grep -iE 'TICKET-ID|keyword'`). Lines with `-` are already present by content even if the SHA differs.
3. Create a fresh branch off the target: `git checkout -b <feature>-to-<target> origin/<target>`.
4. Cherry-pick ONLY the `+` commits in chronological order: `git cherry-pick <sha1> <sha2> ...`.
5. Verify no foreign drift entered the slice. Compare the committed slice to target using an explicit two-arg diff (NOT a bare working-tree diff):
   `git diff --name-only origin/<target> HEAD`
   Cross-check against the commit's own files: `git show --stat --name-only HEAD`. Both must list only the expected feature files.
6. If a bare `git diff --name-only origin/<target>` shows extra files, suspect uncommitted local work in the working tree from another task. Confirm with `git status --short` and the explicit two-arg diff; untracked/unstaged foreign files are NOT in your commit and must be left intact.
7. Run the project's build/tests + coverage, then the quality/security gate against the target base (`--base origin/<target>`).
8. Verify the merge is clean BEFORE opening the PR: `git merge-tree --write-tree origin/<target> <branch> >/dev/null 2>&1; echo "merge_clean_exit=$?"` (0 = clean).
9. Push as an isolated command (do not chain with `&&`/`2>&1` if a push-destination policy guards it): `git push -u origin <branch>`.
10. Open the PR with `--base <target> --head <branch>` and the mandatory PR template.

## Gotchas
- Never use `git merge-base --is-ancestor` to decide what to promote when earlier promotion used cherry-picks: content travels under a new SHA and ancestry misses it, causing duplicates. `git cherry` compares by patch-id and is the correct tool.
- A bare `git diff --name-only origin/<target>` includes uncommitted working-tree changes and mixes in unrelated local work. Always use the explicit two-arg form `git diff --name-only origin/<target> HEAD` and confirm against `git show --stat --name-only HEAD`.
- The branch suffix, PR base, and cut-from branch must all name the SAME target environment. A branch cut from `stage` only merges cleanly into `stage`.
- Leave another task's uncommitted/untracked files in the working tree untouched; verify they are outside your commit rather than assuming the cherry-pick pulled them in.
