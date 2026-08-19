#!/usr/bin/env bash
# Launch today's apply-portal cloud agents (reliable daily trigger).
#
# Cursor Automations cron sometimes does not fire even when enabled. This
# script is the durable 9 AM IST launcher (GitHub Actions + manual). It skips a
# portal when a same-day agent for that portal already exists, so leaving the
# Cursor Automations enabled does not double-launch.
#
# Usage:
#   bash scripts/launch-daily-portals.sh
#   bash scripts/launch-daily-portals.sh --dry-run
#   bash scripts/launch-daily-portals.sh --portal linkedin,indeed
#   bash scripts/launch-daily-portals.sh --force   # launch even if same-day agent exists
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_BASE="${CURSOR_API_BASE_URL:-https://api.cursor.com}"
ENV_NAME="${CURSOR_CLOUD_ENV_NAME:-rafi-solibri/myrepo}"
TODAY="${DAILY_LAUNCH_DATE:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"
DRY_RUN=0
FORCE=0
PORTAL_ARG=""
APPLY_PORTALS=(linkedin foundit cutshort naukri instahyre indeed hitechcity)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    --portal) PORTAL_ARG="${2:-}"; shift 2 ;;
    --help|-h)
      echo "Usage: bash scripts/launch-daily-portals.sh [--dry-run] [--force] [--portal a,b]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

job_label() {
  case "$1" in
    linkedin) echo "LinkedIn Daily" ;;
    foundit) echo "Foundit Daily" ;;
    cutshort) echo "Cutshort Daily" ;;
    naukri) echo "Naukri Daily" ;;
    instahyre) echo "Instahyre Daily" ;;
    indeed) echo "Indeed Daily" ;;
    hitechcity) echo "Hitech City / Knowledge City Daily" ;;
    *) echo "$1" ;;
  esac
}

prompt_file_for() {
  case "$1" in
    linkedin) echo "automation-prompts/01-linkedin.md" ;;
    foundit) echo "automation-prompts/02-foundit.md" ;;
    cutshort) echo "automation-prompts/03-cutshort.md" ;;
    naukri) echo "automation-prompts/04-naukri-general.md" ;;
    instahyre) echo "automation-prompts/05-instahyre.md" ;;
    indeed) echo "automation-prompts/06-indeed.md" ;;
    hitechcity) echo "automation-prompts/08-hitech-city.md" ;;
  esac
}

name_needles() {
  # Lowercase substrings that identify a same-day agent for this portal.
  case "$1" in
    linkedin) echo "linkedin" ;;
    foundit) echo "foundit" ;;
    cutshort) echo "cutshort" ;;
    naukri) echo "naukri" ;;
    instahyre) echo "instahyre" ;;
    indeed) echo "indeed" ;;
    hitechcity) echo "hitech" ;;
  esac
}

daily_prompt_for() {
  local portal="$1"
  local label pfile extra
  label="$(job_label "$portal")"
  pfile="$(prompt_file_for "$portal")"
  case "$portal" in
    linkedin)
      extra="Run bash scripts/preflight-portal-run.sh linkedin then bash scripts/launch-chrome-cdp.sh linkedin. Use resumes/Rafi_Resume.docx. Execute the daily LinkedIn apply job now."
      ;;
    foundit|cutshort|instahyre)
      extra="Run bash scripts/preflight-portal-run.sh $portal first. Use resumes/Rafi_Resume.docx. Execute the daily ${label} apply job now."
      ;;
    naukri)
      extra="Run bash scripts/preflight-portal-run.sh naukri then bash scripts/launch-chrome-cdp.sh naukri. CRITICAL STEP 0: refresh Naukri profile resume with resumes/Rafi_Resume.docx via node tools/naukri/update_profile_resume.js (or node tools/naukri/daily_apply.js which does STEP 0) BEFORE applying. Then execute the daily Naukri apply job."
      ;;
    indeed)
      extra="FIRST: node tools/indeed/preflight.js (WARP+UC Turnstile clear + filelock patch + IP rotate). If it still exits 5 after that, stop and report — do not invent applies. Otherwise: bash scripts/preflight-portal-run.sh indeed, then node tools/indeed/daily_apply.js (preferred) or python3 tools/indeed/uc_daily_apply.py. Use resumes/Rafi_Resume.docx. Report submitted/skipped/blocked."
      ;;
    hitechcity)
      extra="Run bash scripts/preflight-portal-run.sh hitechcity then bash scripts/launch-chrome-cdp.sh hitechcity. Use resumes/Rafi_Resume.docx. Execute via python3 tools/hitechcity/daily_apply.py (HITECHCITY_PARALLEL_TABS=10 by default — do not set tabs=1)."
      ;;
  esac
  cat <<EOF
