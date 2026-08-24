#!/usr/bin/env node
/**
 * Unattended Hirist CDP login recovery for daily cron.
 *
 * Tries, in order:
 * 1. Already signed in (token cookie + applied-jobs not loginish)
 * 2. Open header Login modal → Continue with Google (GSI cookies / password)
 * 3. Email OTP path is not automated (needs inbox); reports login_required
 *
 * Exit 0 = logged in. 5 = login required / missing creds. 6 = CAPTCHA/checkpoint.
 */
"use strict";

const path = require("path");
const fs = require("fs");

const CDP = process.env.HIRIST_CDP || "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "../..");
const HOME = "https://www.hirist.tech/";
const APPLIED = "https://www.hirist.tech/applied-jobs";
const TIMEOUT_MS = Number(process.env.HIRIST_AUTO_LOGIN_TIMEOUT_MS || 150000);
const AUTH_COOKIE_RE = /^(token|access_token|auth_token|hjuid|userToken|JSID)$/i;

const EMAIL = (
  process.env.LINKEDIN_EMAIL ||
  process.env.GOOGLE_EMAIL ||
  process.env.HIRIST_EMAIL ||
  ""
).trim();

function passwordCandidates() {
  const keys = [
    "LINKEDIN_PASSWORD",
    "GOOGLE_PASSWORD",
    "HIRIST_PASSWORD",
    "NAUKRI_WORKDAY_PASSWORD",
    "ATS_PASSWORD",
  ];
  const out = [];
  const seen = new Set();
  for (const k of keys) {
    const v = String(process.env[k] || "").trim();
    if (v && !seen.has(v)) {
      seen.add(v);
      out.push(v);
    }
  }
  return out;
}

function artDir() {
  if (fs.existsSync("/opt/cursor/artifacts")) return "/opt/cursor/artifacts";
  const d = path.join(ROOT, "artifacts");
  fs.mkdirSync(d, { recursive: true });
  return d;
}

function isLoggedOut(url, bodyText) {
  const u = String(url || "");
  const text = String(bodyText || "");
  if (/\/login\/?/i.test(u) && !/applied-jobs|myprofile|jobfeed/i.test(u)) return true;
  if (/sign in to continue|log in to continue|candidate login/i.test(text)) return true;
  if (
    /\b(login|register|sign in)\b/i.test(text) &&
    !/\b(applied jobs|my profile|job feed|saved jobs|logout|sign out)\b/i.test(text)
  ) {
    if (/find your dream tech job|download app|login as recruiter/i.test(text)) return true;
  }
  return false;
}

async function loadPlaywright() {
  try {
    return require("playwright-core").chromium;
  } catch {
    return require(path.join(ROOT, "tools/node_modules/playwright-core")).chromium;
  }
}

async function hasAuth(ctx) {
  const cookies = await ctx.cookies([
    "https://www.hirist.tech",
    "https://hirist.tech",
    "https://gladiator.hirist.tech",
  ]);
  return cookies.some((c) => AUTH_COOKIE_RE.test(c.name) && c.value);
}

