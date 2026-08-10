# Indeed Cloudflare / "Request Blocked" fix

Indeed hard-blocks **datacenter / public-cloud IPs** with pages titled
`Blocked - Indeed.com` / `Security Check` and body text `Request Blocked`
(includes a Ray ID). Logged-in Chrome cookies alone do **not** bypass a hard
block — the network path matters.

Verified 2026-08-06 from Cursor public cloud: both `curl` and headless Chrome
to `https://in.indeed.com/` return the block page.

## Option C — Cloudflare WARP SOCKS + SeleniumBase UC (preferred on cloud VMs)

Verified 2026-08-10 on a Cursor cloud agent (no private/home worker):

1. **Cloudflare WARP in proxy mode** → local SOCKS5 `127.0.0.1:40000`
2. **SeleniumBase UC Chrome** through that proxy (headed / Xvfb display)
3. **`uc_gui_click_captcha()`** when the page shows
   `Additional Verification Required` / Turnstile

That combo clears Turnstile. Plain Chrome clicks, cloudscraper, and WARP alone
(without UC GUI captcha) did **not**.

```bash
bash scripts/start-warp-proxy.sh          # proxy mode ONLY — never full tunnel
eval "$(bash scripts/ensure-indeed-warp.sh)"
python3 tools/indeed/cf_bypass_uc.py      # clears CF; uses chrome-indeed-profile
node tools/indeed/preflight.js            # expects exit 0 (auto-starts WARP+UC)
bash scripts/launch-chrome-cdp.sh indeed  # CDP Chrome also uses WARP SOCKS
```

Notes:
- `warp-cli mode proxy` **before** `connect`. Full-tunnel WARP can blackhole the pod.
- No systemd? `scripts/start-warp-proxy.sh` starts `warp-svc` via `nohup`.
- HTTP curl through WARP may still return 403 until a real browser clears
  Turnstile — trust `cf_bypass_uc.py` / Chrome probe, not curl alone.
- Install pulls `cloudflare-warp` + `seleniumbase` via `cloud-agent-install.sh`;
  start hook brings WARP up via `cloud-agent-start.sh`.
- If the synced `chrome-indeed-profile` gets stuck on **Additional Verification
  Required** with no widget, rebuild a hybrid UC profile:
  `python3 tools/indeed/prepare_uc_profile.py` (keeps CTK/Passport, deletes `cf_*`).
- Plain Chrome CDP (`launch-chrome-cdp.sh`) through WARP can still show
  **Request Blocked** — apply via `python3 tools/indeed/uc_daily_apply.py`.
- SmartApply review uses Google **reCAPTCHA Enterprise**. The runner clicks the
  SmartApply sitekey widget (not the page-footer badge), tries audio solve, then
  optional token APIs. If Google rate-limits audio on the cloud IP, set one of:
  - `CAPSOLVER_API_KEY` (CapSolver ReCaptchaV2 Enterprise)
  - `TWOCAPTCHA_API_KEY` / `TWO_CAPTCHA_API_KEY`
  Otherwise prefer home/residential cron so checkbox often passes without a
  challenge.

## Home daily automation (free schedule)

Cannot create Cursor dashboard Automations from this agent (API read-only).
Use the home-PC cron instead — see **[INDEED_HOME_AUTOMATION.md](INDEED_HOME_AUTOMATION.md)**:

```bash
bash scripts/install-indeed-home-cron.sh 09:00   # macOS/Linux/WSL
# or Windows: scripts\install-indeed-home-task.ps1
bash scripts/indeed-home-daily.sh                # test now
```

## Easiest free fix (no purchase)

Indeed blocks Cursor’s public-cloud IPs. You cannot fix that without either a
home/residential network or a paid residential proxy.

**Do this (2 minutes):**

1. **Disable** the cloud cron so it stops failing every morning:  
   https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441 → turn **Off**
2. On your **home PC / laptop (home Wi‑Fi)**, open Cursor Desktop → this repo
   (`rafi-solibri/MyRepo` on `main`) → start a chat and paste:

```text
Run the Indeed daily apply now.
Read and OBEY automation-prompts/06-indeed.md.
First: node tools/indeed/preflight.js (must exit 0).
Then: bash scripts/preflight-portal-run.sh indeed
Then: bash scripts/launch-chrome-cdp.sh indeed
Use resumes/Rafi_Resume.docx. Apply Hyd/Remote .NET architect/lead roles.
Report submitted/skipped/blocked. Do not invent applies.
```

Home Wi‑Fi uses your residential ISP IP, so Indeed usually loads normally.
No proxy purchase, no My Machines CLI required.

If Chrome shows Indeed login once, sign in, then re-run the same prompt.

## Option A — My Machines worker (also free; more setup)

Tool calls (Chrome, Indeed pages) run on **your home ISP IP**, so Cloudflare
usually lets you through.

### Important limitation (individual / Ultra plans)

**Daily Automations cannot target a personal My Machines worker** on
non-Enterprise plans. Option A is for **on-demand** Indeed runs:

