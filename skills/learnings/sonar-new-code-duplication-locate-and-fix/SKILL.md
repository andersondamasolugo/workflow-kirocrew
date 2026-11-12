---
name: auto/sonar-new-code-duplication-locate-and-fix
description: Locate the real source of SonarCloud new-code duplication from the per-file Duplications view, then collapse it at the structural root
triggers: SonarCloud duplicated lines, new_duplicated_lines_density, quality gate failed duplication, duplicated lines on new code, 3% duplication threshold, twin entities, MappedSuperclass extract
source: auto
session_key: dashboard:chat-21-1793280258
created_at: 2026-10-30T12:53:30+00:00
---

## When to use
A SonarCloud Quality Gate fails only on `Duplicated Lines on New Code` (e.g. 5.6% > 3%) and you need to find the actual duplicated blocks and remove them at the root, not guess or suppress.

## Core insight
Sonar counts ANY block of ~10+ tokenized lines that repeats, even when both copies are brand-new code you wrote. Two structurally-similar siblings (twin entities, twin CRUD services, twin test suites) flag each other mutually. "New" does not mean "not duplicated." Do not assume the duplicated block is where you think — confirm against the real report before touching anything.

## Steps
1. **Read the real per-file report, not a density number.** In SonarCloud go to Measures -> Duplications for the exact branch/PR and read the per-file breakdown. Each flagged file names its duplicated line count and %. Twin pairs appear with near-equal percentages (fileA 24.6% <-> fileB 22.6%). This tells you WHICH files, which is what guessing gets wrong.
2. **Confirm you are looking at the right analysis.** A dashboard showing `branch develop` with an old `Last analysis ... <sha>` does NOT reflect an unmerged PR. Check `gh pr view <n> --json state,mergedAt,baseRefName` and `git rev-parse origin/<base>` to know what the analysis actually contains before diagnosing.
3. **Reproduce the blocks locally without the Sonar token** by normalizing sibling-specific names then diffing, to find the longest contiguous identical run: `norm(){ sed 's/TypeA/X/g;s/TypeB/X/g'; }` then `diff <(norm < a.java) <(norm < b.java)`. Blocks >= ~10 identical lines are what Sonar counts; fragments < 10 are noise. This reveals whether the mass is in main code, tests, or entities — they are separate sources and fixing one does not fix another.
4. **Fix at the structural root — extract the shared block ONCE, do not copy or suppress.** Follow an existing project pattern rather than inventing one (e.g. an existing `@MappedSuperclass` base class, or an existing abstract test base). For JPA entities: extract common fields into a `@MappedSuperclass`, use `@AttributeOverride` where column names differ per table. For twin test suites: extract common `@Test` cases into an abstract base with abstract hooks for what differs; subclasses keep only their exclusive cases.
5. **Separate ownership.** A flagged file may be preexisting debt from another domain (replicated across modules, unrelated to your ticket). Verify with a repo-wide search and leave it out — it is not yours to fix and may keep the gate red regardless.
6. **Verify locally before pushing:** full build + tests must pass (the compiler and Hibernate are the real judges of a mapping/inheritance change), test count must be preserved (inherited `@Test` cases still count per subclass), and re-run the normalized diff to confirm the long identical block is gone.
7. **Be honest about the gate:** the exact % is recomputed by SonarCloud on the PR analysis, not locally. You can prove the structural block disappeared; you cannot prove the final number locally.

## Gotchas
- Lombok `@Builder` on a subclass does NOT include fields inherited from a superclass. `@SuperBuilder` fixes it but requires the ENTIRE superclass chain to use `@SuperBuilder` — if a shared root base (e.g. `Auditable`) is used by many other entities you cannot add it there. Fallback: drop the builder and use `new X()` + inherited setters (verify production doesn't rely on `.builder()` first via grep).
- Chasing the wrong block is the main failure mode: fixing twin ServiceImpls, then twin tests, while the real flagged file was the entity. Always step 1 first.
- Merging two tables to kill duplication is almost always too big a blast radius (touches production rejection logic, DBA-approved DDL, FE, workers) when the gate only asks to lower a duplication %. Duplication of FORM (two POJOs, same fields) is collapsed by a shared base; you don't need to merge the tables / fuse the business concepts to pass the gate.
- Reading twin entities' unique-key semantics matters: a `serviceType` axis changing the business key means the tables are legitimately distinct — collapse shared fields, don't fuse the tables.
