#!/usr/bin/env node
/**
 * Detect Indeed Cloudflare / Akamai IP blocks before attempting applies.
 *
 * Exit codes:
 *   0 — reachable (HTTP and/or Chrome CDP / UC bypass)
 *   5 — still blocked after WARP+UC attempts
 *   1 — unexpected network/runtime error
 *   2 — WARP/proxy misconfiguration
 *
 * Proxy:
 *   - Set INDEED_HTTP_PROXY (residential HTTP or socks5://…)
 *   - Or omit it: auto-starts Cloudflare WARP SOCKS on 127.0.0.1:40000
 *     and clears Turnstile via tools/indeed/cf_bypass_uc.py when needed.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "../..");
const OUT =
  process.env.INDEED_PREFLIGHT_REPORT ||
  "/opt/cursor/artifacts/indeed-preflight.json";
const URL = process.env.INDEED_PREFLIGHT_URL || "https://in.indeed.com/";

function writeReport(report) {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
}

function isCloudflareBlocked(status, text, title) {
  const blob = `${status || ""} ${title || ""} ${text || ""}`;
  return (
    status === 403 ||
    /additional verification required|security check|request blocked|you have been blocked|just a moment|cloudflare|cf-ray|ray id|blocked - indeed/i.test(
      blob,
    )
  );
}

/** curl prefers socks5h:// so DNS goes through the proxy. */
function curlProxy(proxy) {
  if (!proxy) return "";
  if (proxy.startsWith("socks5://")) {
    return "socks5h://" + proxy.slice("socks5://".length);
  }
  return proxy;
}

function ensureWarpProxy(currentProxy) {
  if (process.env.INDEED_SKIP_WARP === "1") {
    return { proxy: currentProxy || "", started: false, skipped: true };
  }
  if (
    currentProxy &&
    !/127\.0\.0\.1:40000|localhost:40000/.test(currentProxy)
  ) {
    return { proxy: currentProxy, started: false, external: true };
  }
  const script = path.join(ROOT, "scripts/ensure-indeed-warp.sh");
  if (!fs.existsSync(script)) {
    return { proxy: currentProxy || "", started: false, missingScript: true };
  }
  const res = spawnSync("bash", [script], {
    encoding: "utf8",
    timeout: 120000,
    cwd: ROOT,
  });
  const out = `${res.stdout || ""}\n${res.stderr || ""}`;
  const m = out.match(/export INDEED_HTTP_PROXY=([^\n]+)/);
  let proxy = currentProxy || "";
  if (m) {
    // printf %q may wrap in $'…' or quotes — strip lightly
    proxy = m[1].replace(/^\$'|'$/g, "").replace(/^'|'$/g, "").replace(/^"|"$/g, "");
  }
  if (res.status !== 0 || !proxy) {
    return {
      proxy: currentProxy || "",
      started: false,
      error: out.slice(0, 800),
      exitCode: res.status,
    };
  }
  process.env.INDEED_HTTP_PROXY = proxy;
  return { proxy, started: true };
}

function curlFetch(url, proxy) {
  const args = [
    "-sS",
    "-L",
    "--max-redirs",
    "3",
    "-o",
    "/tmp/indeed-preflight-body.html",
    "-w",
    "%{http_code}",
    "-A",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "--max-time",
    "45",
  ];
  const px = curlProxy(proxy);
  if (px) args.push("-x", px);
  args.push(url);
  const res = spawnSync("curl", args, { encoding: "utf8" });
  if (res.error) throw res.error;
  const status = Number(String(res.stdout || "").trim()) || 0;
  const text = fs.existsSync("/tmp/indeed-preflight-body.html")
    ? fs.readFileSync("/tmp/indeed-preflight-body.html", "utf8")
    : "";
  return { status, text, curlExit: res.status };
}

/** Extract a JSON object from mixed stdout (SeleniumBase may prepend driver noise). */
function parseJsonBlob(text, fallbackPaths = []) {
  const raw = String(text || "").trim();
  if (raw) {
    try {
      return JSON.parse(raw);
    } catch {
      /* try braced slice below */
    }
    const start = raw.indexOf("{");
    const end = raw.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(raw.slice(start, end + 1));
      } catch {
        /* fall through to report files */
      }
    }
  }
  for (const p of fallbackPaths) {
    if (p && fs.existsSync(p)) {
      try {
        return JSON.parse(fs.readFileSync(p, "utf8"));
      } catch {
        /* try next */
      }
    }
  }
  return null;
}

