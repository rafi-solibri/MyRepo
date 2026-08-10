#!/usr/bin/env node
/**
 * Indeed daily apply gate: preflight (HTTP + Chrome probe) then login check.
 * Full Easy Apply should run on home Wi‑Fi / private worker (cloud Cloudflare).
 *
 * Usage:
 *   node tools/indeed/daily_apply.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { findResume } = require("./resume");

const OUT =
  process.env.INDEED_REPORT ||
  "/opt/cursor/artifacts/indeed-apply-report.json";

function run(cmd, args) {
  return spawnSync(cmd, args, { encoding: "utf8", timeout: 180000 });
}

function main() {
  const report = {
    ts: new Date().toISOString(),
    resume: findResume(),
    applied: [],
    skipped: [],
    blocked: [],
  };

  const pre = run(process.execPath, [path.join(__dirname, "preflight.js")]);
  report.preflightExit = pre.status;
  try {
    report.preflight = JSON.parse(pre.stdout || pre.stderr || "{}");
  } catch {
    report.preflightRaw = (pre.stdout || pre.stderr || "").slice(0, 1000);
  }

  if (pre.status === 5) {
    report.blocked.push({
      reason: "indeed_cloudflare_private_worker_required",
      hint: "Disable cloud Indeed automation; run scripts/indeed-home-daily.sh on home Wi‑Fi or set INDEED_HTTP_PROXY.",
    });
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(5);
  }
  if (pre.status !== 0) {
    report.blocked.push({ reason: "preflight_error", exit: pre.status });
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(pre.status || 1);
  }

  report.ok = true;
  report.hint =
    "Preflight OK. Prefer home cron Easy Apply path. Cloud agents: complete Easy Apply + company ATS with Rafi_Resume.docx; CTC skip only under 35 LPA; title-first filters.";
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

main();
