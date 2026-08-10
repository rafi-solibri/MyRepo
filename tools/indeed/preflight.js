#!/usr/bin/env node
/**
 * Detect Indeed Cloudflare / Akamai IP blocks before attempting applies.
 *
 * Exit codes:
 *   0 — reachable (HTTP and/or Chrome CDP)
 *   5 — blocked; needs private/residential worker OR INDEED_HTTP_PROXY
 *   1 — unexpected network/runtime error
 *
 * Proxy: set INDEED_HTTP_PROXY or HTTPS_PROXY / HTTP_PROXY to a residential
 * proxy URL (http://user:pass@host:port). Preflight and Chrome CDP honor it.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const OUT =
  process.env.INDEED_PREFLIGHT_REPORT ||
  "/opt/cursor/artifacts/indeed-preflight.json";
const URL = process.env.INDEED_PREFLIGHT_URL || "https://in.indeed.com/";
const PROXY =
  process.env.INDEED_HTTP_PROXY ||
  process.env.HTTPS_PROXY ||
  process.env.HTTP_PROXY ||
  process.env.https_proxy ||
  process.env.http_proxy ||
  "";

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
  if (proxy) {
    args.push("-x", proxy);
  }
  args.push(url);
  const res = spawnSync("curl", args, { encoding: "utf8" });
  if (res.error) {
    throw res.error;
  }
  const status = Number(String(res.stdout || "").trim()) || 0;
  const text = fs.existsSync("/tmp/indeed-preflight-body.html")
    ? fs.readFileSync("/tmp/indeed-preflight-body.html", "utf8")
    : "";
  return { status, text, curlExit: res.status };
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
  try {
    return JSON.parse(res.stdout || "{}");
  } catch {
    return {
      ok: false,
      error: (res.stderr || res.stdout || "chrome_probe failed").slice(0, 500),
      exitCode: res.status,
    };
  }
}

async function main() {
  const report = {
    startedAt: new Date().toISOString(),
    url: URL,
    proxyConfigured: Boolean(PROXY),
    proxyHost: PROXY ? PROXY.replace(/\/\/.*@/, "//***@") : null,
    ok: false,
  };

  try {
    const { status, text } = curlFetch(URL, PROXY || undefined);
    report.httpStatus = status;
    report.title = (text.match(/<title[^>]*>([^<]+)/i) || [])[1] || "";
    report.bodySample = text.replace(/\s+/g, " ").slice(0, 500);
    report.httpBlocked = isCloudflareBlocked(status, text, report.title);

    // Browser path (more accurate for real applies). Skipped when SKIP_CHROME_PROBE=1.
    if (process.env.SKIP_CHROME_PROBE !== "1") {
      report.chrome = chromeProbe(URL, PROXY || undefined);
      if (report.chrome && report.chrome.ok) {
        report.ok = true;
        report.reason = "chrome_reachable";
        writeReport(report);
        console.log(JSON.stringify(report, null, 2));
        process.exit(0);
      }
    }

    if (report.httpBlocked || (report.chrome && report.chrome.blocked)) {
      report.reason = "indeed_cloudflare_private_worker_required";
      report.hint = PROXY
        ? "Proxy is set but Indeed still blocked it. Use a residential (not datacenter) proxy, or run Indeed on a My Machines / private worker with a residential IP."
        : "Public-cloud / datacenter IPs are hard-blocked by Indeed (Request Blocked / Ray ID). Fix: (1) start a Cursor My Machines worker on a home/residential network and point the Indeed automation at it, OR (2) set secret INDEED_HTTP_PROXY to a residential proxy URL.";
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
