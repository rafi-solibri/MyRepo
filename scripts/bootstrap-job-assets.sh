#!/usr/bin/env bash
# Ensure Rafi_Resume.docx is available at every path job-apply agents historically search.
# Owner source of truth: resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx
# Upload copy is ALWAYS rebuilt from that master (never reuse a stale Rafi_Resume.docx).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWNER_SRC="$ROOT/resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx"
SRC="$ROOT/resumes/Rafi_Resume.docx"

if [[ ! -f "$OWNER_SRC" ]]; then
  echo "ERROR: missing owner master resume $OWNER_SRC" >&2
  exit 1
fi

PY="$(bash "$ROOT/scripts/resolve-python.sh" 2>/dev/null || echo python3)"
if [[ "$PY" == "py" ]]; then
  py -3 "$ROOT/tools/ensure_upload_resume.py"
else
  "$PY" "$ROOT/tools/ensure_upload_resume.py"
fi

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: missing upload resume $SRC after ensure_upload_resume" >&2
  exit 1
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

echo "Resume ready (rebuilt from Mohammed_Abdul_Rafi_Ahmed_Resume.docx):"
ls -la "$OWNER_SRC" "$SRC" /home/ubuntu/resumes/Rafi_Resume.docx /home/ubuntu/Documents/Rafi_Resume.docx 2>/dev/null || true

# JD tailor dependency (best-effort; tailor also self-installs if missing)
if command -v python3 >/dev/null 2>&1; then
  python3 -c "import docx" 2>/dev/null || python3 -m pip install -q -r "$ROOT/tools/requirements-resume.txt" >/dev/null 2>&1 || true
fi
