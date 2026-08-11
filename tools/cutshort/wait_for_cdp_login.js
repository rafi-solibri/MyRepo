#!/usr/bin/env node
/**
 * Live CDP check / wait for Cutshort session on headed Chrome at :9222.
 * SQLite cookie-name checks are insufficient on Windows App-Bound Encryption —
 * Chrome may keep a stale cutshort_authentication name while the server
 * rejects the session (redirect to /?redirect_url=…).
 *
 * Usage:
 *   node tools/cutshort/wait_for_cdp_login.js            # one-shot probe
 *   node tools/cutshort/wait_for_cdp_login.js --wait 120 # poll seconds
 *   node tools/cutshort/wait_for_cdp_login.js --open-login
 */
"use strict";

const path = require("path");

const CDP = process.env.CUTSHORT_CDP || "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "../..");
const AUTH_COOKIE = "cutshort_authentication";
const DASH = "https://cutshort.io/profile/candidate-dashboard";
const LOGIN = "https://cutshort.io/login";

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i === -1 || i + 1 >= process.argv.length) return null;
  return process.argv[i + 1];
}

function isLoggedOut(url, bodyText) {
  const u = String(url || "");
  const text = String(bodyText || "");
  if (/[?&]redirect_url=/.test(u) || /cutshort\.io\/?\?/.test(u)) return true;
  if (/\/login|\/signin|\/candidate-login/i.test(u)) return true;
  if (
    /Candidate login/i.test(text) &&
    /Employer login/i.test(text) &&
    /Get started/i.test(text)
  ) {
    return true;
  }
  return false;
}

async function main() {
  const waitSec = Number(argValue("--wait") || process.env.CUTSHORT_LOGIN_WAIT_SEC || "0");
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
        hint: "bash scripts/launch-chrome-cdp.sh cutshort",
      })
    );
    process.exit(4);
  }

  const ctx = browser.contexts()[0] || (await browser.newContext());
  const page = ctx.pages()[0] || (await ctx.newPage());

  async function probe() {
    const cookies = await ctx.cookies("https://cutshort.io");
    const hasAuthCookie = cookies.some((c) => c.name === AUTH_COOKIE);
    let url = page.url() || "";
    let body = "";

    if (openLogin || !hasAuthCookie) {
      await page
        .goto(LOGIN, { waitUntil: "domcontentloaded", timeout: 60000 })
        .catch(() => {});
      url = page.url() || "";
    }

    await page
      .goto(DASH, { waitUntil: "domcontentloaded", timeout: 60000 })
      .catch(() => {});
    await page.waitForTimeout(2000).catch(() => {});
    url = page.url() || "";
    body = await page.evaluate(() => (document.body && document.body.innerText) || "").catch(() => "");

    const loggedOut = isLoggedOut(url, body);
    const ok = hasAuthCookie && !loggedOut && /candidate-dashboard|profile/i.test(url);
    return {
      ok,
      hasAuthCookie,
      url,
      preview: String(body || "").slice(0, 160),
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
      "Cutshort CDP login required — sign in in the headed Chrome window " +
        "(profile under ~/.cursor/chrome-cdp-profiles/cutshort). " +
        `Waiting up to ${waitSec}s…`
    );
    console.error("Or: bash scripts/home-headed-login.sh cutshort");
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 8000));
      last = await probe();
      console.error(
        JSON.stringify({
          waiting: true,
          hasAuthCookie: last.hasAuthCookie,
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
      reason: "cutshort_login_required",
      hasAuthCookie: last.hasAuthCookie,
      url: last.url,
      hint: "bash scripts/home-headed-login.sh cutshort",
      note: "Windows ABE: SQLite cutshort_authentication name alone is not proof of a live session.",
    })
  );
  process.exit(5);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, reason: "unexpected", error: String(err) }));
  process.exit(1);
});
