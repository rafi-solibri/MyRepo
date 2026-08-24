#!/usr/bin/env bash
# Human-readable auth gate for the 6 daily job portals.
# Exit 0 when every CDP profile (what daily cron uses) has its auth cookie(s).
# Desktop Default gaps are reported as notes only (non-fatal for cron).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STRICT=0
SYNC=1
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    --no-sync) SYNC=0 ;;
    -h|--help)
      echo "Usage: bash scripts/verify-portal-logins.sh [--strict] [--no-sync]"
      exit 0
      ;;
  esac
done

if [[ "$SYNC" == "1" ]]; then
  if [[ "$STRICT" == "1" ]]; then
    bash scripts/sync-chrome-sessions.sh --strict || true
  else
    bash scripts/sync-chrome-sessions.sh || true
  fi
fi

python3 - <<'PY'
import json, os, shutil, sqlite3, sys, tempfile

PORTALS = [
    ("linkedin", "/home/ubuntu/chrome-cdp-profile", ["li_at"],
     "https://www.linkedin.com/feed/"),
    ("naukri", "/home/ubuntu/.naukri-chrome-profile", ["nauk_rt", "nauk_at"],
     "https://www.naukri.com/mnjuser/homepage"),
    ("foundit", "/home/ubuntu/.config/chrome-foundit", ["MSSOAT"],
     "https://www.foundit.in/seeker/dashboard"),
    ("cutshort", "/home/ubuntu/chrome-cutshort-profile", ["cutshort_authentication"],
     "https://cutshort.io/profile"),
    ("instahyre", "/home/ubuntu/chrome-instahyre-profile", ["sessionid"],
     "https://www.instahyre.com/candidate/opportunities/"),
    ("indeed", "/home/ubuntu/chrome-indeed-profile",
     ["__Secure-PassportAuthProxy-BearerToken", "CTK"],
     "https://www.indeed.com/"),
    ("hirist", "/home/ubuntu/chrome-hirist-profile", ["token"],
     "https://www.hirist.tech/applied-jobs"),
]
SRC = "/home/ubuntu/.config/google-chrome"

def names(root):
    db = os.path.join(root, "Default", "Cookies")
    if not os.path.exists(db):
        return set()
    tmp = tempfile.mktemp(suffix=".db")
    try:
        shutil.copy2(db, tmp)
        con = sqlite3.connect(tmp)
        out = {r[0] for r in con.execute("SELECT name FROM cookies")}
        con.close()
        return out
    except Exception:
        return set()
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass

src_names = names(SRC)
print("=" * 64)
print("Portal login verification (CDP profiles = what daily cron uses)")
print(f"Source profile: {SRC}")
print("=" * 64)

cdp_missing = []
source_missing = []
rows = []
for portal, dest, need, url in PORTALS:
    src_ok = any(n in src_names for n in need)
    dest_ok = any(n in names(dest) for n in need)
    # Cron launches CDP profiles (dest). Source is for sync only.
    mark = "OK  " if dest_ok else "FAIL"
    if not dest_ok:
        cdp_missing.append(portal)
    if not src_ok:
        source_missing.append(portal)
    print(f"[{mark}] {portal:10} source={src_ok}  cdp={dest_ok}  need={','.join(need)}")
    if not dest_ok:
        print(f"         → CDP lacks auth; need seed restore / Desktop login: {url}")
    elif not src_ok:
        print(f"         note: Desktop Default lacks cookie; CDP still OK for cron")
    rows.append({
        "portal": portal,
        "sourceHasAuth": src_ok,
        "destHasAuth": dest_ok,
        "ok": dest_ok,
        "loginUrl": url,
        "need": need,
    })

print("=" * 64)
report = {
    "ok": len(cdp_missing) == 0,
    "missing": cdp_missing,
    "sourceMissing": source_missing,
    "portals": rows,
    "nextStepsIfMissing": [
        "Ensure .portal-sessions seed is on main; install/start call restore-portal-sessions.sh",
        "Or Desktop-login FAIL portals, quit Chrome, refresh .portal-sessions",
        "bash scripts/verify-portal-logins.sh --strict",
        "Update Environment → Save so cron boots the new snapshot",
    ],
}
out_path = "/opt/cursor/artifacts/portal-login-status.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"Wrote {out_path}")

if cdp_missing:
    print(f"MISSING CDP AUTH: {', '.join(cdp_missing)}")
    print("Daily automations WILL hit login walls until these are fixed + snapshot saved.")
    sys.exit(3)

print("All 6 portal CDP profiles have auth cookie NAMES in SQLite.")
print("NOTE: SQLite name presence ≠ live session. LinkedIn often keeps a stale li_at")
print("      row after server invalidation / checkpoint. Cloud cron must still pass")
print("      `bash scripts/launch-chrome-cdp.sh linkedin` live CDP probe (feed URL, not /login|/checkpoint).")
print("      If live check fails: headed login → refresh .portal-sessions → Save snapshot.")
if source_missing:
    print(f"Desktop Default still missing: {', '.join(source_missing)} (non-fatal for cron if CDP OK)")
sys.exit(0)
PY
