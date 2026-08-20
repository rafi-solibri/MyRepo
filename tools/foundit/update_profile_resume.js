#!/usr/bin/env node
/**
 * Upload / replace Foundit profile resume (used before Falcon apply so the
 * portal-attached CV matches the JD-tailored docx).
 *
 *   node tools/foundit/update_profile_resume.js /path/to/Rafi_Resume.docx
 *
 * Requires Chrome CDP on :9222 (foundit profile).
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const { findResume } = require("./resume");

const CDP = process.env.FOUNDIT_CDP || "http://127.0.0.1:9222";
const PROFILE_URL = "https://www.foundit.in/seeker/profile";

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * @param {import('playwright-core').BrowserContext} context
 * @param {string} resumePath
 * @returns {Promise<{ok:boolean, via?:string, resumeName?:string, error?:string}>}
 */
async function updateFounditProfileResume(context, resumePath) {
  if (!resumePath || !fs.existsSync(resumePath)) {
    return { ok: false, error: "resume_missing" };
  }
  const page = await context.newPage();
  const uploads = [];
  const onResp = async (resp) => {
    const u = resp.url();
    if (/attachResume|uploadResume|resume/i.test(u) && /seeker-profile|falcon/i.test(u)) {
      uploads.push({ url: u.slice(0, 180), status: resp.status() });
    }
  };
  page.on("response", onResp);
  try {
    await page.goto(PROFILE_URL, { waitUntil: "domcontentloaded", timeout: 60000 });
    await sleep(2500);

    // Prefer Replace resume → filechooser; also set hidden input[name=resume]
    let via = null;
    const replaceBtn = page
      .locator("button:has-text('Replace resume'), button:has-text('Upload resume'), button:has-text('Update resume')")
      .first();
    if (await replaceBtn.isVisible({ timeout: 4000 }).catch(() => false)) {
      try {
        const [chooser] = await Promise.all([
          page.waitForEvent("filechooser", { timeout: 8000 }),
          replaceBtn.click(),
        ]);
        await chooser.setFiles(resumePath);
        via = "filechooser";
      } catch (_) {
        /* fall through to input */
      }
    }

    if (!via) {
      const input = page.locator('input[type="file"][name="resume"], input[type="file"]').first();
      if ((await input.count()) === 0) {
        return { ok: false, error: "resume_file_input_not_found" };
      }
      await input.setInputFiles(resumePath);
      via = "input[type=file]";
    }

    // Wait for attachResume success
    const deadline = Date.now() + 25000;
    while (Date.now() < deadline) {
      if (uploads.some((u) => u.status >= 200 && u.status < 300 && /attachResume/i.test(u.url))) {
        break;
      }
      await sleep(500);
    }

    await sleep(1500);
    const resumeName = await page.evaluate(() => {
      const bits = [...document.querySelectorAll("p, span, a, div")]
        .map((el) => (el.textContent || "").trim())
        .filter((t) => /Rafi_Resume|\.docx|\.pdf/i.test(t) && t.length < 80);
      return bits[0] || "";
    });

    const attached = uploads.some(
      (u) => u.status >= 200 && u.status < 300 && /attachResume/i.test(u.url)
    );
    return {
      ok: attached || /Rafi_Resume/i.test(resumeName),
      via,
      resumeName,
      uploads: uploads.slice(0, 8),
      error: attached ? undefined : "attachResume_not_confirmed",
    };
  } catch (e) {
    return { ok: false, error: String(e).slice(0, 300) };
  } finally {
    page.off("response", onResp);
    await page.close().catch(() => {});
  }
}

async function main() {
  const resumePath = process.argv[2] || findResume();
  const browser = await chromium.connectOverCDP(CDP, { timeout: 120000 });
  const context = browser.contexts()[0] || (await browser.newContext());
  const result = await updateFounditProfileResume(context, resumePath);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.ok ? 0 : 1);
}

module.exports = { updateFounditProfileResume, PROFILE_URL };

if (require.main === module) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