DAILY APPLY RUN — ${label} — ${TODAY} IST.
Read and OBEY the full instructions in ${pfile} (the fenced text block).
${extra}
Do not invent applies. Follow automation-prompts/AUTO_FIX.md for code-fixable blockers.
EOF
}

repo_https_url() {
  if [[ -n "${CURSOR_REPO_URL:-}" ]]; then
    printf '%s' "$CURSOR_REPO_URL"
    return
  fi
  local url
  url="$(git -C "$ROOT" remote get-url origin 2>/dev/null || true)"
  url="${url%.git}"
  url="$(printf '%s' "$url" | sed -E 's#https://[^@]+@#https://#; s#^git@github.com:#https://github.com/#')"
  printf '%s' "$url"
}

cursor_api() {
  local method="$1" path="$2" data="${3:-}"
  local tmp http
  tmp="$(mktemp)"
  local -a args=(-sS -u "${CURSOR_API_KEY}:" -H "Content-Type: application/json" -X "$method" -o "$tmp" -w "%{http_code}")
  if [[ -n "$data" ]]; then
    args+=(--data "$data")
  fi
  http="$(curl "${args[@]}" "${API_BASE}${path}" || true)"
  if [[ "$http" != 2* ]]; then
    echo "cursor_api $method $path HTTP $http" >&2
    head -c 400 "$tmp" >&2 || true
    echo >&2
    rm -f "$tmp"
    return 1
  fi
  cat "$tmp"
  rm -f "$tmp"
}

same_day_agent_exists() {
  local portal="$1"
  local needle body
  needle="$(name_needles "$portal")"
  [[ -z "${CURSOR_API_KEY:-}" ]] && return 1
  body="$(cursor_api GET "/v1/agents?limit=50" 2>/dev/null || cursor_api GET "/v0/agents?limit=50" 2>/dev/null || echo "")"
  [[ -z "$body" ]] && return 1
  DAILY_NEEDLE="$needle" DAILY_TODAY="$TODAY" python3 -c '
import json, os, sys
from datetime import datetime, timezone, timedelta
needle = os.environ["DAILY_NEEDLE"].lower()
today = os.environ["DAILY_TODAY"]
# IST day window in UTC: 18:30 previous UTC day → 18:29 today UTC (approx)
y, m, d = map(int, today.split("-"))
ist = timezone(timedelta(hours=5, minutes=30))
start = datetime(y, m, d, 0, 0, 0, tzinfo=ist).astimezone(timezone.utc)
end = start + timedelta(days=1)
try:
    data = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
items = data.get("items") or data.get("agents") or []
if isinstance(data, list):
    items = data
for it in items:
    if not isinstance(it, dict):
        continue
    name = str(it.get("name") or "").lower()
    if needle not in name:
        continue
    # Skip notification / ensure-missing / hotel noise
    if "notification" in name or "hotel" in name:
        continue
    if "ensure missing" in name:
        continue
    created = it.get("createdAt") or it.get("created_at") or it.get("createdAtMs")
    ts = None
    if isinstance(created, (int, float)):
        ms = float(created)
        if ms > 1e12:
            ms /= 1000.0
        ts = datetime.fromtimestamp(ms, tz=timezone.utc)
    elif isinstance(created, str) and created:
        try:
            ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except Exception:
            ts = None
    if ts is None:
        # Name matched and we cannot date — treat as existing to avoid dupes
        raise SystemExit(0)
    if start <= ts < end:
        status = str(it.get("status") or "").upper()
        if status in ("ARCHIVED", "EXPIRED", "ERROR"):
            continue
        raise SystemExit(0)
raise SystemExit(1)
' <<<"$body" 2>/dev/null
}

