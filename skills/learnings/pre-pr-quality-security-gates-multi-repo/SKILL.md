---
name: auto/pre-pr-quality-security-gates-multi-repo
description: Run tests, Sonar local, and OWASP read audits per repo and consolidate fixes before pushing multi-repo PRs
triggers: sonar local gate, flow-security-gate, pre-commit gates, amend unpushed commit, merge-tree PR check, OWASP read audit, multi-repo PR
source: auto
session_key: dashboard:chat-30-1793877162
created_at: 2026-11-05T13:08:33+00:00
---

## When to use
Before pushing and opening PRs for a feature spread across multiple repos (DB/BE/FE), when you must consolidate pending local changes and prove quality+security gates on the FINAL commit of each repo before delivery. Applies on any repo stack (Java/Spring, Angular, SQL).

## Steps
1. Reconstruct real state with hard data, never trust memory. Per repo: `git branch --show-current`, `git log --oneline -5`, `git status -s`. Flag any tracked-but-uncommitted change and any untracked local scaffolding that must NOT ship.
2. For each pending change, read the surrounding code before deciding. Prefer the root fix that DELETES dead code over one that adds a flag/branch. Confirm no observable behavior change by reading the methods/tests the change touches.
3. Before amending an unpushed commit: verify HEAD is the target commit (`git rev-parse --short HEAD`), confirm the branch does NOT exist on origin (`git ls-remote --heads origin <branch>` or `git log --oneline origin/<branch>..HEAD`) so the amend is safe, then stage ONLY the changed file(s) and check `git diff --cached --stat` shows exactly those before `git commit --amend --no-edit`.
4. Re-run tests after any code change. If a spec asserted the old (bad) pattern, update the assertion to validate the CORRECT behavior, not the anti-pattern. Read the JUnit/coverage XML for real counts before claiming green.
5. Sonar local gate (quality): ensure Docker daemon is up (ask user to open Docker Desktop; do NOT auto-start). On macOS the working socket may be `unix://$HOME/.docker/run/docker.sock` not `/var/run/docker.sock` — set `DOCKER_HOST` accordingly. Generate coverage first (BE: `gradlew test jacocoTestReport` -> jacoco.xml; FE: jest `--coverage` -> coverage/lcov.info). Run the gate against the branch diff: `python3 <gate-script> <dir> --base origin/<base>`. BE = module dir, FE = repo root.
6. Distinguish the gate (diff `origin/<base>...HEAD`, only this feature) from the SonarQube dashboard New Code (by date, whole project). A low dashboard % can be foreign lines in the date window, not your HU — prove it by comparing line counts side by side.
7. OWASP read-only audit (flow-security-gate) on the staged/branch diff: classify stack by file extensions, audit A01-A10 by READING attack-surface files (controller/DTO/repo/service for BE; templates/service for FE). Report CLEAN only with 0 Critical/High.
8. Delivery: show the exact delta per repo (files in vs scaffolding out) and STOP for explicit user OK. Verify each repo's PR state first (`gh pr list --head <branch>` / `gh pr view`) — a PR may already exist.
9. Per PR: `git fetch origin <base>`, isolated `git push origin <branch>`, verify clean merge `git merge-tree --write-tree origin/<base> origin/<branch>; echo $?` (0=clean), then `gh pr create --base <base> --body-file <file>`. Keep the PR body footer template VERBATIM from the canonical template file (never paraphrase or strip template instruction lines).

## Gotchas
- Never auto-start Docker Desktop; the agent starts only the container once the daemon responds.
- Inline shell comments leak to jest/zsh as test patterns — omit them in test commands.
- Pass the explicit JDK path and credentials to spawned subagents; without memory they scan disk for the JDK.
- A PR footer template's instruction line (e.g. 'Relación de acá los Link...') is part of the literal template, not filler — keep it and every change-type gloss verbatim. Store the canonical text in a template FILE (no length cap), and have lessons only POINT to it (lesson `rule` field caps at ~500 chars and silently truncates/overwrites overlapping lessons).
- Only check `[x]` the change types that actually apply (e.g. feature + test).
- Re-measure Sonar after ANY amend — prior coverage numbers predate the change.
