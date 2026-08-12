#!/usr/bin/env node
/**
 * Live CDP check / wait for Naukri session on headed Chrome at :9222.
 * SQLite cookie-name checks are insufficient on Windows App-Bound Encryption —
 * and while system Chrome is open the Cookies DB is locked (preflight exit 3).
 *
 * Usage:
 *   node tools/naukri/wait_for_cdp_login.js            # one-shot probe
 *   node tools/naukri/wait_for_cdp_login.js --wait 180 # poll seconds
 *   node tools/naukri/wait_for_cdp_login.js --open-login
 */
"use strict";

const path = require("path");

const CDP = process.env.NAUKRI_CDP || "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "../..");
const AUTH_COOKIES = ["nauk_rt", "nauk_at"];
const HOME = "https://www.naukri.com/mnjuser/homepage";
const PROFILE = "https://www.naukri.com/mnjuser/profile";
const LOGIN = "https://www.naukri.com/nlogin/login";

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i === -1 || i + 1 >= process.argv.length) return null;
  return process.argv[i + 1];
}

function isLoggedOut(url, bodyText) {
  const u = String(url || "");
  const text = String(bodyText || "");
  if (/\/nlogin|\/login|mnj\/login/i.test(u)) return true;
  if (/sign\s*in|login with otp|enter password|register now/i.test(text) &&
      !/Hi,?\s*Rafi|Recommended jobs|Update profile|mnjuser/i.test(text + u)) {
    return true;
  }
  return false;
}

async function main() {
  const waitSec = Number(argValue("--wait") || process.env.NAUKRI_LOGIN_WAIT_SEC || "0");
  const openLogin = process.argv.includes("--open-login");

  let chromium;
  try {
    chromium = require("playwright-core").chromium;
  } catch {
    try {
      // eslint-disable-next-line import/no-dynamic-require
      chromium = require(path.join(ROOT, "tools/node_modules/playwright-core")).chromium;
    } catch (err) {
      console.error(
        JSON.stringify({
          ok: false,
          reason: "playwright_core_missing",
          error: String(err && err.message ? err.message : err),
        })
      );
      process.exit(2);
    }
  }

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
        hint: "bash scripts/launch-chrome-cdp.sh naukri",
      })
    );
    process.exit(4);
  }

  const ctx = browser.contexts()[0] || (await browser.newContext());
  const page = await ctx.newPage();

  async function probe() {
    const cookies = await ctx.cookies("https://www.naukri.com");
    const hasAuthCookie = cookies.some((c) => AUTH_COOKIES.includes(c.name));
    let url = page.url() || "";
    let body = "";

    if (openLogin && !hasAuthCookie) {
      await page
        .goto(LOGIN, { waitUntil: "domcontentloaded", timeout: 60000 })
        .catch(() => {});
      url = page.url() || "";
    }

    await page
      .goto(HOME, { waitUntil: "domcontentloaded", timeout: 90000 })
      .catch(() => {});
    await page.waitForTimeout(2500);
    url = page.url() || "";
    body = await page
      .evaluate(() => (document.body && document.body.innerText) || "")
      .catch(() => "");

    if (isLoggedOut(url, body)) {
      await page
        .goto(PROFILE, { waitUntil: "domcontentloaded", timeout: 60000 })
        .catch(() => {});
      await page.waitForTimeout(1500);
      url = page.url() || "";
      body = await page
        .evaluate(() => (document.body && document.body.innerText) || "")
        .catch(() => "");
    }

    const cookies2 = await ctx.cookies("https://www.naukri.com");
    const hasAuth = cookies2.some((c) => AUTH_COOKIES.includes(c.name));
    const loggedOut = isLoggedOut(url, body);
    const ok = hasAuth && !loggedOut;
    return {
      ok,
      hasAuthCookie: hasAuth,
      url,
      preview: String(body).replace(/\s+/g, " ").slice(0, 220),
      reason: ok
        ? "live_cdp_naukri_ok"
        : loggedOut
          ? "naukri_login_wall"
          : "naukri_auth_cookie_missing",
    };
  }

  const deadline = Date.now() + Math.max(0, waitSec) * 1000;
  let last = await probe();
  while (!last.ok && Date.now() < deadline) {
    await page.waitForTimeout(5000);
    last = await probe();
  }

  console.log(JSON.stringify(last, null, 2));
  await page.close().catch(() => {});
  process.exit(last.ok ? 0 : 3);
}

main().catch((err) => {
  console.error(
    JSON.stringify({
      ok: false,
      reason: "unexpected",
      error: String(err && err.message ? err.message : err),
    })
  );
  process.exit(1);
});
