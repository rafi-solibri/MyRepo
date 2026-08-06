#!/usr/bin/env bash
# Ensure Rafi_Resume.docx is available at every path job-apply agents historically search.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/resumes/Rafi_Resume.docx"

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: missing $SRC" >&2
  exit 1
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
  copy_one "$d/Rafi_Resume.docx"
  copy_one "$d/Rafi_Resume_Architect.docx"
done

echo "Resume ready:"
ls -la "$SRC" /home/ubuntu/resumes/Rafi_Resume.docx /home/ubuntu/Documents/Rafi_Resume.docx 2>/dev/null || true
