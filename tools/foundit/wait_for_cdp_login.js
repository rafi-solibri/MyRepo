#!/usr/bin/env node
/**
 * Live CDP check / wait for Foundit session on headed Chrome at :9222.
 * SQLite cookie-name checks are insufficient on Windows App-Bound Encryption —
 * and unauthenticated Foundit often lands on /rio/sign-out ("Logged out Successfully").
 *
 * Usage:
 *   node tools/foundit/wait_for_cdp_login.js            # one-shot probe
 *   node tools/foundit/wait_for_cdp_login.js --wait 240 # poll seconds
 *   node tools/foundit/wait_for_cdp_login.js --open-login
 */
"use strict";

const path = require("path");

const CDP = process.env.FOUNDIT_CDP || "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "../..");
const AUTH_COOKIE = "MSSOAT";
const DASH = "https://www.foundit.in/seeker/dashboard";
const PROFILE = "https://www.foundit.in/profile";
const LOGIN = "https://www.foundit.in/rio/login";

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i === -1 || i + 1 >= process.argv.length) return null;
  return process.argv[i + 1];
}

function isLoggedOut(url, bodyText) {
  const u = String(url || "");
  const text = String(bodyText || "");
  if (/\/rio\/(login|sign-out)/i.test(u)) return true;
  if (/logged out successfully|select method to login/i.test(text)) return true;
  if (/^login\b|^register\b/i.test(text.trim().slice(0, 80)) && !/Hi,?\s*Rafi|My Applications|dashboard/i.test(text)) {
    return true;
  }
  return false;
}

async function main() {
  const waitSec = Number(argValue("--wait") || process.env.FOUNDIT_LOGIN_WAIT_SEC || "0");
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
        hint: "bash scripts/launch-chrome-cdp.sh foundit",
      })
    );
    process.exit(4);
  }

  const ctx = browser.contexts()[0] || (await browser.newContext());
  const page = ctx.pages()[0] || (await ctx.newPage());

  async function probe() {
    const cookies = await ctx.cookies("https://www.foundit.in");
    const authCookie = cookies.find((c) => c.name === AUTH_COOKIE);
    const hasAuthCookie = Boolean(authCookie && String(authCookie.value || "").length > 0);
    let url = page.url() || "";
    let body = "";

    if (openLogin || !hasAuthCookie) {
      await page.goto(LOGIN, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
      url = page.url() || "";
    }

    await page.goto(DASH, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
    for (let i = 0; i < 6; i++) {
      await page.waitForTimeout(1000).catch(() => {});
      url = page.url() || "";
      if (/\/rio\/(login|sign-out)/i.test(url)) break;
      if (/seeker\/dashboard|\/profile/i.test(url) && hasAuthCookie) break;
    }
    // Profile page is a second signal when dashboard stays empty.
    if (/\/rio\/(login|sign-out)/i.test(url) || !hasAuthCookie) {
      await page.goto(PROFILE, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
      await page.waitForTimeout(1500).catch(() => {});
    }
    url = page.url() || "";
    body = await page
      .evaluate(() => (document.body && document.body.innerText) || "")
      .catch(() => "");

    const loggedOut = isLoggedOut(url, body);
    const hiRafi = /Hi,?\s*Rafi|Rafi Ahmed|Mohammed Abdul/i.test(body);
    const onApp =
      /seeker\/dashboard|\/profile|\/seeker\//i.test(url) && !/\/rio\//i.test(url);
    const ok = hasAuthCookie && !loggedOut && (hiRafi || onApp);
    return {
      ok,
      hasAuthCookie,
      mssoatLen: authCookie ? String(authCookie.value || "").length : 0,
      hiRafi,
      onApp,
      url,
      preview: String(body || "").slice(0, 160).replace(/\s+/g, " "),
    };
  }

  const deadline = Date.now() + Math.max(0, waitSec) * 1000;
  let last = await probe();
  if (last.ok) {
    console.log(JSON.stringify({ ...last, waitedSec: 0 }));
    process.exit(0);
  }

  if (waitSec > 0) {
    console.error(
      "Foundit CDP login required — sign in in the headed Chrome window " +
        "(system Chrome Default on Windows home, or ~/.cursor/chrome-cdp-profiles/foundit). " +
        `Waiting up to ${waitSec}s…`
    );
    console.error("Or: bash scripts/home-headed-login.sh foundit");
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 8000));
      last = await probe();
      console.error(
        JSON.stringify({
          waiting: true,
          hasAuthCookie: last.hasAuthCookie,
          mssoatLen: last.mssoatLen,
          url: last.url,
          secsLeft: Math.max(0, Math.round((deadline - Date.now()) / 1000)),
        })
      );
      if (last.ok) {
        console.log(
          JSON.stringify({
            ...last,
            waitedSec: Math.round(waitSec - (deadline - Date.now()) / 1000),
          })
        );
        process.exit(0);
      }
    }
  }

  console.log(
    JSON.stringify({
      ok: false,
      reason: "foundit_login_required",
      hasAuthCookie: last.hasAuthCookie,
      mssoatLen: last.mssoatLen,
      url: last.url,
      preview: last.preview,
      hint: "bash scripts/home-headed-login.sh foundit",
      note: "Windows ABE: SQLite MSSOAT name alone is not proof of a live session; live CDP must show dashboard/Hi Rafi.",
    })
  );
  process.exit(5);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, reason: "unexpected", error: String(err) }));
  process.exit(1);
});