async function probeLoggedIn(page, ctx) {
  if (!(await hasAuth(ctx))) return false;
  await page.goto(APPLIED, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(1500).catch(() => {});
  const url = page.url() || "";
  const body = await page.evaluate(() => document.body?.innerText || "").catch(() => "");
  return !isLoggedOut(url, body) && !/\/login\/?/i.test(url);
}

async function dismissCookies(page) {
  const gotIt = page.getByRole("button", { name: /got it/i }).first();
  if (await gotIt.count().catch(() => 0)) {
    await gotIt.click({ timeout: 3000 }).catch(() => {});
  }
}

async function openLoginModal(page) {
  await page.goto(HOME, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(1500).catch(() => {});
  await dismissCookies(page);

  // Prefer exact header Login (not "Login as Recruiter").
  const candidates = [
    page.locator('header a, header button, nav a, nav button').filter({ hasText: /^Login$/i }),
    page.getByRole("link", { name: /^Login$/i }),
    page.getByRole("button", { name: /^Login$/i }),
    page.locator('a, button').filter({ hasText: /^Login$/i }),
  ];
  for (const loc of candidates) {
    const el = loc.first();
    if (await el.count().catch(() => 0)) {
      const text = ((await el.innerText().catch(() => "")) || "").trim();
      if (/recruiter/i.test(text)) continue;
      await el.click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(1200).catch(() => {});
      break;
    }
  }

  // Modal / drawer should show Google or email field.
  const modalish = page.locator('[role="dialog"], .modal, [class*="Modal"], [class*="login"]').first();
  if (await modalish.count().catch(() => 0)) {
    await modalish.waitFor({ state: "visible", timeout: 8000 }).catch(() => {});
  }
}

async function clickGoogleInModal(page) {
  const scopes = [
    page.locator('[role="dialog"]'),
    page.locator('[class*="Modal"]'),
    page.locator("body"),
  ];
  const patterns = [
    /continue with google/i,
    /^google$/i,
    /sign in with google/i,
    /login with google/i,
  ];
  for (const scope of scopes) {
    if (!(await scope.count().catch(() => 0))) continue;
    for (const re of patterns) {
      const btn = scope.getByRole("button", { name: re }).first();
      if (await btn.count().catch(() => 0)) {
        await btn.click({ timeout: 5000 }).catch(() => {});
        return true;
      }
      const link = scope.getByRole("link", { name: re }).first();
      if (await link.count().catch(() => 0)) {
        await link.click({ timeout: 5000 }).catch(() => {});
        return true;
      }
      const any = scope.locator("button, a, div[role=button]").filter({ hasText: re }).first();
      if (await any.count().catch(() => 0)) {
        await any.click({ timeout: 5000 }).catch(() => {});
        return true;
      }
    }
  }
  // Last resort: Google GSI iframe button
  for (const frame of page.frames()) {
    if (!/accounts\.google\.com\/gsi/i.test(frame.url() || "")) continue;
    const btn = frame.locator('div[role="button"], button').first();
    if (await btn.count().catch(() => 0)) {
      await btn.click({ timeout: 5000 }).catch(() => {});
      return true;
    }
  }
  return false;
}

async function handleGoogleAuth(page, context) {
  const deadline = Date.now() + TIMEOUT_MS;
  const passwords = passwordCandidates();

  while (Date.now() < deadline) {
    if (await probeLoggedIn(page, context)) return true;

    const pages = context.pages();
    const googlePage =
      pages.find((p) => /accounts\.google\.com/i.test(p.url() || "")) ||
      (/accounts\.google\.com/i.test(page.url() || "") ? page : null);

    if (!googlePage) {
      await page.waitForTimeout(800).catch(() => {});
      continue;
    }

    const url = googlePage.url() || "";
    const text = await googlePage.evaluate(() => document.body?.innerText || "").catch(() => "");

    if (/captcha|unusual traffic|verify it.?s you|2-step|challenge\/iap/i.test(text + url)) {
      return "captcha";
    }

    if (EMAIL && /accountchooser|signin\/oauth|gsi\/select/i.test(url + text)) {
      const acc = googlePage
        .locator(`[data-email="${EMAIL}"], [data-identifier="${EMAIL}"]`)
        .first();
      if (await acc.count().catch(() => 0)) {
        await acc.click({ timeout: 5000 }).catch(() => {});
      } else {
        const byText = googlePage.getByText(EMAIL, { exact: false }).first();
        if (await byText.count().catch(() => 0)) await byText.click({ timeout: 5000 }).catch(() => {});
      }
    }

    if (/\/signin\/identifier/i.test(url) && EMAIL) {
      const emailBox = googlePage.locator('input[type="email"], #identifierId').first();
      if (await emailBox.count().catch(() => 0)) {
        await emailBox.fill(EMAIL).catch(() => {});
        await googlePage.locator("#identifierNext, button:has-text('Next')").first().click().catch(() => {});
      }
    }

    if (/\/challenge\/pwd|\/signin\/challenge/i.test(url) && passwords.length) {
      const pwdBox = googlePage.locator('input[type="password"], input[name="Passwd"]').first();
      if (await pwdBox.count().catch(() => 0)) {
        for (const pwd of passwords) {
          await pwdBox.fill("").catch(() => {});
          await pwdBox.fill(pwd).catch(() => {});
          await googlePage.locator("#passwordNext, button:has-text('Next')").first().click().catch(() => {});
          await googlePage.waitForTimeout(2500).catch(() => {});
          const t2 = await googlePage.evaluate(() => document.body?.innerText || "").catch(() => "");
          if (!/wrong password|incorrect password|couldn.?t sign you in/i.test(t2)) break;
        }
      }
    }

    const cont = googlePage
      .locator("#submit_approve_access, button:has-text('Continue'), button:has-text('Allow')")
      .first();
    if (await cont.count().catch(() => 0)) {
      await cont.click({ timeout: 5000 }).catch(() => {});
    }

    await page.waitForTimeout(1200).catch(() => {});
  }
  return false;
}

async function dumpUi(page, name) {
  const shot = path.join(artDir(), name);
  await page.screenshot({ path: shot, fullPage: true }).catch(() => {});
  const info = await page
    .evaluate(() => {
      const els = Array.from(document.querySelectorAll("button, a, input, div[role=button]"))
        .map((el) => ({
          tag: el.tagName,
          text: (el.innerText || el.value || el.getAttribute("aria-label") || "").trim().slice(0, 60),
          href: el.getAttribute("href"),
        }))
        .filter((x) => x.text)
        .slice(0, 80);
      return { url: location.href, text: (document.body?.innerText || "").slice(0, 800), els };
    })
    .catch(() => ({}));
  fs.writeFileSync(path.join(artDir(), name.replace(/\.png$/, ".json")), JSON.stringify(info, null, 2));
  return shot;
}

async function main() {
  const chromium = await loadPlaywright();
  let browser;
  try {
    browser = await chromium.connectOverCDP(CDP);
  } catch (err) {
    console.error(
      JSON.stringify({
        ok: false,
        reason: "cdp_connect_failed",
        cdp: CDP,
        error: String(err && err.message ? err.message : err),
      })
    );
    process.exit(4);
  }

  const context = browser.contexts()[0] || (await browser.newContext());
  const page = context.pages()[0] || (await context.newPage());

  if (await probeLoggedIn(page, context)) {
    console.log(JSON.stringify({ ok: true, method: "already_logged_in" }));
    process.exit(0);
  }

  await openLoginModal(page);
  await dumpUi(page, "hirist-login-modal.png");

  const popupPromise = context.waitForEvent("page", { timeout: 20000 }).catch(() => null);
  const clicked = await clickGoogleInModal(page);
  if (!clicked) {
    const shot = await dumpUi(page, "hirist-auto-login-no-google.png");
    console.error(
      JSON.stringify({
        ok: false,
        reason: "google_button_missing",
        screenshot: shot,
        hint: "Sign in once: bash scripts/home-headed-login.sh hirist",
      })
    );
    process.exit(5);
  }

  const popup = await popupPromise;
  if (popup) await popup.waitForLoadState("domcontentloaded").catch(() => {});

  const result = await handleGoogleAuth(page, context);
  if (result === "captcha") {
    console.error(JSON.stringify({ ok: false, reason: "captcha_or_checkpoint" }));
    process.exit(6);
  }
  if (result === true || (await probeLoggedIn(page, context))) {
    console.log(JSON.stringify({ ok: true, method: "google_sso" }));
    process.exit(0);
  }

  const shot = await dumpUi(page, "hirist-auto-login-failed.png");
  console.error(
    JSON.stringify({
      ok: false,
      reason: "login_failed",
      hasEmail: Boolean(EMAIL),
      passwordCandidates: passwordCandidates().length,
      screenshot: shot,
      url: page.url(),
    })
  );
  process.exit(5);
}

main().catch((err) => {
  console.error(
    JSON.stringify({
      ok: false,
      reason: "exception",
      error: String(err && err.stack ? err.stack : err),
    })
  );
  process.exit(5);
});
