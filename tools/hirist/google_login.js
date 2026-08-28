#!/usr/bin/env node
/**
 * Hirist login via Google / Gmail SSO on the CDP Chrome profile.
 *
 * Prefer Continue with Google (GOOGLE_EMAIL / LINKEDIN_EMAIL). When Google shows
 * 2FA / authenticator, print ASK_OWNER_GOOGLE_2FA in the agent chat and wait.
 * Email verification codes: try tools/ats/email_otp.py (Gmail CDP / IMAP).
 *
 * Usage:
 *   node tools/hirist/google_login.js
 *   node tools/hirist/google_login.js --wait 300
 */
"use strict";

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const CDP = process.env.HIRIST_CDP || "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "../..");
const LOGIN = "https://www.hirist.tech/login";
const APPLIED = "https://www.hirist.tech/applied-jobs";
const GMAIL = process.env.GOOGLE_EMAIL || process.env.LINKEDIN_EMAIL || process.env.APPLY_EMAIL || "";
const WAIT_SEC = Number(
  process.env.HIRIST_GOOGLE_LOGIN_WAIT_SEC ||
    process.env.GOOGLE_2FA_WAIT_SEC ||
    "300"
);

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i === -1 || i + 1 >= process.argv.length) return null;
  return process.argv[i + 1];
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function passwordCandidates() {
  const keys = ["GOOGLE_PASSWORD", "LINKEDIN_PASSWORD", "GMAIL_PASSWORD"];
  const out = [];
  for (const k of keys) {
    const v = (process.env[k] || "").trim();
    if (v && !out.includes(v)) out.push(v);
  }
  return out;
}

function isHiristAuthCookieName(name) {
  return /^(HIRIST_CK1|hirist_seeker_enc|token|access_token|auth_token|hjuid|userToken|JSID)$/i.test(
    String(name || "")
  );
}

function isGooglePasswordChallenge(url, body) {
  const u = String(url || "");
  const text = String(body || "");
  if (/signin\/challenge\/pwd/i.test(u)) return true;
  if (/accounts\.google\.com/i.test(u) && /enter your password|wrong password/i.test(text)) {
    return true;
  }
  return false;
}

function isGoogle2faChallenge(url, body) {
  const u = String(url || "");
  const text = String(body || "");
  if (isGooglePasswordChallenge(u, text)) return false;
  if (/signin\/challenge\/(totp|ipp|az|sk|iap|selection)/i.test(u)) return true;
  return /2[- ]step|authenticator|verification code|check your phone|tap yes|confirm it.?s you/i.test(
    `${u}\n${text}`
  );
}

function prompt2faBanner(detail) {
  const wait = Number(argValue("--wait") || WAIT_SEC);
  const msg = [
    "",
    "================================================================",
    "ASK_OWNER_GOOGLE_2FA (hirist)",
    "================================================================",
    "Google is asking for a 2-factor / authenticator / phone prompt code.",
    "1) Open Google Authenticator (or the Google phone prompt) on your mobile NOW.",
    "2) Type the 6-digit code into the focused Chrome tab (or tap Yes on the phone).",
    "3) Leave this Cursor chat open — the agent is waiting and will continue after success.",
    `Waiting up to ${wait}s for the challenge to clear…`,
    detail ? `Detail: ${String(detail).slice(0, 200)}` : "",
    "================================================================",
    "",
  ]
    .filter(Boolean)
    .join("\n");
  console.error(msg);
  console.log(msg);
}

function runPython2faWait(waitSec) {
  const py = `
import os, sys
sys.path.insert(0, ${JSON.stringify(ROOT)})
from playwright.sync_api import sync_playwright
from tools.google_2fa_prompt import is_google_2fa_challenge, wait_owner_google_2fa

cdp = os.environ.get("HIRIST_CDP", "http://127.0.0.1:9222")
wait = int(${Number(waitSec)})
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(cdp)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = None
    for pg in ctx.pages:
        u = pg.url or ""
        if "accounts.google.com" in u or "hirist.tech" in u:
            page = pg
            break
    if page is None:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
    if is_google_2fa_challenge(page):
        ok = wait_owner_google_2fa(page, portal="hirist", wait_sec=wait)
        print("2fa_ok" if ok else "2fa_timeout")
        sys.exit(0 if ok else 6)
    print("no_2fa")
`;
  const r = spawnSync("python3", ["-c", py], {
    cwd: ROOT,
    env: process.env,
    encoding: "utf8",
    timeout: (Number(waitSec) + 60) * 1000,
  });
  if (r.stdout) process.stdout.write(r.stdout);
  if (r.stderr) process.stderr.write(r.stderr);
  return r.status === 0;
}

