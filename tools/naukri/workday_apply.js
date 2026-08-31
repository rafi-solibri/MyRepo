/**
 * Workday apply helper for Naukri company-ATS redirects.
 * Handles Apply → Autofill/Manual → Create Account / Sign In → multi-step Next.
 * Never invents success — thank-you / submitted text only.
 */
"use strict";

function firstEnv(...keys) {
  for (const k of keys) {
    const v = String(process.env[k] || "").trim();
    if (v) return v;
  }
  return "";
}

const EMAIL = firstEnv("APPLY_EMAIL", "NAUKRI_APPLY_EMAIL", "LINKEDIN_EMAIL");
const PASS = firstEnv(
  "WORKDAY_PASSWORD",
  "ATS_PASSWORD",
  "NAUKRI_WORKDAY_PASSWORD",
  "NAUKRI_ATS_PASSWORD",
  "LINKEDIN_PASSWORD"
);
if (EMAIL) {
  process.env.APPLY_EMAIL = process.env.APPLY_EMAIL || EMAIL;
  process.env.NAUKRI_APPLY_EMAIL = process.env.NAUKRI_APPLY_EMAIL || EMAIL;
}
if (PASS) {
  process.env.WORKDAY_PASSWORD = process.env.WORKDAY_PASSWORD || PASS;
  process.env.ATS_PASSWORD = process.env.ATS_PASSWORD || PASS;
}

function workdayCompliantPassword(raw) {
  let pw = String(raw || "").trim();
  if (
    pw.length >= 12 &&
    /[A-Z]/.test(pw) &&
    /[a-z]/.test(pw) &&
    /[0-9]/.test(pw) &&
    /[^A-Za-z0-9]/.test(pw)
  ) {
    return pw;
  }
  let extra = "";
  if (!/[A-Z]/.test(pw)) extra += "A";
  if (!/[a-z]/.test(pw)) extra += "a";
  if (!/[0-9]/.test(pw)) extra += "1";
  if (!/[^A-Za-z0-9]/.test(pw)) extra += "!";
  pw += extra;
  if (pw.length < 12) {
    pw = (pw + "Aa1!Aa1!Aa1!").slice(0, 12);
  }
  return pw;
}

/** Workday phone fields reject "+91 …" when country code is already India (+91). */
function normalizeWorkdayPhone(raw) {
  let s = String(raw || "").trim();
  s = s.replace(/^\+?\s*91[\s-]*/, "");
  s = s.replace(/[^\d]/g, "");
  if (s.length > 10 && s.startsWith("91")) s = s.slice(2);
  return s.slice(0, 10) || "8790251698";
}

const CREATE_PASS = workdayCompliantPassword(PASS);

/**
 * Classify Workday auth page text. Ignores static "Password Requirements"
 * checklists that always mention "minimum of N characters".
 */
function authFailureReason(text) {
  const t = text || "";
  // Explicit live validation phrases — never the static requirements bullet list.
  if (
    /Password must include|password does not meet|doesn't meet the password|does not meet (the )?password requirements|password is (too short|invalid)|choose a (stronger|different) password|password.*(too weak|not strong)/i.test(
      t
    )
  ) {
    return "ats_password_policy";
  }
  // "Errors Found" banner + password must/does-not — still a live failure.
  if (
    /\berrors?(?:\s+and\s+alerts?)?\s+found\b/i.test(t) &&
    /password.*(does not meet|must include|is required)/i.test(t)
  ) {
    return "ats_password_policy";
  }
  if (
    /wrong email address or password|account might be locked|incorrect email or password|not recognize|invalid email or password/i.test(
      t
    )
  ) {
    return "ats_login_wall";
  }
  return null;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * Blackbaud (and older tenants) have no consent checkbox / copy on Create
 * Account. Requiring a checked box there no-ops submit and leaves Sign In
 * as the only path — which then walls if the tenant account does not exist.
 * Wells Fargo-style pages still require the checkbox/label to be present.
 */
