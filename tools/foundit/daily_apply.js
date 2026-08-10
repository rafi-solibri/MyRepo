#!/usr/bin/env node
/**
 * Foundit daily apply runner — Raven search + filters.js classifyJob + Falcon apply
 * via Chrome CDP. Completes external ATS when redirected.
 *
 * Usage:
 *   bash scripts/preflight-portal-run.sh foundit
 *   bash scripts/launch-chrome-cdp.sh foundit
 *   node tools/foundit/daily_apply.js
 *
 * Env:
 *   FOUNDIT_CDP, FOUNDIT_REPORT, FOUNDIT_MAX_APPLIES, FOUNDIT_AGE_DAYS (csv)
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const { classifyJob } = require("./filters");
const {
  findResume,
  EXPECTED_CTC_LPA,
  CURRENT_CTC_LPA,
  FORBIDDEN_DRY_RUN,
} = require("./resume");

const CDP = process.env.FOUNDIT_CDP || "http://127.0.0.1:9222";
const OUT =
  process.env.FOUNDIT_REPORT ||
  "/opt/cursor/artifacts/foundit-apply-report.json";
const MAX_APPLIES = Number(process.env.FOUNDIT_MAX_APPLIES || 50);
const MAX_EXTERNAL_MS = Number(process.env.FOUNDIT_EXTERNAL_MS || 3.5 * 60 * 1000);
const RESUME = findResume();

const QUERIES = [
  ".net architect",
  ".net lead",
  "solutions architect .net",
  "engineering manager .net",
  "principal .net",
  "azure .net architect",
  "software architect .net",
  "technical architect .net",
  "dotnet architect",
  "dotnet lead",
  "staff engineer .net",
  "principal engineer .net",
  "tech lead .net",
  "senior .net architect",
];

function parseAges() {
  const raw = process.env.FOUNDIT_AGE_DAYS || "1,3,7,14,30,60";
  const ages = raw
    .split(",")
    .map((s) => Number(String(s).trim()))
    .filter((n) => Number.isFinite(n) && n > 0);
  return ages.length ? ages : [1, 3, 7, 14, 30, 60];
}
const AGE_DAYS = parseAges();

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function extractBearer(mssoRaw) {
  if (!mssoRaw) return null;
  const raw = decodeURIComponent(String(mssoRaw));
  const first = raw.split("::")[0];
  let decoded = first;
  try {
    decoded = Buffer.from(first, "base64").toString("utf8");
  } catch {
    decoded = first;
  }
  let jwt = decoded.includes("::") ? decoded.split("::")[0] : decoded;
  const m =
    jwt.match(/Bearer\s+([A-Za-z0-9\-_\.]+)/i) ||
    jwt.match(/(eyJ[A-Za-z0-9\-_\.]+)/);
  if (m) jwt = m[1];
  const parts = String(jwt || "").split(".");
  if (parts.length !== 3) return null;
  return jwt;
}

async function getBearer(context) {
  const cookies = await context.cookies("https://www.foundit.in");
  const msso = cookies.find((c) => c.name === "MSSOAT");
  return extractBearer(msso?.value);
}

function apiHeaders(bearer) {
  const headers = {
    "content-type": "application/json",
    "x-source-site-context": "rexmonster",
    "x-source-country": "IN",
    accept: "application/json",
  };
  if (bearer) headers.Authorization = `Bearer ${bearer}`;
  return headers;
}

async function ensureFounditPage(context) {
  let page =
    context.pages().find((p) => /foundit\.in/i.test(p.url())) ||
    context.pages()[0];
  if (!page) page = await context.newPage();
  if (!/foundit\.in/i.test(page.url())) {
    await page.goto("https://www.foundit.in/seeker/dashboard", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await sleep(1500);
  }
  return page;
}

async function rehome(page) {
  if (!/foundit\.in/i.test(page.url())) {
    await page.goto("https://www.foundit.in/seeker/dashboard", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await sleep(800);
  }
}

async function pageFetch(page, { url, method, bearer, body }) {
  await rehome(page);
  return page.evaluate(
    async ({ url, method, bearer, body }) => {
      const headers = {
        "content-type": "application/json",
        "x-source-site-context": "rexmonster",
        "x-source-country": "IN",
        accept: "application/json",
      };
      if (bearer) headers.Authorization = `Bearer ${bearer}`;
      const res = await fetch(url, {
        method: method || "GET",
        credentials: "include",
        headers,
        body: body != null ? JSON.stringify(body) : undefined,
      });
      const text = await res.text();
      let json = null;
      try {
        json = JSON.parse(text);
      } catch {
        json = { raw: text.slice(0, 500) };
      }
      return { status: res.status, json, text: text.slice(0, 800) };
    },
    { url, method, bearer, body }
  );
}

async function ravenSearch(page, bearer, query, start = 0) {
  // Prefer Hyd+remote; also run unrestricted and local-filter later via classifyJob.
  const bodies = [
    {
      query,
      locations: ["hyderabad / secunderabad", "remote"],
      start,
      limit: 20,
      sort: 1,
    },
    {
      query,
      locations: [],
      start,
      limit: 20,
      sort: 1,
    },
  ];
  const jobs = [];
  for (const body of bodies) {
    const res = await pageFetch(page, {
      url: "https://www.foundit.in/raven/api/public/search/v1/jobs",
      method: "POST",
      bearer,
      body,
    });
    const data = Array.isArray(res.json?.data)
      ? res.json.data
      : Array.isArray(res.json)
        ? res.json
        : [];
    jobs.push(...data);
  }
  return jobs;
}

async function jobDetail(page, bearer, jobId) {
  const res = await pageFetch(page, {
    url: `https://www.foundit.in/home/api/jobDetail?jobId=${encodeURIComponent(jobId)}`,
    method: "GET",
    bearer,
  });
  return res.json && !res.json.raw ? res.json : null;
}

async function userJobInfo(page, bearer, jobId) {
  const res = await pageFetch(page, {
    url: "https://www.foundit.in/home/api/userJobInfo",
    method: "POST",
    bearer,
    body: [Number(jobId)],
  });
  const row = Array.isArray(res.json) ? res.json[0] : null;
  return { status: res.status, row, raw: res.text };
}

async function applicationStatus(page, bearer, jobId) {
  const res = await pageFetch(page, {
    url: `https://www.foundit.in/home/api/applicationStatus?jobId=${encodeURIComponent(jobId)}`,
    method: "GET",
    bearer,
  });
  return res.json;
}

async function falconApply(page, bearer, jobId) {
  return pageFetch(page, {
    url: "https://www.foundit.in/falcon/api/users/v9/jobs/apply",
    method: "POST",
    bearer,
    body: { job: { jobId: Number(jobId) } },
  });
}

async function readAppliedTabCount(page) {
  await page.goto(
    "https://www.foundit.in/seeker/dashboard?application_source=Organic&activeTab=applied",
    { waitUntil: "domcontentloaded", timeout: 60000 }
  );
  await sleep(2500);
  return page.evaluate(() => {
    const t = document.body?.innerText || "";
    const m = t.match(/Showing\s+(\d+)\s+jobs/i);
    return m ? Number(m[1]) : null;
  });
}

async function dismissModals(page) {
  for (const sel of [
    "button:has-text('Got it')",
    "button:has-text('Got It')",
    "button:has-text('Later')",
    "button:has-text('Not now')",
    "button:has-text('Skip')",
    "[aria-label='Close']",
    "button:has-text('Close')",
  ]) {
    const el = page.locator(sel).first();
    if (await el.isVisible().catch(() => false)) {
      await el.click().catch(() => {});
      await sleep(300);
    }
  }
}

async function handleScreeningModal(page) {
  await dismissModals(page);
  // Prefer affirmative / available options for notice / location / CTC
  for (const sel of [
    "label:has-text('Yes')",
    "button:has-text('Yes')",
    "input[value='Yes']",
    "label:has-text('Immediate')",
    "label:has-text('Hyderabad')",
    "label:has-text('Remote')",
  ]) {
    const el = page.locator(sel).first();
    if (await el.isVisible().catch(() => false)) {
      await el.click().catch(() => {});
      await sleep(200);
    }
  }
  await page
    .evaluate(
      ({ cur, exp }) => {
        const inputs = [...document.querySelectorAll("input, textarea")];
        for (const inp of inputs) {
          if (inp.type === "file" || inp.offsetParent === null) continue;
          const ctx = (
            (inp.placeholder || "") +
            " " +
            (inp.name || "") +
            " " +
            (inp.getAttribute("aria-label") || "") +
            " " +
            (inp.closest("label,div,fieldset,li")?.innerText || "")
          ).slice(0, 240);
          if (/expected/i.test(ctx) && /ctc|salary|lpa|compensation/i.test(ctx)) {
            inp.value = String(exp);
            inp.dispatchEvent(new Event("input", { bubbles: true }));
          } else if (
            /current/i.test(ctx) &&
            /ctc|salary|lpa|compensation/i.test(ctx)
          ) {
            inp.value = String(cur);
            inp.dispatchEvent(new Event("input", { bubbles: true }));
          }
        }
      },
      { cur: CURRENT_CTC_LPA, exp: EXPECTED_CTC_LPA }
    )
    .catch(() => {});
  for (const sel of [
    "button:has-text('Submit')",
    "button:has-text('Apply')",
    "button:has-text('Continue')",
  ]) {
    const b = page.locator(sel).first();
    if (await b.isVisible().catch(() => false)) {
      await b.click().catch(() => {});
      await sleep(1500);
    }
  }
}

function ageDays(job) {
  const ts = Number(job.postedAt || job.freshness || 0);
  if (!ts) return null;
  return Math.floor((Date.now() - ts) / 86400000);
}

function isExternalRedirect(url) {
  if (!url) return false;
  try {
    const u = new URL(url);
    if (/foundit\.in$/i.test(u.hostname) || /monster/i.test(u.hostname))
      return false;
    return true;
  } catch {
    return /linkedin|workday|greenhouse|lever|smartrecruiters|ashby|icims|taleo|keka|myworkday/i.test(
      url
    );
  }
}

async function handleExternal(context, page, meta, redirectUrl, report) {
  const start = Date.now();
  let atsPage = null;
  try {
    atsPage = await context.newPage();
    await atsPage.goto(redirectUrl, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
  } catch (e) {
    report.blocked.push({
      ...meta,
      reason: "external_nav_failed",
      url: redirectUrl,
      error: String(e).slice(0, 200),
      path: "company_ATS",
    });
    if (atsPage) await atsPage.close().catch(() => {});
    return false;
  }

  while (Date.now() - start < MAX_EXTERNAL_MS) {
    const url = atsPage.url();
    const text = await atsPage
      .evaluate(() => (document.body?.innerText || "").slice(0, 2500))
      .catch(() => "");

    if (/captcha|verify you are human|hcaptcha|cloudflare/i.test(text + url)) {
      report.blocked.push({
        ...meta,
        reason: "captcha_wall",
        url,
        path: "company_ATS",
      });
      await atsPage.close().catch(() => {});
      return false;
    }

    if (
      /sign in|log in|login|auth\.linkedin|uas\/login/i.test(url + " " + text) &&
      !/application submitted|thank you for appl/i.test(text)
    ) {
      const guest = atsPage
        .locator(
          "text=/Continue as guest|Apply without|Don't have an account|Continue without/i"
        )
        .first();
      if (await guest.isVisible().catch(() => false)) {
        await guest.click().catch(() => {});
        await sleep(1000);
      } else {
        report.blocked.push({
          ...meta,
          reason: "ats_login_wall",
          url,
          path: "company_ATS",
        });
        await atsPage.close().catch(() => {});
        return false;
      }
    }

    // Cookie / privacy banners
    for (const sel of [
      "button:has-text('Accept')",
      "button:has-text('Accept All')",
      "button:has-text('I Agree')",
      "button:has-text('Allow all')",
    ]) {
      const el = atsPage.locator(sel).first();
      if (await el.isVisible().catch(() => false)) {
        await el.click().catch(() => {});
        await sleep(400);
      }
    }

    if (RESUME) {
      const fileInputs = atsPage.locator("input[type='file']");
      const n = await fileInputs.count().catch(() => 0);
      for (let i = 0; i < Math.min(n, 3); i++) {
        await fileInputs.nth(i).setInputFiles(RESUME).catch(() => {});
      }
      await sleep(800);
    }

    await atsPage
      .evaluate(
        ({ cur, exp, phone, email }) => {
          const fill = (inp, val) => {
            if (!inp || inp.disabled) return;
            if (inp.tagName === "SELECT") return;
            inp.focus();
            inp.value = String(val);
            inp.dispatchEvent(new Event("input", { bubbles: true }));
            inp.dispatchEvent(new Event("change", { bubbles: true }));
          };
          for (const inp of document.querySelectorAll("input, textarea")) {
            if (inp.type === "file" || inp.type === "hidden") continue;
            if (inp.offsetParent === null) continue;
            const ctx = (
              (inp.placeholder || "") +
              " " +
              (inp.name || "") +
              " " +
              (inp.id || "") +
              " " +
              (inp.getAttribute("aria-label") || "") +
              " " +
              (inp.closest("label,div,fieldset,li")?.innerText || "")
            )
              .toLowerCase()
              .slice(0, 260);
            if (/expected/.test(ctx) && /ctc|salary|compensation|lpa|pay/.test(ctx))
              fill(inp, exp);
            else if (
              /current/.test(ctx) &&
              /ctc|salary|compensation|lpa|pay/.test(ctx)
            )
              fill(inp, cur);
            else if (/phone|mobile|tel/.test(ctx) && !inp.value) fill(inp, phone);
            else if (/e-?mail/.test(ctx) && !inp.value) fill(inp, email);
            else if (/notice|availability|join/.test(ctx) && !inp.value)
              fill(inp, "Immediate");
            else if (/location|city|prefer/.test(ctx) && !inp.value)
              fill(inp, "Hyderabad / Remote");
            else if (/linkedin/.test(ctx) && !inp.value)
              fill(inp, "https://www.linkedin.com/in/");
          }
        },
        {
          cur: CURRENT_CTC_LPA,
          exp: EXPECTED_CTC_LPA,
          phone: "8790251698",
          email: "rafi.success@gmail.com",
        }
      )
      .catch(() => {});

    for (const sel of [
      "button:has-text('Submit application')",
      "button:has-text('Submit Application')",
      "button:has-text('Submit')",
      "button:has-text('Easy Apply')",
      "button:has-text('Apply')",
      "input[type='submit']",
    ]) {
      const b = atsPage.locator(sel).first();
      if (await b.isVisible().catch(() => false)) {
        await b.click().catch(() => {});
        await sleep(1800);
      }
    }

    const after = await atsPage
      .evaluate(() => (document.body?.innerText || "").slice(0, 3000))
      .catch(() => "");
    if (
      /thank you for appl|application (has been )?submitted|successfully submitted|we have received your application|application received|your application was sent/i.test(
        after
      )
    ) {
      const entry = {
        ...meta,
        path: "company_ATS",
        atsUrl: atsPage.url(),
        resume: RESUME,
        confirmed: true,
      };
      report.external.push(entry);
      report.applied.push(entry);
      await atsPage.close().catch(() => {});
      return true;
    }

    const next = atsPage
      .locator(
        "button:has-text('Next'), button:has-text('Continue'), button:has-text('Review'), button:has-text('Save and Continue')"
      )
      .first();
    if (await next.isVisible().catch(() => false)) {
      await next.click().catch(() => {});
      await sleep(1500);
      continue;
    }
    await sleep(1500);
    break;
  }

  report.blocked.push({
    ...meta,
    reason: "external_incomplete_or_timeout",
    url: atsPage.url(),
    path: "company_ATS",
  });
  await atsPage.close().catch(() => {});
  return false;
}

function writeReport(report) {
  report.tsEnd = new Date().toISOString();
  report.counts = {
    applied: report.applied.length,
    external: report.external.length,
    skipped: report.skipped.length,
    blocked: report.blocked.length,
    duplicates: report.duplicates.length,
    scanned: report.scanned,
    classifiedPass: report.classifiedPass,
  };
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
}

async function main() {
  if (!RESUME) {
    console.error("Rafi_Resume.docx missing");
    process.exit(4);
  }
  // Never call canJobApply — documented forbid
  void FORBIDDEN_DRY_RUN;

  const report = {
    ts: new Date().toISOString(),
    portal: "foundit",
    resume: RESUME,
    expectedCtcLpa: EXPECTED_CTC_LPA,
    currentCtcLpa: CURRENT_CTC_LPA,
    maxApplies: MAX_APPLIES,
    ageDays: AGE_DAYS,
    queries: QUERIES,
    appliedBefore: null,
    appliedAfter: null,
    scanned: 0,
    classifiedPass: 0,
    applied: [],
    external: [],
    skipped: [],
    blocked: [],
    duplicates: [],
    referralDrafts: [],
    note: "Foundit Raven+Falcon daily apply via CDP; eligibility via userJobInfo/applicationStatus only.",
  };

  let browser;
  try {
    browser = await chromium.connectOverCDP(CDP);
  } catch (e) {
    report.blocked.push({
      reason: "cdp_connect_failed",
      error: String(e).slice(0, 300),
    });
    writeReport(report);
    console.error(JSON.stringify(report, null, 2));
    process.exit(2);
  }

  const context = browser.contexts()[0] || (await browser.newContext());
  let page = await ensureFounditPage(context);
  await dismissModals(page);

  const body = await page.evaluate(() =>
    (document.body?.innerText || "").slice(0, 2000)
  );
  if (/sign in|log in|login/i.test(body) && !/hi[, ]+\s*rafi/i.test(body)) {
    report.blocked.push({ reason: "foundit_login_required" });
    writeReport(report);
    console.error(JSON.stringify(report, null, 2));
    process.exit(3);
  }
  report.loggedIn = true;

  report.appliedBefore = await readAppliedTabCount(page);
  console.log("Applied tab before:", report.appliedBefore);

  let bearer = await getBearer(context);
  if (!bearer) {
    report.blocked.push({ reason: "msssoat_bearer_missing" });
    writeReport(report);
    console.error(JSON.stringify(report, null, 2));
    process.exit(5);
  }

  const seen = new Set();
  const candidatesByAge = new Map(AGE_DAYS.map((d) => [d, []]));

  for (const q of QUERIES) {
    for (let start = 0; start < 60; start += 20) {
      let jobs = [];
      try {
        jobs = await ravenSearch(page, bearer, q, start);
      } catch (e) {
        report.blocked.push({
          reason: "raven_search_error",
          query: q,
          error: String(e).slice(0, 200),
        });
        break;
      }
      if (!jobs.length) break;
      for (const job of jobs) {
        const id = String(job.jobId || job.id || "");
        if (!id || seen.has(id)) continue;
        seen.add(id);
        report.scanned += 1;

        let classified = classifyJob(job);
        if (!classified.pass && classified.needsEnrich) {
          const detail = await jobDetail(page, bearer, id);
          if (detail) {
            classified = classifyJob({ ...job, ...detail });
          }
        }
        if (!classified.pass) {
          report.skipped.push({
            jobId: id,
            title: job.title || job.jobTitle,
            company: job.companyName || job.company?.name,
            reason: classified.reason,
          });
          continue;
        }
        report.classifiedPass += 1;
        const days = ageDays(job);
        const bucket =
          AGE_DAYS.find((d) => days == null || days <= d) ||
          AGE_DAYS[AGE_DAYS.length - 1];
        candidatesByAge.get(bucket).push({
          job,
          c: classified,
          days,
        });
      }
      await sleep(200);
    }
  }

  // Flatten in age order (newest windows first)
  const queue = [];
  const queued = new Set();
  for (const d of AGE_DAYS) {
    for (const item of candidatesByAge.get(d) || []) {
      const id = String(item.job.jobId || item.job.id);
      if (queued.has(id)) continue;
      queued.add(id);
      queue.push(item);
    }
  }
  report.queueSize = queue.length;
  console.log(
    `Scanned ${report.scanned}, pass ${report.classifiedPass}, queue ${queue.length}`
  );

  for (const item of queue) {
    if (report.applied.length >= MAX_APPLIES) break;
    const job = item.job;
    const c = item.c;
    const jobId = String(job.jobId || job.id);
    const meta = {
      jobId,
      title: c.title,
      company: c.company,
      loc: c.loc,
      days: item.days,
      skills: c.skills,
    };

    // Refresh bearer periodically
    if (report.applied.length % 8 === 0) {
      bearer = (await getBearer(context)) || bearer;
    }

    let uji;
    try {
      uji = await userJobInfo(page, bearer, jobId);
    } catch (e) {
      report.blocked.push({
        ...meta,
        reason: "userJobInfo_error",
        error: String(e).slice(0, 200),
      });
      continue;
    }
    if (uji.row?.applied) {
      report.duplicates.push({ ...meta, via: "userJobInfo" });
      continue;
    }
    const st = await applicationStatus(page, bearer, jobId).catch(() => null);
    if (st?.appliedAt) {
      report.duplicates.push({ ...meta, via: "applicationStatus" });
      continue;
    }

    const redirect =
      job.redirectUrl || job.applyUrl || c.redirectUrl || null;

    // Prefer Falcon Quick Apply for native / quickApply jobs; still try Falcon first.
    let applyRes;
    try {
      applyRes = await falconApply(page, bearer, jobId);
    } catch (e) {
      report.blocked.push({
        ...meta,
        reason: "falcon_error",
        error: String(e).slice(0, 200),
      });
      continue;
    }

    if (applyRes.status === 401 || /Kindly login|Bad Base64/i.test(applyRes.text)) {
      bearer = (await getBearer(context)) || bearer;
      applyRes = await falconApply(page, bearer, jobId).catch((e) => ({
        status: 0,
        json: { error: String(e) },
        text: String(e),
      }));
    }

    const msg = JSON.stringify(applyRes.json || {}).slice(0, 600);
    console.log("FALCON", jobId, applyRes.status, msg.slice(0, 160));

    if (/DUPLICATE_APPLY/i.test(msg)) {
      report.duplicates.push({ ...meta, via: "falcon" });
      continue;
    }

    if (/SCREENING_QUESTIONNAIRE/i.test(msg)) {
      try {
        await page.goto(`https://www.foundit.in/job/seeker/${jobId}`, {
          waitUntil: "domcontentloaded",
          timeout: 60000,
        });
        await sleep(1500);
        await handleScreeningModal(page);
        // confirm
        const uji2 = await userJobInfo(page, bearer, jobId);
        if (uji2.row?.applied) {
          report.applied.push({
            ...meta,
            path: "Foundit screening UI",
            resume: RESUME,
          });
          continue;
        }
      } catch (e) {
        report.blocked.push({
          ...meta,
          reason: "screening_ui_failed",
          detail: String(e).slice(0, 200),
        });
        continue;
      }
      report.blocked.push({
        ...meta,
        reason: "screening_unconfirmed",
        detail: msg.slice(0, 200),
      });
      continue;
    }

    if (
      applyRes.status !== 200 ||
      /CANNOT_APPLY|Kindly login|Bad Base64/i.test(msg)
    ) {
      // Fall back to external redirect if present
      if (redirect && isExternalRedirect(redirect)) {
        await handleExternal(context, page, meta, redirect, report);
        page = await ensureFounditPage(context);
        continue;
      }
      report.blocked.push({
        ...meta,
        reason: "falcon_non_success",
        detail: msg.slice(0, 240),
      });
      continue;
    }

    // Success path — may still include redirect for company ATS
    const redirectFromApply =
      applyRes.json?.redirectUrl ||
      applyRes.json?.data?.redirectUrl ||
      applyRes.json?.job?.redirectUrl ||
      redirect;

    if (redirectFromApply && isExternalRedirect(redirectFromApply)) {
      const ok = await handleExternal(
        context,
        page,
        meta,
        redirectFromApply,
        report
      );
      page = await ensureFounditPage(context);
      if (!ok) {
        // Falcon may have recorded apply even if ATS incomplete — verify
        const uji3 = await userJobInfo(page, bearer, jobId);
        if (uji3.row?.applied) {
          report.applied.push({
            ...meta,
            path: "Foundit Falcon (ATS incomplete)",
            atsUrl: redirectFromApply,
            resume: RESUME,
          });
        }
      }
      continue;
    }

    // Confirm via userJobInfo — do not invent applies
    const ujiConfirm = await userJobInfo(page, bearer, jobId);
    if (ujiConfirm.row?.applied || /SUCCESS|applied|APPLICATION/i.test(msg)) {
      // Prefer hard confirm
      if (ujiConfirm.row?.applied || /SUCCESS/i.test(msg)) {
        report.applied.push({
          ...meta,
          path: "Foundit Falcon Quick Apply",
          resume: RESUME,
          falcon: msg.slice(0, 180),
        });
      } else {
        report.blocked.push({
          ...meta,
          reason: "falcon_unclear_no_confirm",
          detail: msg.slice(0, 200),
        });
      }
    } else {
      // soft success language without confirmation
      report.blocked.push({
        ...meta,
        reason: "apply_not_confirmed",
        detail: msg.slice(0, 200),
      });
    }
    await sleep(400);
  }

  report.appliedAfter = await readAppliedTabCount(page).catch(() => null);
  report.deltaAppliedTab =
    report.appliedBefore != null && report.appliedAfter != null
      ? report.appliedAfter - report.appliedBefore
      : null;

  // Top 3 LinkedIn referral drafts for confirmed applies
  report.referralDrafts = report.applied.slice(0, 3).map((a) => ({
    role: a.title,
    company: a.company,
    message: `Hi — I just applied for ${a.title} at ${a.company} via Foundit. I'm a Solutions Architect / Tech Lead (.NET, Azure/AWS, microservices), Hyderabad + remote, immediate joiner, expected CTC 65 LPA. Would you be open to referring me or a quick 15–20 min screen? Thanks — Mohammed Abdul Rafi Ahmed`,
  }));

  writeReport(report);
  console.log(JSON.stringify(report.counts, null, 2));
  console.log(
    "Applied tab:",
    report.appliedBefore,
    "→",
    report.appliedAfter,
    "delta",
    report.deltaAppliedTab
  );
  console.log("Report:", OUT);

  // Keep CDP browser alive for the agent; disconnect only.
  await browser.close().catch(() => {});
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
