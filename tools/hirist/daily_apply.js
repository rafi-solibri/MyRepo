#!/usr/bin/env node
/**
 * Hirist daily apply — CDP login + gladiator.hirist.tech search/apply API.
 *
 * Usage:
 *   bash scripts/preflight-portal-run.sh hirist
 *   bash scripts/launch-chrome-cdp.sh hirist
 *   node tools/hirist/daily_apply.js
 *
 * Env:
 *   HIRIST_CDP            default http://127.0.0.1:9222
 *   HIRIST_REPORT         default /opt/cursor/artifacts/hirist-apply-report.json
 *   HIRIST_MAX_APPLIES    default 40
 *   HIRIST_DRY_RUN=1      search/filter only (no apply POST)
 *   HIRIST_TAILOR=0       disable JD resume tailor for external ATS
 */
"use strict";

const fs = require("fs");
const path = require("path");
function loadChromium() {
  try {
    return require("playwright-core").chromium;
  } catch {
    return require(path.join(__dirname, "../node_modules/playwright-core")).chromium;
  }
}
const { skipReason, hasDotNet, hasTargetSeniority } = require("./filters");
const { findResume, EXPECTED_CTC_LPA, CURRENT_CTC_LPA } = require("./resume");
const { completeExternalPage } = require("../ats/complete_page");
const { tailorResumeForJob } = require("../resume_tailor");
const { companyAllowed, allowlistActive } = require("../hitechcity/campus_allowlist");

const CDP = process.env.HIRIST_CDP || "http://127.0.0.1:9222";
const API = "https://gladiator.hirist.tech/job";
const OUT =
  process.env.HIRIST_REPORT ||
  (fs.existsSync("/opt/cursor/artifacts")
    ? "/opt/cursor/artifacts/hirist-apply-report.json"
    : path.join(process.cwd(), "artifacts", "hirist-apply-report.json"));
const HOME_REPORT =
  process.env.HIRIST_HOME_REPORT ||
  (fs.existsSync("/opt/cursor/artifacts")
    ? "/opt/cursor/artifacts/hirist-daily-run.json"
    : path.join(process.cwd(), "artifacts", "hirist-daily-run.json"));
const MAX_APPLIES = Number(process.env.HIRIST_MAX_APPLIES || 40);
const DRY_RUN = process.env.HIRIST_DRY_RUN === "1";
const TAILOR = process.env.HIRIST_TAILOR !== "0";
const TODAY = new Date().toISOString().slice(0, 10);

/** Hyderabad location id from Hirist extract-param API. */
const HYD_LOC = JSON.stringify([{ id: 4, name: "hyderabad" }]);

