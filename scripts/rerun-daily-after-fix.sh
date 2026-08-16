#!/usr/bin/env bash
# Same-day re-run of a daily automation after a code-fix PR lands on main.
#
# Daily cron/home jobs often merge a blocker fix, then stop — so that day's
# applies never use the fix. This helper pulls main and either:
#   1) launches a fresh Cursor cloud agent on main (preferred on cloud), or
#   2) re-executes the portal's durable apply helper in this session.
#
# Usage:
#   bash scripts/rerun-daily-after-fix.sh
#   bash scripts/rerun-daily-after-fix.sh --portal naukri
#   bash scripts/rerun-daily-after-fix.sh --merged-pr https://github.com/org/repo/pull/123
#   bash scripts/rerun-daily-after-fix.sh --detect-from-title "fix(naukri): …"
#   bash scripts/rerun-daily-after-fix.sh --detect-from-files file1 file2
#   bash scripts/rerun-daily-after-fix.sh --dry-run --portal linkedin
# Cap: 5 same-day re-runs per portal (IST). Override with POST_FIX_RERUN_MAX.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_BASE="${CURSOR_API_BASE_URL:-https://api.cursor.com}"
ENV_NAME="${CURSOR_CLOUD_ENV_NAME:-rafi-solibri/myrepo}"
MAX_RERUNS="${POST_FIX_RERUN_MAX:-5}"
TODAY="${POST_FIX_RERUN_DATE:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"
DRY_RUN=0
NO_EXEC=0
DETECT_ONLY=0
MERGED_PR=""
PORTAL_ARG=""
TITLE_ARG=""
FILES_ARGS=()

APPLY_PORTALS=(linkedin foundit cutshort naukri instahyre indeed hitechcity)
ALL_JOBS=(linkedin foundit cutshort naukri instahyre indeed hitechcity notification hotels)

usage() {
  cat <<'EOF'
Usage: bash scripts/rerun-daily-after-fix.sh [options]

  --portal NAME          Portal/job to re-run (repeatable via comma list)
  --merged-pr URL        PR just merged; detect portal(s) from title + files
  --detect-from-title T  Print portal ids for a commit/PR title and exit
  --detect-from-files    Print portal ids for the remaining path args and exit
  --dry-run              Print the plan; do not launch or exec
  --no-exec              Launch a cloud agent if possible; never exec locally
  --help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --portal) PORTAL_ARG="${2:-}"; shift 2 ;;
    --merged-pr) MERGED_PR="${2:-}"; shift 2 ;;
    --detect-from-title) TITLE_ARG="${2:-}"; DETECT_ONLY=1; shift 2 ;;
    --detect-from-files) DETECT_ONLY=1; shift; FILES_ARGS=("$@"); break ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no-exec) NO_EXEC=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

is_apply_portal() {
  local p="$1" x
  for x in "${APPLY_PORTALS[@]}"; do
    [[ "$x" == "$p" ]] && return 0
  done
  return 1
}

is_job() {
  local p="$1" x
  for x in "${ALL_JOBS[@]}"; do
    [[ "$x" == "$p" ]] && return 0
  done
  return 1
}

# Map a commit/PR title like "fix(naukri): …" to portal ids.
portals_from_title() {
  local title="${1:-}"
  local lower
  lower="$(printf '%s' "$title" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    fix\(linkedin\)*|*\(linkedin\)*|fix/linkedin*|cursor/linkedin-*) echo linkedin ;;
    fix\(foundit\)*|*\(foundit\)*|fix/foundit*|cursor/foundit-*) echo foundit ;;
    fix\(cutshort\)*|*\(cutshort\)*|fix/cutshort*|cursor/cutshort-*) echo cutshort ;;
    fix\(naukri\)*|*\(naukri\)*|fix/naukri*|cursor/naukri-*) echo naukri ;;
    fix\(instahyre\)*|*\(instahyre\)*|fix/instahyre*|cursor/instahyre-*) echo instahyre ;;
    fix\(indeed\)*|*\(indeed\)*|fix/indeed*|cursor/indeed-*) echo indeed ;;
    fix\(hitechcity\)*|fix\(hitech-city\)*|*\(hitechcity\)*|*\(hitech-city\)*|cursor/hitechcity-*|cursor/hitech-city-*) echo hitechcity ;;
    fix\(notification\)*|*\(notification\)*|cursor/notification-*) echo notification ;;
    fix\(hotels\)*|fix\(hotel\)*|*\(hotels\)*|cursor/hotels-*) echo hotels ;;
  esac
}

