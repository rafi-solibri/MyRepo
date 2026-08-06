#!/usr/bin/env bash
# Copy authenticated sessions from Desktop Chrome (Default) into each
# portal CDP profile. Cron agents launch non-default --user-data-dir
# (Default rejects DevTools); without this sync they boot empty and hit login walls.
set -euo pipefail

SRC_ROOT="${CHROME_SOURCE_PROFILE:-/home/ubuntu/.config/google-chrome}"
SRC_DEFAULT="$SRC_ROOT/Default"

if [[ ! -d "$SRC_DEFAULT" ]]; then
  echo "ERROR: source Chrome profile missing: $SRC_DEFAULT" >&2
  echo "Log into LinkedIn/Naukri/Foundit/Cutshort/Instahyre/Indeed in Desktop Chrome, then Save Environment snapshot." >&2
  exit 1
fi

if [[ ! -f "$SRC_DEFAULT/Cookies" ]]; then
  echo "ERROR: no Cookies DB in $SRC_DEFAULT" >&2
  exit 1
fi

# Portal CDP profiles (must stay non-default for --remote-debugging-port).
DESTS=(
  "${LINKEDIN_CHROME_PROFILE:-/home/ubuntu/chrome-cdp-profile}"
  "${NAUKRI_CHROME_PROFILE:-/home/ubuntu/.naukri-chrome-profile}"
  "${FOUNDIT_CHROME_PROFILE:-/home/ubuntu/.config/chrome-foundit}"
  "${CUTSHORT_CHROME_PROFILE:-/home/ubuntu/chrome-cutshort-profile}"
  "${INSTAHYRE_CHROME_PROFILE:-/home/ubuntu/chrome-instahyre-profile}"
  "${INDEED_CHROME_PROFILE:-/home/ubuntu/chrome-indeed-profile}"
  "${LINKEDIN_CHROME_PROFILE_ALT:-/home/ubuntu/chrome-linkedin-profile}"
)

copy_tree() {
  local src="$1" dest="$2"
  mkdir -p "$dest"
  # Prefer rsync; fall back to cp -a.
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude='SingletonLock' \
      --exclude='SingletonCookie' \
      --exclude='SingletonSocket' \
      --exclude='lockfile' \
      --exclude='RunningChromeVersion' \
      --exclude='.com.google.Chrome*' \
      --exclude='GpuCache' \
      --exclude='Code Cache' \
      --exclude='Cache' \
      --exclude='ShaderCache' \
      --exclude='BrowserMetrics*' \
      "$src/" "$dest/"
  else
    rm -rf "$dest"
    mkdir -p "$(dirname "$dest")"
    cp -a "$src" "$dest"
    rm -f "$dest/SingletonLock" "$dest/SingletonCookie" "$dest/SingletonSocket" \
      "$dest/lockfile" "$dest/RunningChromeVersion" 2>/dev/null || true
  fi
}

sync_one() {
  local dest_root="$1"
  mkdir -p "$dest_root/Default"
  if [[ -f "$SRC_ROOT/Local State" ]]; then
    cp -f "$SRC_ROOT/Local State" "$dest_root/Local State"
  fi
  copy_tree "$SRC_DEFAULT" "$dest_root/Default"
  # First-run marker so Chrome does not wipe the copied profile.
  touch "$dest_root/First Run" 2>/dev/null || true
  echo "synced -> $dest_root"
}

echo "Source: $SRC_DEFAULT"
for d in "${DESTS[@]}"; do
  sync_one "$d"
done

# Quick auth cookie presence check (best-effort; Chrome may lock DB).
python3 - <<'PY' || true
import os, shutil, sqlite3, tempfile
src = "/home/ubuntu/.config/google-chrome/Default/Cookies"
need = {
  "linkedin": "li_at",
  "naukri": "nauk_rt",
  "foundit": "MSSOAT",
  "cutshort": "cutshort_authentication",
  "instahyre": "sessionid",
  "indeed": "__Secure-PassportAuthProxy-BearerToken",
}
if not os.path.exists(src):
  print("cookie check: source Cookies missing")
  raise SystemExit(0)
tmp = tempfile.mktemp(suffix=".db")
shutil.copy2(src, tmp)
con = sqlite3.connect(tmp)
names = {r[0] for r in con.execute("SELECT name FROM cookies")}
con.close()
os.remove(tmp)
missing = [p for p, n in need.items() if n not in names]
present = [p for p, n in need.items() if n in names]
print("auth present:", ", ".join(present) if present else "(none)")
if missing:
  print("auth MISSING (login + Save Snapshot required):", ", ".join(missing))
else:
  print("all 6 portal auth cookies present in source Default profile")
PY

echo "Chrome session sync complete."
