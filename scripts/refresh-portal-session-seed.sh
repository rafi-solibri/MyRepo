#!/usr/bin/env bash
# Copy live CDP Cookies into .portal-sessions so the next cloud boot restores them.
#
# Usage:
#   bash scripts/refresh-portal-session-seed.sh linkedin
#   bash scripts/refresh-portal-session-seed.sh linkedin --commit   # git add/commit seed (private repo)
#
# Requires Chrome to be quit OR uses a copy of the Cookies DB (Chrome may lock the live file).
# Prefer calling after a successful live CDP login while Chrome is still up — we copy via shutil.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORTAL="${1:-}"
DO_COMMIT=0
for a in "${@:2}"; do
  case "$a" in
    --commit) DO_COMMIT=1 ;;
  esac
done

case "$PORTAL" in
  linkedin|hitechcity)
    DEST_NAME=linkedin
    NEED=li_at
    PROFILE="${DOC_PROFILE:-${LINKEDIN_CHROME_PROFILE:-/home/ubuntu/chrome-cdp-profile}}"
    ;;
  naukri)
    DEST_NAME=naukri
    NEED=nauk_rt
    PROFILE="${NAUKRI_CHROME_PROFILE:-/home/ubuntu/.naukri-chrome-profile}"
    ;;
  foundit)
    DEST_NAME=foundit
    NEED=MSSOAT
    PROFILE="${FOUNDIT_CHROME_PROFILE:-/home/ubuntu/.config/chrome-foundit}"
    ;;
  cutshort)
    DEST_NAME=cutshort
    NEED=cutshort_authentication
    PROFILE="${CUTSHORT_CHROME_PROFILE:-/home/ubuntu/chrome-cutshort-profile}"
    ;;
  instahyre)
    DEST_NAME=instahyre
    NEED=sessionid
    PROFILE="${INSTAHYRE_CHROME_PROFILE:-/home/ubuntu/chrome-instahyre-profile}"
    ;;
  indeed)
    DEST_NAME=indeed
    NEED=__Secure-PassportAuthProxy-BearerToken
    PROFILE="${INDEED_CHROME_PROFILE:-/home/ubuntu/chrome-indeed-profile}"
    ;;
  *)
    echo "Usage: bash scripts/refresh-portal-session-seed.sh <linkedin|naukri|foundit|cutshort|instahyre|indeed> [--commit]" >&2
    exit 2
    ;;
esac

SEED="$ROOT/.portal-sessions"
SRC_COOKIES="$PROFILE/Default/Cookies"
if [[ ! -f "$SRC_COOKIES" ]]; then
  echo "ERROR: missing Cookies at $SRC_COOKIES" >&2
  exit 3
fi

# Verify required cookie name exists (SQLite name check).
python3 - "$SRC_COOKIES" "$NEED" <<'PY'
import shutil, sqlite3, sys, tempfile
src, need = sys.argv[1], sys.argv[2]
tmp = tempfile.mktemp(suffix=".db")
shutil.copy2(src, tmp)
con = sqlite3.connect(tmp)
names = {r[0] for r in con.execute("SELECT name FROM cookies")}
con.close()
import os
os.remove(tmp)
if need not in names:
    print(f"ERROR: {need} not in {src}", file=sys.stderr)
    raise SystemExit(4)
print(f"ok: {need} present in live profile Cookies")
PY

mkdir -p "$SEED/cdp/$DEST_NAME/Default" "$SEED/source/Default"

# Copy Cookies (+ journal if present) into seed cdp/<portal> and source (linkedin/source).
cp -a "$SRC_COOKIES" "$SEED/cdp/$DEST_NAME/Default/Cookies"
if [[ -f "$PROFILE/Default/Cookies-journal" ]]; then
  cp -a "$PROFILE/Default/Cookies-journal" "$SEED/cdp/$DEST_NAME/Default/Cookies-journal"
fi
# Also keep linkedin_alt in sync for LinkedIn.
if [[ "$DEST_NAME" == "linkedin" ]]; then
  mkdir -p "$SEED/cdp/linkedin_alt/Default"
  cp -a "$SRC_COOKIES" "$SEED/cdp/linkedin_alt/Default/Cookies"
  [[ -f "$PROFILE/Default/Cookies-journal" ]] && cp -a "$PROFILE/Default/Cookies-journal" "$SEED/cdp/linkedin_alt/Default/Cookies-journal" || true
  # Source Default used by restore-portal-sessions for Desktop sync
  cp -a "$SRC_COOKIES" "$SEED/source/Default/Cookies"
  [[ -f "$PROFILE/Default/Cookies-journal" ]] && cp -a "$PROFILE/Default/Cookies-journal" "$SEED/source/Default/Cookies-journal" || true
  if [[ -f "$PROFILE/Local State" ]]; then
    cp -a "$PROFILE/Local State" "$SEED/source/Local State" || true
  fi
fi

python3 - "$SEED" "$DEST_NAME" <<'PY'
import json, os, sys, time
from datetime import datetime, timezone
seed, portal = sys.argv[1], sys.argv[2]
path = os.path.join(seed, "manifest.json")
data = {}
if os.path.isfile(path):
    try:
        data = json.load(open(path))
    except Exception:
        data = {}
ports = data.get("portalsPresent") or {}
ports[portal] = True
if portal == "linkedin":
    ports["linkedin_alt"] = True
data["portalsPresent"] = ports
data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
data["updatedPortal"] = portal
data["note"] = data.get("note") or "Private session seed for Cloud Agent install restore. Do not share publicly."
json.dump(data, open(path, "w"), indent=2)
print("updated", path, "updatedAt", data["updatedAt"])
PY

echo "Refreshed .portal-sessions seed for $DEST_NAME from $PROFILE"

# Also push the live Cookies into Desktop Default so the next preflight sync
# cannot wipe CDP with a stale source li_at / auth cookie.
LIVE_SRC="${CHROME_SOURCE_PROFILE:-/home/ubuntu/.config/google-chrome}"
if [[ -d "$LIVE_SRC/Default" ]]; then
  mkdir -p "$LIVE_SRC/Default"
  if cp -a "$SRC_COOKIES" "$LIVE_SRC/Default/Cookies" 2>/dev/null; then
    [[ -f "$PROFILE/Default/Cookies-journal" ]] && cp -a "$PROFILE/Default/Cookies-journal" "$LIVE_SRC/Default/Cookies-journal" 2>/dev/null || true
    echo "Also updated live Desktop Cookies at $LIVE_SRC/Default/Cookies"
  else
    echo "NOTE: could not update live Desktop Cookies (Chrome may have the DB locked)." >&2
  fi
fi

if [[ "$DO_COMMIT" == "1" ]]; then
  git add -A "$SEED"
  if git diff --cached --quiet; then
    echo "No seed changes to commit."
  else
    git commit -m "chore(sessions): refresh ${DEST_NAME} portal seed after live login"
    echo "Committed seed refresh (push separately if desired)."
  fi
fi
