/**
 * Node ATS completer for Playwright pages (Instahyre / Cutshort / Foundit).
 * Workday uses the durable Naukri helper; other hosts get resume + questions + Next.
 */
"use strict";

const { completeWorkdayApply, isSubmittedText } = require("../naukri/workday_apply");
const { fillCommonAtsQuestions } = require("../naukri/ats_form");

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function looksWorkday(page) {
  const url = page.url() || "";
  if (/community\.workday\.com\/maintenance|maintenance-page/i.test(url)) return false;
  if (/myworkdayjobs|myworkdaysite|workdayjobs/i.test(url)) return true;
  return page
    .evaluate(
      () =>
        /Autofill with Resume|Apply Manually/i.test(document.body?.innerText || "") ||
        !!document.querySelector("[data-automation-id]")
    )
    .catch(() => false);
}

function isUnavailable(url, text) {
  return /maintenance-page|scheduled maintenance|we('ll| will) be back|temporarily unavailable|community\.workday\.com\/maintenance|no longer accepting applications|position has been filled|job is no longer available|requisition is closed/i.test(
    `${url || ""} ${text || ""}`
  );
}

async function preferGuestApply(page) {
  for (const sel of [
    "a:has-text('Apply without Indeed')",
    "button:has-text('Apply without Indeed')",
    "a:has-text('Apply manually')",
    "button:has-text('Apply manually')",
    "a:has-text(\"I'm interested\")",
    "button:has-text(\"I'm interested\")",
    "a:has-text('Apply for this job online')",
    "button:has-text('Apply for this job online')",
    "a:has-text('Apply for this job')",
    "button:has-text('Apply for this job')",
    "a:has-text('Apply Now')",
    "button:has-text('Apply Now')",
    "a:has-text('Apply')",
    "button:has-text('Apply')",
  ]) {
    const b = page.locator(sel).first();
    if (await b.isVisible().catch(() => false)) {
      const label = ((await b.innerText().catch(() => "")) || "").trim();
      const href = ((await b.getAttribute("href").catch(() => "")) || "").trim();
      if (/oneclick|with indeed|with linkedin|with google|indeed\.com\/oauth/i.test(`${label} ${href}`)) {
        continue;
      }
      if (/sign in|log in|applied/i.test(label) && !/^apply/i.test(label)) continue;
      await b.click().catch(() => {});
      await sleep(1200);
      return true;
    }
  }
  return false;
}

async function completeExternalPage(page, resumePath, { maxMs = 6.5 * 60 * 1000 } = {}) {
  const start = Date.now();
  const landing = `${page.url() || ""} ${await page.evaluate(() => (document.body?.innerText || "").slice(0, 1200)).catch(() => "")}`;
  if (isUnavailable(page.url(), landing)) {
    return { ok: false, reason: "job_unavailable", url: page.url() };
  }
  if (await looksWorkday(page)) {
    return completeWorkdayApply(page, resumePath, {
      maxMs: Math.max(60_000, maxMs - (Date.now() - start)),
    });
  }
  let noAdvance = 0;
  await preferGuestApply(page);
  while (Date.now() - start < maxMs && noAdvance < 6) {
    const url = page.url() || "";
    if (/b2clogin\.com|login\.microsoftonline|accounts\.google\.com|okta\.com|secure\.indeed\.com\/(?:auth|oauth)|oneclick\.smartrecruiters/i.test(url)) {
      return { ok: false, reason: "ats_login_wall", url };
    }
    const text = await page
      .evaluate(() => (document.body?.innerText || "").slice(0, 2500))
      .catch(() => "");
    if (isSubmittedText(text)) return { ok: true, url };
    const challenge = await page
      .locator(
        "iframe[src*='recaptcha/bframe'], iframe[src*='hcaptcha.com'], iframe[src*='challenges.cloudflare.com']"
      )
      .first()
      .isVisible()
      .catch(() => false);
    if (challenge) return { ok: false, reason: "captcha_wall", url };

    if (isUnavailable(url, text)) return { ok: false, reason: "job_unavailable", url };
    await preferGuestApply(page);
    if (resumePath) {
      const files = page.locator("input[type='file']");
      const n = await files.count();
      for (let i = 0; i < Math.min(n, 3); i++) {
        await files.nth(i).setInputFiles(resumePath).catch(() => {});
      }
    }
    await fillCommonAtsQuestions(page).catch(() => {});
    for (const sel of [
      "button:has-text('Submit application')",
      "button:has-text('Submit')",
      "button:has-text('Next')",
      "button:has-text('Continue')",
      "button:has-text('Save and Continue')",
      "input[type='submit']",
    ]) {
      const b = page.locator(sel).first();
      if (await b.isVisible().catch(() => false)) {
        const label = ((await b.innerText().catch(() => "")) || "").trim();
        if (/sign in|log in|create account/i.test(label)) continue;
        await b.click({ force: true }).catch(() => {});
        noAdvance = 0;
        await sleep(1600);
        break;
      }
    }
    const after = await page
      .evaluate(() => (document.body?.innerText || "").slice(0, 2500))
      .catch(() => "");
    if (isSubmittedText(after)) return { ok: true, url: page.url() };
    noAdvance += 1;
    await sleep(1000);
  }
  return { ok: false, reason: "external_incomplete_or_timeout", url: page.url() };
}

module.exports = { completeExternalPage, looksWorkday };
