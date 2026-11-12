---
name: auto/triage-bulk-code-review-findings
description: Classify a large batch of code-review/linter findings by root cause and ownership before fixing, correcting only in-scope real issues
triggers: code review findings, sonar suggestions, 65 remediations, bulk linter findings, bot review comments, fix all suggestions
source: auto
session_key: dashboard:chat-21-1793280258
created_at: 2026-11-04T02:39:22+00:00
---

## When to use
A reviewer, bot, or Sonar/OWASP report hands you a long list (dozens) of findings and asks to "fix everything". Before touching code, triage — treating the list as N literal tasks wastes effort on code you don't own and on false positives, and risks dirtying a PR or stepping on another team.

## Steps
1. Read every finding fully. Do NOT start fixing top-to-bottom.
2. Classify each by the file path it points at:
   - **Out of scope / not your code**: the path belongs to a different feature/HU/module not in the current PR or branch. These are NOT yours to fix here — fixing them pollutes the PR and steps on another team. Route them to their own PR/ticket.
   - **False positive or style opinion**: findings that ask to undo a deliberate design decision (e.g. inheritance vs composition), large redesigns framed as defects (God-component / >N lines splits), or cosmetics (comment wording, language mix, barrel exports) that the quality gate does not block.
   - **Real, in-scope**: genuine defects in code you own and that the PR touches.
3. Collapse the real findings by ROOT CAUSE. Several findings usually share one cause → one fix, not N patches. Example groupings: all `as unknown as` casts → relax the shared generic constraint once; parser abort + try/catch + chunk handling → one fix in the parser service; null-safe + dynamic-regex → one fix in the exporter.
4. Present the classification to the user BEFORE implementing: count of real vs out-of-scope vs false-positive, the grouped root-cause fixes, and the explicit reason for each discard. This is a stop-and-confirm point — the user chooses scope.
5. On confirmation, implement only the real grouped fixes. Fix shared/base code first (non-parallelizable core that others consume), then parallelize disjoint feature surfaces.
6. Verify: typecheck + full affected test suite + real build. For risk-bearing changes add an independent verifier (fresh context) that re-runs everything and checks behavior equivalence.
7. Commit grouped by root cause / by owning feature, never by file type. Report what was fixed and the discarded items with their reason.

## Gotchas
- Effort pressure ("launch 40 agents, fix all 65") is not a reason to fix out-of-scope or false-positive items. Doing so is the opposite of quality and burns tokens/cost on the wrong work.
- A finding pointing at a file outside the current branch/PR belongs to that file's own change — fixing it here creates cross-team conflicts and an unreviewable PR.
- Bot/AI review findings are advisory and do NOT block; the real gate is Sonar Blocker/Critical, coverage, ratings. Don't enter an endless fix-every-suggestion loop — the bot always finds more.
- A finding that asks to undo a recently-made, justified design choice (composition vs inheritance) is an opinion, not a defect; moving code doesn't fix anything.
- Verify the finding's claimed mechanism against the real code (path:line) — the mechanism is a hypothesis, only the symptom is evidence. A cast-removal finding may already be fixable by one generic-constraint change rather than per-call-site edits.
- Prefer deleting/relaxing over adding: the correct root-cause fix for duplicated casts is usually loosening one type constraint, not adding more casts elsewhere.