# Shared infra that every apply portal loads. A fix here should re-run all
# apply jobs that already failed on the old code today.
is_shared_apply_path() {
  local f="$1"
  case "$f" in
    tools/chrome_session.js|tools/ats/*|scripts/launch-chrome-cdp.sh|scripts/preflight-portal-run.sh|scripts/resolve-python.sh|scripts/sync-chrome-sessions.sh|scripts/kill-chrome-cdp.sh|scripts/restore-portal-sessions.sh|scripts/bootstrap-job-assets.sh|tools/resume_paths.py|scripts/home-headed-login.sh|scripts/cloud-agent-install.sh|scripts/cloud-agent-start.sh)
      return 0
      ;;
  esac
  return 1
}

portals_from_files() {
  local f shared=0
  local -A seen=()
  for f in "$@"; do
    case "$f" in
      tools/linkedin/*|automation-prompts/issues/linkedin.md) seen[linkedin]=1 ;;
      tools/foundit/*|automation-prompts/issues/foundit.md) seen[foundit]=1 ;;
      tools/cutshort/*|automation-prompts/issues/cutshort.md) seen[cutshort]=1 ;;
      tools/naukri/*|automation-prompts/issues/naukri.md) seen[naukri]=1 ;;
      tools/instahyre/*|automation-prompts/issues/instahyre.md) seen[instahyre]=1 ;;
      tools/indeed/*|automation-prompts/issues/indeed.md) seen[indeed]=1 ;;
      tools/hitechcity/*|automation-prompts/issues/hitechcity.md) seen[hitechcity]=1 ;;
      scripts/send-job-status-email.mjs|scripts/fetch-home-result.sh|scripts/fetch-indeed-home-result.sh|scripts/notification-home-daily.sh|automation-prompts/issues/notification.md)
        seen[notification]=1
        ;;
      tools/hotels/*|automation-prompts/issues/hotels.md) seen[hotels]=1 ;;
      scripts/ensure-missing-daily-runs.sh|scripts/run-portal-with-autofix.sh|scripts/append-issue-fix.sh|scripts/assert-no-conflict-markers.sh)
        # Infra helpers — docs/merge safety only; do not fan out to every portal.
        ;;
      scripts/rerun-daily-after-fix.sh|scripts/auto-merge-fix-pr.sh|scripts/test-rerun-daily-after-fix.sh|automation-prompts/*|.github/workflows/*)
        ;;
      *)
        if is_shared_apply_path "$f"; then
          shared=1
        fi
        ;;
    esac
  done
  if [[ "$shared" -eq 1 ]]; then
    local p
    for p in "${APPLY_PORTALS[@]}"; do
      seen[$p]=1
    done
  fi
  local p
  for p in "${ALL_JOBS[@]}"; do
    [[ -n "${seen[$p]:-}" ]] && echo "$p"
  done
}

uniq_portals() {
  local -A seen=()
  local p
  for p in "$@"; do
    p="$(printf '%s' "$p" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
    [[ -z "$p" ]] && continue
    is_job "$p" || continue
    [[ -n "${seen[$p]:-}" ]] && continue
    seen[$p]=1
    echo "$p"
  done
}

automation_id() {
  case "$1" in
    linkedin) echo beb6ef8e-908f-11f1-ba66-0e7d0216e441 ;;
    foundit) echo 5d1b07b2-90a9-11f1-ba66-0e7d0216e441 ;;
    cutshort) echo d6ba8b9d-9094-11f1-ba66-0e7d0216e441 ;;
    naukri) echo 003b88eb-909a-11f1-ba66-0e7d0216e441 ;;
    instahyre) echo 1d0ea682-9093-11f1-ba66-0e7d0216e441 ;;
    indeed) echo 91b09fd7-9093-11f1-ba66-0e7d0216e441 ;;
    notification) echo 8e34696c-90b1-11f1-ba66-0e7d0216e441 ;;
    hitechcity) echo b65968f7-953d-11f1-ba66-0e7d0216e441 ;;
    hotels) echo "" ;;
  esac
}

job_label() {
  case "$1" in
    linkedin) echo "LinkedIn Daily" ;;
    foundit) echo "Foundit Daily" ;;
    cutshort) echo "Cutshort Daily" ;;
    naukri) echo "Naukri Daily" ;;
    instahyre) echo "Instahyre Daily" ;;
    indeed) echo "Indeed Daily" ;;
    notification) echo "Notification Job" ;;
    hitechcity) echo "Hitech City / Knowledge City Daily" ;;
    hotels) echo "Hotel Price Tracker" ;;
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
    notification) echo "automation-prompts/07-notification.md" ;;
    hitechcity) echo "automation-prompts/08-hitech-city.md" ;;
    hotels) echo "tools/hotels/AUTOMATION.md" ;;
  esac
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

agent_prompt_for() {
  local portal="$1"
  local id label pfile extra
  id="$(automation_id "$portal")"
  label="$(job_label "$portal")"
  pfile="$(prompt_file_for "$portal")"
  extra=""
  case "$portal" in
    linkedin)
      extra="Run bash scripts/preflight-portal-run.sh $portal then bash scripts/launch-chrome-cdp.sh $portal."
      ;;
    hitechcity)
      extra="Run bash scripts/preflight-portal-run.sh hitechcity then bash scripts/launch-chrome-cdp.sh hitechcity. Set HITECHCITY_CAREERS_ONLY=1 and run python3 tools/hitechcity/daily_apply.py so company career portals apply first in parallel (HITECHCITY_PARALLEL_TABS=10 default; do not wait on LinkedIn CAPTCHA). Success = confirmation text only."
      ;;
    foundit|cutshort|instahyre)
      extra="Run bash scripts/preflight-portal-run.sh $portal first."
      ;;
    naukri)
      extra="Run bash scripts/preflight-portal-run.sh naukri then bash scripts/launch-chrome-cdp.sh naukri. STEP 0: refresh Naukri profile resume before applies (node tools/naukri/daily_apply.js does this)."
      ;;
    indeed)
      extra="FIRST: node tools/indeed/preflight.js (WARP+UC). If it still exits 5 after that, stop and report. Otherwise bash scripts/preflight-portal-run.sh indeed then node tools/indeed/daily_apply.js."
      ;;
    notification)
      extra="Compile today's portal results and email rafi.success@gmail.com. Fetch home JSON with bash scripts/fetch-home-result.sh <portal> --today."
      ;;
    hotels)
      extra="Run PYTHONPATH=. python3 -m tools.hotels.automation -v --out-dir /tmp/hotel-email and send the email."
      ;;
  esac
  cat <<EOF
SAME-DAY POST-FIX RE-RUN of ${label}. POST_FIX_RERUN=1. Date=${TODAY} IST.
A code-fixable blocker was patched and merged to main during today's earlier run. That earlier run did NOT apply with the fix. You MUST execute the daily job now WITH THE MERGED CODE so today's applies/email actually happen.

FIRST:
  git fetch origin main
  git checkout -f main
  git pull --ff-only origin main

Then read and OBEY the full instructions in ${pfile} (the fenced text block when present).
${extra}
Use resumes/Rafi_Resume.docx. Do not invent applies. Skip jobs already applied today.

Auto-fix is still allowed if you hit a NEW code-fixable blocker, but do not launch more than ${MAX_RERUNS} post-fix re-runs for this portal on ${TODAY}. If you are already at the cap, merge the fix and stop.

Automation (read-only): ${id:+https://cursor.com/automations/${id}}
Merged PR: ${MERGED_PR:-unknown}
EOF
}

artifact_dir() {
  if [[ -d /opt/cursor/artifacts && -w /opt/cursor/artifacts ]]; then
    echo /opt/cursor/artifacts
  else
    mkdir -p "$ROOT/artifacts"
    echo "$ROOT/artifacts"
  fi
}

marker_path() {
  echo "$(artifact_dir)/post-fix-rerun-$1-$TODAY.json"
}

marker_count() {
  local f="$1"
  if [[ ! -f "$f" ]]; then
    echo 0
    return
  fi
  python3 - "$f" <<'PY' 2>/dev/null || echo 0
import json, sys
p = sys.argv[1]
try:
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    print(int(d.get("count") or 0))
except Exception:
    print(0)
PY
}

write_marker() {
  local portal="$1" mode="$2" extra="${3:-}"
  local f count
  f="$(marker_path "$portal")"
  count="$(marker_count "$f")"
  count=$((count + 1))
  python3 - "$f" "$portal" "$TODAY" "$count" "$mode" "$extra" "${MERGED_PR:-}" <<'PY'
import json, sys, datetime
path, portal, day, count, mode, extra, pr = sys.argv[1:8]
prev = {}
try:
    with open(path, encoding="utf-8") as fh:
        prev = json.load(fh)
except Exception:
    prev = {}
launches = list(prev.get("launches") or [])
entry = {
    "at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "mode": mode,
}
if extra:
    entry["detail"] = extra
launches.append(entry)
out = {
    "portal": portal,
    "date": day,
    "count": int(count),
    "mergedPr": pr or None,
    "launches": launches,
}
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
    fh.write("\n")
print(path)
PY
}

is_home_local() {
  [[ "${HOME_LOCAL:-}" == "1" ]] && return 0
  [[ "${CHROME_CDP_MODE:-}" == "system" ]] && return 0
  case "${MSYSTEM:-}" in MINGW*|MSYS*|CYGWIN*) return 0 ;; esac
  [[ "${OS:-}" == "Windows_NT" ]] && return 0
  return 1
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

count_existing_cloud_reruns() {
  local portal="$1"
  local label needle body
  label="$(job_label "$portal")"
  needle="${label} post-fix re-run ${TODAY}"
  if [[ -z "${CURSOR_API_KEY:-}" ]]; then
    echo 0
    return
  fi
  body="$(cursor_api GET "/v1/agents?limit=50" 2>/dev/null || cursor_api GET "/v0/agents?limit=50" 2>/dev/null || echo "")"
  POST_FIX_NEEDLE="$needle" python3 -c '
import json, os, sys
needle = os.environ.get("POST_FIX_NEEDLE", "").lower()
raw = sys.stdin.read().strip()
if not raw:
    print(0)
    raise SystemExit
try:
    data = json.loads(raw)
except Exception:
    print(0)
    raise SystemExit
items = data.get("items") or data.get("agents") or []
print(sum(1 for it in items if needle in str(it.get("name") or "").lower()))
' <<<"$body" 2>/dev/null || echo 0
}

launch_cloud_agent() {
  local portal="$1"
  local name prompt repo payload body url
  if [[ -z "${CURSOR_API_KEY:-}" ]]; then
    echo "cloud-launch: CURSOR_API_KEY unset" >&2
    return 1
  fi
  name="$(job_label "$portal") post-fix re-run ${TODAY}"
  prompt="$(agent_prompt_for "$portal")"
  repo="$(repo_https_url)"
  payload="$(python3 - "$name" "$prompt" "$ENV_NAME" "$repo" "$portal" <<'PY'
import json, sys
name, prompt, env_name, repo, portal = sys.argv[1:6]
print(json.dumps({
    "name": name,
    "prompt": {"text": prompt},
    "env": {"type": "cloud", "name": env_name},
    "autoCreatePR": False,
    "envVars": {"POST_FIX_RERUN": "1", "POST_FIX_PORTAL": portal},
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
    "envVars": {"POST_FIX_RERUN": "1", "POST_FIX_PORTAL": portal},
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
  payload="$(python3 - "$prompt" "$repo" <<'PY'
import json, sys
prompt, repo = sys.argv[1:3]
print(json.dumps({
    "prompt": {"text": prompt},
    "source": {"repository": repo, "ref": "main"},
    "target": {"autoCreatePr": False},
}))
PY
)"
  echo "cloud-launch: retry /v0/agents ref=main" >&2
  if body="$(cursor_api POST "/v0/agents" "$payload" 2>/dev/null)"; then
    url="$(python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("url") or d.get("id") or "")' <<<"$body")"
    echo "cloud-launch: started $url" >&2
    printf '%s' "$url"
    return 0
  fi
  echo "cloud-launch: all API attempts failed" >&2
  return 1
}

pull_main() {
  echo "post-fix: fetching origin main so this session has the merged fix"
  git fetch origin main >/dev/null 2>&1 || true
  git checkout -f main >/dev/null 2>&1 || git checkout -f master >/dev/null 2>&1 || true
  git pull --ff-only origin main >/dev/null 2>&1 || true
  git log -1 --oneline || true
}

resolve_py() {
  if [[ -x "$ROOT/scripts/resolve-python.sh" ]]; then
    bash "$ROOT/scripts/resolve-python.sh"
  else
    echo python3
  fi
}

exec_portal_job() {
  local portal="$1"
  local py rc=0
  export POST_FIX_RERUN=1
  export POST_FIX_PORTAL="$portal"
  py="$(resolve_py)"
  echo "same-session exec: $portal (python=$py)"
  case "$portal" in
    linkedin)
      bash "$ROOT/scripts/preflight-portal-run.sh" linkedin
      bash "$ROOT/scripts/launch-chrome-cdp.sh" linkedin
      set +e
      "$py" "$ROOT/tools/linkedin/linkedin_easy_apply.py"
      rc=$?
      "$py" "$ROOT/tools/linkedin/linkedin_external_apply.py"
      rc=$((rc | $?))
      set -e
      ;;
    foundit|cutshort|instahyre)
      bash "$ROOT/scripts/preflight-portal-run.sh" "$portal"
      bash "$ROOT/scripts/launch-chrome-cdp.sh" "$portal" || true
      set +e
      node "$ROOT/tools/$portal/daily_apply.js"
      rc=$?
      set -e
      ;;
    naukri)
      bash "$ROOT/scripts/preflight-portal-run.sh" naukri
      bash "$ROOT/scripts/launch-chrome-cdp.sh" naukri
      set +e
      node "$ROOT/tools/naukri/daily_apply.js"
      rc=$?
      set -e
      ;;
    indeed)
      bash "$ROOT/scripts/preflight-portal-run.sh" indeed || true
      set +e
      node "$ROOT/tools/indeed/daily_apply.js"
      rc=$?
      set -e
      ;;
    hitechcity)
      bash "$ROOT/scripts/preflight-portal-run.sh" hitechcity
      bash "$ROOT/scripts/launch-chrome-cdp.sh" hitechcity
      set +e
      HITECHCITY_CAREERS_ONLY=1 "$py" "$ROOT/tools/hitechcity/daily_apply.py"
      rc=$?
      set -e
      ;;
    hotels)
      set +e
      PYTHONPATH="$ROOT" "$py" -m tools.hotels.automation -v --out-dir /tmp/hotel-email
      rc=$?
      set -e
      ;;
    notification)
      echo "same-session exec: notification is agent-composed mail — launching/re-prompting, not a blind send."
      echo "SAME_SESSION_RERUN_REQUIRED=notification"
      return 0
      ;;
    *)
      echo "ERROR: no exec recipe for $portal" >&2
      return 2
      ;;
  esac
  echo "same-session exec: $portal finished rc=$rc"
  return "$rc"
}

collect_portals() {
  local -a found=()
  local p title files

  if [[ -n "$TITLE_ARG" ]]; then
    uniq_portals $(portals_from_title "$TITLE_ARG")
    return
  fi
  if [[ ${#FILES_ARGS[@]} -gt 0 ]]; then
    uniq_portals $(portals_from_files "${FILES_ARGS[@]}")
    return
  fi

  if [[ -n "$PORTAL_ARG" ]]; then
    # `read` returns 1 at EOF even on success — must not trip `set -e`.
    IFS=',' read -r -a found <<<"$PORTAL_ARG" || true
  fi
  if [[ -n "${PORTAL:-}" ]]; then
    found+=("$PORTAL")
  fi
  if [[ -n "${POST_FIX_PORTAL:-}" ]]; then
    found+=("$POST_FIX_PORTAL")
  fi

  title=""
  files=""
  if [[ -n "$MERGED_PR" ]] && command -v gh >/dev/null 2>&1; then
    title="$(gh pr view "$MERGED_PR" --json title -q .title 2>/dev/null || true)"
    files="$(gh pr view "$MERGED_PR" --json files -q '.files[].path' 2>/dev/null || true)"
  fi
  if [[ -z "$title" ]]; then
    title="$(git log -1 --pretty=%s 2>/dev/null || true)"
  fi
  if [[ -z "$files" ]]; then
    files="$(git diff --name-only origin/main...HEAD 2>/dev/null || git diff --name-only HEAD~1 2>/dev/null || true)"
  fi

  if [[ -n "$title" ]]; then
    # shellcheck disable=SC2207
    found+=($(portals_from_title "$title" || true))
  fi
  if [[ -n "$files" ]]; then
    # shellcheck disable=SC2086,SC2207
    found+=($(portals_from_files $files || true))
  fi

  local branch
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [[ -n "$branch" ]]; then
    # shellcheck disable=SC2207
    found+=($(portals_from_title "$branch" || true))
  fi

  uniq_portals "${found[@]}"
}

if [[ "$DETECT_ONLY" -eq 1 ]]; then
  mapfile -t PORTALS < <(collect_portals)
  if [[ ${#PORTALS[@]} -eq 0 ]]; then
    exit 0
  fi
  printf '%s\n' "${PORTALS[@]}"
  exit 0
fi

mapfile -t PORTALS < <(collect_portals)
if [[ ${#PORTALS[@]} -eq 0 ]]; then
  echo "post-fix re-run: no portal detected (pass --portal). Skip."
  exit 0
fi

echo "post-fix re-run: date=$TODAY portals=${PORTALS[*]} dry_run=$DRY_RUN home=$(is_home_local && echo yes || echo no)"

overall=0
for portal in "${PORTALS[@]}"; do
  echo "-------- $portal --------"
  marker="$(marker_path "$portal")"
  local_count="$(marker_count "$marker")"
  cloud_count=0
  if ! is_home_local; then
    cloud_count="$(count_existing_cloud_reruns "$portal" || echo 0)"
  fi
  used="$local_count"
  if [[ "${cloud_count:-0}" -gt "$used" ]]; then
    used="$cloud_count"
  fi
  if [[ "$used" -ge "$MAX_RERUNS" ]]; then
    echo "SKIP $portal: already $used same-day post-fix re-run(s) (cap $MAX_RERUNS)"
    continue
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY-RUN would re-run $portal (used=$used cap=$MAX_RERUNS)"
    echo "agent name: $(job_label "$portal") post-fix re-run ${TODAY}"
    continue
  fi

  # Reserve the slot before work so a nested auto-merge cannot loop.
  write_marker "$portal" "started" >/dev/null
  pull_main

  launched=0
  detail=""
  if ! is_home_local && [[ -n "${CURSOR_API_KEY:-}" ]]; then
    set +e
    detail="$(launch_cloud_agent "$portal")"
    lrc=$?
    set -e
    if [[ "$lrc" -eq 0 ]]; then
      launched=1
      echo "OK: fresh cloud job for $portal → $detail"
      echo "This session should STOP applying; the new job has the merged fix."
    else
      echo "WARNING: cloud launch failed for $portal — falling back to same-session exec"
    fi
  fi

  if [[ "$launched" -eq 1 ]]; then
    continue
  fi
  if [[ "$NO_EXEC" -eq 1 ]]; then
    echo "SAME_SESSION_RERUN_REQUIRED=$portal"
    continue
  fi
  if [[ "${POST_FIX_RERUN:-}" == "1" ]]; then
    echo "SKIP nested same-session exec for $portal (already inside a post-fix re-run). Merge is on main; a fresh cloud job was not launched."
    continue
  fi

  set +e
  exec_portal_job "$portal"
  erc=$?
  set -e
  if [[ "$erc" -ne 0 ]]; then
    echo "WARNING: same-session exec for $portal exited $erc"
    overall=1
  fi
done

exit "$overall"
