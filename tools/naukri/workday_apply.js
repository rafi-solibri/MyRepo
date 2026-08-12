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
  // pressSequentially keeps React controlled inputs + special chars (e.g. %) reliable.
  if (typeof el.pressSequentially === "function") {
    await el.pressSequentially(String(value), { delay: 25 }).catch(async () => {
      await el.fill(String(value)).catch(() => {});
    });
  } else {
    await el.fill(String(value)).catch(() => {});
  }
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

  // Newer Workday Candidate Home hides email/password behind SSO chooser.
  // Must click "Sign in with email" (or Create Account) before fields mount.
  async function revealEmailAuth() {
    const emailReady = await page
      .locator("[data-automation-id='email']")
      .first()
      .isVisible()
      .catch(() => false);
    if (emailReady) return true;
    for (const label of [
      "Sign in with email",
      "Sign In with Email",
      "Use email",
      "Continue with email",
    ]) {
      if (await clickWorkdayControl(page, label)) {
        await sleep(1500);
        break;
      }
    }
    // Prefer Create Account when the chooser exposes it without email fields yet.
    const stillNoEmail = !(await page
      .locator("[data-automation-id='email']")
      .first()
      .isVisible()
      .catch(() => false));
    if (stillNoEmail) {
      const createLink = page
        .locator(
          "[data-automation-id='createAccountLink'], button:has-text('Create Account'), a:has-text('Create Account')"
        )
        .first();
      if (await createLink.isVisible().catch(() => false)) {
        await createLink.click({ force: true }).catch(() => {});
        await sleep(1500);
      }
    }
    return page
      .locator("[data-automation-id='email']")
      .first()
      .isVisible()
      .catch(() => false);
  }

  async function pageAuthText() {
    return page
      .evaluate(() => (document.body?.innerText || "").slice(0, 2000))
      .catch(() => "");
  }

  async function submitCreateAccount() {
    await typeInto(page, "[data-automation-id='email']", EMAIL);
    await typeInto(page, "[data-automation-id='password']", PASS);
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
    const createSubmit = page
      .locator(
        "[data-automation-id='createAccountSubmitButton'], button[type='submit']:has-text('Create Account')"
      )
      .first();
    if (await createSubmit.isVisible().catch(() => false)) {
      await createSubmit.click({ force: true }).catch(() => {});
    } else {
      await clickWorkdayControl(page, "Create Account");
    }
    await sleep(3500);
  }

  async function submitSignIn() {
    await typeInto(page, "[data-automation-id='email']", EMAIL);
    await typeInto(page, "[data-automation-id='password']", PASS);
    const signInSubmit = page
      .locator(
        "[data-automation-id='signInSubmitButton'], button[type='submit']:has-text('Sign In')"
      )
      .first();
    if (await signInSubmit.isVisible().catch(() => false)) {
      await signInSubmit.click({ force: true }).catch(() => {});
    } else {
      await clickWorkdayControl(page, "Sign In");
    }
    await sleep(3500);
  }

  function authFailureReason(text) {
    if (
      /Password must include|minimum of \d+ characters|password requirements/i.test(
        text || ""
      )
    ) {
      return "ats_password_policy";
    }
    if (
      /wrong email address or password|account might be locked|incorrect|not recognize|invalid email or password/i.test(
        text || ""
      )
    ) {
      return "ats_login_wall";
    }
    return null;
  }

  // Create Account (preferred) or Sign In — requires NAUKRI_WORKDAY_PASSWORD.
  let emailVisible = await revealEmailAuth();
  if (emailVisible) {
    if (!PASS) {
      return { ok: false, reason: "ats_login_wall", url: page.url() };
    }
    // Prefer Create Account when the link/form is available (new Candidate Home).
    const createLink = page
      .locator(
        "[data-automation-id='createAccountLink'], button:has-text('Create Account'), a:has-text('Create Account')"
      )
      .first();
    let verifyVisible = await page
      .locator("[data-automation-id='verifyPassword']")
      .first()
      .isVisible()
      .catch(() => false);
    if (
      !verifyVisible &&
      (await createLink.isVisible().catch(() => false))
    ) {
      await createLink.click({ force: true }).catch(() => {});
      await sleep(1500);
      verifyVisible = await page
        .locator("[data-automation-id='verifyPassword']")
        .first()
        .isVisible()
        .catch(() => false);
    }
    if (verifyVisible) {
      await submitCreateAccount();
      const createText = await pageAuthText();
      const createFail = authFailureReason(createText);
      if (createFail === "ats_password_policy") {
        return { ok: false, reason: createFail, url: page.url() };
      }
      // Account may already exist — fall back to Sign In.
      if (
        createFail === "ats_login_wall" ||
        /already have an account|already exists|sign in instead/i.test(createText)
      ) {
        const signInLink = page
          .locator(
            "[data-automation-id='signInLink'], button:has-text('Sign In'), a:has-text('Sign In')"
          )
          .first();
        if (await signInLink.isVisible().catch(() => false)) {
          await signInLink.click({ force: true }).catch(() => {});
          await sleep(1200);
        }
        await submitSignIn();
      }
    } else {
      await submitSignIn();
      const signText = await pageAuthText();
      const signFail = authFailureReason(signText);
      if (signFail === "ats_login_wall") {
        // Wrong password / no account — try Create Account once.
        const createAfterFail = page
          .locator(
            "[data-automation-id='createAccountLink'], button:has-text('Create Account')"
          )
          .first();
        if (await createAfterFail.isVisible().catch(() => false)) {
          await createAfterFail.click({ force: true }).catch(() => {});
          await sleep(1500);
          if (
            await page
              .locator("[data-automation-id='verifyPassword']")
              .first()
              .isVisible()
              .catch(() => false)
          ) {
            await submitCreateAccount();
            const createText = await pageAuthText();
            const createFail = authFailureReason(createText);
            if (createFail) {
              return { ok: false, reason: createFail, url: page.url() };
            }
          } else {
            return { ok: false, reason: signFail, url: page.url() };
          }
        } else {
          return { ok: false, reason: signFail, url: page.url() };
        }
      }
    }
  }

  // If bounced to /login or still on SSO chooser, reveal email form and Sign In
  // (do NOT click Create Account again — post-create redirects land here).
  {
    const chooserText = await pageAuthText();
    if (/\/login/i.test(page.url()) || /Sign in with email/i.test(chooserText)) {
      emailVisible = await revealEmailAuth();
      if (PASS && emailVisible) {
        await submitSignIn();
      }
      const loginText = await pageAuthText();
      const fail = authFailureReason(loginText);
      if (fail) {
        // Account may not exist on this tenant — one Create Account attempt.
        if (fail === "ats_login_wall") {
          const createLink = page
            .locator("[data-automation-id='createAccountLink']")
            .first();
          if (await createLink.isVisible().catch(() => false)) {
            await createLink.click({ force: true }).catch(() => {});
            await sleep(1200);
            if (
              await page
                .locator("[data-automation-id='verifyPassword']")
                .first()
                .isVisible()
                .catch(() => false)
            ) {
              await submitCreateAccount();
              const createText = await pageAuthText();
              const createFail = authFailureReason(createText);
              if (createFail) {
                return { ok: false, reason: createFail, url: page.url() };
              }
              // After create, tenant often redirects to /login — sign in once more.
              if (/\/login/i.test(page.url()) || /Sign in with email/i.test(createText)) {
                await revealEmailAuth();
                await submitSignIn();
                const again = authFailureReason(await pageAuthText());
                if (again) {
                  return { ok: false, reason: again, url: page.url() };
                }
              }
            } else {
              return { ok: false, reason: fail, url: page.url() };
            }
          } else {
            return { ok: false, reason: fail, url: page.url() };
          }
        } else {
          return { ok: false, reason: fail, url: page.url() };
        }
      }
    }
  }

  // Still on SSO chooser with no email form → wall (do not burn the Next loop)
  {
    const stuckChooser = await page
      .evaluate(() => (document.body?.innerText || "").slice(0, 1500))
      .catch(() => "");
    const hasEmailField = await page
      .locator("[data-automation-id='email']")
      .first()
      .isVisible()
      .catch(() => false);
    if (
      /Sign in with email|Sign in with Google|Sign in with LinkedIn/i.test(
        stuckChooser
      ) &&
      !hasEmailField &&
      !(await page.locator("input[type='file']").count())
    ) {
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
