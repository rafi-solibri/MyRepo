#!/usr/bin/env node
/**
 * Live CDP check for Indeed session on Chrome at :9222.
 *
 * Cookie *names* (BearerToken) can outlive OauthExpires/JWT — verify values
 * and/or account settings Sign In wall.
 *
 * Usage:
 *   node tools/indeed/wait_for_cdp_login.js
 *   node tools/indeed/wait_for_cdp_login.js --wait 120
 *   node tools/indeed/wait_for_cdp_login.js --open-login
 */
"use strict";

const path = require("path");

const CDP = process.env.INDEED_CDP || "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "../..");
const HOME = "https://in.indeed.com/";
const ACCOUNT = "https://secure.indeed.com/settings/account";
const AUTH = "https://secure.indeed.com/auth?hl=en_IN&co=IN&continue=https%3A%2F%2Fin.indeed.com%2F";

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i === -1 || i + 1 >= process.argv.length) return null;
  return process.argv[i + 1];
}

function jwtExp(token) {
  if (!token || String(token).split(".").length < 3) return null;
  try {
    let payload = String(token).split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const pad = "=".repeat((4 - (payload.length % 4)) % 4);
    const claims = JSON.parse(Buffer.from(payload + pad, "base64").toString("utf8"));
    return typeof claims.exp === "number" ? claims.exp : null;
  } catch {
    return null;
  }
}

function looksSignedIn(url, body) {
  const blob = `${url}\n${body}`;
  return /account settings|messages unread|manage your account security|sign out|welcome,\s*\w+/i.test(
    blob
  );
}

function looksLoginWall(url, body) {
  const blob = `${url}\n${body}`;
  return /sign in \| indeed accounts|ready to take the next step|continue with apple/i.test(
    blob
  );
}

async function main() {
  const waitSec = Number(argValue("--wait") || process.env.INDEED_LOGIN_WAIT_SEC || "0");
  const openLogin = process.argv.includes("--open-login");

  let chromium;
  try {
    chromium = require("playwright-core").chromium;
  } catch {
    try {
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
        hint: "bash scripts/launch-chrome-cdp.sh indeed",
      })
    );
    process.exit(4);
  }

  const ctx = browser.contexts()[0] || (await browser.newContext());
  let page = ctx.pages()[0] || (await ctx.newPage());

  const deadline = Date.now() + Math.max(0, waitSec) * 1000;
  let last = { ok: false, reason: "unchecked" };

  do {
    try {
      const cookies = await ctx.cookies([
        "https://secure.indeed.com/",
        "https://in.indeed.com/",
        "https://www.indeed.com/",
      ]);
      const byName = Object.fromEntries(cookies.map((c) => [c.name, c.value]));
      const bearer = byName["__Secure-PassportAuthProxy-BearerToken"] || "";
      const oauthExpRaw = byName["__Secure-PassportAuthProxy-OauthExpires"] || "";
      const oauthExp = /^\d+$/.test(oauthExpRaw) ? Number(oauthExpRaw) : null;
      const exp = jwtExp(bearer) || oauthExp;
      const expired = exp != null && Date.now() / 1000 > exp;

      if (expired) {
        last = {
          ok: false,
          reason: "indeed_session_expired",
          oauthExpires: oauthExp,
          jwtExp: jwtExp(bearer),
          hasBearer: Boolean(bearer),
          hint: "bash scripts/home-headed-login.sh indeed && bash scripts/refresh-portal-session-seed.sh indeed",
        };
      } else {
        await page.goto(ACCOUNT, { waitUntil: "domcontentloaded", timeout: 45000 });
        await page.waitForTimeout(1500);
        const url = page.url() || "";
        let body = "";
        try {
          body = await page.locator("body").innerText({ timeout: 5000 });
        } catch {
          body = "";
        }
        if (looksSignedIn(url, body) && !looksLoginWall(url, body)) {
          last = {
            ok: true,
            reason: "live_cdp_indeed_ok",
            url: url.slice(0, 200),
            hasBearer: Boolean(bearer),
            oauthExpires: oauthExp,
          };
          console.log(JSON.stringify(last));
          process.exit(0);
        }
        if (looksLoginWall(url, body)) {
          last = {
            ok: false,
            reason: "indeed_login_required",
            url: url.slice(0, 200),
            hasBearer: Boolean(bearer),
            expired,
          };
        } else {
          last = {
            ok: Boolean(bearer) && !expired,
            reason: bearer && !expired ? "cookie_ok_unconfirmed_nav" : "indeed_login_required",
            url: url.slice(0, 200),
            hasBearer: Boolean(bearer),
          };
          if (last.ok) {
            console.log(JSON.stringify(last));
            process.exit(0);
          }
        }
      }

      if (openLogin && !last.ok) {
        await page.goto(AUTH, { waitUntil: "domcontentloaded", timeout: 45000 }).catch(() => {});
      }
    } catch (err) {
      last = {
        ok: false,
        reason: "probe_error",
        error: String(err && err.message ? err.message : err).slice(0, 200),
      };
    }

    if (Date.now() >= deadline) break;
    await new Promise((r) => setTimeout(r, 2000));
  } while (Date.now() < deadline);

  console.log(JSON.stringify(last));
  process.exit(last.ok ? 0 : 3);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, reason: "unexpected", error: String(err) }));
  process.exit(1);
});
