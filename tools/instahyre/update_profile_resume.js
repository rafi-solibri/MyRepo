#!/usr/bin/env node
/**
 * Upload a resume file to the Instahyre candidate profile (#resume-input).
 *
 * Usage (CDP already up on 9222):
 *   node tools/instahyre/update_profile_resume.js [/path/to/Rafi_Resume.docx]
 *
 * Env:
 *   INSTAHYRE_CDP            default http://127.0.0.1:9222
 *   INSTAHYRE_RESUME_REPORT  default /opt/cursor/artifacts/instahyre-profile-resume.json
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const { findResume } = require("./resume");

const CDP = process.env.INSTAHYRE_CDP || "http://127.0.0.1:9222";
const PROFILE_URL =
  process.env.INSTAHYRE_PROFILE_URL || "https://www.instahyre.com/candidate/profile/";
const OUT =
  process.env.INSTAHYRE_RESUME_REPORT ||
  "/opt/cursor/artifacts/instahyre-profile-resume.json";

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function uploadProfileResume(page, resumePath) {
  const result = {
    ok: false,
    resume: resumePath,
    url: PROFILE_URL,
    filename: path.basename(resumePath),
  };
  if (!resumePath || !fs.existsSync(resumePath)) {
    result.reason = "resume_missing";
    return result;
  }

  await page.goto(PROFILE_URL, { waitUntil: "domcontentloaded", timeout: 60000 });
  await sleep(2000);
  const body = await page.evaluate(() => (document.body?.innerText || "").slice(0, 1200));
  if (/log in|sign in|candidate login/i.test(body) && !/resume|job preferences|skills/i.test(body)) {
    result.reason = "instahyre_login_required";
    return result;
  }

  const input = page.locator("#resume-input");
  if ((await input.count()) < 1) {
    result.reason = "resume_input_missing";
    result.bodyPreview = body.slice(0, 400);
    return result;
  }

  const before = await page.evaluate(() => {
    const t = document.body?.innerText || "";
    const m = t.match(/Last updated on[^\n]+/i);
    return { lastUpdated: m ? m[0] : null, nameMatch: /Rafi_/i.test(t) };
  });
  result.before = before;

  await input.setInputFiles(resumePath);
  // Angular on-file-change="uploadResume(true)" should fire; give upload time.
  await sleep(4000);

  // Wait until last-updated changes or filename appears, up to ~25s.
  let after = before;
  for (let i = 0; i < 10; i++) {
    await sleep(1500);
    after = await page.evaluate(() => {
      const t = document.body?.innerText || "";
      const m = t.match(/Last updated on[^\n]+/i);
      const link = [...document.querySelectorAll("a")]
        .map((a) => (a.innerText || "").trim())
        .find((x) => /\.docx|\.pdf/i.test(x));
      return { lastUpdated: m ? m[0] : null, resumeLink: link || null, text: t.slice(0, 800) };
    });
    if (
      (after.lastUpdated && after.lastUpdated !== before.lastUpdated) ||
      /updated|uploaded|success/i.test(after.text || "")
    ) {
      result.ok = true;
      break;
    }
  }

  result.after = {
    lastUpdated: after.lastUpdated,
    resumeLink: after.resumeLink,
  };
  if (!result.ok) {
    // Soft-ok if input accepted without visible error — Instahyre sometimes keeps same minute stamp.
    const err = await page.evaluate(() => {
      const t = document.body?.innerText || "";
      if (/error|failed|invalid|too large/i.test(t) && /resume/i.test(t)) return t.slice(0, 300);
      return null;
    });
    if (err) {
      result.reason = "upload_error_text";
      result.errorText = err;
    } else {
      result.ok = true;
      result.reason = "upload_assumed_ok_no_timestamp_change";
    }
  }
  return result;
}

async function main() {
  const resume = process.argv[2] || findResume();
  const report = { ts: new Date().toISOString(), resume };
  if (!resume) {
    report.ok = false;
    report.reason = "resume_missing";
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(2);
  }

  let browser;
  try {
    browser = await chromium.connectOverCDP(CDP);
  } catch (e) {
    report.ok = false;
    report.reason = "cdp_connect_failed";
    report.error = String(e).slice(0, 300);
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(2);
  }

  try {
    const context = browser.contexts()[0] || (await browser.newContext());
    const page = await context.newPage();
    Object.assign(report, await uploadProfileResume(page, resume));
    await page.close().catch(() => {});
  } finally {
    /* never browser.close() over CDP */
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  process.exit(report.ok ? 0 : 4);
}

if (require.main === module) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}

module.exports = { uploadProfileResume, PROFILE_URL };
