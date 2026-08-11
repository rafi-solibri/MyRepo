#!/usr/bin/env bash
# Create (if needed) a ready PR for the current branch and merge it into main.
# Usage:
#   bash scripts/auto-merge-fix-pr.sh
#   bash scripts/auto-merge-fix-pr.sh --title "fix(portal): …" --body "…"
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TITLE=""
BODY=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --title) TITLE="${2:-}"; shift 2 ;;
    --body) BODY="${2:-}"; shift 2 ;;
    --help|-h)
      echo "Usage: bash scripts/auto-merge-fix-pr.sh [--title T] [--body B]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" == "main" || "$BRANCH" == "master" || "$BRANCH" == "HEAD" ]]; then
  echo "ERROR: refuse to auto-merge from $BRANCH — use a feature branch"
  exit 3
fi

git fetch origin main >/dev/null 2>&1 || true
git push -u origin HEAD

PR_URL="$(gh pr view --json url -q .url 2>/dev/null || true)"
if [[ -z "$PR_URL" ]]; then
  if [[ -z "$TITLE" ]]; then
    TITLE="$(git log -1 --pretty=%s)"
  fi
  if [[ -z "$BODY" ]]; then
    BODY="$(cat <<EOF
## Summary
- Auto-opened by home/cloud daily runner after a code-fixable blocker fix.

## Test plan
- [ ] Relevant portal preflight / unit smoke
- [ ] Re-run durable apply helper when safe

EOF
)"
  fi
  PR_URL="$(gh pr create --base main --title "$TITLE" --body "$BODY")"
  echo "Created PR: $PR_URL"
else
  echo "Existing PR: $PR_URL"
fi

# Never leave draft — user wants automatic merge.
gh pr ready >/dev/null 2>&1 || true

# Prefer squash. Try enable auto-merge first, then immediate merge if allowed.
set +e
gh pr merge --auto --squash --delete-branch
auto_rc=$?
if [[ "$auto_rc" -ne 0 ]]; then
  gh pr merge --squash --delete-branch
  merge_rc=$?
else
  merge_rc=0
fi
set -e

STATE="$(gh pr view --json state,autoMergeRequest,mergeStateStatus -q '{state:.state,auto:.autoMergeRequest.enabledAt,mergeState:.mergeStateStatus}' 2>/dev/null || echo "{}")"
echo "PR merge status: $STATE"

if [[ "$merge_rc" -ne 0 && "$auto_rc" -ne 0 ]]; then
  echo "WARNING: could not merge yet — resolve conflicts/checks, then re-run:"
  echo "  bash scripts/auto-merge-fix-pr.sh"
  exit 4
fi

echo "OK: PR merged or auto-merge enabled → $PR_URL"
exit 0
