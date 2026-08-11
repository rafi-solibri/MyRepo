/**
 * Workday apply helper for Naukri company-ATS redirects.
 * Handles Apply → Autofill/Manual → Create Account / Sign In → multi-step Next.
 * Never invents success — thank-you / submitted text only.
 */
"use strict";

const EMAIL = process.env.NAUKRI_APPLY_EMAIL || "rafi.success@gmail.com";
const PASS =
  process.env.NAUKRI_WORKDAY_PASSWORD || process.env.NAUKRI_ATS_PASSWORD || "";

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function clickWorkdayControl(page, ariaOrText) {
  const filter = page
    .locator(`[data-automation-id='click_filter'][aria-label='${ariaOrText}']`)
    .first();
  if (await filter.isVisible().catch(() => false)) {
    await filter.click({ force: true }).catch(() => {});
    return true;
  }
  const byAria = page.locator(`[aria-label='${ariaOrText}']`).first();
  if (await byAria.isVisible().catch(() => false)) {
    await byAria.click({ force: true }).catch(() => {});
    return true;
  }
  const byText = page.getByText(ariaOrText, { exact: false }).first();
  if (await byText.isVisible().catch(() => false)) {
    await byText.click({ force: true }).catch(() => {});
    return true;
  }
  return false;
}

async function typeInto(page, selector, value) {
  const el = page.locator(selector).first();
  if (!(await el.isVisible().catch(() => false))) return false;
  await el.click({ force: true }).catch(() => {});
  await el.fill("").catch(() => {});
  await page.keyboard.type(String(value), { delay: 15 });
  return true;
}

async function dismissCookies(page) {
  for (const t of ["Accept Cookies", "Accept", "Decline"]) {
    const b = page.locator(`button:has-text('${t}')`).first();
    if (await b.isVisible().catch(() => false)) {
      await b.click().catch(() => {});
      await sleep(300);
    }
  }
}

function isSubmittedText(text) {
  return /thank you for appl|application (has been )?submitted|successfully submitted|we have received your application|application received/i.test(
    text || ""
  );
}

/**
 * @returns {{ ok: boolean, reason?: string, url?: string }}
 */