function chromeProbe(url, proxy) {
  const probe = path.join(__dirname, "chrome_probe.js");
  if (!fs.existsSync(probe)) return null;
  const env = { ...process.env };
  if (proxy) env.INDEED_HTTP_PROXY = proxy;
  const res = spawnSync(process.execPath, [probe, url], {
    encoding: "utf8",
    env,
    timeout: 120000,
  });
  const parsed = parseJsonBlob(res.stdout || "");
  if (parsed) return parsed;
  return {
    ok: false,
    error: (res.stderr || res.stdout || "chrome_probe failed").slice(0, 500),
    exitCode: res.status,
  };
}

function rotateWarp(proxy) {
  if (!proxy || !/127\.0\.0\.1:40000|localhost:40000/.test(proxy)) {
    return { rotated: false, skipped: "external_proxy" };
  }
  const script = path.join(ROOT, "scripts/start-warp-proxy.sh");
  if (!fs.existsSync(script)) {
    return { rotated: false, error: "start-warp-proxy.sh missing" };
  }
  const res = spawnSync("bash", [script, "rotate"], {
    encoding: "utf8",
    timeout: 120000,
    cwd: ROOT,
  });
  return {
    rotated: res.status === 0,
    exitCode: res.status,
    log: `${res.stdout || ""}\n${res.stderr || ""}`.slice(-800),
  };
}

function ucBypass(proxy, opts = {}) {
  const script = path.join(__dirname, "cf_bypass_uc.py");
  if (!fs.existsSync(script)) return { ok: false, error: "cf_bypass_uc.py missing" };
  const reportPath =
    process.env.INDEED_CF_BYPASS_REPORT ||
    "/opt/cursor/artifacts/indeed-cf-bypass.json";
  // Remove stale report so a failed run cannot inherit a prior ok:true.
  try {
    if (fs.existsSync(reportPath)) fs.unlinkSync(reportPath);
  } catch {
    /* ignore */
  }
  const attempts = String(opts.attempts || process.env.INDEED_CF_ATTEMPTS || "4");
  const rounds = String(opts.rounds || process.env.INDEED_CF_ROUNDS || "3");
  const env = {
    ...process.env,
    INDEED_HTTP_PROXY: proxy || "",
    INDEED_CF_ATTEMPTS: attempts,
    INDEED_CF_ROUNDS: rounds,
  };
  // Multi-round bypass (with WARP rotate inside Python) can take several minutes.
  const timeoutMs = Number(process.env.INDEED_CF_BYPASS_TIMEOUT_MS || 720000);
  const res = spawnSync(
    "python3",
    [script, "--attempts", attempts, "--rounds", rounds],
    {
      encoding: "utf8",
      env,
      timeout: timeoutMs,
    },
  );
  const parsed = parseJsonBlob(`${res.stdout || ""}\n${res.stderr || ""}`, [
    reportPath,
  ]);
  if (parsed) {
    return { ...parsed, exitCode: res.status };
  }
  return {
    ok: false,
    error: (res.stderr || res.stdout || "uc bypass failed").slice(0, 800),
    exitCode: res.status,
  };
}

function probeOnce(proxy) {
  const { status, text } = curlFetch(URL, proxy || undefined);
  const title = (text.match(/<title[^>]*>([^<]+)/i) || [])[1] || "";
  const httpBlocked = isCloudflareBlocked(status, text, title);
  let chrome = null;
  if (process.env.SKIP_CHROME_PROBE !== "1") {
    chrome = chromeProbe(URL, proxy || undefined);
  }
  return {
    httpStatus: status,
    title,
    bodySample: text.replace(/\s+/g, " ").slice(0, 500),
    httpBlocked,
    chrome,
    chromeOk: Boolean(chrome && chrome.ok),
    blocked: Boolean(
      httpBlocked || (chrome && chrome.blocked) || (chrome && chrome.ok === false),
    ),
  };
}

