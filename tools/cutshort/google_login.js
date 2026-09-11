#!/usr/bin/env node
/**
 * Portal login via Google / Gmail SSO on the CDP Chrome profile.
 *
 * /login is a 404 — Candidate login is a homepage modal:
 *   "Signup or login with Google"
 *
 * Prefer Continue with Google (GOOGLE_EMAIL / LINKEDIN_EMAIL). When Google shows
 * 2FA / authenticator, print ASK_OWNER_GOOGLE_2FA in the agent chat and wait.
 * Email verification codes: try tools/ats/email_otp.py (Gmail CDP / IMAP).
 *
 * HARD: GOOGLE_PASSWORD only on Google forms — never LINKEDIN_PASSWORD.
 *
 * Usage:
 *   node tools/<portal>/google_login.js
 *   node tools/<portal>/google_login.js --wait 300
 */
"use strict";

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const PORTAL = process.env.DAILY_PORTAL || ["cut", "short"].join("");
const CDP = process.env[`${PORTAL.toUpperCase()}_CDP`] || process.env.PORTAL_CDP || "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "../..");
const HOME = `https://${PORTAL}.io/`;
const DASH = `https://${PORTAL}.io/profile/candidate-dashboard`;
const AUTH_COOKIE = `${PORTAL}_authentication`;
const GMAIL = process.env.GOOGLE_EMAIL || process.env.LINKEDIN_EMAIL || process.env.APPLY_EMAIL || "";
const WAIT_SEC = Number(
  process.env[`${PORTAL.toUpperCase()}_GOOGLE_LOGIN_WAIT_SEC`] ||
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

/** Google forms only — never cross-feed LINKEDIN_PASSWORD. */
function passwordCandidates() {
  const keys = ["GOOGLE_PASSWORD", "GMAIL_PASSWORD"];
  const out = [];
  for (const k of keys) {
    const v = (process.env[k] || "").trim();
    if (v && !out.includes(v)) out.push(v);
  }
  return out;
}

function isLoggedOut(url, bodyText) {
  const u = String(url || "");
  const text = String(bodyText || "");
  const hostRe = new RegExp(`${PORTAL}\\.io\\/?\\?`);
  if (/[?&]redirect_url=/.test(u) || hostRe.test(u)) return true;
  if (/\/login|\/signin|\/candidate-login/i.test(u)) return true;
  if (
    /Candidate login/i.test(text) &&
    /Employer login|For Employers|Sign in as a employer/i.test(text) &&
    /Get started/i.test(text)
  ) {
    return true;
  }
  return false;
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
  if (/signin\/challenge\/(totp|ipp|az|sk|iap|selection|dp)/i.test(u)) return true;
  return /2[- ]step|authenticator|verification code|check your phone|tap yes|confirm it.?s you/i.test(
    `${u}\n${text}`
  );
}

function prompt2faBanner(detail) {
  const wait = Number(argValue("--wait") || WAIT_SEC);
  const msg = [
    "",
    "================================================================",
    `ASK_OWNER_GOOGLE_2FA (${PORTAL})`,
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

cdp = os.environ.get((os.environ.get("DAILY_PORTAL") or ("cut"+"short")).upper() + "_CDP", "http://127.0.0.1:9222")
wait = int(${Number(waitSec)})
portal = os.environ.get("DAILY_PORTAL") or ("cut" + "short")
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(cdp)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = None
    for pg in ctx.pages:
        u = pg.url or ""
        if "accounts.google.com" in u or (portal + ".io") in u:
            page = pg
            break
    if page is None:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
    if is_google_2fa_challenge(page):
        ok = wait_owner_google_2fa(page, portal=portal, wait_sec=wait)
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
  console.error(
    "portal: prefer Gmail mailbox OTP via tools/ats/email_otp.py when Google sends email codes"
  );
  return true;
}

async function loadChromium() {
  try {
    return require("playwright-core").chromium;
  } catch {
    return require(path.join(ROOT, "tools/node_modules/playwright-core")).chromium;
  }
}

async function probeLoggedIn(page, ctx) {
  const cookies = await ctx.cookies(HOME.replace(/\/$/, "")).catch(() => []);
  const hasAuth = cookies.some((c) => c.name === AUTH_COOKIE);
  await page.goto(DASH, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  for (let i = 0; i < 6; i++) {
    await sleep(800);
    const u = page.url() || "";
    if (/[?&]redirect_url=/.test(u) || /\/login/i.test(u)) break;
  }
  await sleep(800);
  const url = page.url() || "";
  const body = await page
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
  const onDash = /\/profile\/candidate-dashboard/i.test(url);
  const dashSignals =
    /Matches for you|Recommended jobs|Your profile|Edit profile|Applications|Awaiting response/i.test(
      body
    );
  const loggedOut = isLoggedOut(url, body);
  return {
    ok: hasAuth && !loggedOut && onDash && dashSignals,
    url,
    hasAuth,
    onDash,
    dashSignals,
  };
}

async function openCandidateLoginModal(page) {
  await page.goto(HOME, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await sleep(1500);
  const already = await page
    .getByRole("button", { name: /signup or login with google/i })
    .count()
    .catch(() => 0);
  if (already > 0) return true;
  try {
    const btn = page.getByRole("button", { name: /candidate login/i });
    if ((await btn.count()) > 0) {
      await btn.first().click({ timeout: 8000 });
      await sleep(1200);
      return true;
    }
  } catch {
    /* fall through */
  }
  const clicked = await page
    .evaluate(() => {
      const el = [...document.querySelectorAll("button, a, [role=button]")].find((e) =>
        /candidate login/i.test((e.innerText || "").trim())
      );
      if (el) {
        el.click();
        return true;
      }
      return false;
    })
    .catch(() => false);
  if (clicked) await sleep(1200);
  return clicked;
}

/** Tick the terms checkbox. Do not click the Terms/Privacy text (opens /terms). */
async function agreeToTermsCheckbox(page) {
  const boxes = page.locator("input[type=checkbox]");
  const n = await boxes.count().catch(() => 0);
  for (let i = 0; i < n; i++) {
    const box = boxes.nth(i);
    if (!(await box.isVisible().catch(() => false))) continue;
    const checked = await box.isChecked().catch(() => false);
    if (!checked) {
      await box.click({ timeout: 8000, force: true }).catch(() => {});
      await sleep(400);
    }
    if (await box.isChecked().catch(() => false)) return true;
  }
  const ok = await page
    .evaluate(() => {
      const input = [...document.querySelectorAll("input[type=checkbox]")].find((el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      });
      if (!input) return false;
      if (!input.checked) input.click();
      return !!input.checked;
    })
    .catch(() => false);
  return Boolean(ok);
}

async function clickGoogleSso(page) {
  const patterns = [
    /signup or login with google/i,
    /sign up or login with google/i,
    /continue with google/i,
    /sign in with google/i,
    /login with google/i,
  ];
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
    const loc = page
      .locator("text=/Signup or login with Google|Continue with Google|Sign in with Google/i")
      .first();
    if (await loc.isVisible().catch(() => false)) {
      await loc.click({ timeout: 8000 });
      return true;
    }
  } catch {
    /* ignore */
  }
  const clicked = await page
    .evaluate(() => {
      const el = [...document.querySelectorAll("button, a, [role=button]")].find((e) =>
        /google/i.test((e.innerText || "").trim())
      );
      if (el) {
        el.click();
        return (el.innerText || "").trim();
      }
      return "";
    })
    .catch(() => "");
  return Boolean(clicked);
}

async function completeGooglePopup(ctx, page) {
  await sleep(2000);
  let popup = null;
  for (const pg of ctx.pages()) {
    const u = pg.url() || "";
    if (/accounts\.google\.com/i.test(u)) {
      popup = pg;
      break;
    }
  }
  if (!popup) {
    const deadline = Date.now() + 12000;
    while (!popup && Date.now() < deadline) {
      await sleep(400);
      for (const pg of ctx.pages()) {
        const u = pg.url() || "";
        if (/accounts\.google\.com/i.test(u)) {
          popup = pg;
          break;
        }
      }
    }
  }
  if (!popup) popup = page;

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
    if (!filled.ok && filled.reason === "no_password_secret") {
      console.log(JSON.stringify({ ok: false, reason: "google_password_missing" }));
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
  const hostRe = new RegExp(`${PORTAL}\\.io`, "i");
  const page = ctx.pages().find((p) => hostRe.test(p.url())) || (await ctx.newPage());

  let probe = await probeLoggedIn(page, ctx);
  if (probe.ok) {
    console.log(JSON.stringify({ ok: true, reason: "already_logged_in", url: probe.url }));
    process.exit(0);
  }

  const modal = await openCandidateLoginModal(page);
  if (!modal) {
    console.log(
      JSON.stringify({
        ok: false,
        reason: "candidate_login_modal_missing",
        url: page.url(),
        hint: "Homepage had no Candidate login — try bash scripts/home-headed-login.sh <portal>",
      })
    );
    process.exit(5);
  }

  await agreeToTermsCheckbox(page);
  const clicked = await clickGoogleSso(page);
  if (!clicked) {
    console.log(
      JSON.stringify({
        ok: false,
        reason: "google_sso_button_missing",
        url: page.url(),
        hint: "Candidate login modal had no Google button — try bash scripts/home-headed-login.sh <portal>",
      })
    );
    process.exit(5);
  }

  const googleOk = await completeGooglePopup(ctx, page);
  if (!googleOk) {
    console.log(
      JSON.stringify({
        ok: false,
        reason: "google_login_incomplete",
        hint: "Password rejected, 2FA timeout, or SSO did not finish — check ASK_OWNER_GOOGLE_2FA",
      })
    );
    process.exit(6);
  }

  const deadline = Date.now() + Math.max(30, waitSec) * 1000;
  while (Date.now() < deadline) {
    probe = await probeLoggedIn(page, ctx);
    if (probe.ok) {
      console.log(
        JSON.stringify({
          ok: true,
          reason: "google_login_ok",
          url: probe.url,
          email: GMAIL ? "set" : "",
        })
      );
      process.exit(0);
    }
    await sleep(4000);
  }

  console.log(
    JSON.stringify({
      ok: false,
      reason: "portal_login_required",
      url: page.url(),
      hint: "Google SSO did not establish session — re-run with ASK_OWNER_GOOGLE_2FA if challenged",
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
  isGooglePasswordChallenge,
  isGoogle2faChallenge,
  isLoggedOut,
  isGoogle2faChallenge,
  passwordCandidates,
  AUTH_COOKIE,
  HOME,
  DASH,
  PORTAL,
};
