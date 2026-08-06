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

STRICT=0
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=1
fi

# Portal CDP profiles (must stay non-default for --remote-debugging-port).
# Keep cookie names in sync with tools/chrome_session.js.
PORTALS=(linkedin naukri foundit cutshort instahyre indeed linkedin_alt)
DESTS=(
  "${LINKEDIN_CHROME_PROFILE:-/home/ubuntu/chrome-cdp-profile}"
  "${NAUKRI_CHROME_PROFILE:-/home/ubuntu/.naukri-chrome-profile}"
  "${FOUNDIT_CHROME_PROFILE:-/home/ubuntu/.config/chrome-foundit}"
  "${CUTSHORT_CHROME_PROFILE:-/home/ubuntu/chrome-cutshort-profile}"
  "${INSTAHYRE_CHROME_PROFILE:-/home/ubuntu/chrome-instahyre-profile}"
  "${INDEED_CHROME_PROFILE:-/home/ubuntu/chrome-indeed-profile}"
  "${LINKEDIN_CHROME_PROFILE_ALT:-/home/ubuntu/chrome-linkedin-profile}"
)
COOKIE_SETS=(
  "li_at"
  "nauk_rt nauk_at"
  "MSSOAT"
  "cutshort_authentication"
  "sessionid"
  "__Secure-PassportAuthProxy-BearerToken CTK"
  "li_at"
)
# linkedin_alt is a compatibility profile; do not fail strict mode solely for it.
REQUIRED=(1 1 1 1 1 1 0)

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
  local portal="$1" dest_root="$2"
  shift 2
  mkdir -p "$dest_root/Default"
  if [[ -f "$SRC_ROOT/Local State" ]]; then
    cp -f "$SRC_ROOT/Local State" "$dest_root/Local State"
  fi
  copy_tree "$SRC_DEFAULT" "$dest_root/Default"
  # First-run marker so Chrome does not wipe the copied profile.
  touch "$dest_root/First Run" 2>/dev/null || true
  echo "synced $portal -> $dest_root"
}

has_auth() {
  local profile_root="$1"
  shift
  python3 - "$profile_root" "$@" <<'PY'
import os, shutil, sqlite3, sys, tempfile

profile_root, *needed = sys.argv[1:]
db = os.path.join(profile_root, "Default", "Cookies")
if not os.path.exists(db):
    raise SystemExit(1)

tmp = tempfile.mktemp(suffix=".db")
try:
    shutil.copy2(db, tmp)
    con = sqlite3.connect(tmp)
    names = {r[0] for r in con.execute("SELECT name FROM cookies")}
    con.close()
finally:
    try:
        os.remove(tmp)
    except OSError:
        pass

raise SystemExit(0 if any(n in names for n in needed) else 1)
PY
}

echo "Source: $SRC_DEFAULT"
missing_required=0
for i in "${!PORTALS[@]}"; do
  portal="${PORTALS[$i]}"
  dest="${DESTS[$i]}"
  read -r -a cookies <<< "${COOKIE_SETS[$i]}"

  if has_auth "$SRC_ROOT" "${cookies[@]}"; then
    sync_one "$portal" "$dest" "${cookies[@]}"
    continue
  fi

  if has_auth "$dest" "${cookies[@]}"; then
    echo "skipped $portal -> source lacks auth; preserved existing authenticated profile at $dest"
    continue
  fi

  echo "MISSING $portal auth in source and destination profile: $dest" >&2
  if [[ "${REQUIRED[$i]}" == "1" ]]; then
    missing_required=$((missing_required + 1))
  fi
done

node tools/chrome_session.js status || true

echo "Chrome session sync complete."
if [[ "$STRICT" == "1" && "$missing_required" -gt 0 ]]; then
  echo "ERROR: $missing_required required portal profile(s) still lack auth." >&2
  exit 3
fi