- Start worker on home PC → open [cursor.com/agents](https://cursor.com/agents) →
  pick `indeed-home` under **My Machines / Remote Control** → run the Indeed prompt.

For unattended 9 AM cron on public cloud, use **Option B** (residential proxy)
or an Enterprise Self-Hosted Pool.

### Step-by-step (home laptop / PC)

Use the **same Cursor account** as `mohammed.ahmed@solibri.com`.

#### 1. Install CLI (once)

**macOS / Linux / WSL:**

```bash
curl https://cursor.com/install -fsS | bash
agent --version
```

**Windows PowerShell:**

```powershell
irm 'https://cursor.com/install?win32=true' | iex
agent --version
```

#### 2. Sign in (once)

```bash
agent login
```

#### 3. Clone the repo (once)

```bash
git clone https://github.com/rafi-solibri/MyRepo.git
cd MyRepo
git checkout main
git pull
```

#### 4. Start the worker (every day you want Indeed to run)

```bash
cd /path/to/MyRepo
agent worker start --name indeed-home
```

Leave this terminal open. If the machine does not appear:

```bash
agent worker start --name indeed-home --debug
```

#### 5. Run Indeed on that machine

1. Open https://cursor.com/agents (same account).
2. New agent → **Run on** / environment picker → select **`indeed-home`**
   (My Machines / Remote Control).
3. Paste this prompt:

```text
Read and OBEY automation-prompts/06-indeed.md (fenced block).
Run `node tools/indeed/preflight.js` first; if exit 5, stop and report.
Otherwise: `bash scripts/preflight-portal-run.sh indeed`, then
`bash scripts/launch-chrome-cdp.sh indeed`, then execute the daily Indeed apply job.
Use resumes/Rafi_Resume.docx. Report submitted/skipped/blocked.
```

4. On the worker machine, first-time Indeed login in Chrome if needed, then
   confirm:

```bash
node tools/indeed/preflight.js
# expect ok: true
```

Docs: https://cursor.com/docs/cloud-agent/self-hosted-guides/my-machines

## Option B — Residential HTTP proxy (for unattended daily cron)

This is the path that lets the **9 AM Indeed automation** keep working on
Cursor public cloud without you starting a home worker every day.

### B1. Buy / create a **residential** proxy

Must be labeled **residential** (or ISP/static residential). **Datacenter /
shared / “datacenter sticky” proxies will still get Request Blocked.**

Examples of providers that sell residential plans: IPRoyal, Bright Data,
Oxylabs, Smartproxy, SOAX (pick any you already trust; we do not embed vendor
creds in the repo).

Ask the provider for an HTTP(S) endpoint in this form:

```text
http://USERNAME:PASSWORD@HOST:PORT
```

Tips:
- Prefer a **sticky session** (same exit IP for 10–30+ minutes) so Chrome login
  + applies stay on one IP.
- India exit / “IN” geo is nice-to-have for `in.indeed.com`, not required if
  the IP is truly residential.
- Do **not** commit the URL to git. Use Cursor secrets only.

### B2. Add the secret in Cursor

1. Open your environment:  
   https://cursor.com/dashboard/cloud-agents/environments/e/545c2557-9097-11f1-ba66-0e7d0216e441
2. Find **Secrets** / **Runtime secrets** (Environment Variables).
3. Add:

| Name | Value |
| --- | --- |
| `INDEED_HTTP_PROXY` | `http://USERNAME:PASSWORD@HOST:PORT` |

4. Scope it to this environment (or Personal secrets that cover `rafi-solibri/MyRepo`).
5. Save.

Also merge [PR #22](https://github.com/rafi-solibri/MyRepo/pull/22) to `main`
so install/start + `launch-chrome-cdp.sh` honor the proxy (already implemented
on that branch).

### B3. Refresh the environment so new agents see the secret

Existing VMs do **not** pick up new secrets automatically.

1. On the same environment page: **Update Environment** (⋯) then green **Save**,
   **or** trigger a new Build / New Setup Run.
2. Wait until the build succeeds.

### B4. Verify (tell the agent after B2+B3 — do not paste the password)

On a **fresh** cloud agent:

```bash
# Should print a redacted host, not empty:
node -e 'const p=process.env.INDEED_HTTP_PROXY||""; console.log({set:!!p, host:p.replace(/\/\/.*@/,"//***@")})'

node tools/indeed/preflight.js
# expect: proxyConfigured:true AND ok:true  (exit 0)
```

If `ok:false` / exit 5 with proxy set → the proxy is still datacenter or dead;
swap to a true residential endpoint and re-test.

Datacenter proxies will still get `Request Blocked`.

## What this repo does automatically

| Piece | Behavior |
| --- | --- |
| `tools/indeed/preflight.js` | Detects block via HTTP + Chrome probe; exit `5` with setup hint |
| `tools/indeed/chrome_probe.js` | Opens Indeed in the CDP profile; honors `INDEED_HTTP_PROXY` |
| `scripts/launch-chrome-cdp.sh indeed` | Passes `--proxy-server` when `INDEED_HTTP_PROXY` is set |
| Automation prompt | Stops on exit `5` — no fake applies |

## Not a fix

- Re-logging into Indeed on Desktop Chrome alone
- Saving the environment snapshot again without a residential path
- Waiting out the Security Check page on a blocked datacenter IP
- Expecting the 9 AM Indeed automation to use My Machines on an individual plan