function main() {
  const initialProxy =
    process.env.INDEED_HTTP_PROXY ||
    process.env.HTTPS_PROXY ||
    process.env.HTTP_PROXY ||
    process.env.https_proxy ||
    process.env.http_proxy ||
    "";

  const report = {
    startedAt: new Date().toISOString(),
    url: URL,
    ok: false,
  };

  try {
    const warp = ensureWarpProxy(initialProxy);
    report.warp = {
      started: Boolean(warp.started),
      external: Boolean(warp.external),
      skipped: Boolean(warp.skipped),
      error: warp.error || null,
    };
    const proxy = warp.proxy || initialProxy || "";
    report.proxyConfigured = Boolean(proxy);
    report.proxyHost = proxy ? proxy.replace(/\/\/.*@/, "//***@") : null;

    if (warp.error && !proxy) {
      report.reason = "warp_proxy_failed";
      report.hint =
        "Could not start Cloudflare WARP SOCKS. Install cloudflare-warp or set INDEED_HTTP_PROXY.";
      writeReport(report);
      console.error(JSON.stringify(report, null, 2));
      process.exit(2);
    }

    let probe = probeOnce(proxy);
    Object.assign(report, {
      httpStatus: probe.httpStatus,
      title: probe.title,
      bodySample: probe.bodySample,
      httpBlocked: probe.httpBlocked,
      chrome: probe.chrome,
    });

    if (probe.chromeOk) {
      report.ok = true;
      report.reason = "chrome_reachable";
      writeReport(report);
      console.log(JSON.stringify(report, null, 2));
      process.exit(0);
    }

    // HTTP 403 alone is expected through WARP until Turnstile is cleared in a
    // real browser — try SeleniumBase UC (multi-strategy + WARP rotate rounds).
    if (probe.blocked && process.env.INDEED_SKIP_UC_BYPASS !== "1") {
      const maxPreflightRounds = Number(
        process.env.INDEED_PREFLIGHT_UC_ROUNDS || "2",
      );
      report.ucBypassRounds = [];
      for (let r = 1; r <= maxPreflightRounds; r++) {
        const bypass = ucBypass(proxy);
        report.ucBypass = bypass;
        report.ucBypassRounds.push({
          n: r,
          ok: Boolean(bypass && bypass.ok),
          reason: bypass && (bypass.reason || bypass.error || null),
          exitIp:
            bypass &&
            bypass.rounds &&
            bypass.rounds[0] &&
            bypass.rounds[0].exitIp
              ? bypass.rounds[0].exitIp
              : null,
        });
        if (bypass && bypass.ok) {
          probe = probeOnce(proxy);
          Object.assign(report, {
            httpStatus: probe.httpStatus,
            title: probe.title,
            bodySample: probe.bodySample,
            httpBlocked: probe.httpBlocked,
            chrome: probe.chrome,
          });
          report.ok = true;
          report.reason = probe.chromeOk
            ? "chrome_reachable_after_uc_bypass"
            : "uc_bypass_cleared";
          writeReport(report);
          console.log(JSON.stringify(report, null, 2));
          process.exit(0);
        }
        // Extra outer rotate between preflight UC invocations (Python also rotates).
        if (r < maxPreflightRounds) {
          const rot = rotateWarp(proxy);
          report.ucBypassRounds[r - 1].warpRotate = rot;
        }
      }
    }

    if (probe.httpBlocked || (probe.chrome && probe.chrome.blocked) || !probe.chromeOk) {
      report.reason = "indeed_cloudflare_still_blocked";
      report.hint =
        "WARP SOCKS + SeleniumBase UC (multi-strategy + IP rotate) did not clear Indeed. Set residential INDEED_HTTP_PROXY or run scripts/indeed-home-daily.sh. See automation-prompts/INDEED_CLOUDFLARE.md";
      report.setupDoc = "automation-prompts/INDEED_CLOUDFLARE.md";
      writeReport(report);
      console.error(JSON.stringify(report, null, 2));
      process.exit(5);
    }

    report.ok = true;
    report.reason = "reachable";
    writeReport(report);
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    report.reason = "network_error";
    report.error = String(error).slice(0, 500);
    writeReport(report);
    console.error(JSON.stringify(report, null, 2));
    process.exit(1);
  }
}

main();
