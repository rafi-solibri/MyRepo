#!/usr/bin/env node
/**
 * Live CDP check / wait for Instahyre session on headed Chrome at :9222.
 * SQLite cookie-name checks are insufficient on Windows App-Bound Encryption —
 * Chrome may keep a stale sessionid name while /login/ still loads.
 *
 * Usage:
 *   node tools/instahyre/wait_for_cdp_login.js            # one-shot probe
 *   node tools/instahyre/wait_for_cdp_login.js --wait 120 # poll seconds
 *   node tools/instahyre/wait_for_cdp_login.js --open-login
 */
"use strict";

const path = require("path");

const CDP = process.env.INSTAHYRE_CDP || "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "../..");
const AUTH_COOKIE = "sessionid";
const OPS = "https://www.instahyre.com/candidate/opportunities/";
const LOGIN = "https://www.instahyre.com/login/";

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i === -1 || i + 1 >= process.argv.length) return null;
  return process.argv[i + 1];
}

function isLoggedOut(url, bodyText) {
  const u = String(url || "");
  const text = String(bodyText || "");
  if (/\/login\/?/i.test(u)) return true;
  if (/candidate login|log in to continue|sign in to continue/i.test(text)) return true;
  if (/^log in|^sign in/i.test(text.trim()) && !/opportunities|interested|matching/i.test(text)) {
    return true;
  }
  return false;
}

async function main() {
  const waitSec = Number(argValue("--wait") || process.env.INSTAHYRE_LOGIN_WAIT_SEC || "0");
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
        hint: "bash scripts/launch-chrome-cdp.sh instahyre",
      })
    );
    process.exit(4);
  }

  const ctx = browser.contexts()[0] || (await browser.newContext());
  // Prefer a fresh tab — pages()[0] is often LinkedIn/Naukri/Foundit from a
  // prior home portal run; goto from those tabs can ERR_ABORT / stick on login.
  const page = await ctx.newPage();

  async function probe() {
    const cookies = await ctx.cookies("https://www.instahyre.com");
    const sessionCookie = cookies.find((c) => c.name === AUTH_COOKIE);
    const hasAuthCookie = Boolean(sessionCookie && String(sessionCookie.value || "").length > 0);
    let url = page.url() || "";
    let body = "";

    if (openLogin || !hasAuthCookie) {
      await page
        .goto(LOGIN, { waitUntil: "domcontentloaded", timeout: 60000 })
        .catch(() => {});
      url = page.url() || "";
    }

    await page.goto(OPS, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
    // Stale sessions often bounce to /login/ after a brief opportunities flash.
    for (let i = 0; i < 6; i++) {
      await page.waitForTimeout(1000).catch(() => {});
      url = page.url() || "";
      if (/\/login\/?/i.test(url)) break;
    }
    await page.waitForTimeout(1500).catch(() => {});
    url = page.url() || "";
    body = await page
      .evaluate(() => (document.body && document.body.innerText) || "")
      .catch(() => "");

    const loggedOut = isLoggedOut(url, body);
    const onOps = /\/candidate\/opportunities/i.test(url);
    const opsSignals = /opportunities|interested|matching|undecided|express interest/i.test(body);
    const ok = hasAuthCookie && !loggedOut && onOps && opsSignals;
    return {
      ok,
      hasAuthCookie,
      sessionLen: sessionCookie ? String(sessionCookie.value || "").length : 0,
      onOps,
      opsSignals,
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
      "Instahyre CDP login required — sign in in the headed Chrome window " +
        "(profile under ~/.cursor/chrome-cdp-profiles/instahyre). " +
        `Waiting up to ${waitSec}s…`
    );
    console.error("Or: bash scripts/home-headed-login.sh instahyre");
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 8000));
      last = await probe();
      console.error(
        JSON.stringify({
          waiting: true,
          hasAuthCookie: last.hasAuthCookie,
          sessionLen: last.sessionLen,
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
      reason: "instahyre_login_required",
      hasAuthCookie: last.hasAuthCookie,
      sessionLen: last.sessionLen,
      url: last.url,
      hint: "bash scripts/home-headed-login.sh instahyre",
      note: "Windows ABE: SQLite sessionid name alone is not proof of a live session.",
    })
  );
  process.exit(5);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, reason: "unexpected", error: String(err) }));
  process.exit(1);
});
