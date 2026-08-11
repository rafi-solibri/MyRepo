# Auto-fix, push, and merge (every daily automation run)

**Mandatory for LinkedIn, Hitech City / Knowledge City, Foundit, Cutshort, Naukri, Instahyre, Indeed (home), Notification, Hotel Price Tracker, and all home-local evening replicas.**

When a run hits a **code-fixable** issue or blocker, do not only report it. Fix the durable helper, push a feature branch, open a PR, and **merge it into `main` automatically** so the next cron/home run picks it up.

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
gh pr merge --auto --squash      # queue auto-merge when checks finish
# If checks are green / none required and mergeable:
gh pr merge --squash --delete-branch
```

7. After the PR is merged (or auto-merge is enabled), `git fetch origin main && git checkout main && git pull --ff-only origin main` before continuing applies when safe. Do not invent applies.
8. Home batch runners call `restore_main` between portals — still push+merge your fix first so `main` has it for the next portal.

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

## Failure mode

If `gh pr merge` fails (conflicts, required reviews, failing checks): resolve conflicts on the branch, push, re-run `bash scripts/auto-merge-fix-pr.sh`. Do not leave the fix as draft-only.
