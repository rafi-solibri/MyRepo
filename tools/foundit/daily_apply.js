#!/usr/bin/env node
/**
 * Minimal Foundit daily apply runner — classifies Raven/search cards via filters.js
 * then drives Quick Apply / external ATS through Chrome CDP.
 *
 * Usage:
 *   bash scripts/preflight-portal-run.sh foundit
 *   bash scripts/launch-chrome-cdp.sh foundit
 *   node tools/foundit/daily_apply.js
 *
 * Agents should prefer this over reinventing apply flows each run.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const { classifyJob } = require("./filters");
const { findResume } = require("./resume");

const CDP = process.env.FOUNDIT_CDP || "http://127.0.0.1:9222";
const OUT =
  process.env.FOUNDIT_REPORT ||
  "/opt/cursor/artifacts/foundit-apply-report.json";
const MAX_APPLIES = Number(process.env.FOUNDIT_MAX_APPLIES || 50);

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  const resume = findResume ? findResume() : null;
  const report = {
    ts: new Date().toISOString(),
    resume,
    applied: [],
    skipped: [],
    blocked: [],
    note:
      "Runner scaffolds classification + CDP session. Prefer UI Quick Apply path; agents may extend card scraping.",
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
  await page.goto("https://www.foundit.in/seeker/dashboard", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await sleep(2000);
  const body = await page.evaluate(() => (document.body?.innerText || "").slice(0, 1500));
  if (/sign in|log in|login/i.test(body) && !/hi[, ]+\s*rafi/i.test(body)) {
    report.blocked.push({ reason: "foundit_login_required" });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(3);
  }

  report.loggedIn = true;
  report.maxApplies = MAX_APPLIES;
  report.hint =
    "Logged in. Use Raven/search + classifyJob(job) before each apply. Cap stuck ATS ~3–4 min.";
  // Self-check classifyJob stays available for agents scraping cards mid-run
  report.classifySelfCheck = classifyJob({
    title: "Principal Engineer - .NET Core",
    skills: [{ text: ".NET Core" }],
    locations: [{ text: "Hyderabad" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  });

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