const QUERY_WAVES = [
  "Solution Architect .NET",
  "Technical Architect .NET Azure",
  "Software Architect C#",
  "Engineering Manager .NET",
  "Tech Lead .NET",
  "Principal Engineer .NET",
  "Staff Engineer Azure",
  "Cloud Architect Azure",
  ".NET Architect Hyderabad",
  "Full Stack Architect .NET",
];

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function preferScore(title, skills) {
  const t = title || "";
  let s = 0;
  if (/\b(principal|staff|architect|engineering manager|tech(?:nical)?\s+lead)\b/i.test(t))
    s += 40;
  if (/\b(lead|manager|head)\b/i.test(t)) s += 20;
  if (/\bsenior\b|\bsr\.?\b/i.test(t)) s += 10;
  if (hasDotNet(t, skills)) s += 25;
  if (/\b(azure|aws|cloud|\.net|c#|asp\.?net)\b/i.test(`${t} ${skills}`)) s += 5;
  return s;
}

function locsOf(job) {
  const locs = job?.locations || [];
  if (Array.isArray(locs)) {
    return locs.map((l) => (typeof l === "string" ? l : l?.name || "")).filter(Boolean).join(", ");
  }
  return String(job?.otherLocation || "");
}

function skillsOf(job) {
  const tags = job?.tags || [];
  if (Array.isArray(tags)) {
    return tags.map((t) => (typeof t === "string" ? t : t?.name || "")).filter(Boolean).join(", ");
  }
  return String(job?.tagIdString || "");
}

function companyOf(job) {
  return (
    job?.companyData?.companyName ||
    job?.companyName ||
    job?.createdByAlias ||
    ""
  );
}

function salaryOf(job) {
  const min = Number(job?.minSal || 0);
  const max = Number(job?.maxSal || 0);
  if (max > 0) {
    // Hirist often stores INR absolute; convert rough LPA when huge.
    const maxLpa = max > 1000 ? max / 1e5 : max;
    const minLpa = min > 1000 ? min / 1e5 : min;
    return `${minLpa}-${maxLpa} LPA`;
  }
  return "";
}

function writeReports(state) {
  const finishedAt = new Date().toISOString();
  const applied = state.applied || [];
  const external = state.external || [];
  const rejected = state.rejected || [];
  const blocked = state.blocked || [];
  const skipped = state.skipped || [];
  const seen = state.seen || [];

  const detail = {
    portal: "hirist",
    ts: finishedAt,
    ok: blocked.length === 0,
    counts: {
      applied: applied.length,
      external: external.length,
      rejected: rejected.length,
      blocked: blocked.length,
      skipped: skipped.length,
      seen: seen.length,
    },
    applied,
    external,
    rejected,
    blocked,
    skipped,
    seen: seen.slice(0, 200),
    notes: state.notes || [],
    blockerSummary: blocked[0]
      ? `${blocked[0].reason}${blocked[0].detail ? " — " + blocked[0].detail : ""}`
      : null,
  };
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(detail, null, 2) + "\n");

  const home = {
    portal: "hirist",
    source: process.env.HIRIST_SOURCE || "cloud",
    date: TODAY,
    finishedAt,
    ok: blocked.length === 0 && (applied.length > 0 || seen.length > 0),
    counts: detail.counts,
    applied,
    external,
    rejected,
    blocked,
    skipped,
    seen: seen.slice(0, 100),
    blockerSummary: detail.blockerSummary,
    notes: state.notes || [],
  };
  fs.mkdirSync(path.dirname(HOME_REPORT), { recursive: true });
  fs.writeFileSync(HOME_REPORT, JSON.stringify(home, null, 2) + "\n");
  return { detail, home };
}

async function apiGet(page, url) {
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
  }, url);
}

async function apiPost(page, url, body) {
  return page.evaluate(
    async ({ u, body }) => {
      const xsrf = document.cookie
        .split(";")
        .map((x) => x.trim())
        .find((x) => x.startsWith("XSRF-TOKEN="))
        ?.split("=")
        .slice(1)
        .join("=");
      const r = await fetch(u, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          version: "2",
          "X-Requested-With": "XMLHttpRequest",
          ...(xsrf ? { "X-XSRF-TOKEN": decodeURIComponent(xsrf) } : {}),
        },
        body: JSON.stringify(body),
      });
      const text = await r.text();
      let json = null;
      try {
        json = JSON.parse(text);
      } catch {
        json = { raw: text.slice(0, 400) };
      }
      return { status: r.status, json };
    },
    { u: url, body }
  );
}

function isLoggedOutUrl(url, body) {
  const u = String(url || "");
  const text = String(body || "");
  if (/\/login\/?/i.test(u) && !/applied-jobs|myprofile/i.test(u)) return true;
  if (/please login|sign in to continue|login\/signup to proceed/i.test(text)) return true;
  return false;
}

