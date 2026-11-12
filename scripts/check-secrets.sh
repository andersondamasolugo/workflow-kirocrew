#!/usr/bin/env bash
# Fails if the repo contains likely secrets, personal emails or user-specific absolute paths.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

FOUND=0
check() {
  local label="$1" pattern="$2"
  local hits
  hits="$(grep -rInE "$pattern" . --exclude-dir=.git --exclude=check-secrets.sh || true)"
  if [ -n "$hits" ]; then echo "== $label"; echo "$hits" | cut -c1-200; FOUND=1; fi
}

check "Token-like values" '(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[bp]-[A-Za-z0-9-]{10,}|squ_[a-f0-9]{20,}|sq[ap]_[a-f0-9]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,})'
check "Private keys" 'BEGIN [A-Z ]*PRIVATE KEY'
check "Hardcoded credentials" '(password|passwd|api[_-]?key|secret)["'"'"' ]*[:=]["'"'"' ]*[A-Za-z0-9/+_-]{10,}'
check "User absolute paths" '/Users/[a-z0-9._-]+/|C:\\Users\\'
check "Personal emails" '[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+@segurosbolivar\.com'

if [ "$FOUND" -eq 0 ]; then echo "check-secrets: OK"; else echo "check-secrets: REVIEW the findings above"; fi
exit "$FOUND"
