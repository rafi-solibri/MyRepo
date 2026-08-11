#!/usr/bin/env bash
# Copy authenticated sessions from Desktop Chrome (Default) into each
# portal CDP profile. Cron agents launch non-default --user-data-dir
# (Default rejects DevTools); without this sync they boot empty and hit login walls.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Prefer real Python on Windows (Store python3 stub is broken).
PYTHON_ARGS=()
if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x /c/Python314/python.exe ]]; then
  PYTHON_BIN="/c/Python314/python.exe"
elif [[ -x /c/Python313/python.exe ]]; then
  PYTHON_BIN="/c/Python313/python.exe"
elif command -v py >/dev/null 2>&1; then
  PYTHON_BIN="py"
  PYTHON_ARGS=(-3)
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  PYTHON_BIN="python"
fi
export PYTHON_BIN

SRC_ROOT="${CHROME_SOURCE_PROFILE:-$(node tools/chrome_session.js path source)}"
SRC_DEFAULT="$SRC_ROOT/Default"

if [[ ! -d "$SRC_DEFAULT" ]]; then
  echo "ERROR: source Chrome profile missing: $SRC_DEFAULT" >&2
  echo "Log into LinkedIn/Naukri/Foundit/Cutshort/Instahyre/Indeed in Desktop Chrome, then Save Environment snapshot." >&2
  exit 1
fi

# Chrome 120+ on Windows stores cookies under Default/Network/Cookies.
SRC_COOKIES=""
for cand in "$SRC_DEFAULT/Network/Cookies" "$SRC_DEFAULT/Cookies"; do
  if [[ -f "$cand" ]]; then
    SRC_COOKIES="$cand"
    break
  fi
done
if [[ -z "$SRC_COOKIES" ]]; then
  echo "ERROR: no Cookies DB in $SRC_DEFAULT (checked Network/Cookies and Cookies)" >&2
  exit 1
fi

# Preflight sync runs before launching the portal browser. If a previous runner
# crashed, a stale CDP Chrome can still hold a destination profile open and race
# the copy below.
pkill -f "remote-debugging-port=9222" 2>/dev/null || true

STRICT=0
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=1
fi

