#!/usr/bin/env bash
# Print a working Python interpreter path (avoid Windows Store python3 stub).
set -euo pipefail
if [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN}" ]]; then
  echo "$PYTHON_BIN"
  exit 0
fi
for cand in \
  /c/Python314/python.exe \
  /c/Python313/python.exe \
  /c/Python312/python.exe \
  "$LOCALAPPDATA/Programs/Python/Python314/python.exe" \
  "$LOCALAPPDATA/Programs/Python/Python313/python.exe"; do
  if [[ -n "$cand" && -x "$cand" ]]; then
    echo "$cand"
    exit 0
  fi
done
if command -v py >/dev/null 2>&1; then
  # `py -3` wrapper: callers that need args should detect py separately.
  echo "py"
  exit 0
fi
# Prefer real python over WindowsApps stub.
for cand in python python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    resolved="$(command -v "$cand")"
    case "$resolved" in
      *WindowsApps*) continue ;;
    esac
    echo "$resolved"
    exit 0
  fi
done
echo "python3"
