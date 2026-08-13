# Auto-fix, push, and merge (every daily automation run)

**Mandatory for LinkedIn, Hitech City / Knowledge City, Foundit, Cutshort, Naukri, Instahyre, Indeed (home), Notification, Hotel Price Tracker, and all home-local evening replicas.**

When a run hits a **code-fixable** issue or blocker, do not only report it. Fix the durable helper, push a feature branch, open a PR, **merge it into `main` automatically**, and **same-day re-run that portal's job** so today's applies use the fix — do not wait for tomorrow's cron.

## Do this every run when applicable

1. Prefer fixing under durable paths:
   - `tools/{linkedin,hitechcity,foundit,cutshort,naukri,instahyre,indeed,hotels}/…`
   - `scripts/*.sh` / `scripts/*.mjs` / `scripts/*.ps1`
   - `automation-prompts/*.md` (prompt corrections)
2. Keep the change minimal and portal-scoped. Add/adjust a small test when filters/classifiers change.
3. Append a one-line row to `automation-prompts/ISSUES_AND_FIXES.md` under today’s date section.
4. Git workflow (feature branch — never commit straight to `main`):

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

5. Open a **ready-for-review** PR into `main` (not draft) with title/body describing the blocker and the fix. Mention artifact paths / evidence.
6. **Merge automatically** (required):

```bash
# Preferred helper (creates PR if needed, enables auto-merge, merges when possible):
bash scripts/auto-merge-fix-pr.sh

# Or manually:
gh pr create --title "fix(<portal>): …" --body "…" --base main   # skip if PR exists
gh pr ready                      # if it was opened as draft by mistake
gh pr merge --squash --delete-branch   # this repo: immediate squash (auto-merge queue disabled)
```

7. **Same-day re-run (required)** — merging is not the end of the job. Today's applies must use the fix; do not wait for tomorrow's cron.

   `bash scripts/auto-merge-fix-pr.sh` already calls `scripts/rerun-daily-after-fix.sh` after a successful merge. That helper:

   1. Detects which daily job(s) the fix belongs to (PR title `fix(naukri): …`, paths under `tools/<portal>/`, or **all apply portals** when shared infra like `tools/chrome_session.js` changed).
   2. `git fetch origin main && git checkout main && git pull --ff-only origin main`.
   3. On cloud: launches a **fresh** Cursor cloud agent on `main` (needs secret `CURSOR_API_KEY` from [Cursor Dashboard → API Keys](https://cursor.com/dashboard/api)) with `POST_FIX_RERUN=1`. That new job runs the portal's daily apply prompt with the merged code.
   4. If no API key, or on home-local (`HOME_LOCAL=1`): **re-executes** the durable apply helper in this session (`daily_apply.js` / LinkedIn helpers / `hitechcity/daily_apply.py` / hotel automation).
   5. Caps at **2** same-day post-fix re-runs per portal (IST date) so a new blocker cannot loop forever.

   If you merged without the helper:

```bash
bash scripts/rerun-daily-after-fix.sh --portal <portal>
# or, after a merged PR:
bash scripts/rerun-daily-after-fix.sh --merged-pr https://github.com/rafi-solibri/myrepo/pull/NNN
```

   Jobs: `linkedin` `foundit` `cutshort` `naukri` `instahyre` `indeed` `hitechcity` `notification` `hotels`.

8. After the re-run is launched or the helper is re-executing, do not invent applies. Skip jobs already submitted today. Home batch runners call `restore_main` between portals — still push+merge+re-run your fix first so `main` has it.

## What counts as code-fixable

| Example | Action |
| --- | --- |
| Wrong skip filter / false skip / false apply | Update `filters.js` / `filters.py` / `resume_and_filters.js` + test |
| Runner stuck on overlay / CTA / API shape | Patch `daily_apply.js` / Easy Apply helper |
| Questionnaire payload locks empty | Fix `questionnaire.js` |
| Resume path / preflight / CDP launch bug | Fix `scripts/` or portal resume helper |
| Windows home CDP / Chrome path / ABE helper gaps | Fix `tools/chrome_session.js`, `scripts/launch-chrome-cdp.sh`, `scripts/home-headed-login.sh` |
| Prompt drift vs runner | Update matching `automation-prompts/0N-*.md` |
| Home runner / publish / fetch / Task Scheduler bugs | Fix `scripts/portal-home-daily.sh`, `publish-home-result.sh`, etc. |

## Do NOT try to “fix in code”

| Blocker | Report only (owner action) |
| --- | --- |
| Portal Sign-in / missing cookies / stale CDP session after helper exists | Headed login: `bash scripts/home-headed-login.sh <portal>` (or Desktop Chrome → verify → Save snapshot for cloud) |
| Indeed Cloudflare hard-block after WARP+UC multi-strategy + IP rotate still exits 5 | Home cron / My Machines `indeed-home` / residential `INDEED_HTTP_PROXY` |
| Windows `agent worker` better-sqlite3 127/137 | Cursor packaging bug — use WSL (`scripts/fix-windows-agent-worker.ps1 -LaunchWsl`) |
| Missing secrets (`RESEND_*`, proxy creds) | Set in Cursor secrets / dashboard |
| CAPTCHA / email OTP / SMS walls | Cap ~3–4 min, mark blocked, continue |
| Automations UI Agent instructions | API is read-only — rely on ONE_TIME_LOADERS + merge to `main` |

## Parallel runs

Each portal agent uses its **own** feature branch/PR. Do not force-push shared branches. Notification Job may link today’s merged fix PRs in the daily mail but should not invent apply counts from them.

## Owner secret for same-day cloud re-runs

Set **`CURSOR_API_KEY`** on the Cloud Agent environment (and optionally GitHub Actions) so a merged fix can launch a **new** cloud job on `main` the same day. Create a key at https://cursor.com/dashboard/api. Without it, `scripts/rerun-daily-after-fix.sh` still re-executes the durable helper in the current session.

## Failure mode

If `gh pr merge` fails (conflicts, required reviews, failing checks): resolve conflicts on the branch, push, re-run `bash scripts/auto-merge-fix-pr.sh`. Do not leave the fix as draft-only. Do not skip the same-day re-run once merge succeeds.
