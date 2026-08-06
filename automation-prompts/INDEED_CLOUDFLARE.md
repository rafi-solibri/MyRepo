# Indeed Cloudflare / "Request Blocked" fix

Indeed hard-blocks **datacenter / public-cloud IPs** with pages titled
`Blocked - Indeed.com` / `Security Check` and body text `Request Blocked`
(includes a Ray ID). Logged-in Chrome cookies do **not** bypass this — the
block is on the network path, not the session.

Verified 2026-08-06 from Cursor public cloud: both `curl` and headless Chrome
to `https://in.indeed.com/` return the block page.

## Option A — My Machines on your home PC (do this now)

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

1. Get a **residential** (not datacenter) proxy URL, e.g. `http://user:pass@host:port`.
2. In the Cloud Agent environment secrets, set:

```text
INDEED_HTTP_PROXY=http://user:pass@host:port
```

3. Re-Save / rebuild the environment so cron pods inherit the secret.
4. Preflight + `launch-chrome-cdp.sh indeed` will route Indeed through the proxy.

```bash
node tools/indeed/preflight.js
# proxyConfigured:true and ok:true when the residential proxy works
```

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
