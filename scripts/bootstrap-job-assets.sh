#!/usr/bin/env bash
# Ensure Rafi_Resume.docx is available at every path job-apply agents historically search.
# Owner source: resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx (copied into Rafi_Resume.docx).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWNER_SRC="$ROOT/resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx"
SRC="$ROOT/resumes/Rafi_Resume.docx"

# Prefer owner-named file when present so drops of a new master resume propagate.
if [[ -f "$OWNER_SRC" ]]; then
  if [[ ! -f "$SRC" ]] || ! cmp -s "$OWNER_SRC" "$SRC"; then
    cp -f "$OWNER_SRC" "$SRC"
  fi
fi

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: missing $SRC (and no $OWNER_SRC)" >&2
  exit 1
fi

# Naukri (and some ATS) reject >2MB client-side. Master embeds large fonts —
# strip embeds into the upload copy; leave OWNER_SRC untouched.
PY="$(bash "$ROOT/scripts/resolve-python.sh" 2>/dev/null || echo python3)"
if [[ "$PY" == "py" ]]; then
  py -3 "$ROOT/tools/compress_resume_docx.py" "$SRC" || true
else
  "$PY" "$ROOT/tools/compress_resume_docx.py" "$SRC" || true
fi
if [[ "$(wc -c <"$SRC")" -gt 2097152 ]]; then
  echo "ERROR: $SRC is still >2MB after compress; Naukri profile upload will silently fail" >&2
  ls -la "$SRC" "$OWNER_SRC" 2>/dev/null || true
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

# JD tailor dependency (best-effort; tailor also self-installs if missing)
if command -v python3 >/dev/null 2>&1; then
  python3 -c "import docx" 2>/dev/null || python3 -m pip install -q -r "$ROOT/tools/requirements-resume.txt" >/dev/null 2>&1 || true
fi
