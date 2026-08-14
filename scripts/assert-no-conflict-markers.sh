#!/usr/bin/env bash
# Fail if any tracked (or given) files contain unresolved git conflict markers.
# Usage:
#   bash scripts/assert-no-conflict-markers.sh
#   bash scripts/assert-no-conflict-markers.sh path1 path2
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGETS=("$@")
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  # Default: docs + scripts that agents frequently touch during parallel merges
  mapfile -t TARGETS < <(
    git ls-files 'automation-prompts/**' 'scripts/**' 'tools/**' 'reports/**' 2>/dev/null \
      | grep -E '\.(md|sh|js|mjs|py|json|yml|yaml)$' || true
  )
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "assert-no-conflict-markers: no files to scan"
  exit 0
fi

bad=0
for f in "${TARGETS[@]}"; do
  [[ -f "$f" ]] || continue
  if grep -nE '^(<<<<<<< |>>>>>>> |=======$)' "$f" >/tmp/conflict-markers.$$.txt 2>/dev/null; then
    echo "CONFLICT MARKERS in $f:" >&2
    sed "s|^|$f:|" /tmp/conflict-markers.$$.txt >&2 || true
    bad=1
  fi
done
rm -f /tmp/conflict-markers.$$.txt

if [[ "$bad" -ne 0 ]]; then
  echo "ERROR: unresolved conflict markers present — refuse to merge/push until cleaned." >&2
  echo "Hint: prefer portal logs via scripts/append-issue-fix.sh (never shared ISSUES_AND_FIXES.md)." >&2
  exit 5
fi

echo "OK: no conflict markers"
exit 0
