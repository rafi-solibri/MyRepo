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
const { resolvePython } = require("../chrome_session");

const OUT =
  process.env.INDEED_REPORT ||
  "/opt/cursor/artifacts/indeed-apply-report.json";

function run(cmd, args, timeoutMs = 180000) {
  return spawnSync(cmd, args, { encoding: "utf8", timeout: timeoutMs });
}

function runPython(args, timeoutMs = 180000) {
  const py = resolvePython();
  if (py === "py") return run("py", ["-3", ...args], timeoutMs);
  return run(py, args, timeoutMs);
}

/** UC runner prints progress logs then a final JSON object on stdout. */
function parseJsonTail(text) {
  const raw = String(text || "").trim();
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    /* fall through */
  }
  const start = raw.lastIndexOf("\n{");
  const idx = start >= 0 ? start + 1 : raw.lastIndexOf("{");
  if (idx < 0) return null;
  try {
    return JSON.parse(raw.slice(idx));
  } catch {
    return null;
  }
}

function main() {
  const report = {
    ts: new Date().toISOString(),
    resume: findResume(),
    applied: [],
    skipped: [],
    blocked: [],
  };

  // UC Turnstile + WARP rotate regularly exceeds 3m; 180s spawnSync
  // timeout was aborting a successful clear as preflight_error (null status).
  const pre = run(
    process.execPath,
    [path.join(__dirname, "preflight.js")],
    Number(process.env.INDEED_PREFLIGHT_TIMEOUT_MS || 360000),
  );
  report.preflightExit = pre.status;
  const preParsed = parseJsonTail(
    `${pre.stdout || ""}\n${pre.stderr || ""}`,
  );
  if (preParsed) {
    report.preflight = preParsed;
  } else {
    report.preflightRaw = (pre.stdout || pre.stderr || "").slice(0, 1000);
    try {
      const pf = "/opt/cursor/artifacts/indeed-preflight.json";
      if (fs.existsSync(pf)) {
        report.preflight = JSON.parse(fs.readFileSync(pf, "utf8"));
      }
    } catch {
      /* ignore */
    }
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
  // Home residential: INDEED_SKIP_WARP=1 → UC without proxy.
  if (process.env.INDEED_SKIP_UC_APPLY !== "1") {
    const uc = path.join(__dirname, "uc_daily_apply.py");
    // Full inventory: search + SmartApply + company-site ATS (up to ~390s each).
    // 30m was killing the runner mid-inventory after a few ATS timeouts.
    const apply = runPython(
      [uc],
      Number(process.env.INDEED_UC_TIMEOUT_MS || 5400000),
    );
    report.ucApplyExit = apply.status;
    const parsed = parseJsonTail(apply.stdout || "");
    if (parsed) {
      report.ucApply = parsed;
    } else {
      report.ucApplyRaw = (apply.stdout || apply.stderr || "").slice(0, 2000);
      // Prefer on-disk artifact written by uc_daily_apply.py.
      try {
        const daily = "/opt/cursor/artifacts/indeed-daily-run.json";
        if (fs.existsSync(daily)) {
          report.ucApply = JSON.parse(fs.readFileSync(daily, "utf8"));
        }
      } catch {
        /* ignore */
      }
    }
    const counts = report.ucApply && report.ucApply.counts;
    if (counts) {
      report.applied = report.ucApply.applied || [];
      report.skipped = report.ucApply.skipped || [];
      report.blocked = report.ucApply.blocked || [];
      report.rejected = report.ucApply.rejected || [];
      report.counts = counts;
    }
    report.ok = apply.status === 0 || Boolean(report.ucApply && report.ucApply.ok);
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
