# Auto-fix & push (every daily automation run)

**Mandatory for LinkedIn, Hitech City / Knowledge City, Foundit, Cutshort, Naukri, Instahyre, Indeed (home), Notification, and Hotel Price Tracker.**

When a run hits a **code-fixable** issue or blocker, do not only report it. Fix the durable helper, push to the repo, and open a PR so the next cron picks it up from `main` (via ONE_TIME_LOADERS).

## Do this every run when applicable

1. Prefer fixing under durable paths:
   - `tools/{linkedin,hitechcity,foundit,cutshort,naukri,instahyre,indeed,hotels}/…`
   - `scripts/*.sh` / `scripts/*.mjs`
   - `automation-prompts/*.md` (prompt corrections)
2. Keep the change minimal and portal-scoped. Add/adjust a small test when filters/classifiers change.
3. Append a one-line row to `automation-prompts/ISSUES_AND_FIXES.md` under today’s date section.
4. Git workflow (feature branch — never commit straight to `main` unless repo policy already allows it):

```bash
git fetch origin main
git checkout -b cursor/<portal>-fix-<short-slug>-a239   # or continue current agent branch
# …edit durable code…
git add -A
git commit -m "$(cat <<'EOF'
fix(<portal>): <one-line description of blocker fix>

EOF
)"
git push -u origin HEAD
```

5. Open or update a **draft PR** into `main` with title/body describing the blocker and the fix. Mention artifact paths / evidence.
6. Continue the apply/hotel/notification job after the fix when safe (re-run the durable runner). Do not invent applies.

## What counts as code-fixable

| Example | Action |
| --- | --- |
| Wrong skip filter / false skip / false apply | Update `filters.js` / `filters.py` / `resume_and_filters.js` + test |
| Runner stuck on overlay / CTA / API shape | Patch `daily_apply.js` / Easy Apply helper |
| Questionnaire payload locks empty | Fix `questionnaire.js` |
| Resume path / preflight / CDP launch bug | Fix `scripts/` or portal resume helper |
| Prompt drift vs runner | Update matching `automation-prompts/0N-*.md` |

## Do NOT try to “fix in code”

| Blocker | Report only (owner action) |
| --- | --- |
| Portal Sign-in / missing cookies in snapshot | Desktop login → `verify-portal-logins.sh --strict` → Save snapshot |
| Indeed Cloudflare hard-block after WARP+UC multi-strategy + IP rotate still exits 5 | Home cron / My Machines `indeed-home` / residential `INDEED_HTTP_PROXY` (intermittent Turnstile misses are code-fixed via `cf_bypass_uc.py`) |
| Windows `agent worker` better-sqlite3 127/137 | Cursor packaging bug — use WSL (`scripts/fix-windows-agent-worker.ps1 -LaunchWsl`) |
| Missing secrets (`RESEND_*`, proxy creds) | Set in Cursor secrets / dashboard |
| CAPTCHA / email OTP / SMS walls | Cap ~3–4 min, mark blocked, continue |
| Automations UI Agent instructions | API is read-only — rely on ONE_TIME_LOADERS + merge to `main` |

## Parallel runs

Each portal agent uses its **own** feature branch/PR. Do not force-push shared branches. Notification Job may link open fix PRs in the daily mail but should not invent apply counts from them.
