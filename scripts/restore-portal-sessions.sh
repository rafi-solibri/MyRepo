#!/usr/bin/env bash
# Restore authenticated portal Chrome sessions seeded in .portal-sessions/
# into Desktop Default Chrome + per-portal CDP profiles.
#
# Why: Cloud Agent environment builds boot from a base disk that may lack
# Desktop logins. Saving environment *config* alone re-runs install on that
# empty base, so daily cron keeps hitting Sign-in walls. This seed is copied
# during install/start so the build's final snapshot retains the sessions.
#
# Safe to re-run. Never overwrites a destination that already has auth cookies
# unless FORCE_RESTORE_SESSIONS=1.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEED="${PORTAL_SESSION_SEED:-$ROOT/.portal-sessions}"
FORCE="${FORCE_RESTORE_SESSIONS:-0}"

if [[ ! -d "$SEED/source/Default" ]]; then
  echo "restore-portal-sessions: no seed at $SEED (skipping)"
  exit 0
fi

if [[ ! -f "$SEED/source/Default/Cookies" ]]; then
  echo "restore-portal-sessions: seed Cookies missing (skipping)"
  exit 0
fi

has_all_auth() {
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
# ALL required cookie names must be present (one marker per portal group is passed in).
raise SystemExit(0 if all(n in names for n in needed) else 1)
PY
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

restore_tree() {
  local src="$1" dest="$2"
  mkdir -p "$dest/Default"
  if [[ -f "$src/Local State" ]]; then
    cp -a "$src/Local State" "$dest/Local State"
  fi
  if [[ -f "$src/First Run" ]]; then
    cp -a "$src/First Run" "$dest/First Run"
  else
    touch "$dest/First Run"
  fi
  mkdir -p "$dest/Default"
  if [[ -f "$src/Default/Cookies" ]]; then
    cp -a "$src/Default/Cookies" "$dest/Default/Cookies"
  fi
  if [[ -f "$src/Default/Cookies-journal" ]]; then
    cp -a "$src/Default/Cookies-journal" "$dest/Default/Cookies-journal"
  fi
  if [[ -f "$src/Default/Preferences" ]]; then
    cp -a "$src/Default/Preferences" "$dest/Default/Preferences"
  fi
  # Drop stale singleton locks so Chrome can start.
  rm -f "$dest/SingletonLock" "$dest/SingletonCookie" "$dest/SingletonSocket" \
    "$dest/Default/lockfile" 2>/dev/null || true
}

SRC_DEST="${CHROME_SOURCE_PROFILE:-/home/ubuntu/.config/google-chrome}"
# One marker cookie per required portal. Default must have ALL of these or we
# re-seed from .portal-sessions (Cutshort-only disks used to skip restore).
REQUIRED_SOURCE_COOKIES=(
  li_at
  nauk_rt
  MSSOAT
  cutshort_authentication
  sessionid
  CTK
)

if [[ "$FORCE" == "1" ]] || ! has_all_auth "$SRC_DEST" "${REQUIRED_SOURCE_COOKIES[@]}"; then
  echo "restore-portal-sessions: seeding Desktop Default -> $SRC_DEST"
  restore_tree "$SEED/source" "$SRC_DEST"
else
  echo "restore-portal-sessions: Desktop Default already has all 6 portal auth cookies; leaving in place"
fi

declare -A PORTALS=(
  [linkedin]="${LINKEDIN_CHROME_PROFILE:-/home/ubuntu/chrome-cdp-profile}"
  [naukri]="${NAUKRI_CHROME_PROFILE:-/home/ubuntu/.naukri-chrome-profile}"
  [foundit]="${FOUNDIT_CHROME_PROFILE:-/home/ubuntu/.config/chrome-foundit}"
  [cutshort]="${CUTSHORT_CHROME_PROFILE:-/home/ubuntu/chrome-cutshort-profile}"
  [instahyre]="${INSTAHYRE_CHROME_PROFILE:-/home/ubuntu/chrome-instahyre-profile}"
  [indeed]="${INDEED_CHROME_PROFILE:-/home/ubuntu/chrome-indeed-profile}"
  [hirist]="${HIRIST_CHROME_PROFILE:-/home/ubuntu/chrome-hirist-profile}"
  [linkedin_alt]="${LINKEDIN_CHROME_PROFILE_ALT:-/home/ubuntu/chrome-linkedin-profile}"
)

declare -A NEED=(
  [linkedin]="li_at"
  [naukri]="nauk_rt nauk_at"
  [foundit]="MSSOAT"
  [cutshort]="cutshort_authentication"
  [instahyre]="sessionid"
  [indeed]="__Secure-PassportAuthProxy-BearerToken CTK"
  [hirist]="hirist_seeker_enc token"
  [linkedin_alt]="li_at"
)

for portal in linkedin naukri foundit cutshort instahyre indeed hirist linkedin_alt; do
  dest="${PORTALS[$portal]}"
  seed_dir="$SEED/cdp/$portal"
  [[ -d "$seed_dir/Default" ]] || seed_dir="$SEED/source"
  read -r -a cookies <<< "${NEED[$portal]}"
  if [[ "$FORCE" == "1" ]] || ! has_auth "$dest" "${cookies[@]}"; then
    echo "restore-portal-sessions: seeding $portal -> $dest"
    restore_tree "$seed_dir" "$dest"
  else
    echo "restore-portal-sessions: $portal already authenticated; leaving $dest"
  fi
done

echo "restore-portal-sessions: done"
if [[ -f "$SEED/manifest.json" ]]; then
  echo "restore-portal-sessions: seed manifest:"
  cat "$SEED/manifest.json"
fi
