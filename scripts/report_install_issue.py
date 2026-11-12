#!/usr/bin/env python3
"""Build (and optionally file) a redacted GitHub issue for a failed kit installation.

Usage:
    python3 scripts/report_install_issue.py --step "install.sh" --log install.log
    python3 scripts/report_install_issue.py --step "install.sh" --log install.log --submit

Without --submit the issue body is only printed, so the user can review it first.
With --submit the issue is created with the GitHub CLI; if gh is missing or not
authenticated, a pre-filled issue URL is printed instead.
"""
from __future__ import annotations

import argparse
import getpass
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

REPO = "andersondamasolugo/workflow-kirocrew"
LABEL = "install-failure"
MAX_LOG_LINES = 80
MAX_URL_BODY = 6000

SECRET_PATTERNS = [
    (re.compile(r"(gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}"), "<redacted-token>"),
    (re.compile(r"\bsq[aup]_[A-Za-z0-9]{20,}"), "<redacted-token>"),
    (re.compile(r"\bxox[abp]-[A-Za-z0-9-]{10,}"), "<redacted-token>"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "<redacted-token>"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.?[A-Za-z0-9_-]*"), "<redacted-jwt>"),
    (re.compile(r"(?i)(authorization:\s*(?:basic|bearer)\s+)\S+"), r"\1<redacted>"),
    (re.compile(r"(?i)\b([A-Za-z_]*(?:token|password|passwd|secret|api[_-]?key)[A-Za-z_]*)\s*[=:]\s*\S+"), r"\1=<redacted>"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "<redacted-email>"),
]


def redact(text: str) -> str:
    """Remove secrets, emails, the user name and the home directory from text."""
    home = str(Path.home())
    for variant in {home, home.replace("\\", "/"), home.replace("/", "\\")}:
        if variant:
            text = text.replace(variant, "~")
    user = getpass.getuser()
    if user and len(user) > 2:
        text = re.sub(re.escape(user), "<user>", text, flags=re.IGNORECASE)
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def read_log_tail(path: str | None) -> str:
    """Return the redacted last lines of the log file, or a placeholder."""
    if not path:
        return "(no log provided)"
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"(could not read log: {type(exc).__name__})"
    return redact("\n".join(lines[-MAX_LOG_LINES:]))


def kit_version() -> str:
    """Return the latest changelog version of the kit, or 'unknown'."""
    changelog = Path(__file__).resolve().parent.parent / "CHANGELOG.md"
    try:
        match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog.read_text(encoding="utf-8"), re.MULTILINE)
    except OSError:
        return "unknown"
    return match.group(1) if match else "unknown"


def build_body(step: str, log_tail: str, notes: str) -> str:
    """Compose the Markdown body of the issue."""
    return "\n".join([
        "## What failed",
        f"Step: `{redact(step)}`",
        "",
        "## Environment",
        f"- OS: {platform.system()} {platform.release()} ({platform.machine()})",
        f"- Python: {platform.python_version()}",
        f"- Kit version: {kit_version()}",
        f"- Shell: {redact(os.environ.get('SHELL') or os.environ.get('ComSpec') or 'unknown')}",
        "",
        "## Notes",
        redact(notes) if notes else "(none)",
        "",
        "## Log (redacted, last lines)",
        "```text",
        log_tail,
        "```",
        "",
        "_Reported automatically by `scripts/report_install_issue.py`. Secrets, emails, user name and home path were redacted._",
    ])


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command capturing text output."""
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def existing_issue_url(title: str) -> str:
    """Return the URL of an open issue with the same title, or ''."""
    result = run(["gh", "issue", "list", "--repo", REPO, "--state", "open",
                  "--search", f'"{title}" in:title', "--json", "url,title", "--jq",
                  f'[.[] | select(.title == "{title}")][0].url // ""'])
    return result.stdout.strip() if result.returncode == 0 else ""


def submit(title: str, body: str) -> int:
    """Create the issue with gh, or print a pre-filled URL when gh cannot be used."""
    if shutil.which("gh") and run(["gh", "auth", "status"]).returncode == 0:
        duplicate = existing_issue_url(title)
        if duplicate:
            print(f"An open issue with this title already exists: {duplicate}")
            return 0
        run(["gh", "label", "create", LABEL, "--repo", REPO, "--color", "d73a4a",
             "--description", "Installation failure of the kit", "--force"])
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
            handle.write(body)
            body_file = handle.name
        try:
            result = run(["gh", "issue", "create", "--repo", REPO, "--title", title,
                          "--body-file", body_file, "--label", LABEL])
        finally:
            os.unlink(body_file)
        if result.returncode == 0:
            print(f"Issue created: {result.stdout.strip()}")
            return 0
        print(f"gh could not create the issue: {redact(result.stderr.strip())}", file=sys.stderr)
    query = urllib.parse.urlencode({"title": title, "body": body[:MAX_URL_BODY], "labels": LABEL})
    print("Open this link in your browser to file the issue (review it first):")
    print(f"https://github.com/{REPO}/issues/new?{query}")
    return 1


def main() -> int:
    """Parse arguments, print the redacted report and optionally submit it."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--step", required=True, help="what was being run when it failed")
    parser.add_argument("--log", help="file with the output of the failed command")
    parser.add_argument("--notes", default="", help="extra context")
    parser.add_argument("--submit", action="store_true", help="create the issue (only after the user approved the body)")
    args = parser.parse_args()

    title = f"Install failure: {redact(args.step)[:80]} on {platform.system()}"
    body = build_body(args.step, read_log_tail(args.log), args.notes)
    print(f"TITLE: {title}\n\n{body}\n")
    if not args.submit:
        print("Review the text above. Re-run with --submit to file it.")
        return 0
    return submit(title, body)


if __name__ == "__main__":
    sys.exit(main())
