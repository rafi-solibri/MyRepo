#!/usr/bin/env node
/**
 * Launch Chrome with the Indeed CDP profile, open a URL, and report whether
 * Indeed's Cloudflare/Akamai "Request Blocked" / Security Check page appears.
 *
 * Honors INDEED_HTTP_PROXY / HTTPS_PROXY via Chrome --proxy-server.
 * Usage: node tools/indeed/chrome_probe.js [url]
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { spawn, spawnSync } = require("child_process");
const http = require("http");

const URL = process.argv[2] || process.env.INDEED_PREFLIGHT_URL || "https://in.indeed.com/";
const PROXY =
  process.env.INDEED_HTTP_PROXY ||
  process.env.HTTPS_PROXY ||
  process.env.HTTP_PROXY ||
  process.env.https_proxy ||
  process.env.http_proxy ||
  "";
const PORT = Number(process.env.INDEED_PROBE_CDP_PORT || 9333);
// Temp profile: Cloudflare block is IP-based; avoid SingletonLock fights with apply Chrome.
const PROFILE =
  process.env.INDEED_PROBE_PROFILE ||
  `/tmp/cursor/indeed-cf-probe-profile-${PORT}`;

function findChrome() {
  const candidates = [
    process.env.CHROME_BIN,
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
  ].filter(Boolean);
  for (const c of candidates) {
    const r = spawnSync("bash", ["-lc", `command -v ${JSON.stringify(c)}`], {
      encoding: "utf8",
    });
    const p = (r.stdout || "").trim();
    if (p) return p;
  }
  return null;
}

function waitCdp(port, ms = 20000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const tick = () => {
      http
        .get(`http://127.0.0.1:${port}/json/version`, (res) => {
          let data = "";
          res.on("data", (c) => (data += c));
          res.on("end", () => {
            try {
              resolve(JSON.parse(data));
            } catch (e) {
              reject(e);
            }
          });
        })
        .on("error", () => {
          if (Date.now() - start > ms) reject(new Error("CDP not ready"));
          else setTimeout(tick, 300);
        });
    };
    tick();
  });
}

function proxyServerArg(proxyUrl) {
  if (!proxyUrl) return null;
  try {
    const u = new URL(proxyUrl);
    // Chrome --proxy-server wants host:port (auth via separate mechanism is limited;
    // prefer proxies without embedded user:pass, or use a local forwarder).
    if (u.username || u.password) {
      // Chrome cannot take user:pass in --proxy-server reliably; pass full URL form
      // that some builds accept: http://user:pass@host:port
      return proxyUrl.replace(/\/$/, "");
    }
    return `${u.hostname}:${u.port || (u.protocol === "https:" ? 443 : 80)}`;
  } catch {
    return proxyUrl;
  }
}

async function cdpEval(wsUrl, expression) {
  // Prefer websocket via python helper to avoid extra Node deps.
  spawnSync(
    "python3",
    ["-c", "import websocket"],
    { encoding: "utf8" },
  ).status !== 0 &&
    spawnSync("python3", ["-m", "pip", "install", "-q", "websocket-client"], {
      encoding: "utf8",
    });

  const py = `
import json, sys, time, websocket
ws = websocket.create_connection(sys.argv[1], timeout=20)
msg_id = 0
def send(method, params=None, sessionId=None):
    global msg_id
    msg_id += 1
    payload = {"id": msg_id, "method": method}
    if params: payload["params"] = params
    if sessionId: payload["sessionId"] = sessionId
    ws.send(json.dumps(payload))
    deadline = time.time() + 20
    while time.time() < deadline:
        data = json.loads(ws.recv())
        if data.get("id") == msg_id:
            return data
    raise TimeoutError(method)
tid = send("Target.createTarget", {"url": "about:blank"})["result"]["targetId"]
sid = send("Target.attachToTarget", {"targetId": tid, "flatten": True})["result"]["sessionId"]
send("Page.enable", sessionId=sid)
send("Page.navigate", {"url": sys.argv[2]}, sessionId=sid)
last = None
blocked = True
for i in range(10):
    time.sleep(3)
    r = send("Runtime.evaluate", {
        "expression": sys.argv[3],
        "returnByValue": True,
    }, sessionId=sid)
    last = r.get("result", {}).get("result", {}).get("value")
    try:
        obj = json.loads(last)
    except Exception:
        obj = {"raw": last}
    title = (obj.get("title") or "")
    text = (obj.get("text") or "")
    blob = (title + " " + text).lower()
    if not any(x in blob for x in [
        "security check", "request blocked", "you have been blocked",
        "additional verification", "just a moment", "blocked - indeed",
    ]):
        blocked = False
        break
print(json.dumps({"blocked": blocked, "sample": last}))
ws.close()
`;
  const expr =
    'JSON.stringify({title:document.title,url:location.href,text:(document.body&&document.body.innerText||"").slice(0,400)})';
  const res = spawnSync(
    "python3",
    ["-c", py, wsUrl, URL, expr],
    { encoding: "utf8", timeout: 90000 },
  );
  if (res.status !== 0) {
    return {
      blocked: true,
      error: (res.stderr || res.stdout || "cdp eval failed").slice(0, 500),
    };
  }
  try {
    return JSON.parse(res.stdout || "{}");
  } catch {
    return { blocked: true, error: "bad probe json", raw: res.stdout };
  }
}

async function main() {
  const chrome = findChrome();
  if (!chrome) {
    console.log(JSON.stringify({ ok: false, blocked: true, error: "chrome_not_found" }));
    process.exit(2);
  }

  fs.mkdirSync(PROFILE, { recursive: true });
  fs.mkdirSync("/tmp/cursor", { recursive: true });

  // Kill any prior probe chrome on this port + clear stale singleton locks.
  spawnSync("pkill", ["-f", `remote-debugging-port=${PORT}`], { stdio: "ignore" });
  try {
    for (const name of ["SingletonLock", "SingletonCookie", "SingletonSocket"]) {
      fs.rmSync(path.join(PROFILE, name), { force: true });
    }
  } catch (_) {}

  const args = [
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    `--remote-debugging-address=127.0.0.1`,
    `--remote-debugging-port=${PORT}`,
    "--remote-allow-origins=*",
    `--user-data-dir=${PROFILE}`,
    "about:blank",
  ];
  const proxyArg = proxyServerArg(PROXY);
  if (proxyArg) args.splice(args.length - 1, 0, `--proxy-server=${proxyArg}`);

  const log = `/tmp/cursor/indeed-chrome-probe-${PORT}.log`;
  const child = spawn(chrome, args, {
    detached: true,
    stdio: ["ignore", fs.openSync(log, "w"), fs.openSync(log, "a")],
  });
  child.unref();

  try {
    const version = await waitCdp(PORT);
    const result = await cdpEval(version.webSocketDebuggerUrl, URL);
    const blocked = Boolean(result.blocked);
    const out = {
      ok: !blocked,
      blocked,
      url: URL,
      proxyConfigured: Boolean(PROXY),
      sample: result.sample || null,
      error: result.error || null,
    };
    console.log(JSON.stringify(out));
    process.exit(blocked ? 5 : 0);
  } catch (e) {
    console.log(
      JSON.stringify({
        ok: false,
        blocked: true,
        error: String(e).slice(0, 500),
        url: URL,
      }),
    );
    process.exit(1);
  } finally {
    spawnSync("pkill", ["-f", `remote-debugging-port=${PORT}`], { stdio: "ignore" });
  }
}

main();
