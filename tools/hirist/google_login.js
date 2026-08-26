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

async function loadChromium() {
  try {
    return require("playwright-core").chromium;
  } catch {
    return require(path.join(ROOT, "tools/node_modules/playwright-core")).chromium;
  }
}

async function probeLoggedIn(page, ctx) {
  await page.goto(APPLIED, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await sleep(1500);
  const url = page.url() || "";
  const body = await page
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
  const cookies = await ctx.cookies("https://www.hirist.tech").catch(() => []);
  const hasAuth = cookies.some((c) =>
    /^(token|access_token|auth_token|hjuid|userToken|JSID)$/i.test(c.name)
  );
  const onAuthed = /applied-jobs|myprofile|jobfeed/i.test(url);
  const loggedOut =
    /\/login\/?/i.test(url) || /sign in to continue|candidate login/i.test(body);
  return { ok: !loggedOut && (hasAuth || onAuthed), url, hasAuth };
}

async function clickGoogleSso(page) {
  const patterns = [
    /continue with google/i,
    /sign in with google/i,
    /login with google/i,
    /google/i,
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
  // Fallback: any element with Google branding text.
  try {
    const loc = page.locator("text=/Continue with Google|Sign in with Google|Google/i").first();
    if (await loc.isVisible().catch(() => false)) {
      await loc.click({ timeout: 8000 });
      return true;
    }
  } catch {
    /* ignore */
  }
  return false;
}

async function completeGooglePopup(ctx, page) {
  await sleep(2000);
  let popup = null;
  for (const pg of ctx.pages) {
    const u = pg.url() || "";
    if (/accounts\.google\.com/i.test(u)) {
      popup = pg;
      break;
    }
  }
  if (!popup) popup = page;

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

  // Password if asked
  const body = await popup
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
  if (/enter your password|password/i.test(body)) {
    const pws = passwordCandidates();
    for (const pw of pws) {
      try {
        const box = popup.locator("input[type='password']").first();
        if (await box.isVisible().catch(() => false)) {
          await box.fill("");
          await box.pressSequentially(pw, { delay: 20 });
          const next = popup.getByRole("button", { name: /^Next$/i });
          if ((await next.count()) > 0) await next.first().click({ timeout: 5000 });
          else await box.press("Enter");
          await sleep(2500);
          break;
        }
      } catch {
        /* try next password */
      }
    }
  }

  const url = popup.url() || "";
  const text = await popup
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
  if (
    /2[- ]step|authenticator|verification code|check your phone|challenge/i.test(
      `${url}\n${text}`
    )
  ) {
    prompt2faBanner(url);
    tryEmailOtpFill();
    const wait = Number(argValue("--wait") || WAIT_SEC);
    const ok = runPython2faWait(wait);
    return ok;
  }
  return true;
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
  const clicked = await clickGoogleSso(page);
  if (!clicked) {
    console.log(
      JSON.stringify({
        ok: false,
        reason: "google_sso_button_missing",
        url: page.url(),
        hint: "Hirist login page had no Google button — try bash scripts/home-headed-login.sh hirist",
      })
    );
    process.exit(5);
  }

  const googleOk = await completeGooglePopup(ctx, page);
  if (!googleOk) {
    console.log(
      JSON.stringify({
        ok: false,
        reason: "google_2fa_timeout",
        hint: "Enter authenticator code in Chrome when ASK_OWNER_GOOGLE_2FA appears in chat",
      })
    );
    process.exit(6);
  }

  // Allow redirects back to Hirist
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

  console.log(
    JSON.stringify({
      ok: false,
      reason: "hirist_login_required",
      url: page.url(),
      hint: "Google SSO did not establish Hirist session — re-run with ASK_OWNER_GOOGLE_2FA if challenged",
    })
  );
  process.exit(5);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, reason: "unexpected", error: String(err) }));
  process.exit(1);
});
