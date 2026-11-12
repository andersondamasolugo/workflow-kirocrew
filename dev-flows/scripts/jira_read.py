#!/usr/bin/env python3
"""Read Jira Cloud issues through the REST API (cross-platform, no MCP needed).

Configuration (nothing is stored in the repo):
  JIRA_SITE   site host, e.g. mycompany.atlassian.net
  JIRA_EMAIL  your Atlassian account email
  JIRA_API_TOKEN, or the macOS Keychain / Linux Secret Service entry 'jira-api-token'

Usage:
    python3 jira_read.py GD929-1234
    python3 jira_read.py --jql "parent = GD929-1000 ORDER BY key"
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request

from read_secret import read_secret

ISSUE_FIELDS = "summary,status,description,issuelinks"
SEARCH_FIELDS = "summary,status,issuetype"
BLOCK_NODES = {"paragraph", "listItem", "heading", "codeBlock"}


def flatten_adf(node: object) -> str:
    """Flatten an Atlassian Document Format node into plain text."""
    if isinstance(node, dict):
        text = node.get("text", "")
        children = "".join(flatten_adf(child) for child in node.get("content", []))
        suffix = "\n" if node.get("type") in BLOCK_NODES else ""
        return f"{text}{children}{suffix}"
    if isinstance(node, list):
        return "".join(flatten_adf(item) for item in node)
    return ""


def api_get(site: str, auth: str, path: str, params: dict | None = None) -> dict:
    """GET a Jira Cloud REST v3 path and return the decoded JSON."""
    url = f"https://{site}/rest/api/3/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def print_issue(issue: dict) -> None:
    """Print key, summary, status and flattened description of one issue."""
    fields = issue["fields"]
    print(f"{issue['key']} [{fields['status']['name']}] {fields['summary']}")
    description = flatten_adf(fields.get("description")).strip()
    if description:
        print(description)


def main() -> int:
    """Validate credentials, then fetch the requested issue or JQL results."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("key", nargs="?", help="issue key, e.g. GD929-1234")
    parser.add_argument("--jql", help="JQL search instead of a single issue")
    args = parser.parse_args()
    site, email = os.environ.get("JIRA_SITE", ""), os.environ.get("JIRA_EMAIL", "")
    token = read_secret("jira-api-token", "JIRA_API_TOKEN")
    if not (site and email and token) or not (args.key or args.jql):
        print("Set JIRA_SITE, JIRA_EMAIL and JIRA_API_TOKEN, and pass an issue key or --jql.", file=sys.stderr)
        return 2
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    api_get(site, auth, "myself")
    if args.jql:
        result = api_get(site, auth, "search/jql", {"jql": args.jql, "fields": SEARCH_FIELDS, "maxResults": 50})
        for issue in result.get("issues", []):
            print(f"{issue['key']} [{issue['fields']['status']['name']}] {issue['fields']['summary']}")
        return 0
    print_issue(api_get(site, auth, f"issue/{args.key}", {"fields": ISSUE_FIELDS}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
