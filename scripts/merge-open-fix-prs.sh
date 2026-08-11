#!/usr/bin/env bash
# Merge any open ready fix PRs into main (safety net after a portal/home run).
# Usage:
#   bash scripts/merge-open-fix-prs.sh
#   bash scripts/merge-open-fix-prs.sh --author "@me"
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

AUTHOR_FILTER=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --author) AUTHOR_FILTER=(--author "$2"); shift 2 ;;
    --help|-h)
      echo "Usage: bash scripts/merge-open-fix-prs.sh [--author @me]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "WARNING: gh not found — skip open-PR sweep"
  exit 0
fi

git fetch origin main >/dev/null 2>&1 || true

# Prefer our fix/* / cursor/* branches with fix( titles; also catch AUTO_FIX PRs.
PRS_JSON="$(
  gh pr list --base main --state open --limit 50 \
    "${AUTHOR_FILTER[@]}" \
    --json number,title,isDraft,headRefName,url \
    --jq '.[] | select(
        (.title | test("(?i)^fix\\("))
        or (.headRefName | test("(?i)fix|auto-fix|home-"))
      ) | "\(.number)\t\(.isDraft)\t\(.title)\t\(.url)"' 2>/dev/null || true
)"

if [[ -z "${PRS_JSON//[[:space:]]/}" ]]; then
  echo "No open fix PRs to merge"
  exit 0
fi

failed=0
while IFS= read -r row; do
  [[ -z "$row" ]] && continue
  num="${row%%$'\t'*}"
  rest="${row#*$'\t'}"
  is_draft="${rest%%$'\t'*}"
  title_url="${rest#*$'\t'}"
  echo "Sweeping PR #$num ($title_url)"
  if [[ "$is_draft" == "true" ]]; then
    gh pr ready "$num" >/dev/null 2>&1 || true
  fi
  set +e
  gh pr merge "$num" --squash --delete-branch
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    gh pr merge "$num" --auto --squash --delete-branch
    rc=$?
  fi
  set -e
  if [[ "$rc" -ne 0 ]]; then
    echo "WARNING: could not merge PR #$num yet"
    failed=1
  else
    echo "Merged PR #$num"
  fi
done <<< "$PRS_JSON"

exit "$failed"
