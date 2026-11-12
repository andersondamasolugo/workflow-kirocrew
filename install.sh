#!/usr/bin/env bash
# Installs the Kiro GB Workflow kit into ~/.kiro.
# Usage: ./install.sh [--dry-run] [--force]
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIRO="${KIRO_HOME:-$HOME/.kiro}"
DRY=0; FORCE=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --force) FORCE=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

BACKUP="$KIRO/.gb-backup-$(date +%Y%m%d-%H%M%S)"
COPIED=0; SKIPPED=0

# copy_item <source> <destination>: copies a file or directory honoring --dry-run/--force.
copy_item() {
  local from="$1" to="$2"
  if [ -e "$to" ] && [ "$FORCE" -eq 0 ]; then
    echo "skip (exists): $to"; SKIPPED=$((SKIPPED + 1)); return
  fi
  if [ "$DRY" -eq 1 ]; then echo "would copy: $to"; COPIED=$((COPIED + 1)); return; fi
  if [ -e "$to" ]; then
    mkdir -p "$BACKUP/$(dirname "${to#$KIRO/}")"
    cp -R "$to" "$BACKUP/${to#$KIRO/}"
    rm -rf "$to"
  fi
  mkdir -p "$(dirname "$to")"
  cp -R "$from" "$to"
  COPIED=$((COPIED + 1))
}

for dir in "$SRC"/agents/*/; do
  name="$(basename "$dir")"
  if [ "$name" = "judgment-day" ]; then
    for f in "$dir"*.md; do copy_item "$f" "$KIRO/agents/$(basename "$f")"; done
    continue
  fi
  copy_item "$dir/agent.json" "$KIRO/agents/$name.json"
  copy_item "$dir/prompt.md" "$KIRO/crew/agents/$name/prompt.md"
done

COLLAB_SKILLS=" chained-pr cognitive-doc-design comment-writer judgment-day rdd-defect-workflow skill-creator skill-improver systemic-issue-triage work-unit-commits "
for dir in "$SRC"/skills/*/; do
  name="$(basename "$dir")"
  if [ "$name" = "learnings" ]; then
    for l in "$dir"*/; do copy_item "$l" "$KIRO/crew/skills/auto/$(basename "$l")"; done
  elif [[ "$COLLAB_SKILLS" == *" $name "* ]]; then
    copy_item "$dir" "$KIRO/skills/$name"
  else
    copy_item "$dir" "$KIRO/crew/skills/$name"
  fi
done

copy_item "$SRC/steering/dev-flows" "$KIRO/steering/dev-flows"
copy_item "$SRC/steering/dev-flow-router.md" "$KIRO/steering/dev-flow-router.md"
for part in scripts templates workflows; do
  copy_item "$SRC/dev-flows/$part" "$KIRO/crew/dev-flows/$part"
done

echo "Done. copied=$COPIED skipped=$SKIPPED dry_run=$DRY"
[ "$SKIPPED" -gt 0 ] && echo "Use --force to overwrite (backup goes to $BACKUP)."
echo "Next: configure your local secrets, see docs/05-onboarding.md"
exit 0