function isCreateAccountConsentRequired({
  checkboxPresent = false,
  consentCopyPresent = false,
} = {}) {
  return Boolean(checkboxPresent || consentCopyPresent);
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
  for (const t of [
    "Accept All Cookies",
    "Accept Cookies",
    "Accept all",
    "Accept",
    "Decline",
  ]) {
    const b = page.locator(`button:has-text('${t}')`).first();
    if (await b.isVisible().catch(() => false)) {
      await b.click({ force: true }).catch(() => {});
      await sleep(400);
    }
  }
  // Workday cookie banner sometimes uses data-automation / link-style controls.
  for (const sel of [
    "[data-automation-id='legalNoticeAcceptButton']",
    "button[id*='cookie' i]",
    "button[class*='cookie' i]",
  ]) {
    const el = page.locator(sel).first();
    if (await el.isVisible().catch(() => false)) {
      await el.click({ force: true }).catch(() => {});
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
  const landingUrl = page.url() || "";
  const landingText = await page
    .evaluate(() => (document.body?.innerText || "").slice(0, 1500))
    .catch(() => "");
  if (
    /maintenance-page|scheduled maintenance|we('ll| will) be back|temporarily unavailable|community\.workday\.com\/maintenance/i.test(
      `${landingUrl} ${landingText}`
    )
  ) {
    return { ok: false, reason: "job_unavailable", url: landingUrl };
  }
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
  const startApp = page.getByText("Start Your Application", { exact: false }).first();
  if (await startApp.isVisible().catch(() => false)) {
    // Some tenants show chooser under this heading — click Autofill/Manual below.
  }
  if (await autofill.isVisible().catch(() => false)) {
    await autofill.click({ force: true }).catch(() => {});
    await sleep(2000);
  }
  // If Autofill did not leave the chooser (cookie overlay / dead click), try Manual.
  const stillChooser = await page
    .getByText("Autofill with Resume", { exact: false })
    .first()
    .isVisible()
    .catch(() => false);
  if (stillChooser && (await manual.isVisible().catch(() => false))) {
    await manual.click({ force: true }).catch(() => {});
    await sleep(2000);
  } else if (
    !(await autofill.isVisible().catch(() => false)) &&
    (await manual.isVisible().catch(() => false))
  ) {
    await manual.click({ force: true }).catch(() => {});
    await sleep(1500);
  }
  await dismissCookies(page);

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

  async function ensureCreateAccountConsent() {
    // Wells Fargo / newer tenants: "Yes, I have reviewed the above and consent…"
    // Older copy: "Yes, I have read and consent…". Playwright .check() alone often
    // does not toggle Workday's styled checkbox — click the label (or input).
    const consentRe =
      /Yes, I have reviewed the above and consent|Yes, I have read and consent|I acknowledge|I agree|I have read|consent to the terms/i;
    const label = page.locator("label").filter({ hasText: consentRe }).first();
    const labelVisible = await label.isVisible().catch(() => false);
    if (labelVisible) {
      await label.click({ force: true }).catch(() => {});
      await sleep(200);
    } else {
      const copy = page.getByText(consentRe).first();
      if (await copy.isVisible().catch(() => false)) {
        await copy.click({ force: true }).catch(() => {});
        await sleep(200);
      }
    }
    const cb = page.locator("[data-automation-id='createAccountCheckbox']").first();
    const checkboxPresent = (await cb.count().catch(() => 0)) > 0;
    const consentCopyPresent =
      labelVisible ||
      (await page.getByText(consentRe).first().isVisible().catch(() => false));
    if (!isCreateAccountConsentRequired({ checkboxPresent, consentCopyPresent })) {
      return true;
    }
    if (checkboxPresent) {
      const checked = await cb.isChecked().catch(() => false);
      if (!checked) {
        await cb.click({ force: true }).catch(() => {});
        await sleep(200);
      }
      if (!(await cb.isChecked().catch(() => false))) {
        await cb.check({ force: true }).catch(() => {});
        await sleep(200);
      }
      return cb.isChecked().catch(() => false);
    }
    return false;
  }

  async function submitCreateAccount() {
    await typeInto(page, "[data-automation-id='email']", EMAIL);
    await typeInto(page, "[data-automation-id='password']", CREATE_PASS);
    await typeInto(page, "[data-automation-id='verifyPassword']", CREATE_PASS);
    const consented = await ensureCreateAccountConsent();
    if (!consented) {
      // Do not burn submit without consent — Workday silently stays on Create Account.
      return;
    }
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

  async function goSignInFromCreate() {
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
      // Password-policy on Create Account: still try Sign In (tenant account may
      // already exist from a prior apply; static requirements text also used to
      // false-trigger before errOnly scoping — never hard-stop the ATS path).
      if (
        createFail === "ats_password_policy" ||
        createFail === "ats_login_wall" ||
        /already have an account|already exists|sign in instead/i.test(createText)
      ) {
        await goSignInFromCreate();
        const afterSign = authFailureReason(await pageAuthText());
        if (afterSign) {
          return { ok: false, reason: afterSign, url: page.url() };
        }
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
  const earlyAuthFail = authFailureReason(authText);
  if (earlyAuthFail) {
    return { ok: false, reason: earlyAuthFail, url: page.url() };
  }
  if (
    (/Create Account\/Sign In|current step 1 of/i.test(authText) ||
      /\/login/i.test(page.url()) ||
      (/Sign In/i.test(authText) &&
        (await page.locator("[data-automation-id='email']").count()) > 0)) &&
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
      await submitCreateAccount();
      await sleep(1500);
    }
    const stillAuthText = await page
      .evaluate(() => (document.body?.innerText || "").slice(0, 1500))
      .catch(() => "");
    const stillFail = authFailureReason(stillAuthText);
    if (stillFail) {
      return { ok: false, reason: stillFail, url: page.url() };
    }
    const stillAuth =
      /\/login/i.test(page.url()) ||
      ((await page.locator("input[type='password']").count()) > 0 &&
        /Create Account\/Sign In|Don't have an account yet/i.test(stillAuthText));
    if (stillAuth) {
      return { ok: false, reason: "ats_login_wall", url: page.url() };
    }
  }

  async function fillFieldInput(formFieldId, value) {
    // Prefer the nested input. A union with the wrapper matches the wrapper
    // first in document order, so fills silently no-op on Broadcom/Workday.
    let el = page.locator(`[data-automation-id='${formFieldId}'] input`).first();
    if (!(await el.isVisible().catch(() => false))) {
      el = page.locator(`[data-automation-id='${formFieldId}']`).first();
    }
    if (!(await el.isVisible().catch(() => false))) return false;
    await el.click({ force: true }).catch(() => {});
    await el.fill("").catch(() => {});
    if (typeof el.pressSequentially === "function") {
      await el.pressSequentially(String(value), { delay: 15 }).catch(async () => {
        await el.fill(String(value)).catch(() => {});
      });
    } else {
      await el.fill(String(value)).catch(() => {});
    }
    return true;
  }

  async function pickPromptOption(formFieldId, optionPatterns) {
    const root = page.locator(`[data-automation-id='${formFieldId}']`).first();
    if (!(await root.isVisible().catch(() => false))) return false;
    const already = ((await root.innerText().catch(() => "")) || "").trim();
    if (
      (/\d+\s+item selected|1 item selected/i.test(already) &&
        !/0 items selected/i.test(already)) ||
      (/^(BA|BS|MA|MS|MBA|PhD|B\.?Tech)/im.test(already) &&
        !/Select One/i.test(already))
    ) {
      return true;
    }
    const listBtn = root.locator("button[aria-haspopup='listbox']").first();
    const opener = (await listBtn.isVisible().catch(() => false))
      ? listBtn
      : root
          .locator(
            "[data-automation-id='multiselectInputContainer'], [data-automation-id='selectWidget'], button, input"
          )
          .first();
    await opener.click({ force: true }).catch(() => {});
    await sleep(900);
    for (const re of optionPatterns) {
      const leaf = page
        .locator(
          "[data-uxi-widget-type='multiselectlistitem'], [data-automation-id='promptLeafNode'], [role='option'], [data-automation-id='promptOption']"
        )
        .filter({ hasText: re })
        .first();
      if (!(await leaf.isVisible().catch(() => false))) continue;
      const box = await leaf.boundingBox().catch(() => null);
      if (box) {
        await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
      } else {
        await leaf.click({ force: true }).catch(() => {});
      }
      await sleep(500);
      // Native listbox: typing the short code (e.g. BS) + Enter is reliable.
      if (/Select One/i.test((await root.innerText().catch(() => "")) || "")) {
        const hint = String(re.source || re)
          .replace(/[\^\$\\]/g, "")
          .slice(0, 8);
        if (hint) {
          await page.keyboard.type(hint, { delay: 40 }).catch(() => {});
          await page.keyboard.press("Enter").catch(() => {});
          await sleep(400);
        }
      }
      break;
    }
    await page.keyboard.press("Escape").catch(() => {});
    await sleep(300);
    return true;
  }

  async function fillMyInformation() {
    // Previously worked here? → No
    const prev = page.locator(
      "[data-automation-id='formField-candidateIsPreviousWorker']"
    );
    if (await prev.isVisible().catch(() => false)) {
      await prev.getByText(/^No$/i).first().click({ force: true }).catch(() => {});
    }

    // Prefer India when Country shows United States / Select One.
    const country = page
      .locator(
        "[data-automation-id='formField-country'] button, [data-automation-id='countryDropdown']"
      )
      .first();
    if (await country.isVisible().catch(() => false)) {
      const cText = ((await country.innerText().catch(() => "")) || "").trim();
      if (/united states|select one|^$/i.test(cText) && !/india/i.test(cText)) {
        await country.click({ force: true }).catch(() => {});
        await sleep(600);
        const india = page.getByText(/^India$/i).first();
        if (await india.isVisible().catch(() => false)) {
          await india.click({ force: true }).catch(() => {});
          await sleep(800);
        } else {
          await page.keyboard.press("Escape").catch(() => {});
        }
      }
    }

    // Title-case given/family only — multi-word Given Name(s) with 3+ capitals
    // triggers Workday "verify capitalization" alerts (Broadcom etc.).
    const firstName = "Mohammed";
    const lastName = "Ahmed";
    const phone = normalizeWorkdayPhone("8790251698");

    await fillFieldInput("legalNameSection_firstName", firstName);
    await fillFieldInput("legalNameSection_lastName", lastName);
    await fillFieldInput("formField-legalName--firstName", firstName);
    await fillFieldInput("formField-legalName--lastName", lastName);
    await fillFieldInput("addressSection_city", "Hyderabad");
    await fillFieldInput("formField-addressLine1", "Hyderabad, Telangana");
    await fillFieldInput("formField-city", "Hyderabad");
    await fillFieldInput("formField-postalCode", "500032");
    await fillFieldInput("phone", phone);
    await fillFieldInput("formField-phoneNumber", phone);

    await pickPromptOption("formField-phoneType", [/^Mobile$/i, /Cell/i, /Mobile/i]);
    await pickPromptOption("formField-countryPhoneCode", [
      /\+91/,
      /India/i,
    ]);
    await pickPromptOption("formField-source", [
      /^Job Board$/i,
      /Naukri/i,
      /Internet/i,
      /Online/i,
      /Other/i,
      /Company Websites/i,
    ]);

    // Aria-label fallbacks — always overwrite autofill ALL-CAPS / +91 phone.
    for (const [re, val] of [
      [/given name|first name/i, firstName],
      [/family name|last name/i, lastName],
      [/^city$/i, "Hyderabad"],
      [/postal|zip/i, "500032"],
      [/phone number|mobile/i, phone],
      [/email/i, EMAIL],
    ]) {
      const el = page.getByLabel(re).first();
      if (await el.isVisible().catch(() => false)) {
        const cur = await el.inputValue().catch(() => "");
        if (cur !== val) {
          await el.fill("").catch(() => {});
          await el.fill(val).catch(() => {});
        }
      }
    }
  }

  async function selectListboxShort(formFieldId, typeText, acceptRe, rootLoc) {
    const root = rootLoc || page.locator(`[data-automation-id='${formFieldId}']`).first();
    if (!(await root.isVisible().catch(() => false))) return false;
    const cur = ((await root.innerText().catch(() => "")) || "").trim();
    if (acceptRe.test(cur) && !/Select One/i.test(cur)) return true;
    const btn = root.locator("button[aria-haspopup='listbox'], button").first();
    if (!(await btn.isVisible().catch(() => false))) return false;
    await btn.click({ force: true }).catch(() => {});
    await sleep(500);
    // Broadcom-style coded degrees: "70-Bachelor"
    const opt = page
      .locator("[role='option']")
      .filter({ hasText: acceptRe })
      .first();
    if (await opt.isVisible().catch(() => false)) {
      await opt.click({ force: true }).catch(() => {});
      await sleep(400);
    } else {
      await page.keyboard.type(String(typeText), { delay: 40 }).catch(() => {});
      await page.keyboard.press("Enter").catch(() => {});
      await sleep(500);
    }
    await page.keyboard.press("Escape").catch(() => {});
    const after = ((await root.innerText().catch(() => "")) || "").trim();
    return acceptRe.test(after) && !/Select One/i.test(after);
  }

  /**
   * Autofill often leaves Company blank while stuffing the employer into Role Description.
   * Fill every empty companyName (+ location) from title / description heuristics.
   */
  async function fillWorkExperience() {
    const companyInputs = page.locator(
      "[data-automation-id='formField-companyName'] input[name='companyName'], input[name='companyName']"
    );
    const n = await companyInputs.count().catch(() => 0);
    if (!n) return;

    const TITLE_COMPANY = [
      [/nemetschek|solibri/i, "Nemetschek"],
      [/unitedhealth|uhg/i, "UnitedHealth Group"],
      [/epam/i, "EPAM Systems"],
      [/cdk/i, "ADP / CDK Global"],
      [/^adp$/i, "ADP"],
      [/ncr/i, "NCR"],
      [/infosys/i, "Infosys"],
    ];

    for (let i = 0; i < n; i++) {
      const el = companyInputs.nth(i);
      if (!(await el.isVisible().catch(() => false))) continue;
      let cur = ((await el.inputValue().catch(() => "")) || "").trim();
      if (cur) continue;

      const meta = await el
        .evaluate((input) => {
          const titleId = String(input.id || "").replace(/companyName$/i, "jobTitle");
          const titleEl = titleId ? document.getElementById(titleId) : null;
          const title = (titleEl?.value || "").trim();
          const descId = String(input.id || "").replace(/companyName$/i, "roleDescription");
          const descEl = descId ? document.getElementById(descId) : null;
          const desc = (descEl?.value || "").trim();
          const firstLine = (desc.split("\n")[0] || "").trim();
          return { title, firstLine, desc };
        })
        .catch(() => ({ title: "", firstLine: "", desc: "" }));

      let company = "";
      if (
        meta.firstLine &&
        meta.firstLine.length < 80 &&
        !/^·|^-|^•/.test(meta.firstLine) &&
        !/architected|developed|led |optimized|engineered/i.test(meta.firstLine)
      ) {
        company = meta.firstLine;
      }
      for (const [re, name] of TITLE_COMPANY) {
        if (re.test(company) || re.test(meta.desc) || re.test(meta.title)) {
          company = name;
          break;
        }
      }
      if (!company || /lead|engineer|developer|architect/i.test(company)) {
        if (/senior developer/i.test(meta.title)) company = "ADP / CDK Global";
        else if (/systems engineer/i.test(meta.title)) company = "Infosys";
        else if (/technical lead|technical architect/i.test(meta.title))
          company = "NCR";
        else company = company && company.length < 60 ? company : "NCR";
      }

      await el.click({ force: true }).catch(() => {});
      await el.fill("").catch(() => {});
      await el.fill(String(company)).catch(() => {});
      await sleep(200);
    }

    const locInputs = page.locator(
      "[data-automation-id='formField-location'] input[name='location'], input[name='location']"
    );
    const ln = await locInputs.count().catch(() => 0);
    for (let i = 0; i < ln; i++) {
      const el = locInputs.nth(i);
      if (!(await el.isVisible().catch(() => false))) continue;
      const cur = ((await el.inputValue().catch(() => "")) || "").trim();
      if (!cur) {
        await el.fill("Hyderabad").catch(() => {});
      }
    }
  }

  async function fillEducation() {
    const schoolInputs = page.locator(
      "[data-automation-id='formField-schoolName'] input"
    );
    const schoolCount = await schoolInputs.count().catch(() => 0);
    const SCHOOL = "V.R. Siddhartha Engineering College";

    for (let i = 0; i < schoolCount; i++) {
      const el = schoolInputs.nth(i);
      if (!(await el.isVisible().catch(() => false))) continue;
      const cur = ((await el.inputValue().catch(() => "")) || "").trim();
      if (/Siddhartha|Acharya Nagarjuna|University|College/i.test(cur)) continue;
      await el.click({ force: true }).catch(() => {});
      await el.fill("").catch(() => {});
      await el.fill(SCHOOL).catch(() => {});
      await sleep(600);
      const schoolOpt = page
        .locator("[data-automation-id='promptOption']")
        .filter({ hasText: /Siddhartha/i })
        .first();
      if (await schoolOpt.isVisible().catch(() => false)) {
        await schoolOpt.click({ force: true }).catch(() => {});
      } else {
        await page.keyboard.press("Enter").catch(() => {});
      }
      await page.keyboard.press("Escape").catch(() => {});
      await sleep(300);
    }

    // Legacy single-root path when inputs are not plain text.
    if (!schoolCount) {
      const schoolRoot = page.locator("[data-automation-id='formField-schoolName']");
      if (await schoolRoot.first().isVisible().catch(() => false)) {
        const schoolText = ((await schoolRoot.first().innerText().catch(() => "")) || "");
        if (!/Siddhartha|Acharya Nagarjuna|University|College/i.test(schoolText) || /required/i.test(schoolText)) {
          await fillFieldInput("formField-schoolName", SCHOOL);
        }
      }
    }

    // Fill every degree Select One (Broadcom has 2 education rows; options like "70-Bachelor").
    const degreeRoots = page.locator("[data-automation-id='formField-degree']");
    const degreeCount = await degreeRoots.count().catch(() => 0);
    for (let i = 0; i < Math.max(degreeCount, 1); i++) {
      const root = degreeCount ? degreeRoots.nth(i) : degreeRoots.first();
      if (!(await root.isVisible().catch(() => false))) continue;
      const cur = ((await root.innerText().catch(() => "")) || "").trim();
      if (
        /\bBS\b|Bachelor|B\.?\s*Tech|70-Bachelor/i.test(cur) &&
        !/Select One/i.test(cur)
      ) {
        continue;
      }
      const ok = await selectListboxShort(
        "formField-degree",
        "70-Bachelor",
        /70-Bachelor|\bBS\b|Bachelor/i,
        root
      );
      if (!ok) {
        await pickPromptOption("formField-degree", [
          /70-Bachelor/i,
          /^BS$/i,
          /^Bachelor of Science/i,
          /^BA$/i,
          /B\.?\s*Tech/i,
          /^Bachelor/i,
        ]);
      }
    }

    const fosRoots = page.locator("[data-automation-id='formField-fieldOfStudy']");
    const fosCount = await fosRoots.count().catch(() => 0);
    for (let i = 0; i < Math.max(fosCount, 1); i++) {
      const root = fosCount ? fosRoots.nth(i) : fosRoots.first();
      if (!(await root.isVisible().catch(() => false))) continue;
      const cur = ((await root.innerText().catch(() => "")) || "").trim();
      if (/Information Technology|Computer Science/i.test(cur) && !/0 items selected/i.test(cur)) {
        continue;
      }
      await pickPromptOption("formField-fieldOfStudy", [
        /Information Technology/i,
        /Computer Science/i,
        /Computer Engineering/i,
        /IT\b/i,
      ]);
    }
  }

  async function fillVoluntaryAndQuestions() {
    // Prefer-not-to-answer / decline self-ID where present.
    for (const re of [
      /Prefer not to answer/i,
      /I Decline/i,
      /Decline To Self Identify/i,
      /^No$/i,
    ]) {
      const opts = page.getByText(re);
      const n = await opts.count().catch(() => 0);
      for (let i = 0; i < Math.min(n, 8); i++) {
        const el = opts.nth(i);
        if (await el.isVisible().catch(() => false)) {
          await el.click({ force: true }).catch(() => {});
          await sleep(200);
        }
      }
    }
    // Common Yes/No application questions — answer No for prior worker / conviction, Yes for work auth.
    const pairs = [
      [/authorized to work|legally authorized/i, /^Yes$/i],
      [/require sponsorship|visa sponsorship/i, /^No$/i],
      [/previously (worked|employed)|former employee|conflict of interest/i, /^No$/i],
      [/relatives? (employed|work)/i, /^No$/i],
      [/criminal|conviction|felony/i, /^No$/i],
      [/export control|ITAR/i, /^No$/i],
    ];
    for (const [qRe, aRe] of pairs) {
      const block = page.locator("fieldset, div, li").filter({ hasText: qRe }).first();
      if (!(await block.isVisible().catch(() => false))) continue;
      const ans = block.getByText(aRe).first();
      if (await ans.isVisible().catch(() => false)) {
        await ans.click({ force: true }).catch(() => {});
        await sleep(200);
      }
    }
  }

  async function clickAdvance() {
    const footerNext = page
      .locator(
        "[data-automation-id='pageFooterNextButton'], button[data-automation-id='bottom-navigation-next-button']"
      )
      .first();
    if (await footerNext.isVisible().catch(() => false)) {
      await footerNext.click({ force: true }).catch(() => {});
      return true;
    }
    for (const label of ["Save and Continue", "Next", "Continue", "Submit"]) {
      if (await clickWorkdayControl(page, label)) return true;
    }
    return false;
  }

  while (Date.now() - start < maxMs) {
    const text = await page
      .evaluate(() => (document.body?.innerText || "").slice(0, 3000))
      .catch(() => "");
    if (isSubmittedText(text)) {
      return { ok: true, url: page.url() };
    }

    // Autofill step often shows a bare "Loading" spinner — wait, do not bail.
    if (/^\s*Loading\b|\bLoading\s*$/m.test(text.slice(0, 900)) && !/First Name|My Information|How Did You Hear/i.test(text)) {
      await sleep(2000);
      continue;
    }

    if (resumePath) {
      const file = page.locator("input[type='file']").first();
      // Avoid re-uploading the same resume every loop (SS&C stacks duplicates).
      const alreadyUploaded = /successfully uploaded|Rafi_Resume\.docx/i.test(text);
      if ((await file.count()) && !alreadyUploaded) {
        await file.setInputFiles(resumePath).catch(() => {});
        await sleep(1500);
      }
    }

    await fillMyInformation();
    await fillWorkExperience();
    await fillEducation();
    if (/Voluntary Disclosure|Application Question|Self Identify|Review/i.test(text)) {
      await fillVoluntaryAndQuestions();
    }

    let advanced = await clickAdvance();
    if (advanced) {
      await sleep(2500);
      continue;
    }
    const text2 = await page
      .evaluate(() => (document.body?.innerText || "").slice(0, 3000))
      .catch(() => "");
    if (isSubmittedText(text2)) return { ok: true, url: page.url() };
    // Still loading / animating — keep waiting within budget.
    if (/\bLoading\b/i.test(text2.slice(0, 900))) {
      await sleep(2000);
      continue;
    }
    // Validation errors: keep filling within budget instead of bailing once.
    if (
      /Errors(?:\s+and\s+Alerts)?\s+Found|is required and must have a value|Enter a valid format for Phone/i.test(
        text2
      )
    ) {
      await sleep(800);
      continue;
    }
    return {
      ok: false,
      reason: "external_incomplete_or_timeout",
      url: page.url(),
    };
  }
  return { ok: false, reason: "external_incomplete_or_timeout", url: page.url() };
}

module.exports = {
  completeWorkdayApply,
  isSubmittedText,
  workdayCompliantPassword,
  normalizeWorkdayPhone,
  authFailureReason,
  isCreateAccountConsentRequired,
  EMAIL,
};
