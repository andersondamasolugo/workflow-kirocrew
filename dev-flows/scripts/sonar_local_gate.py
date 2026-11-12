#!/usr/bin/env python3
"""Local SonarQube pre-commit gate.

Runs sonar-scanner against a local SonarQube server using the project's
sonar-local.properties, waits for the server-side processing, and evaluates the
lines changed by the diff the way SonarCloud's quality gate evaluates New Code:

    BLOCK  any new BUG or VULNERABILITY, any new BLOCKER/CRITICAL (or HIGH/BLOCKER
           impact) issue, any security hotspot to review on a changed line,
           coverage of changed lines < 80%, duplicated changed lines > 3%
    WARN   other new code smells (should be fixed, do not fail the gate)
    INFO   pre-existing issues on touched files (outside the changed lines)

Usage:
    sonar_local_gate.py <project_dir> [--base <git-ref>] [--no-scan]

<project_dir> is the directory holding sonar-local.properties: the repo root
for the frontend, or ONE microservice module in a backend monorepo (run it once
per module touched by the diff). Diff paths are made relative to that directory.

Diff scope (first non-empty wins): --base <ref> diff, staged diff, working tree diff.
The token is read from the macOS Keychain item 'sonar-local-token'
(security add-generic-password -a "$USER" -s sonar-local-token -w), or from
SONAR_TOKEN when present. It must be a User Token (squ_) to read hotspots and
sources. The token is never printed.

Last line of output is exactly one of:
    SONAR-LOCAL: CLEAN    the changed lines would pass the gate
    SONAR-LOCAL: BLOCKED  fix the BLOCK lines before committing
    SONAR-LOCAL: SKIPPED  server down, no token, no config or scan failure
                          (fall back to the read-only Sonar review)
Exit codes: 0 CLEAN, 1 BLOCKED, 2 SKIPPED.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOST = os.environ.get("SONAR_LOCAL_HOST", "http://localhost:9000")
CONFIG_FILE = "sonar-local.properties"
KEYCHAIN_SERVICE = "sonar-local-token"
SCANNER_FALLBACK = Path.home() / "tools"
CE_TIMEOUT_SECONDS = 600
BLOCKING_TYPES = {"BUG", "VULNERABILITY"}
BLOCKING_IMPACTS = {"HIGH", "BLOCKER"}
BLOCKING_LEGACY = {"BLOCKER", "CRITICAL"}
MIN_NEW_COVERAGE = 80.0
MAX_NEW_DUPLICATION = 3.0
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def skip(reason: str) -> None:
    """Print the SKIPPED verdict with its reason and exit with code 2."""
    print(f"reason: {reason}")
    print("SONAR-LOCAL: SKIPPED")
    sys.exit(2)


def read_token() -> str:
    """Return the scanner token from SONAR_TOKEN or the macOS Keychain, or '' if absent."""
    token = os.environ.get("SONAR_TOKEN", "").strip()
    if token:
        return token
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, check=False,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except FileNotFoundError:
        return ""


def api_get(path: str, token: str, params: dict | None = None) -> dict:
    """GET a SonarQube Web API path and return the decoded JSON body."""
    url = f"{HOST}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url)
    if token:
        auth = base64.b64encode(f"{token}:".encode()).decode()
        request.add_header("Authorization", f"Basic {auth}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def read_properties(path: Path) -> dict:
    """Parse a simple key=value .properties file."""
    props = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            props[key.strip()] = value.strip()
    return props


def diff_scope(repo: Path, base: str | None) -> tuple[list[str], list[str]]:
    """Pick the diff to audit (base ref, staged, then working tree) and return (git args, files)."""
    scopes = ([[f"{base}...HEAD"]] if base else []) + [["--staged"], []]
    for scope in scopes:
        cmd = ["git", "diff", "--relative", "--name-only", "--diff-filter=d", *scope]
        out = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=False)
        files = [f for f in out.stdout.splitlines() if f.strip()]
        if files:
            label = " ".join(scope) or "working tree"
            print(f"diff scope: {label} ({len(files)} files)")
            return scope, files
    return [], []


def changed_lines(repo: Path, scope: list[str]) -> dict[str, set[int]]:
    """Map each diff file to the line numbers added or modified in its new version."""
    cmd = ["git", "diff", "--relative", "-U0", "--diff-filter=d", *scope]
    out = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=False).stdout
    lines: dict[str, set[int]] = {}
    current = None
    for row in out.splitlines():
        if row.startswith("+++ "):
            current = row[6:] if row.startswith("+++ b/") else None
            if current:
                lines.setdefault(current, set())
        elif current and (match := HUNK_HEADER.match(row)):
            start, count = int(match.group(1)), int(match.group(2) or "1")
            lines[current].update(range(start, start + count))
    return lines


def find_scanner() -> str:
    """Locate the sonar-scanner launcher on PATH or under ~/tools."""
    on_path = shutil.which("sonar-scanner")
    if on_path:
        return on_path
    for candidate in sorted(SCANNER_FALLBACK.glob("sonar-scanner-*/bin/sonar-scanner")):
        return str(candidate)
    return ""


def run_scan(repo: Path, token: str) -> str:
    """Run the scanner and return the Compute Engine task id from report-task.txt."""
    scanner = find_scanner()
    if not scanner:
        skip("sonar-scanner not found on PATH or under ~/tools")
    env = dict(os.environ)
    env["SONAR_TOKEN"] = token
    if not env.get("JAVA_HOME"):
        java_home = subprocess.run(["/usr/libexec/java_home", "-v", "17"],
                                   capture_output=True, text=True, check=False)
        if java_home.returncode == 0:
            env["JAVA_HOME"] = java_home.stdout.strip()
    print("scanning... (this takes a few minutes)")
    result = subprocess.run(
        [scanner, f"-Dproject.settings={CONFIG_FILE}", "-Dsonar.qualitygate.wait=false"],
        cwd=repo, env=env, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        print("\n".join(result.stdout.splitlines()[-15:]))
        skip("scanner failed (see tail above)")
    work_dir = read_properties(repo / CONFIG_FILE).get("sonar.working.directory", ".scannerwork")
    return read_properties(repo / work_dir / "report-task.txt").get("ceTaskId", "")


def wait_for_task(task_id: str, token: str) -> None:
    """Poll the Compute Engine until the analysis report is processed."""
    deadline = time.time() + CE_TIMEOUT_SECONDS
    while time.time() < deadline:
        status = api_get("/api/ce/task", token, {"id": task_id})["task"]["status"]
        if status == "SUCCESS":
            return
        if status in {"FAILED", "CANCELED"}:
            skip(f"server-side processing {status}")
        time.sleep(5)
    skip("timed out waiting for server-side processing")


def fetch_issues(project_key: str, token: str) -> list[dict]:
    """Fetch all open issues of the project, paging through the Web API."""
    issues, page = [], 1
    while True:
        body = api_get("/api/issues/search", token, {
            "components": project_key, "issueStatuses": "OPEN,CONFIRMED",
            "ps": 500, "p": page,
        })
        issues += body.get("issues", [])
        if page * 500 >= body.get("paging", {}).get("total", 0):
            return issues
        page += 1


def fetch_hotspots(project_key: str, token: str) -> list[dict] | None:
    """Fetch hotspots to review, or None when the token cannot read them."""
    try:
        return api_get("/api/hotspots/search", token,
                       {"project": project_key, "status": "TO_REVIEW", "ps": 500}).get("hotspots", [])
    except urllib.error.HTTPError as error:
        print(f"  [WARN ] hotspots not checked: HTTP {error.code} (needs a User Token, squ_)")
        return None


def file_of(component: str) -> str:
    """Strip the project key prefix from a component key."""
    return component.split(":", 1)[-1]


def is_new(item: dict, changed: dict[str, set[int]]) -> bool:
    """True when the issue/hotspot sits on a changed line (file-level ones count as new)."""
    path = file_of(item.get("component", ""))
    if path not in changed:
        return False
    line = item.get("line") or item.get("textRange", {}).get("startLine")
    return line is None or line in changed[path]


def blocks_gate(issue: dict) -> bool:
    """True when a new issue would fail the SonarCloud gate (ratings A, no blocker/critical)."""
    impacts = {i.get("severity") for i in issue.get("impacts", [])}
    return (issue.get("type") in BLOCKING_TYPES
            or issue.get("severity") in BLOCKING_LEGACY
            or bool(impacts & BLOCKING_IMPACTS))


def severity_label(issue: dict) -> str:
    """Human-readable type and severity of an issue."""
    impacts = issue.get("impacts", [])
    detail = ",".join(f"{i['softwareQuality']}:{i['severity']}" for i in impacts) or issue.get("severity", "?")
    return f"{issue.get('type', '?')} {detail}"


def new_code_metrics(project_key: str, changed: dict[str, set[int]], token: str) -> dict:
    """Measure coverage and duplication over the changed lines, from per-line source data."""
    totals = {"coverable": 0, "covered": 0, "lines": 0, "duplicated": 0, "uncovered": {}}
    for path, numbers in changed.items():
        if not numbers:
            continue
        try:
            rows = api_get("/api/sources/lines", token, {"key": f"{project_key}:{path}"}).get("sources", [])
        except urllib.error.HTTPError:
            continue  # excluded from analysis or not a source file
        for row in rows:
            if row.get("line") not in numbers:
                continue
            totals["lines"] += 1
            totals["duplicated"] += 1 if row.get("duplicated") else 0
            if "lineHits" in row:
                totals["coverable"] += 1
                if row["lineHits"] > 0:
                    totals["covered"] += 1
                else:
                    totals["uncovered"].setdefault(path, []).append(row["line"])
    return totals


def compact_ranges(numbers: list[int]) -> str:
    """Render sorted line numbers as compact ranges, e.g. 3-5,9."""
    parts, start, prev = [], None, None
    for number in sorted(numbers):
        if start is None:
            start = prev = number
        elif number == prev + 1:
            prev = number
        else:
            parts.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = number
    if start is not None:
        parts.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(parts)


def main() -> None:
    """Entry point: scan, evaluate the changed lines against the gate and print the verdict."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo")
    parser.add_argument("--base", help="git ref to diff against (e.g. origin/develop)")
    parser.add_argument("--no-scan", action="store_true", help="reuse the last analysis")
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()

    config = repo / CONFIG_FILE
    if not config.is_file():
        skip(f"{CONFIG_FILE} not found in {repo}")
    project_key = read_properties(config).get("sonar.projectKey", "")
    key_q = urllib.parse.quote(project_key)
    try:
        if api_get("/api/system/status", "").get("status") != "UP":
            skip(f"SonarQube at {HOST} is not UP")
    except (urllib.error.URLError, OSError):
        skip(f"SonarQube at {HOST} is unreachable (start the container: docker start sonarqube)")
    token = read_token()
    if not token:
        skip(f"no token: set SONAR_TOKEN or Keychain item '{KEYCHAIN_SERVICE}'")

    scope, files = diff_scope(repo, args.base)
    if not files:
        skip("empty diff, nothing to audit")
    changed = changed_lines(repo, scope)
    if not args.no_scan:
        task_id = run_scan(repo, token)
        if task_id:
            wait_for_task(task_id, token)

    file_set = set(files)
    issues = [i for i in fetch_issues(project_key, token) if file_of(i.get("component", "")) in file_set]
    new_issues = [i for i in issues if is_new(i, changed)]
    blocking = [i for i in new_issues if blocks_gate(i)]
    hotspots = fetch_hotspots(project_key, token) or []
    new_hotspots = [h for h in hotspots if is_new(h, changed)]
    metrics = new_code_metrics(project_key, changed, token)
    reasons = []

    print(f"changed lines: {sum(len(v) for v in changed.values())} in {len(changed)} files")
    for issue in sorted(new_issues, key=lambda i: not blocks_gate(i)):
        mark = "BLOCK" if blocks_gate(issue) else "WARN "
        print(f"  [{mark}] {file_of(issue['component'])}:{issue.get('line', '?')} {issue.get('rule')} "
              f"{severity_label(issue)} - {issue.get('message')}")
        if blocks_gate(issue):
            print(f"          {HOST}/project/issues?id={key_q}&open={issue['key']}")
    if blocking:
        reasons.append(f"{len(blocking)} new blocking issue(s)")
    for spot in new_hotspots:
        print(f"  [BLOCK] {file_of(spot['component'])}:{spot.get('line', '?')} HOTSPOT "
              f"{spot.get('ruleKey')} - {spot.get('message')}")
        print(f"          {HOST}/security_hotspots?id={key_q}&hotspots={spot['key']}")
    if new_hotspots:
        reasons.append(f"{len(new_hotspots)} hotspot(s) to review on new code")

    if metrics["coverable"]:
        coverage = 100.0 * metrics["covered"] / metrics["coverable"]
        mark = "BLOCK" if coverage < MIN_NEW_COVERAGE else "ok   "
        print(f"  [{mark}] coverage on new code: {coverage:.1f}% "
              f"({metrics['covered']}/{metrics['coverable']} lines, gate >= {MIN_NEW_COVERAGE:.0f}%)")
        if coverage < MIN_NEW_COVERAGE:
            reasons.append(f"new code coverage {coverage:.1f}%")
            for path, numbers in metrics["uncovered"].items():
                print(f"          uncovered {path}: {compact_ranges(numbers)}")
    else:
        print("  [info ] coverage on new code: n/a (no coverable changed lines or no coverage report)")
    if metrics["lines"]:
        duplication = 100.0 * metrics["duplicated"] / metrics["lines"]
        mark = "BLOCK" if duplication > MAX_NEW_DUPLICATION else "ok   "
        print(f"  [{mark}] duplication on new code: {duplication:.1f}% "
              f"({metrics['duplicated']}/{metrics['lines']} lines, gate <= {MAX_NEW_DUPLICATION:.0f}%)")
        if duplication > MAX_NEW_DUPLICATION:
            reasons.append(f"new code duplication {duplication:.1f}%")

    preexisting = len(issues) - len(new_issues)
    if preexisting:
        print(f"  [info ] {preexisting} pre-existing issue(s) on touched files, outside the changed lines")
    print(f"dashboard: {HOST}/dashboard?id={key_q}")
    print(f"issues:    {HOST}/project/issues?id={key_q}&issueStatuses=OPEN%2CCONFIRMED")
    if reasons:
        print(f"reason: {'; '.join(reasons)}")
    print("SONAR-LOCAL: BLOCKED" if reasons else "SONAR-LOCAL: CLEAN")
    sys.exit(1 if reasons else 0)


if __name__ == "__main__":
    main()