async function ensureLoggedIn(page) {
  // jobfeed is the post-login landing page; applied-jobs can hang on a stale tab.
  await page.goto("https://www.hirist.tech/jobfeed", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await sleep(1500);
  const url = page.url();
  const body = await page.evaluate(() => (document.body && document.body.innerText) || "");
  if (isLoggedOutUrl(url, body)) {
    return { ok: false, url, preview: body.slice(0, 200) };
  }
  // Soft check: jobfeed also 401s when logged out via API
  const feed = await apiGet(page, `${API}/jobfeed`);
  if (feed.status === 401 || feed.json?.error?.name === "UNAUTHORISED_ACCESS") {
    return { ok: false, url, preview: "jobfeed_401", api: feed.json };
  }
  return { ok: true, url };
}

async function searchJobs(page, query, pageNo = 0) {
  const params = new URLSearchParams({
    query,
    size: "20",
    page: String(pageNo),
    locations: HYD_LOC,
  });
  // Also try remote/WFH via a second query without hard loc filter when needed —
  // primary wave pins Hyd; WFH flag on results still passes filters.
  const res = await apiGet(page, `${API}/search?${params.toString()}`);
  let jobs = [];
  if (Array.isArray(res.json?.data)) jobs = res.json.data;
  else if (Array.isArray(res.json?.data?.jobs)) jobs = res.json.data.jobs;
  else if (Array.isArray(res.json?.jobs)) jobs = res.json.jobs;
  return { status: res.status, jobs, raw: res.json };
}

async function applyInApp(page, jobIds) {
  return apiPost(page, `${API}/apply-multiple`, { jobIds });
}

async function main() {
  const resume = findResume();
  const state = {
    applied: [],
    external: [],
    rejected: [],
    blocked: [],
    skipped: [],
    seen: [],
    notes: [],
  };
  if (!resume) {
    state.blocked.push({
      reason: "resume_missing",
      detail: "Rafi_Resume.docx not found after bootstrap",
    });
    writeReports(state);
    process.exit(2);
  }
  state.notes.push(`resume=${resume}`);
  state.notes.push(`ctc=${CURRENT_CTC_LPA}->${EXPECTED_CTC_LPA}`);

  // google_login.js / wait_for_cdp_login.js must be the sole Playwright CDP client.
  // Connecting here first then spawnSync-ing google_login deadlocks page.goto.
  const { spawnSync } = require("child_process");
  const root = path.join(__dirname, "../..");
  const waitSec = Number(process.env.GOOGLE_2FA_WAIT_SEC || "300");
  const spawnOpts = { cwd: root, env: process.env, stdio: "inherit" };
  const probe = spawnSync(process.execPath, [path.join(__dirname, "wait_for_cdp_login.js")], {
    ...spawnOpts,
    timeout: 90_000,
  });
  let googleLoginExit = null;
  if (probe.status !== 0) {
    console.error("[hirist] session missing — trying Google/Gmail login…");
    const gl = spawnSync(
      process.execPath,
      [path.join(__dirname, "google_login.js"), "--wait", String(waitSec)],
      { ...spawnOpts, timeout: (waitSec + 90) * 1000 }
    );
    googleLoginExit = gl.status;
  }

  let browser;
  try {
    browser = await loadChromium().connectOverCDP(CDP);
  } catch (err) {
    state.blocked.push({
      reason: "cdp_connect_failed",
      detail: String(err && err.message ? err.message : err),
    });
    writeReports(state);
    process.exit(4);
  }

  const ctx = browser.contexts()[0] || (await browser.newContext());
  const page = await ctx.newPage();

  const login = await ensureLoggedIn(page);
  if (!login.ok) {
    state.blocked.push({
      reason: "hirist_login_required",
      detail: login.preview || login.url,
      googleLoginExit,
      probeExit: probe.status,
    });
    writeReports(state);
    console.log(JSON.stringify({ ok: false, counts: { applied: 0 }, blocked: state.blocked }, null, 2));
    process.exit(5);
  }
  state.notes.push(
    googleLoginExit != null
      ? `login_ok_after_google url=${login.url} googleExit=${googleLoginExit}`
      : `login_ok url=${login.url}`
  );

  const seenIds = new Set();
  const candidates = [];

  for (const query of QUERY_WAVES) {
    if (candidates.length >= MAX_APPLIES * 4) break;
    for (let pageNo = 0; pageNo < 3; pageNo++) {
      const { status, jobs } = await searchJobs(page, query, pageNo);
      if (status === 401) {
        state.blocked.push({ reason: "hirist_login_required", detail: "search_401" });
        writeReports(state);
        process.exit(5);
      }
      if (!jobs.length) break;
      for (const job of jobs) {
        const id = job?.id;
        if (!id || seenIds.has(id)) continue;
        seenIds.add(id);
        const title = job.title || job.jobdesignation || "";
        const company = companyOf(job);
        const location = locsOf(job);
        const skills = skillsOf(job);
        const salary = salaryOf(job);
        const expMax = job.max != null ? Number(job.max) : null;
        const wfh = Number(job.workFromHome || 0);
        state.seen.push({
          id,
          title,
          company,
          location,
          score: preferScore(title, skills),
        });

        if (allowlistActive() && !companyAllowed(company)) {
          state.skipped.push({ id, title, company, reason: "campus_allowlist" });
          continue;
        }

        // applyStatus: 0 often means already applied / closed for apply
        if (Number(job.applyStatus) === 0 && !job.applyUrl) {
          state.skipped.push({ id, title, company, reason: "already_applied_or_closed" });
          continue;
        }

        const reason = skipReason(title, {
          company,
          location,
          skills,
          salary,
          expMax,
          workFromHome: wfh,
        });
        if (reason) {
          state.skipped.push({ id, title, company, reason });
          continue;
        }

        candidates.push({
          id,
          title,
          company,
          location,
          skills,
          applyUrl: job.applyUrl || "",
          jobDetailUrl: job.jobDetailUrl || `https://www.hirist.tech/j/job-${id}`,
          score: preferScore(title, skills),
        });
      }
      await sleep(400);
    }
  }

  candidates.sort((a, b) => b.score - a.score);
  state.notes.push(`candidates=${candidates.length} seen=${seenIds.size}`);

  let applies = 0;
  for (const job of candidates) {
    if (applies >= MAX_APPLIES) break;

    if (DRY_RUN) {
      state.notes.push(`dry_run would_apply id=${job.id} ${job.title}`);
      continue;
    }

    // External company ATS when applyUrl is a non-hirist URL
    const ext = String(job.applyUrl || "").trim();
    if (ext && /^https?:\/\//i.test(ext) && !/hirist\.(tech|com)/i.test(ext)) {
      let resumePath = resume;
      if (TAILOR) {
        try {
          const tailored = tailorResumeForJob({
            master: resume,
            jobId: String(job.id),
            title: job.title,
            company: job.company,
            description: `${job.title}\n${job.skills}\n${job.location}`,
            skills: job.skills,
          });
          if (tailored?.ok && tailored.out) resumePath = tailored.out;
        } catch (err) {
          state.notes.push(`tailor_failed id=${job.id} ${String(err.message || err).slice(0, 80)}`);
        }
      }
      const extPage = await ctx.newPage();
      try {
        await extPage.goto(ext, { waitUntil: "domcontentloaded", timeout: 60000 });
        const result = await completeExternalPage(extPage, resumePath);
        if (result?.ok || result?.submitted) {
          state.external.push({
            id: job.id,
            title: job.title,
            company: job.company,
            path: ext,
            reason: "external_ats",
          });
          applies += 1;
        } else {
          state.rejected.push({
            id: job.id,
            title: job.title,
            company: job.company,
            reason: result?.reason || "external_incomplete",
            path: ext,
          });
        }
      } catch (err) {
        state.rejected.push({
          id: job.id,
          title: job.title,
          company: job.company,
          reason: `external_error:${String(err.message || err).slice(0, 80)}`,
        });
      } finally {
        await extPage.close().catch(() => {});
      }
      await sleep(800);
      continue;
    }

    // In-app Hirist apply
    const res = await applyInApp(page, [job.id]);
    const okStatus = res.status >= 200 && res.status < 300;
    const errName = res.json?.error?.name || res.json?.status?.message || "";
    if (res.status === 401 || /UNAUTHORISED/i.test(String(errName))) {
      state.blocked.push({ reason: "hirist_login_required", detail: "apply_401" });
      break;
    }
    if (okStatus && !res.json?.error) {
      state.applied.push({
        id: job.id,
        title: job.title,
        company: job.company,
        path: "hirist_apply",
        url: job.jobDetailUrl,
      });
      applies += 1;
    } else {
      const reason =
        res.json?.error?.message ||
        res.json?.status?.message ||
        `apply_http_${res.status}`;
      if (/already applied|duplicate/i.test(String(reason))) {
        state.skipped.push({ id: job.id, title: job.title, company: job.company, reason: "already_applied" });
      } else {
        state.rejected.push({
          id: job.id,
          title: job.title,
          company: job.company,
          reason: String(reason).slice(0, 160),
        });
      }
    }
    await sleep(700);
  }

  const { detail } = writeReports(state);
  console.log(
    JSON.stringify(
      {
        ok: detail.ok,
        counts: detail.counts,
        applied: detail.applied.slice(0, 10),
        external: detail.external.slice(0, 5),
        blocked: detail.blocked,
        notes: detail.notes,
        report: OUT,
        homeReport: HOME_REPORT,
      },
      null,
      2
    )
  );
  process.exit(detail.blocked.length ? 5 : 0);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, reason: "unexpected", error: String(err) }));
  process.exit(1);
});
