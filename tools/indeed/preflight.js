#!/usr/bin/env node
/** Detect Indeed Cloudflare/public-cloud blockers before attempting applies. */
"use strict";

const fs = require("fs");
const path = require("path");

const OUT =
  process.env.INDEED_PREFLIGHT_REPORT ||
  "/opt/cursor/artifacts/indeed-preflight.json";
const URL = process.env.INDEED_PREFLIGHT_URL || "https://in.indeed.com/";

function writeReport(report) {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
}

function isCloudflareBlocked(status, text) {
  return (
    status === 403 ||
    /additional verification required|security check|cloudflare|cf-ray|ray id|request blocked|blocked - indeed/i.test(
      text || "",
    )
  );
}

async function main() {
  const report = {
    startedAt: new Date().toISOString(),
    url: URL,
    ok: false,
  };

  try {
    const res = await fetch(URL, {
      redirect: "manual",
      headers: {
        "user-agent":
          "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148 Safari/537.36",
      },
    });
    const text = await res.text().catch(() => "");
    report.status = res.status;
    report.title = (text.match(/<title[^>]*>([^<]+)/i) || [])[1] || "";
    report.bodySample = text.replace(/\s+/g, " ").slice(0, 500);

    if (isCloudflareBlocked(res.status, text)) {
      report.reason = "indeed_cloudflare_private_worker_required";
      report.hint =
        "Indeed blocks datacenter IPs. Fix: (1) run on home Wi‑Fi / private residential worker, or (2) set secret INDEED_HTTP_PROXY and relaunch via scripts/launch-chrome-cdp.sh indeed. See automation-prompts/INDEED_CLOUDFLARE.md.";
      report.proxyConfigured = Boolean(process.env.INDEED_HTTP_PROXY);
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
