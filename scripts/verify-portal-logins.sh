#!/usr/bin/env bash
# Human-readable auth gate for the 6 daily job portals.
# Exit 0 only when all required portals have auth cookies in Desktop Default
# AND in each CDP profile (after a safe sync).
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
print("Portal login verification (Desktop Default Chrome cookies)")
print(f"Source profile: {SRC}")
print("=" * 64)

missing = []
rows = []
for portal, dest, need, url in PORTALS:
    src_ok = any(n in src_names for n in need)
    dest_ok = any(n in names(dest) for n in need)
    mark = "OK  " if (src_ok and dest_ok) else "FAIL"
    if not (src_ok and dest_ok):
        missing.append(portal)
    print(f"[{mark}] {portal:10} source={src_ok}  cdp={dest_ok}  need={','.join(need)}")
    if not src_ok:
        print(f"         → open Desktop Chrome and sign in: {url}")
    rows.append({
        "portal": portal,
        "sourceHasAuth": src_ok,
        "destHasAuth": dest_ok,
        "ok": src_ok and dest_ok,
        "loginUrl": url,
        "need": need,
    })

print("=" * 64)
report = {
    "ok": len(missing) == 0,
    "missing": missing,
    "portals": rows,
    "nextStepsIfMissing": [
        "Open Cloud Agent Desktop for this environment",
        "In Default Chrome (not a CDP profile window), sign into each FAIL portal until the home/feed page loads",
        "Fully quit Chrome (all windows)",
        "bash scripts/verify-portal-logins.sh --strict",
        "Save / Update snapshot on the environment dashboard",
    ],
}
out_path = "/opt/cursor/artifacts/portal-login-status.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"Wrote {out_path}")

if missing:
    print(f"MISSING AUTH: {', '.join(missing)}")
    print("Daily automations WILL hit login walls until these are fixed + snapshot saved.")
    sys.exit(3)

print("All 6 portals authenticated in source and CDP profiles.")
sys.exit(0)
PY
