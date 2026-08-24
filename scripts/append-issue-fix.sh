#!/usr/bin/env bash
# Append one issue/fix row to the portal-scoped log (never the shared ISSUES file).
# Usage:
#   bash scripts/append-issue-fix.sh <portal> "<issue>" "<fix>"
#   bash scripts/append-issue-fix.sh naukri "chat Save no-op" "force Save + stuck detection"
#
# Why: parallel cloud/home portal agents previously all edited
# automation-prompts/ISSUES_AND_FIXES.md and left conflict markers on main.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORTAL="$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
ISSUE="${2:-}"
FIX="${3:-}"
SOURCE="${ISSUE_FIX_SOURCE:-}"
TODAY="${ISSUE_FIX_DATE:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"

VALID=(linkedin foundit cutshort naukri instahyre indeed hirist hitechcity notification hotels)
ok=0
for p in "${VALID[@]}"; do
  [[ "$p" == "$PORTAL" ]] && ok=1 && break
done
if [[ "$ok" -ne 1 || -z "$ISSUE" || -z "$FIX" ]]; then
  echo "Usage: bash scripts/append-issue-fix.sh <portal> \"<issue>\" \"<fix>\"" >&2
  echo "Portals: ${VALID[*]}" >&2
  exit 2
fi

if [[ -z "$SOURCE" ]]; then
  if [[ "${HOME_LOCAL:-}" == "1" || "${CHROME_CDP_MODE:-}" == "system" ]]; then
    SOURCE="home"
  else
    SOURCE="cloud"
  fi
fi

DIR="$ROOT/automation-prompts/issues"
FILE="$DIR/${PORTAL}.md"
mkdir -p "$DIR"

if [[ ! -f "$FILE" ]]; then
  title="$PORTAL"
  cat >"$FILE" <<EOF
# ${title} — issues & fixes

Portal-scoped log. Append via \`bash scripts/append-issue-fix.sh ${PORTAL} "issue" "fix"\`.

EOF
fi

# Escape pipes so markdown tables stay intact
esc() { printf '%s' "$1" | sed 's/|/\\|/g'; }
ISSUE_E="$(esc "$ISSUE")"
FIX_E="$(esc "$FIX")"
HEAD="## ${TODAY} (${SOURCE})"

python3 - "$FILE" "$HEAD" "$ISSUE_E" "$FIX_E" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
head = sys.argv[2]
issue = sys.argv[3]
fix = sys.argv[4]
text = path.read_text(encoding="utf-8")
row = f"| {issue} | {fix} |"
table_hdr = "| Issue | Fix |\n| --- | --- |"

if head in text:
    # Insert row after the header under this section
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    inserted = False
    while i < len(lines):
        out.append(lines[i])
        if not inserted and lines[i].rstrip("\n") == head:
            # consume blank + table header if present
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                out.append(lines[j]); j += 1
            if j < len(lines) and lines[j].startswith("| Issue |"):
                out.append(lines[j]); j += 1
                if j < len(lines) and lines[j].startswith("| ---"):
                    out.append(lines[j]); j += 1
                out.append(row + "\n")
                inserted = True
                i = j
                continue
            else:
                out.append("\n")
                out.append(table_hdr + "\n")
                out.append(row + "\n")
                inserted = True
                i = j
                continue
        i += 1
    if not inserted:
        text = text.rstrip() + f"\n\n{head}\n\n{table_hdr}\n{row}\n"
        path.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")
    else:
        path.write_text("".join(out), encoding="utf-8")
else:
    # Prepend today's section after the title block (after first blank line following H1)
    lines = text.splitlines()
    insert_at = 0
    for idx, ln in enumerate(lines):
        if ln.startswith("# "):
            insert_at = idx + 1
            break
    while insert_at < len(lines) and lines[insert_at].strip() != "":
        # skip intro paragraph(s)
        insert_at += 1
        if insert_at < len(lines) and lines[insert_at].strip() == "":
            break
    block = ["", head, "", *table_hdr.split("\n"), row, ""]
    new_lines = lines[:insert_at] + block + lines[insert_at:]
    path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")

print(path)
PY

echo "Appended to automation-prompts/issues/${PORTAL}.md"
