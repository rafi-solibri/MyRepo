#!/usr/bin/env node
/**
 * Live CDP check / wait for Hirist session on headed Chrome at :9222.
 *
 * Usage:
 *   node tools/hirist/wait_for_cdp_login.js            # one-shot probe
 *   node tools/hirist/wait_for_cdp_login.js --wait 120 # poll seconds
 *   node tools/hirist/wait_for_cdp_login.js --open-login
 */
"use strict";

const path = require("path");

const CDP = process.env.HIRIST_CDP || "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "../..");
const HOME = "https://www.hirist.tech/";
const LOGIN = "https://www.hirist.tech/login";
const APPLIED = "https://www.hirist.tech/applied-jobs";
const AUTH_COOKIE_RE =
  /^(hirist_seeker_enc|token|access_token|auth_token|hjuid|userToken|JSID)$/i;

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i === -1 || i + 1 >= process.argv.length) return null;
  return process.argv[i + 1];
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
    // Marketing homepage still shows Login/Register when logged out.
    if (/find your dream tech job|download app|login as recruiter/i.test(text)) return true;
  }
  return false;
}

async function main() {
  const waitSec = Number(argValue("--wait") || process.env.HIRIST_LOGIN_WAIT_SEC || "0");
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
        hint: "bash scripts/launch-chrome-cdp.sh hirist",
      })
    );
    process.exit(4);
  }

  const ctx = browser.contexts()[0] || (await browser.newContext());
  const page = await ctx.newPage();

  async function probe() {
    const cookies = await ctx.cookies("https://www.hirist.tech");
    const authCookies = cookies.filter((c) => AUTH_COOKIE_RE.test(c.name) && c.value);
    const hasAuthCookie = authCookies.length > 0;
    let url = page.url() || "";
    let body = "";

    if (openLogin || !hasAuthCookie) {
      await page.goto(LOGIN, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
      url = page.url() || "";
    }

    await page.goto(APPLIED, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
    for (let i = 0; i < 6; i++) {
      await page.waitForTimeout(1000).catch(() => {});
      url = page.url() || "";
      if (/\/login\/?/i.test(url)) break;
      if (/applied-jobs|myprofile|jobfeed/i.test(url)) break;
    }
    await page.waitForTimeout(1200).catch(() => {});
    url = page.url() || "";
    body = await page
      .evaluate(() => (document.body && document.body.innerText) || "")
      .catch(() => "");

    const loggedOut = isLoggedOut(url, body);
    const onAuthed =
      /applied-jobs|myprofile|jobfeed|saved-jobs/i.test(url) ||
      /\b(applied jobs|my profile|saved jobs|job feed)\b/i.test(body);
    const ok = !loggedOut && (hasAuthCookie || onAuthed);
    return {
      ok,
      hasAuthCookie,
      authCookieNames: authCookies.map((c) => c.name),
      onAuthed,
      url,
      preview: String(body || "").slice(0, 160),
      home: HOME,
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
      "Hirist CDP login required — sign in in the headed Chrome window " +
        "(profile under ~/.cursor/chrome-cdp-profiles/hirist). " +
        `Waiting up to ${waitSec}s…`
    );
    console.error("Or: bash scripts/home-headed-login.sh hirist");
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
      reason: "hirist_login_required",
      hasAuthCookie: last.hasAuthCookie,
      authCookieNames: last.authCookieNames,
      url: last.url,
      hint: "bash scripts/home-headed-login.sh hirist",
    })
  );
  process.exit(5);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, reason: "unexpected", error: String(err) }));
  process.exit(1);
});