async function completeWorkdayApply(page, resumePath, { maxMs = 3.5 * 60 * 1000 } = {}) {
  const start = Date.now();
  await dismissCookies(page);

  // Open apply menu if on job posting
  const adventure = page
    .locator(
      "a[data-automation-id='adventureButton'], button[data-automation-id='adventureButton']"
    )
    .first();
  if (await adventure.isVisible().catch(() => false)) {
    await adventure.click().catch(() => {});
    await sleep(1500);
  } else {
    await clickWorkdayControl(page, "Apply");
    await sleep(1200);
  }

  const autofill = page.getByText("Autofill with Resume", { exact: false }).first();
  const manual = page.getByText("Apply Manually", { exact: false }).first();
  if (await autofill.isVisible().catch(() => false)) {
    await autofill.click().catch(() => {});
    await sleep(1500);
  } else if (await manual.isVisible().catch(() => false)) {
    await manual.click().catch(() => {});
    await sleep(1500);
  }

  // Create Account (preferred) or Sign In — requires NAUKRI_WORKDAY_PASSWORD.
  const emailVisible = await page
    .locator("[data-automation-id='email']")
    .first()
    .isVisible()
    .catch(() => false);
  if (emailVisible) {
    if (!PASS) {
      return { ok: false, reason: "ats_login_wall", url: page.url() };
    }
    const verifyVisible = await page
      .locator("[data-automation-id='verifyPassword']")
      .first()
      .isVisible()
      .catch(() => false);
    await typeInto(page, "[data-automation-id='email']", EMAIL);
    await typeInto(page, "[data-automation-id='password']", PASS);
    if (verifyVisible) {
      await typeInto(page, "[data-automation-id='verifyPassword']", PASS);
      await page
        .getByText(/Yes, I have read and consent|I acknowledge|I agree|I have read/i)
        .first()
        .click({ force: true })
        .catch(() => {});
      await page
        .locator("[data-automation-id='createAccountCheckbox']")
        .check({ force: true })
        .catch(() => {});
      await sleep(300);
      await clickWorkdayControl(page, "Create Account");
    } else {
      await clickWorkdayControl(page, "Sign In");
    }
    await sleep(3500);
  }

  // If bounced to /login, sign in once
  if (/\/login/i.test(page.url())) {
    await typeInto(page, "[data-automation-id='email']", EMAIL);
    await typeInto(page, "[data-automation-id='password']", PASS);
    await clickWorkdayControl(page, "Sign In");
    await sleep(4000);
    const loginText = await page
      .evaluate(() => (document.body?.innerText || "").slice(0, 1500))
      .catch(() => "");
    if (/wrong email|incorrect|locked|not recognize|invalid/i.test(loginText)) {
      return { ok: false, reason: "ats_login_wall", url: page.url() };
    }
  }

  // Still on auth with password and no progress → wall
  const authText = await page
    .evaluate(() => (document.body?.innerText || "").slice(0, 2000))
    .catch(() => "");
  if (
    (/Create Account\/Sign In|current step 1 of/i.test(authText) ||
      /\/login/i.test(page.url())) &&
    (await page.locator("input[type='password']").count()) > 0 &&
    !(await page.locator("input[type='file']").count())
  ) {
    // one more create attempt if verify field present
    if (
      await page
        .locator("[data-automation-id='verifyPassword']")
        .isVisible()
        .catch(() => false)
    ) {
      await typeInto(page, "[data-automation-id='email']", EMAIL);
      await typeInto(page, "[data-automation-id='password']", PASS);
      await typeInto(page, "[data-automation-id='verifyPassword']", PASS);
      await page
        .getByText(/Yes, I have read and consent|I acknowledge|I agree/i)
        .first()
        .click({ force: true })
        .catch(() => {});
      await clickWorkdayControl(page, "Create Account");
      await sleep(3500);
    }
    const stillAuth =
      /\/login/i.test(page.url()) ||
      ((await page.locator("input[type='password']").count()) > 0 &&
        /Create Account\/Sign In/i.test(
          await page
            .evaluate(() => (document.body?.innerText || "").slice(0, 1200))
            .catch(() => "")
        ));
    if (stillAuth) {
      return { ok: false, reason: "ats_login_wall", url: page.url() };
    }
  }

  while (Date.now() - start < maxMs) {
    const text = await page
      .evaluate(() => (document.body?.innerText || "").slice(0, 3000))
      .catch(() => "");
    if (isSubmittedText(text)) {
      return { ok: true, url: page.url() };
    }

    if (resumePath) {
      const file = page.locator("input[type='file']").first();
      if (await file.count()) {
        await file.setInputFiles(resumePath).catch(() => {});
        await sleep(1500);
      }
    }

    await page
      .evaluate(() => {
        const set = (id, val) => {
          const el = document.querySelector(`[data-automation-id='${id}']`);
          if (!el || el.disabled) return;
          el.focus();
          el.value = val;
          el.dispatchEvent(new Event("input", { bubbles: true }));
          el.dispatchEvent(new Event("change", { bubbles: true }));
        };
        set("legalNameSection_firstName", "Mohammed Abdul Rafi");
        set("legalNameSection_lastName", "Ahmed");
        set("addressSection_city", "Hyderabad");
        set("phone", "8790251698");
        for (const inp of document.querySelectorAll("input,textarea")) {
          if (
            inp.type === "file" ||
            inp.type === "password" ||
            inp.type === "checkbox" ||
            inp.type === "radio" ||
            inp.offsetParent === null
          )
            continue;
          const ctx = (
            (inp.getAttribute("aria-label") || "") +
            " " +
            (inp.getAttribute("data-automation-id") || "") +
            " " +
            (inp.placeholder || "")
          ).toLowerCase();
          if (/email/.test(ctx) && !inp.value) {
            inp.value = "rafi.success@gmail.com";
            inp.dispatchEvent(new Event("input", { bubbles: true }));
          }
          if (/phone|mobile/.test(ctx) && !inp.value) {
            inp.value = "8790251698";
            inp.dispatchEvent(new Event("input", { bubbles: true }));
          }
        }
      })
      .catch(() => {});

    let advanced = false;
    for (const label of ["Next", "Continue", "Submit", "Save and Continue"]) {
      if (await clickWorkdayControl(page, label)) {
        advanced = true;
        await sleep(2200);
        break;
      }
    }
    if (!advanced) {
      const text2 = await page
        .evaluate(() => (document.body?.innerText || "").slice(0, 3000))
        .catch(() => "");
      if (isSubmittedText(text2)) return { ok: true, url: page.url() };
      return {
        ok: false,
        reason: "external_incomplete_or_timeout",
        url: page.url(),
      };
    }
  }
  return { ok: false, reason: "external_incomplete_or_timeout", url: page.url() };
}

module.exports = {
  completeWorkdayApply,
  isSubmittedText,
  EMAIL,
};
