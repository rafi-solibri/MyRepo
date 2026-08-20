/**
 * Upload a (usually JD-tailored) resume to the Cutshort talent-card profile.
 * Dashboard → "Update resume" → hidden file input (pdf/doc/docx).
 */
"use strict";

const fs = require("fs");

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * @param {import('playwright-core').Page} page
 * @param {string} resumePath
 * @returns {Promise<{ ok: boolean, reason?: string, via?: string }>}
 */
async function uploadCutshortProfileResume(page, resumePath) {
  if (!resumePath || !fs.existsSync(resumePath)) {
    return { ok: false, reason: "resume_missing" };
  }

  await page.goto("https://cutshort.io/profile/candidate-dashboard", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });

  // Talent card is client-rendered — wait for the Update resume CTA.
  const updateBtn = page.getByRole("button", { name: /^update resume$/i });
  try {
    await updateBtn.first().waitFor({ state: "visible", timeout: 45000 });
  } catch {
    const body = await page.evaluate(() => document.body?.innerText || "");
    if (/candidate login|log in to continue/i.test(body) || /redirect_url=%2Fprofile/i.test(page.url())) {
      return { ok: false, reason: "login_required" };
    }
    if (!/Update resume/i.test(body)) {
      return { ok: false, reason: "update_resume_button_missing" };
    }
  }

  // Path A: filechooser while clicking Update resume
  try {
    const [chooser] = await Promise.all([
      page.waitForEvent("filechooser", { timeout: 10000 }),
      updateBtn.first().click({ timeout: 10000 }),
    ]);
    await chooser.setFiles(resumePath);
    await sleep(3000);
    return { ok: true, via: "filechooser" };
  } catch {
    /* fall through — some builds use a hidden input instead */
  }

  // Path B: click then setInputFiles on any file input
  await updateBtn.first().click({ timeout: 10000 }).catch(() => {});
  await sleep(1500);

  const inputs = page.locator('input[type="file"]');
  const n = await inputs.count().catch(() => 0);
  if (!n) {
    // Last resort: any element whose leaf text is Update resume
    await page.evaluate(() => {
      const el = [...document.querySelectorAll("button,a,div,span")].find((e) =>
        /^update resume$/i.test((e.innerText || "").trim())
      );
      el?.click();
    });
    await sleep(1500);
  }

  const n2 = await page.locator('input[type="file"]').count().catch(() => 0);
  if (!n2) return { ok: false, reason: "resume_file_input_not_found" };

  let set = false;
  for (let i = 0; i < n2; i++) {
    try {
      await page.locator('input[type="file"]').nth(i).setInputFiles(resumePath, { timeout: 20000 });
      set = true;
      break;
    } catch {
      /* try next */
    }
  }
  if (!set) return { ok: false, reason: "setInputFiles_failed" };
  await sleep(3000);

  const after = await page.evaluate(() => (document.body?.innerText || "").slice(0, 2500));
  if (/failed to upload|upload failed|unsupported (file|format)/i.test(after)) {
    return { ok: false, reason: "upload_error_banner", via: "input" };
  }
  return { ok: true, via: "input" };
}

module.exports = { uploadCutshortProfileResume };
