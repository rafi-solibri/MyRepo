#!/usr/bin/env node
/**
 * Daily Naukri profile resume refresh.
 *
 * Uploads resumes/Rafi_Resume.docx to https://www.naukri.com/mnjuser/profile
 * so recruiters see "Updated today" and the latest CV.
 *
 * Prerequisites:
 * - Logged-in Naukri Chrome CDP on http://127.0.0.1:9222
 * - bash scripts/bootstrap-job-assets.sh already run
 *
 * Usage:
 *   node tools/naukri/update_profile_resume.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { hasAuth } = require("../chrome_session");
const { findResume, CHROME_PROFILE } = require("./resume_and_filters");

const CDP = process.env.NAUKRI_CDP || "http://127.0.0.1:9222";
const PROFILE_URL =
  process.env.NAUKRI_PROFILE_URL || "https://www.naukri.com/mnjuser/profile";
const REPORT =
  process.env.NAUKRI_RESUME_REPORT ||
  "/opt/cursor/artifacts/naukri-profile-resume.json";

const FILE_SELECTORS = ["#attachCV", "#lazyAttachCV", "input[type='file']"];

function todayTokens() {
  const d = new Date();
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  const m = months[d.getMonth()];
  const day = d.getDate();
  const y = d.getFullYear();
  return [
    `${m} ${day}, ${y}`,
    `${m} ${String(day).padStart(2, "0")}, ${y}`,
    `Today`,
    `today`,
    `${day} ${m}`,
    `${m} ${day}`,
  ];
}

async function dismissPopups(page) {
  for (const sel of [
    "button:has-text('Later')",
    "button:has-text('Not now')",
    "button:has-text('Skip')",
    "[aria-label='Close']",
    ".crossIcon",
    "button:has-text('Close')",
  ]) {
    const el = page.locator(sel).first();
    if (await el.isVisible().catch(() => false)) {
      await el.click().catch(() => {});
      await page.waitForTimeout(400);
    }
  }
}

async function ensureLoggedIn(page) {
  await page.goto(PROFILE_URL, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);
  await dismissPopups(page);
  const url = page.url();
  if (/nlogin|login/i.test(url)) {
    return { ok: false, reason: "naukri_login_required", url };
  }
  const body = await page.evaluate(() => document.body.innerText.slice(0, 1500));
  if (/login to continue|sign in|otp for logging/i.test(body) && !/attach|resume|profile/i.test(body)) {
    return { ok: false, reason: "naukri_login_required", url };
  }
  return { ok: true, url };
}

async function uploadResume(page, resumePath) {
  // Prefer hidden file inputs Naukri uses for attachCV
  let uploadedVia = null;
  for (const sel of FILE_SELECTORS) {
    const input = page.locator(sel).first();
    if (await input.count()) {
      try {
        await input.setInputFiles(resumePath, { timeout: 20000 });
        uploadedVia = sel;
        break;
      } catch (e) {
        // try next
      }
    }
  }

  if (!uploadedVia) {
    // Click visible Update/Upload resume then set files on any new file input
    const updateBtn = page
      .locator(
        "text=/Update resume|Upload resume|Replace|Update CV|Upload CV/i"
      )
      .first();
    if (await updateBtn.isVisible().catch(() => false)) {
      const [chooser] = await Promise.all([
        page.waitForEvent("filechooser", { timeout: 8000 }).catch(() => null),
        updateBtn.click().catch(() => {}),
      ]);
      if (chooser) {
        await chooser.setFiles(resumePath);
        uploadedVia = "filechooser";
      } else {
        for (const sel of FILE_SELECTORS) {
          const input = page.locator(sel).first();
          if (await input.count()) {
            await input.setInputFiles(resumePath, { timeout: 20000 });
            uploadedVia = sel;
            break;
          }
        }
      }
    }
  }

  if (!uploadedVia) {
    return { ok: false, reason: "resume_file_input_not_found" };
  }

  await page.waitForTimeout(4000);
  await dismissPopups(page);

  // Save if a save/confirm appears
  for (const sel of [
    "button:has-text('Save')",
    "button:has-text('Submit')",
    "button:has-text('Update')",
    "button[type='submit']",
  ]) {
    const btn = page.locator(sel).first();
    if (await btn.isVisible().catch(() => false)) {
      await btn.click().catch(() => {});
      await page.waitForTimeout(2000);
      break;
    }
  }

  return { ok: true, uploadedVia };
}

async function touchHeadline(page) {
  // Soft activity signal: open resume headline, save without changing meaning.
  try {
    const edit = page
      .locator(
        "text=/Resume headline|Edit resume headline/i"
      )
      .first();
    if (!(await edit.isVisible().catch(() => false))) {
      // try pencil near headline
      const pencil = page.locator("[class*='resumeHeadline'] button, [class*='resume-headline'] button, a:has-text('Edit')").first();
      if (await pencil.isVisible().catch(() => false)) await pencil.click();
      else return { touched: false, reason: "headline_edit_not_found" };
    } else {
      await edit.click().catch(() => {});
    }
    await page.waitForTimeout(1000);
    const box = page.locator("textarea, input[type='text']").first();
    if (!(await box.isVisible().catch(() => false))) {
      return { touched: false, reason: "headline_input_missing" };
    }
    const current = (await box.inputValue().catch(() => "")) || "";
    // Tiny no-op refresh: ensure trailing space normalized (keeps content, triggers save)
    const next = current.trim();
    if (next.length < 5) {
      return { touched: false, reason: "headline_too_short" };
    }
    await box.fill(next);
    const save = page.locator("button:has-text('Save')").first();
    if (await save.isVisible().catch(() => false)) {
      await save.click();
      await page.waitForTimeout(1500);
      await dismissPopups(page);
      return { touched: true, headline: next.slice(0, 120) };
    }
    return { touched: false, reason: "headline_save_missing" };
  } catch (e) {
    return { touched: false, reason: String(e).slice(0, 200) };
  }
}

async function verifyUpdated(page) {
  await page.reload({ waitUntil: "domcontentloaded" }).catch(() => {});
  await page.waitForTimeout(2500);
  const text = await page.evaluate(() => {
    const updateOn = [...document.querySelectorAll(".updateOn, [class*='updateOn'], [class*='update-on']")]
      .map((e) => e.innerText.trim())
      .join(" | ");
    return {
      updateOn,
      bodySlice: document.body.innerText.slice(0, 4000),
      resumeName: (
        [...document.querySelectorAll("a, span, div")]
          .map((e) => (e.innerText || "").trim())
          .find((t) => /Rafi_Resume|\.docx|\.pdf/i.test(t) && t.length < 80) || ""
      ),
    };
  });
  const tokens = todayTokens();
  const blob = `${text.updateOn}\n${text.bodySlice}`;
  const todayHit = tokens.some((t) => blob.includes(t));
  return {
    todayHit,
    updateOn: text.updateOn,
    resumeName: text.resumeName,
    tokensTried: tokens.slice(0, 3),
  };
}

async function main() {
  const resume = findResume();
  const result = {
    startedAt: new Date().toISOString(),
    resume,
    chromeProfileHint: CHROME_PROFILE,
    cdp: CDP,
    auth: {
      destHasAuth: hasAuth("naukri"),
    },
    ok: false,
  };

  if (!resume) {
    result.reason = "Rafi_Resume.docx_missing";
    writeReport(result);
    console.error(JSON.stringify(result, null, 2));
    process.exit(2);
  }

  let chromium;
  try {
    ({ chromium } = require("playwright-core"));
  } catch {
    try {
      ({ chromium } = require("playwright"));
    } catch (e) {
      result.reason = "playwright_missing";
      result.error = String(e);
      writeReport(result);
      console.error(JSON.stringify(result, null, 2));
      process.exit(2);
    }
  }

  let page;
  try {
    const browser = await chromium.connectOverCDP(CDP);
    const context = browser.contexts()[0] || (await browser.newContext());
    page = await context.newPage();
    page.setDefaultTimeout(45000);
  } catch (e) {
    result.reason = "cdp_unreachable";
    result.error = String(e).slice(0, 500);
    result.hint = "Run: bash scripts/launch-chrome-cdp.sh naukri";
    writeReport(result);
    console.error(JSON.stringify(result, null, 2));
    process.exit(2);
  }

  try {
    const login = await ensureLoggedIn(page);
    if (!login.ok) {
      Object.assign(result, login);
      writeReport(result);
      console.error(JSON.stringify(result, null, 2));
      process.exit(3);
    }

    const abs = path.resolve(resume);
    const up = await uploadResume(page, abs);
    result.upload = up;
    if (!up.ok) {
      result.reason = up.reason;
      writeReport(result);
      console.error(JSON.stringify(result, null, 2));
      process.exit(4);
    }

    result.headline = await touchHeadline(page);
    result.verify = await verifyUpdated(page);
    result.ok = true;
    result.finishedAt = new Date().toISOString();
    // Prefer verify todayHit, but upload without crash still counts as attempted success
    if (!result.verify.todayHit) {
      result.ok = true;
      result.warning =
        "Upload finished but 'Updated today' text not confirmed — check profile UI. Recruiters may still see new file.";
    }
    writeReport(result);
    console.log(JSON.stringify(result, null, 2));
    process.exit(0);
  } catch (e) {
    result.reason = "exception";
    result.error = String(e).slice(0, 500);
    writeReport(result);
    console.error(JSON.stringify(result, null, 2));
    process.exit(1);
  } finally {
    if (page) await page.close().catch(() => {});
  }
}

function writeReport(obj) {
  try {
    fs.mkdirSync(path.dirname(REPORT), { recursive: true });
    fs.writeFileSync(REPORT, JSON.stringify(obj, null, 2));
  } catch (_) {
    // ignore
  }
}

if (require.main === module) {
  main();
}

module.exports = { uploadResume, ensureLoggedIn, touchHeadline, PROFILE_URL };
