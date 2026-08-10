#!/usr/bin/env node
/**
 * Indeed daily apply gate: preflight (WARP SOCKS + Chrome/UC probe) then login check.
 * Cloud path: scripts/start-warp-proxy.sh + tools/indeed/cf_bypass_uc.py clear Turnstile.
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

function run(cmd, args, timeoutMs = 180000) {
  return spawnSync(cmd, args, { encoding: "utf8", timeout: timeoutMs });
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
      reason: "indeed_cloudflare_still_blocked",
      hint: "WARP+UC bypass failed. Retry: bash scripts/start-warp-proxy.sh && python3 tools/indeed/cf_bypass_uc.py — or set residential INDEED_HTTP_PROXY.",
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

  // Cloud path: SeleniumBase UC Easy Apply through WARP SOCKS.
  if (process.env.INDEED_SKIP_UC_APPLY !== "1") {
    const uc = path.join(__dirname, "uc_daily_apply.py");
    const apply = run("python3", [uc], 900000);
    report.ucApplyExit = apply.status;
    try {
      report.ucApply = JSON.parse(apply.stdout || "{}");
    } catch {
      report.ucApplyRaw = (apply.stdout || apply.stderr || "").slice(0, 2000);
    }
    report.ok = apply.status === 0;
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
    process.exit(apply.status === 0 ? 0 : apply.status || 1);
  }

  report.ok = true;
  report.hint =
    "Preflight OK. Run: python3 tools/indeed/uc_daily_apply.py (WARP+UC). CTC skip only under 35 LPA; title-first filters.";
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

main();
