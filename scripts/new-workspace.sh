#!/usr/bin/env bash
# Creates (or completes) a Kiro Crew workspace folder for the project repositories.
# Usage: scripts/new-workspace.sh <workspace-path> [--clone] [--dry-run] [--force]
#   --clone    git clone every repository listed in <workspace>/repos.txt that is not there yet
#   --dry-run  print what would be done
#   --force    regenerate the steering and .code-workspace files (repos.txt is never overwritten)
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$SRC/workspace-template"
TARGET=""; CLONE=0; DRY=0; FORCE=0
for arg in "$@"; do
  case "$arg" in
    --clone) CLONE=1 ;;
    --dry-run) DRY=1 ;;
    --force) FORCE=1 ;;
    -*) echo "Unknown option: $arg" >&2; exit 2 ;;
    *) TARGET="$arg" ;;
  esac
done
[ -n "$TARGET" ] || { echo "Usage: $0 <workspace-path> [--clone] [--dry-run] [--force]" >&2; exit 2; }
TARGET="${TARGET/#\~/$HOME}"
NAME="$(basename "$TARGET")"

# run <description> <command...>: executes the command unless --dry-run.
run() {
  local description="$1"; shift
  if [ "$DRY" -eq 1 ]; then echo "would: $description"; else "$@"; fi
}

# write_if_absent <path> <content>: writes the file when missing or --force is set.
write_if_absent() {
  local path="$1" content="$2"
  if [ -e "$path" ] && [ "$FORCE" -eq 0 ]; then echo "skip (exists): $path"; return; fi
  if [ "$DRY" -eq 1 ]; then echo "would write: $path"; return; fi
  printf '%s\n' "$content" > "$path"
  echo "wrote: $path"
}

# repo_folders <repos-file>: prints the folder name of each listed repository.
repo_folders() {
  local url folder
  while read -r url folder _; do
    case "$url" in ''|\#*) continue ;; esac
    folder="${folder:-$(basename "${url%.git}")}"
    echo "$folder"
  done < "$1"
}

# build_code_workspace <repos-file>: prints a .code-workspace JSON listing the workspace and its repos.
build_code_workspace() {
  local folder
  printf '{\n  "folders": [\n    { "path": ".", "name": "%s (root)" }' "$NAME"
  while read -r folder; do
    printf ',\n    { "path": "%s" }' "$folder"
  done < <(repo_folders "$1")
  printf '\n  ]\n}'
}

run "create $TARGET/.kiro/steering" mkdir -p "$TARGET/.kiro/steering"
# repos.txt is user data: never overwritten, not even with --force.
if [ ! -e "$TARGET/repos.txt" ]; then write_if_absent "$TARGET/repos.txt" "$(cat "$TEMPLATE/repos.txt")"; else echo "keep: $TARGET/repos.txt"; fi
STEERING="$(sed "s/__WORKSPACE_NAME__/$NAME/g" "$TEMPLATE/.kiro/steering/gb-workspace.md")"
write_if_absent "$TARGET/.kiro/steering/gb-workspace.md" "$STEERING"

if [ "$DRY" -eq 0 ]; then
  write_if_absent "$TARGET/$NAME.code-workspace" "$(build_code_workspace "$TARGET/repos.txt")"
fi

REPOS="$TARGET/repos.txt"
[ -e "$REPOS" ] || REPOS="$TEMPLATE/repos.txt"

if [ "$CLONE" -eq 1 ]; then
  while read -r url folder _; do
    case "$url" in ''|\#*) continue ;; esac
    folder="${folder:-$(basename "${url%.git}")}"
    if [ -e "$TARGET/$folder" ]; then echo "skip (exists): $folder"; continue; fi
    run "git clone $url $TARGET/$folder" git clone "$url" "$TARGET/$folder"
  done < "$REPOS"
fi

echo "Workspace ready: $TARGET"
echo "Next: open a Kiro Crew chat with this folder as its project directory (see docs/07-workspace.md)."