launch_cloud_agent() {
  local portal="$1"
  local name prompt repo payload body url
  if [[ -z "${CURSOR_API_KEY:-}" ]]; then
    echo "cloud-launch: CURSOR_API_KEY unset" >&2
    return 1
  fi
  name="$(job_label "$portal") ${TODAY}"
  prompt="$(daily_prompt_for "$portal")"
  repo="$(repo_https_url)"
  payload="$(python3 - "$name" "$prompt" "$ENV_NAME" "$repo" "$portal" <<'PY'
import json, sys
name, prompt, env_name, repo, portal = sys.argv[1:6]
print(json.dumps({
    "name": name,
    "prompt": {"text": prompt},
    "env": {"type": "cloud", "name": env_name},
    "autoCreatePR": False,
    "envVars": {"DAILY_PORTAL_LAUNCH": "1", "DAILY_PORTAL": portal},
}))
PY
)"
  echo "cloud-launch: POST /v1/agents name=$name env=$ENV_NAME" >&2
  if body="$(cursor_api POST "/v1/agents" "$payload" 2>/dev/null)"; then
    url="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("agent") or d).get("url") or (d.get("agent") or d).get("id") or "")' <<<"$body")"
    echo "cloud-launch: started $url" >&2
    printf '%s' "$url"
    return 0
  fi
  payload="$(python3 - "$name" "$prompt" "$repo" "$portal" <<'PY'
import json, sys
name, prompt, repo, portal = sys.argv[1:6]
print(json.dumps({
    "name": name,
    "prompt": {"text": prompt},
    "repos": [{"url": repo, "startingRef": "main"}],
    "autoCreatePR": False,
    "envVars": {"DAILY_PORTAL_LAUNCH": "1", "DAILY_PORTAL": portal},
}))
PY
)"
  echo "cloud-launch: retry /v1/agents with repos startingRef=main" >&2
  if body="$(cursor_api POST "/v1/agents" "$payload" 2>/dev/null)"; then
    url="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("agent") or d).get("url") or "")' <<<"$body")"
    echo "cloud-launch: started $url" >&2
    printf '%s' "$url"
    return 0
  fi
  echo "cloud-launch: all API attempts failed for $portal" >&2
  return 1
}

want=()
if [[ -n "$PORTAL_ARG" ]]; then
  IFS=',' read -r -a want <<<"$PORTAL_ARG" || true
else
  want=("${APPLY_PORTALS[@]}")
fi

echo "daily-launch: date=$TODAY portals=${want[*]} dry_run=$DRY_RUN force=$FORCE"

if [[ -z "${CURSOR_API_KEY:-}" ]]; then
  echo "ERROR: CURSOR_API_KEY is required to launch daily portal cloud jobs." >&2
  echo "Set it as a Cloud Agent / GitHub Actions secret: https://cursor.com/dashboard/api" >&2
  exit 1
fi

# Restore seeded sessions before launching (helps Indeed/LinkedIn when dest was wiped).
if [[ "$DRY_RUN" -eq 0 && -x "$ROOT/scripts/restore-portal-sessions.sh" ]]; then
  FORCE_RESTORE_SESSIONS="${FORCE_RESTORE_SESSIONS:-0}" bash "$ROOT/scripts/restore-portal-sessions.sh" \
    || echo "WARNING: restore-portal-sessions failed (continuing)"
fi

launched=0
skipped=0
failed=0
for raw in "${want[@]}"; do
  p="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
  [[ -n "$p" ]] || continue
  echo "=== daily-launch: $p ==="
  if [[ "$FORCE" -eq 0 ]] && same_day_agent_exists "$p"; then
    echo "SKIP $p: same-day cloud agent already exists"
    skipped=$((skipped + 1))
    continue
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN would launch: $(job_label "$p") ${TODAY}"
    launched=$((launched + 1))
    continue
  fi
  if url="$(launch_cloud_agent "$p")"; then
    echo "OK: $p → $url"
    launched=$((launched + 1))
  else
    echo "WARNING: launch failed for $p"
    failed=$((failed + 1))
  fi
done

echo "daily-launch done: launched=$launched skipped=$skipped failed=$failed"
[[ "$failed" -eq 0 ]]