function tryEmailOtpFill() {
  const script = path.join(ROOT, "tools", "ats", "email_otp.py");
  if (!fs.existsSync(script)) return false;
  // Best-effort: module is import-driven; daily ATS complete already wires it.
  // Here we only signal that mailbox OTP should be preferred over owner-only.
  console.error(
    "hirist: prefer Gmail mailbox OTP via tools/ats/email_otp.py when Google/Hirist sends email codes"
  );
  return true;
}

/** Hirist /login is a homepage SPA; Google SSO lives in the Login modal. */
function loginModalVisible(text) {
  const t = String(text || "");
  return (
    /continue with google|sign in with google|login with google/i.test(t) ||
    (/login here/i.test(t) && /email address/i.test(t))
  );
}

async function loadChromium() {
  try {
    return require("playwright-core").chromium;
  } catch {
    return require(path.join(ROOT, "tools/node_modules/playwright-core")).chromium;
  }
}

async function probeLoggedIn(page, ctx) {
  const cookies = await ctx.cookies("https://www.hirist.tech").catch(() => []);
  const hasAuth = cookies.some((c) => isHiristAuthCookieName(c.name));
  if (hasAuth) {
    return { ok: true, url: page.url() || "", hasAuth };
  }
  await page.goto(APPLIED, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await sleep(1500);
  const url = page.url() || "";
  const body = await page
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
  const onAuthed = /applied-jobs|myprofile|jobfeed/i.test(url);
  const loggedOut =
    /\/login\/?/i.test(url) || /sign in to continue|candidate login/i.test(body);
  return { ok: !loggedOut && (hasAuth || onAuthed), url, hasAuth };
}

async function pageText(page) {
  return page
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
}

async function openLoginModal(page) {
  let text = await pageText(page);
  if (loginModalVisible(text)) return true;

  const locators = [
    page.getByRole("button", { name: /^Login$/i }),
    page.locator("button").filter({ hasText: /^Login$/i }),
  ];
  for (const loc of locators) {
    try {
      const n = Math.min(await loc.count(), 8);
      for (let i = 0; i < n; i++) {
        const el = loc.nth(i);
        const label = ((await el.innerText().catch(() => "")) || "").trim();
        // Header "Login" only — never "Login as Recruiter" / "Login here" submit.
        if (!/^login$/i.test(label)) continue;
        if (!(await el.isVisible().catch(() => false))) continue;
        await el.click({ timeout: 8000 });
        await sleep(1500);
        text = await pageText(page);
        if (loginModalVisible(text)) return true;
      }
    } catch {
      /* try next locator */
    }
  }
  return loginModalVisible(await pageText(page));
}

async function clickGoogleSso(page) {
  const patterns = [/continue with google/i, /sign in with google/i, /login with google/i];
  for (const re of patterns) {
    try {
      const btn = page.getByRole("button", { name: re });
      if ((await btn.count()) > 0 && (await btn.first().isVisible().catch(() => false))) {
        await btn.first().click({ timeout: 8000 });
        return true;
      }
    } catch {
      /* try next */
    }
    try {
      const link = page.getByRole("link", { name: re });
      if ((await link.count()) > 0 && (await link.first().isVisible().catch(() => false))) {
        await link.first().click({ timeout: 8000 });
        return true;
      }
    } catch {
      /* try next */
    }
  }
  try {
    const loc = page.locator("text=/Continue with Google|Sign in with Google|Login with Google/i").first();
    if (await loc.isVisible().catch(() => false)) {
      await loc.click({ timeout: 8000 });
      return true;
    }
  } catch {
    /* ignore */
  }
  return false;
}

async function waitForGooglePage(ctx, page, ms = 20000) {
  const deadline = Date.now() + ms;
  while (Date.now() < deadline) {
    const pages = typeof ctx.pages === "function" ? ctx.pages() : ctx.pages || [];
    for (const pg of pages) {
      if (/accounts\.google\.com/i.test(pg.url() || "")) return pg;
    }
    if (/accounts\.google\.com/i.test(page.url() || "")) return page;
    await sleep(500);
  }
  return null;
}

async function loginWithEmailPassword(page, ctx) {
  const email = GMAIL;
  const pws = passwordCandidates();
  if (!email || !pws.length) return false;
  await page.goto("https://www.hirist.tech/", { waitUntil: "domcontentloaded", timeout: 60000 }).catch(
    () => {}
  );
  await sleep(1200);
  if (!(await openLoginModal(page))) return false;
  try {
    const emailBox = page
      .locator("input[type='email'], input[name='email'], input[placeholder*='Email' i]")
      .first();
    const passBox = page
      .locator(".MuiDialog-root input[type='password'], [role='dialog'] input[type='password']")
      .first();
    if (!(await emailBox.isVisible().catch(() => false))) return false;
    await emailBox.click({ timeout: 5000 });
    await emailBox.fill("");
    await emailBox.pressSequentially(email, { delay: 15 });
    if (await passBox.isVisible().catch(() => false)) {
      await passBox.click({ timeout: 5000 });
      await passBox.fill("");
      await passBox.pressSequentially(pws[0], { delay: 15 });
    }
    const submit = page
      .locator("[role='dialog'] button, .MuiDialog-root button")
      .filter({ hasText: /^Login$/i })
      .last();
    if (await submit.isVisible().catch(() => false)) {
      await submit.click({ timeout: 8000 });
    } else {
      await page.getByRole("button", { name: /^Login$/i }).last().click({ timeout: 8000 });
    }
    await sleep(3000);
  } catch {
    return false;
  }
  const probe = await probeLoggedIn(page, ctx);
  return probe.ok;
}

async function completeGooglePopup(ctx, page) {
  let popup = await waitForGooglePage(ctx, page, 20000);
  if (!popup) {
    console.error("hirist: Google SSO click did not open accounts.google.com");
    return false;
  }

  // Account chooser
  try {
    const cards = popup.locator("div[data-identifier], div[data-email], div[role='link']");
    const n = Math.min(await cards.count(), 8);
    for (let i = 0; i < n; i++) {
      const t =
        ((await cards.nth(i).innerText().catch(() => "")) || "") +
        " " +
        ((await cards.nth(i).getAttribute("data-identifier").catch(() => "")) || "");
      if ((GMAIL && t.toLowerCase().includes(GMAIL.toLowerCase())) || /@gmail\.com|Rafi Ahmed/i.test(t)) {
        await cards.nth(i).click({ timeout: 8000 }).catch(() => {});
        await sleep(2000);
        break;
      }
    }
  } catch {
    /* ignore */
  }

  // Password if asked (URL /signin/challenge/pwd or visible Passwd field).
  const urlBefore = popup.url() || "";
  const bodyBefore = await popup
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
  if (isGooglePasswordChallenge(urlBefore, bodyBefore) || (await passwordField(popup))) {
    const filled = await fillGooglePassword(popup);
    if (!filled.ok && filled.reason === "wrong_password") {
      console.log(JSON.stringify({ ok: false, reason: "google_wrong_password" }));
      return false;
    }
  }

  const url = popup.url() || "";
  const text = await popup
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
  if (isGoogle2faChallenge(url, text)) {
    prompt2faBanner(url);
    tryEmailOtpFill();
    const wait = Number(argValue("--wait") || WAIT_SEC);
    const ok = runPython2faWait(wait);
    return ok;
  }
  return true;
}

async function passwordField(popup) {
  const sels = [
    "input[name='Passwd']",
    "input[type='password']",
    "input[autocomplete*='current-password']",
  ];
  for (const sel of sels) {
    try {
      const loc = popup.locator(sel).first();
      if ((await loc.count()) > 0 && (await loc.isVisible().catch(() => false))) return loc;
    } catch {
      /* try next */
    }
  }
  return null;
}

async function fillGooglePassword(popup) {
  const pws = passwordCandidates();
  if (!pws.length) return { ok: false, reason: "no_password_secret" };
  let box = await passwordField(popup);
  const deadline = Date.now() + 15000;
  while (!box && Date.now() < deadline) {
    await sleep(400);
    box = await passwordField(popup);
  }
  if (!box) return { ok: false, reason: "no_password_field" };
  for (const pw of pws) {
    try {
      await box.click({ timeout: 5000 }).catch(() => {});
      await box.fill("");
      await box.pressSequentially(pw, { delay: 20 });
      const next = popup.getByRole("button", { name: /^Next$/i });
      if ((await next.count()) > 0) await next.first().click({ timeout: 8000 });
      else await box.press("Enter");
      await sleep(2500);
      const body = await popup
        .evaluate(() => (document.body && document.body.innerText) || "")
        .catch(() => "");
      if (/wrong password|that.?s not the right password|incorrect password/i.test(body)) {
        continue;
      }
      return { ok: true };
    } catch {
      /* try next password */
    }
  }
  const body = await popup
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
  if (/wrong password|that.?s not the right password|incorrect password/i.test(body)) {
    return { ok: false, reason: "wrong_password" };
  }
  return { ok: true };
}

async function main() {
  const waitSec = Number(argValue("--wait") || WAIT_SEC);
  const chromium = await loadChromium();
  let browser;
  try {
    browser = await chromium.connectOverCDP(CDP);
  } catch (err) {
    console.log(
      JSON.stringify({
        ok: false,
        reason: "cdp_connect_failed",
        error: String(err && err.message ? err.message : err),
      })
    );
    process.exit(4);
  }

  const ctx = browser.contexts()[0] || (await browser.newContext());
  const page = await ctx.newPage();

  let probe = await probeLoggedIn(page, ctx);
  if (probe.ok) {
    console.log(JSON.stringify({ ok: true, reason: "already_logged_in", url: probe.url }));
    process.exit(0);
  }

  await page.goto(LOGIN, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await sleep(1500);
  // /login is the marketing homepage; the SSO CTA is inside the Login modal.
  const modalOpen = await openLoginModal(page);
  if (!modalOpen) {
    console.log(
      JSON.stringify({
        ok: false,
        reason: "login_modal_missing",
        url: page.url(),
        hint: "Click header Login to open the modal, then Continue with Google",
      })
    );
    process.exit(5);
  }
  console.error("hirist: login modal open — clicking Continue with Google");
  const clicked = await clickGoogleSso(page);
  let googleOk = false;
  if (clicked) {
    googleOk = await completeGooglePopup(ctx, page);
  } else {
    console.error("hirist: Google SSO button missing — will try email/password");
  }

  if (googleOk) {
    const deadline = Date.now() + Math.max(30, waitSec) * 1000;
    while (Date.now() < deadline) {
      probe = await probeLoggedIn(page, ctx);
      if (probe.ok) {
        console.log(
          JSON.stringify({
            ok: true,
            reason: "google_login_ok",
            url: probe.url,
            email: GMAIL,
          })
        );
        process.exit(0);
      }
      await sleep(4000);
    }
  }

  console.error("hirist: Google SSO did not finish — trying Hirist email/password");
  if (await loginWithEmailPassword(page, ctx)) {
    console.log(
      JSON.stringify({
        ok: true,
        reason: "email_password_ok",
        url: page.url(),
        email: GMAIL,
      })
    );
    process.exit(0);
  }

  console.log(
    JSON.stringify({
      ok: false,
      reason: clicked && googleOk ? "hirist_login_required" : "google_sso_then_password_failed",
      url: page.url(),
      hint: "Update GOOGLE_PASSWORD if Google says wrong password, or bash scripts/home-headed-login.sh hirist",
    })
  );
  process.exit(5);
}

if (require.main === module) {
  main().catch((err) => {
    console.error(JSON.stringify({ ok: false, reason: "unexpected", error: String(err) }));
    process.exit(1);
  });
}

module.exports = {
  loginModalVisible,
  openLoginModal,
  clickGoogleSso,
  isGooglePasswordChallenge,
  isGoogle2faChallenge,
  isHiristAuthCookieName,
  passwordCandidates,
};
