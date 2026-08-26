/**
 * Shared Hirist session detection.
 *
 * The /applied-jobs route is public when logged out (empty list + marketing
 * chrome). A URL match is NOT proof of login — jobfeed API / auth cookie is.
 */
"use strict";

const API = "https://gladiator.hirist.tech/job";
const AUTH_COOKIE_RE = /^(token|access_token|auth_token|hjuid|userToken|JSID)$/i;

function isLoggedOutUi(url, body) {
  const u = String(url || "");
  const text = String(body || "");
  if (/\/login\/?/i.test(u) && !/applied-jobs|myprofile|jobfeed/i.test(u)) return true;
  if (/please login|sign in to continue|login\/signup to proceed|candidate login/i.test(text)) {
    return true;
  }
  if (
    /\b(login|register|sign in)\b/i.test(text) &&
    !/\b(logout|sign out|my profile)\b/i.test(text) &&
    /find your dream tech job|download app|login as recruiter|login here/i.test(text)
  ) {
    return true;
  }
  return false;
}

function isPublicAppliedJobs(url, body) {
  const u = String(url || "");
  const text = String(body || "");
  if (!/applied-jobs/i.test(u)) return false;
  if (/you don.?t have applied jobs/i.test(text)) return true;
  if (/please login|login\/signup to proceed/i.test(text)) return true;
  return false;
}

/**
 * Decide session from signals. Never treat applied-jobs URL alone as logged in.
 */
function sessionFromSignals({
  url = "",
  body = "",
  hasAuthCookie = false,
  jobfeedStatus = 0,
  jobfeedError = "",
} = {}) {
  const apiOk =
    jobfeedStatus >= 200 &&
    jobfeedStatus < 300 &&
    !/UNAUTHORISED/i.test(String(jobfeedError || ""));
  if (apiOk) return { ok: true, reason: "jobfeed_ok" };
  if (hasAuthCookie && jobfeedStatus === 401) {
    return { ok: false, reason: "stale_cookie" };
  }
  if (isPublicAppliedJobs(url, body)) {
    return { ok: false, reason: "public_applied_jobs" };
  }
  if (isLoggedOutUi(url, body)) {
    return { ok: false, reason: "login_ui" };
  }
  if (jobfeedStatus === 401 || /UNAUTHORISED/i.test(String(jobfeedError || ""))) {
    return { ok: false, reason: "jobfeed_401" };
  }
  if (hasAuthCookie) return { ok: true, reason: "auth_cookie" };
  return { ok: false, reason: "not_logged_in" };
}

async function jobfeedProbe(page) {
  return page.evaluate(async (u) => {
    const r = await fetch(u, {
      credentials: "include",
      headers: {
        Accept: "application/json",
        version: "2",
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    const text = await r.text();
    let json = null;
    try {
      json = JSON.parse(text);
    } catch {
      json = { raw: text.slice(0, 400) };
    }
    return { status: r.status, json };
  }, `${API}/jobfeed`);
}

function cookiesHaveAuth(cookies) {
  return (cookies || []).some((c) => AUTH_COOKIE_RE.test(c.name) && c.value);
}

async function probeSession(page, ctx) {
  const url = page.url() || "";
  const body = await page
    .evaluate(() => (document.body && document.body.innerText) || "")
    .catch(() => "");
  const cookies = await ctx.cookies("https://www.hirist.tech").catch(() => []);
  const hasAuthCookie = cookiesHaveAuth(cookies);
  let feed = { status: 0, json: null };
  try {
    feed = await jobfeedProbe(page);
  } catch {
    feed = { status: 0, json: null };
  }
  const err = feed.json?.error?.name || feed.json?.error?.message || "";
  const decision = sessionFromSignals({
    url,
    body,
    hasAuthCookie,
    jobfeedStatus: feed.status,
    jobfeedError: err,
  });
  return {
    ...decision,
    url,
    hasAuthCookie,
    apiStatus: feed.status,
    apiError: err || null,
    preview: String(body || "").slice(0, 200),
  };
}

module.exports = {
  API,
  AUTH_COOKIE_RE,
  isLoggedOutUi,
  isPublicAppliedJobs,
  sessionFromSignals,
  jobfeedProbe,
  cookiesHaveAuth,
  probeSession,
};
