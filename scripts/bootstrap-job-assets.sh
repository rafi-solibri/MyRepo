#!/usr/bin/env bash
# Ensure Rafi_Resume_Technical_Architect.docx is available at every path
# job-apply agents historically search. Legacy filenames are same-file aliases.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/resumes/Rafi_Resume_Technical_Architect.docx"

if [[ ! -f "$SRC" ]]; then
  # Fallback if only a legacy name exists in repo
  if [[ -f "$ROOT/resumes/Rafi_Resume.docx" ]]; then
    cp -f "$ROOT/resumes/Rafi_Resume.docx" "$SRC"
  else
    echo "ERROR: missing $SRC" >&2
    exit 1
  fi
fi

copy_one() {
  local dest="$1"
  mkdir -p "$(dirname "$dest")" 2>/dev/null || return 0
  if [[ ! -d "$(dirname "$dest")" || ! -w "$(dirname "$dest")" ]]; then
    return 0
  fi
  if [[ -e "$dest" ]] && [[ "$(realpath "$dest" 2>/dev/null || echo x)" == "$(realpath "$SRC")" ]]; then
    return 0
  fi
  cp -f "$SRC" "$dest"
}

for d in \
  "$ROOT/resumes" \
  "/home/ubuntu/resumes" \
  "/home/ubuntu/Documents" \
  "/home/ubuntu/Downloads" \
  "/opt/cursor/artifacts"
do
  copy_one "$d/Rafi_Resume_Technical_Architect.docx"
  copy_one "$d/Rafi_Resume.docx"
  copy_one "$d/Rafi_Resume_Architect.docx"
done

echo "Resume ready:"
ls -la "$SRC" \
  /home/ubuntu/resumes/Rafi_Resume_Technical_Architect.docx \
  /home/ubuntu/Documents/Rafi_Resume_Technical_Architect.docx \
  2>/dev/null || true
