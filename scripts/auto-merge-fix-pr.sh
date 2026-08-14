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

# Refuse to push/merge if this branch still has unresolved conflict markers
# (common when parallel portal agents all edited the shared ISSUES file).
bash "$ROOT/scripts/assert-no-conflict-markers.sh"

git fetch origin main >/dev/null 2>&1 || true

# Rebase onto latest main so same-day sibling portal PRs do not leave markers.
if ! git rebase origin/main; then
  echo "ERROR: rebase onto origin/main failed — resolve conflicts (prefer portal-scoped" >&2
  echo "  automation-prompts/issues/<portal>.md via scripts/append-issue-fix.sh)," >&2
  echo "  then: git add -A && git rebase --continue && bash scripts/auto-merge-fix-pr.sh" >&2
  git rebase --abort >/dev/null 2>&1 || true
  exit 6
fi
bash "$ROOT/scripts/assert-no-conflict-markers.sh"
git push -u origin HEAD --force-with-lease

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
- [ ] Same-day re-run via scripts/rerun-daily-after-fix.sh (do not wait for tomorrow's cron)

EOF
)"
  fi
  # Never open as draft — merge path requires ready PRs.
  PR_URL="$(gh pr create --base main --title "$TITLE" --body "$BODY")"
  echo "Created PR: $PR_URL"
else
  echo "Existing PR: $PR_URL"
fi

# Never leave draft — user wants automatic merge.
gh pr ready >/dev/null 2>&1 || true

# Prefer immediate squash merge. GitHub "auto-merge" queue is optional
# (this repo has enablePullRequestAutoMerge disabled).
set +e
gh pr merge --squash --delete-branch
merge_rc=$?
auto_rc=1
if [[ "$merge_rc" -ne 0 ]]; then
  gh pr merge --auto --squash --delete-branch
  auto_rc=$?
fi
set -e

STATE="$(gh pr view --json state,autoMergeRequest,mergeStateStatus -q '{state:.state,auto:.autoMergeRequest.enabledAt,mergeState:.mergeStateStatus}' 2>/dev/null || echo "{}")"
echo "PR merge status: $STATE"

# gh sometimes returns empty briefly after squash; always query by PR URL
# (branch may already be deleted by --delete-branch).
MERGED=""
for _try in 1 2 3 4 5; do
  MERGED="$(gh pr view "$PR_URL" --json state -q .state 2>/dev/null || true)"
  [[ "$MERGED" == "MERGED" || "$MERGED" == "OPEN" || "$MERGED" == "CLOSED" ]] && break
  sleep 1
done
if [[ "$MERGED" == "MERGED" ]]; then
  echo "OK: PR merged → $PR_URL"
  # Verify main tip did not land conflict markers (parallel squash race).
  git fetch origin main >/dev/null 2>&1 || true
  if git show origin/main:automation-prompts/ISSUES_AND_FIXES.md 2>/dev/null | grep -qE '^(<<<<<<< |>>>>>>> )'; then
    echo "WARNING: origin/main ISSUES_AND_FIXES.md still has conflict markers — run a cleanup PR." >&2
  fi
  echo "Same-day post-fix re-run: apply today's jobs with the merged code (do not wait for tomorrow's cron)."
  bash "$ROOT/scripts/rerun-daily-after-fix.sh" --merged-pr "$PR_URL" \
    || echo "WARNING: post-fix re-run failed (merge still OK) — re-run: bash scripts/rerun-daily-after-fix.sh --merged-pr $PR_URL"
  exit 0
fi

if [[ "$merge_rc" -ne 0 && "$auto_rc" -ne 0 ]]; then
  echo "WARNING: could not merge yet — resolve conflicts/checks, then re-run:"
  echo "  bash scripts/auto-merge-fix-pr.sh"
  exit 4
fi

echo "OK: PR merged or auto-merge enabled → $PR_URL"
exit 0