# Portal CDP profiles (must stay non-default for --remote-debugging-port).
# Keep cookie names in sync with tools/chrome_session.js.
PORTALS=(linkedin naukri foundit cutshort instahyre indeed linkedin_alt)
DESTS=(
  "${LINKEDIN_CHROME_PROFILE:-$(node tools/chrome_session.js path linkedin)}"
  "${NAUKRI_CHROME_PROFILE:-$(node tools/chrome_session.js path naukri)}"
  "${FOUNDIT_CHROME_PROFILE:-$(node tools/chrome_session.js path foundit)}"
  "${CUTSHORT_CHROME_PROFILE:-$(node tools/chrome_session.js path cutshort)}"
  "${INSTAHYRE_CHROME_PROFILE:-$(node tools/chrome_session.js path instahyre)}"
  "${INDEED_CHROME_PROFILE:-$(node tools/chrome_session.js path indeed)}"
  "${LINKEDIN_CHROME_PROFILE_ALT:-${HOME}/.cursor/chrome-cdp-profiles/linkedin-alt}"
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
  # Prefer rsync with heavy cache excludes.
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
    return 0
  elif [[ "${OS:-}" != "Windows_NT" && -z "${MSYSTEM:-}" ]]; then
    mkdir -p "$dest"
    cp -a "$src/." "$dest/"
    rm -f "$dest/SingletonLock" "$dest/SingletonCookie" "$dest/SingletonSocket" \
      "$dest/lockfile" "$dest/RunningChromeVersion" 2>/dev/null || true
    return 0
  fi

  # Windows/Git Bash: full `cp -a` of Default is multi-GB and hangs home runs.
  # Copy only auth/session essentials (cookies + storage + prefs).
  mkdir -p "$dest/Network" "$dest/Local Storage" "$dest/Session Storage" \
    "$dest/IndexedDB" "$dest/Service Worker"
  local rel
  for rel in \
    "Preferences" \
    "Secure Preferences" \
    "Login Data" \
    "Login Data-journal" \
    "Web Data" \
    "Web Data-journal" \
    "Cookies" \
    "Cookies-journal" \
    "Network/Cookies" \
    "Network/Cookies-journal" \
    "Network/Network Persistent State" \
    "Network/TransportSecurity" \
    "Local State"; do
    if [[ -e "$src/$rel" ]]; then
      mkdir -p "$(dirname "$dest/$rel")"
      cp -a "$src/$rel" "$dest/$rel" 2>/dev/null || true
    fi
  done
  for rel in "Local Storage" "Session Storage" "IndexedDB"; do
    if [[ -d "$src/$rel" ]]; then
      rm -rf "$dest/$rel"
      cp -a "$src/$rel" "$dest/$rel" 2>/dev/null || true
    fi
  done
  # Extension-less cookies are enough for portal auth; drop singleton locks.
  rm -f "$dest/SingletonLock" "$dest/SingletonCookie" "$dest/SingletonSocket" \
    "$dest/lockfile" "$dest/RunningChromeVersion" 2>/dev/null || true
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
  "$PYTHON_BIN" "${PYTHON_ARGS[@]}" - "$profile_root" "$@" <<'PY'
import os, shutil, sqlite3, sys, tempfile

profile_root, *needed = sys.argv[1:]
candidates = [
    os.path.join(profile_root, "Default", "Network", "Cookies"),
    os.path.join(profile_root, "Default", "Cookies"),
]
db = next((p for p in candidates if os.path.exists(p)), None)
if not db:
    raise SystemExit(1)

tmp = tempfile.mktemp(suffix=".db")
try:
    try:
        shutil.copy2(db, tmp)
    except OSError:
        # Locked by running Chrome.
        raise SystemExit(2)
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

ensure_source_readable() {
  local rc=0
  set +e
  has_auth "$SRC_ROOT" li_at
  rc=$?
  set -e
  if [[ "$rc" -ne 2 ]]; then
    return 0
  fi
  echo "WARNING: Chrome Cookies DB is locked ($SRC_COOKIES)." >&2
  if [[ "${HOME_CHROME_SYNC_ALLOW_KILL:-1}" != "1" ]]; then
    echo "ERROR: close Desktop Chrome and re-run sync, or set HOME_CHROME_SYNC_ALLOW_KILL=1." >&2
    exit 1
  fi
  echo "Stopping Chrome so portal sessions can sync (HOME_CHROME_SYNC_ALLOW_KILL=1)…"
  if command -v taskkill.exe >/dev/null 2>&1; then
    taskkill.exe //F //IM chrome.exe >/dev/null 2>&1 || true
  else
    pkill -f "Google/Chrome|chrome.exe|google-chrome" 2>/dev/null || true
  fi
  sleep 2
  set +e
  has_auth "$SRC_ROOT" li_at
  rc=$?
  set -e
  if [[ "$rc" -eq 2 ]]; then
    echo "ERROR: Cookies still locked after stopping Chrome." >&2
    exit 1
  fi
}

echo "Source: $SRC_DEFAULT (cookies: $SRC_COOKIES)"

# Chrome 127+ Windows App-Bound Encryption (v20 cookies): blobs from Desktop
# Default will not decrypt under a different --user-data-dir. Copying them into
# CDP profiles causes login walls. On Windows+ABE, preserve CDP profiles and
# require a one-time login inside each ~/.cursor/chrome-cdp-profiles/<portal>.
ABE=0
if [[ -f "$SRC_ROOT/Local State" ]] && grep -q "app_bound_encrypted_key" "$SRC_ROOT/Local State" 2>/dev/null; then
  ABE=1
fi
IS_WIN=0
[[ "${OS:-}" == "Windows_NT" || -n "${MSYSTEM:-}" ]] && IS_WIN=1

if [[ "$IS_WIN" -eq 1 && "$ABE" -eq 1 && "${CHROME_FORCE_COOKIE_SYNC:-0}" != "1" ]]; then
  echo "NOTE: Windows Chrome App-Bound Encryption detected — skipping Default→CDP cookie copy."
  echo "      Use each portal CDP profile after a one-time login (headed Chrome)."
  missing_required=0
  for i in "${!PORTALS[@]}"; do
    portal="${PORTALS[$i]}"
    dest="${DESTS[$i]}"
    read -r -a cookies <<< "${COOKIE_SETS[$i]}"
    mkdir -p "$dest"
    touch "$dest/First Run" 2>/dev/null || true
    set +e
    has_auth "$dest" "${cookies[@]}"
    dest_rc=$?
    set -e
    if [[ "$dest_rc" -eq 0 ]]; then
      echo "preserved $portal auth at $dest"
    else
      echo "MISSING $portal CDP login at $dest (open via launch-chrome-cdp.sh $portal and sign in once)" >&2
      if [[ "${REQUIRED[$i]}" == "1" ]]; then
        missing_required=$((missing_required + 1))
      fi
    fi
  done
  node tools/chrome_session.js status || true
  echo "Chrome session sync complete (Windows ABE preserve mode)."
  if [[ "$STRICT" == "1" && "$missing_required" -gt 0 ]]; then
    echo "ERROR: $missing_required required portal CDP profile(s) still lack auth." >&2
    exit 3
  fi
  exit 0
fi

ensure_source_readable

missing_required=0
for i in "${!PORTALS[@]}"; do
  portal="${PORTALS[$i]}"
  dest="${DESTS[$i]}"
  read -r -a cookies <<< "${COOKIE_SETS[$i]}"

  set +e
  has_auth "$SRC_ROOT" "${cookies[@]}"
  src_rc=$?
  set -e

  if [[ "$src_rc" -eq 0 ]]; then
    sync_one "$portal" "$dest" "${cookies[@]}"
    continue
  fi

  set +e
  has_auth "$dest" "${cookies[@]}"
  dest_rc=$?
  set -e

  if [[ "$dest_rc" -eq 0 ]]; then
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
