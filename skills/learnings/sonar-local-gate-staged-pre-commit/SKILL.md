---
name: auto/sonar-local-gate-staged-pre-commit
description: Measure Sonar local coverage on uncommitted work by staging files and running the gate against the staged diff
triggers: sonar local, sonar-gate, coverage before commit, --staged, --base origin, new code coverage, pre-commit sonar
source: auto
session_key: dashboard:chat-29-1793811970
created_at: 2026-11-05T12:18:05+00:00
---

## When to use
Run the local Sonar gate on FE/BE changes BEFORE committing, to see new-code coverage/quality on exactly the lines you are about to ship. The gate picks the diff source as: `--base <ref>` wins, else `--staged`, else working tree (first non-empty wins).

## Steps
1. Decide the diff source. If work is NOT committed yet and you want Sonar to measure it, `git add` the exact files and run the gate WITHOUT `--base` so it uses the staged diff. If work IS committed, run with `--base origin/<branch>` to measure `origin/<branch>...HEAD`.
2. Stage only the files that belong to the change: `git add <paths>` then verify with `git diff --cached --name-only` (exclude unrelated/local scaffolding).
3. For a frontend coverage read, regenerate the LCOV first: `npx jest --coverage`. A stale LCOV (jest run without `--coverage`) makes the gate report old/low coverage that does not reflect current tests.
4. For a backend module, generate coverage first: `./gradlew test jacocoTestReport --no-daemon` (set JAVA_HOME to the required JDK). The gate reads the jacoco XML.
5. Confirm the Sonar server is up: GET `http://localhost:9000/api/system/status` should return `UP`.
6. Launch the gate in background with a log: `nohup python3 <gate-script> <dir> [--base origin/<branch>] >> <log> 2>&1 &`. FE dir = repo root (one scan); BE dir = the touched `*-ms` module.
7. Poll with `pgrep -f sonar_local_gate` and read the log. Verdict is `SONAR-LOCAL: CLEAN` or `BLOCKED`. Always capture the printed dashboard/issues links.
8. If BLOCKED on new-code coverage, find the exact uncovered `path:line` ranges from the output, write targeted tests for those lines, re-run the affected tests, then re-run the gate until CLEAN (cap at ~3 attempts).

## Gotchas
- The dashboard UI measures the WHOLE project's new code (all branches/HUs), while the gate measures only YOUR diff — they disagree by design. Trust the gate for your PR.
- Stale LCOV is the top false-BLOCKED cause on FE: always `npx jest --coverage` before the gate.
- When emitting a shell tool call after a long narrative, put the tool call FIRST with no preamble text, or the call can leak into reply text and never execute.
- After any interruption/restart, scratch logs may be reclaimed; verify real state with `git status --porcelain` and `git diff --cached --name-only` rather than assuming a prior command landed.
