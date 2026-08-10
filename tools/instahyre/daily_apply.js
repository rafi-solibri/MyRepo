#!/usr/bin/env node
/**
 * Instahyre daily apply scaffold — login check + skipReason helpers.
 *
 * Usage:
 *   bash scripts/preflight-portal-run.sh instahyre
 *   bash scripts/launch-chrome-cdp.sh instahyre
 *   node tools/instahyre/daily_apply.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const { skipReason } = require("./filters");
const { findResume } = require("./resume");

const CDP = process.env.INSTAHYRE_CDP || "http://127.0.0.1:9222";
const OUT =
  process.env.INSTAHYRE_REPORT ||
  "/opt/cursor/artifacts/instahyre-apply-report.json";
const MAX_APPLIES = Number(process.env.INSTAHYRE_MAX_APPLIES || 50);

async function main() {
  const report = {
    ts: new Date().toISOString(),
    resume: findResume(),
    maxApplies: MAX_APPLIES,
    applied: [],
    skipped: [],
    blocked: [],
    filterSelfCheck: {
      qe: skipReason("Quality Engineering Lead", { location: "Hyderabad" }),
      net: skipReason("Staff Software Engineer .NET", { location: "Hyderabad" }),
      ai: skipReason("AI Architect", { location: "Hyderabad", skills: ".NET" }),
    },
  };

  let browser;
  try {
    browser = await chromium.connectOverCDP(CDP);
  } catch (e) {
    report.blocked.push({ reason: "cdp_connect_failed", error: String(e).slice(0, 300) });
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(2);
  }

  const context = browser.contexts()[0] || (await browser.newContext());
  const page = context.pages()[0] || (await context.newPage());
  await page.goto("https://www.instahyre.com/candidate/opportunities/", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await page.waitForTimeout(2000);
  const body = await page.evaluate(() => (document.body?.innerText || "").slice(0, 1500));
  if (/log in|sign in|candidate login/i.test(body) && !/opportunities|interested/i.test(body)) {
    report.blocked.push({ reason: "instahyre_login_required" });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(3);
  }
  report.loggedIn = true;
  report.hint =
    "Logged in. Call skipReason(title,{location,skills,salary}) before Apply. Cap stuck ATS ~3–4 min. Maximize Hyd/remote senior applies.";

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
