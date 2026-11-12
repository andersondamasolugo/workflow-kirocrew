---
name: auto/diagnose-test-pass-stage-missing-master
description: Diagnose why a test passes in develop/stage but fails in master: find the late commit that missed the release cut, verify by SHA ancestry
triggers: test rojo solo en master, passes in stage not master, commit tardio fuera del tag, merge-base is-ancestor, por que no paso el fix a master, release cut gap
source: auto
session_key: dashboard:chat-13-1792725810
created_at: 2026-10-23T14:45:19+00:00
---

## When to use
A unit test (or any code) is green in develop/stage but red in master after a release/tag promotion, and you need to explain WHY the fix didn't reach master and HOW to carry it over. Applies to any multi-branch repo (develop → stage → master) where master receives code via tags/release branches.

## Steps
1. **Confirm the gap by content.** For the failing file, diff it across branches:
   - `git diff --stat origin/master..origin/stage -- <file>` (non-empty → master is behind)
   - `git diff --stat origin/stage..origin/develop -- <file>` (empty → stage and develop agree)
   This tells you master is the only branch missing the change.
2. **Find the commit that introduced the fix** (the symbol/line the test expects):
   - `git log origin/stage -S "<distinctive code string>" --oneline -- <file>`
   - `git log origin/master..origin/stage --oneline -- <file>` → lists commits in stage not yet in master.
3. **Verify SHA reachability** (the heart of the diagnosis):
   - `git merge-base --is-ancestor <fixCommit> origin/stage && echo IN_STAGE || echo NOT`
   - `git merge-base --is-ancestor <fixCommit> origin/master && echo IN_MASTER || echo NOT`
   - `git merge-base --is-ancestor <fixCommit> <releaseTag> && echo IN_TAG || echo NOT`
4. **Compare dates** of the fix commit vs the last release tag / last merge to master:
   - `git show -s --format='%h %ci %s' <fixCommit>`
   - `git log origin/master --format='%h %ci %s' -3 -- <file>`
   If the fix date is AFTER the tag/cut date → root cause is "late commit, missed the release cut", not a merge error.
5. **State the conclusion** with the timeline: tag was cut on date X from stage's tip; the fix landed on stage on date Y > X; therefore the tag never included it. develop/stage have it, master doesn't.

## Gotchas
- A file can have TWO similar blocks (e.g. an atomic redirect for the `id != null` branch AND for the `id resolved by name` branch). A grep that matches the first gives a false "it's already there". Grep for the SPECIFIC block/line the failing test exercises, or read the method.
- `git diff --stat` direction matters: `A..B` shows what B has that A lacks. A branch cut from master diffed against develop will show thousands of DELETIONS of other teams' work — that is expected, not your change; never push such a branch to develop/stage.
- Prefer carrying the ORIGINAL team commit to master (cherry-pick the real SHA) over a hand-rewritten equivalent, so content stays byte-identical (verify with `md5`). But see the SHA-validator gotcha below.
- If master-promotion is gated by a SHA/genealogy validator (e.g. DOFI), a cherry-pick has a NEW SHA not reachable from stage and WILL be rejected even if byte-identical. Confirm the validator model before cherry-picking onto a master-bound branch.
- When the test documents the correct expected behavior and the implementation doesn't meet it, fix the PRODUCTION code, not the test. Defend it by showing `git diff --name-only | grep -i test` returns nothing.
