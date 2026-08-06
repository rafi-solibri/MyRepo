# Indeed Cloudflare / "Request Blocked" fix

Indeed hard-blocks **datacenter / public-cloud IPs** with pages titled
`Blocked - Indeed.com` / `Security Check` and body text `Request Blocked`
(includes a Ray ID). Logged-in Chrome cookies do **not** bypass this — the
block is on the network path, not the session.

Verified 2026-08-06 from Cursor public cloud: both `curl` and headless Chrome
to `https://in.indeed.com/` return the block page.

## Fix options (pick one)

### Option A — My Machines worker (recommended, free if you have a home PC)

Run the Indeed automation tool calls on a machine with a **residential ISP IP**:

1. On your home laptop / PC (same network you browse Indeed normally):

```bash
curl https://cursor.com/install -fsS | bash
agent login
cd /path/to/MyRepo   # clone of github.com/rafi-solibri/MyRepo
agent worker start --name indeed-home
```

2. Keep that process running when Indeed Daily is scheduled (or start it before a manual run).

3. In Cursor → [Indeed Daily 9 AM](https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441):
   - Point the run / environment at your **My Machines** worker `indeed-home`
     (or trigger with `worker=indeed-home` where the product UI supports it).

4. Confirm:

```bash
node tools/indeed/preflight.js
# expect ok:true on the worker machine
```

Docs: https://cursor.com/docs/cloud-agent/self-hosted-guides/my-machines

### Option B — Residential HTTP proxy secret

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
