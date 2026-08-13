#!/usr/bin/env node
/**
 * Foundit daily apply runner — Raven search + classifyJob + Falcon apply,
 * with external ATS handoff when redirectUrl is present.
 *
 * Usage:
 *   bash scripts/preflight-portal-run.sh foundit
 *   bash scripts/launch-chrome-cdp.sh foundit
 *   node tools/foundit/daily_apply.js
 *
 * NEVER calls /home/api/canJobApply (it submits). Eligibility via userJobInfo /
 * applicationStatus only.
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
const { companyAllowed, allowlistActive } = require("../hitechcity/campus_allowlist");

const CDP = process.env.FOUNDIT_CDP || "http://127.0.0.1:9222";
const OUT =
  process.env.FOUNDIT_REPORT ||
  "/opt/cursor/artifacts/foundit-apply-report.json";
const MAX_APPLIES = Number(process.env.FOUNDIT_MAX_APPLIES || 50);
const ATS_CAP_MS = Number(process.env.FOUNDIT_ATS_CAP_MS || 3.5 * 60 * 1000);

const QUERIES = [
  ".net architect",
  ".net lead",
  "solutions architect .net",
  "engineering manager .net",
  "principal .net",
  "azure .net architect",
  "software architect .net",
];

/** Age windows in days; expand when fresher inventory is empty. */
const AGE_WINDOWS = [1, 3, 7, 14, 30, 90, 3650];

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function jwtFromMssoat(raw) {
  if (!raw) return null;
  let val = raw;
  try {
    val = decodeURIComponent(raw);
  } catch (_) {}
  const before = val.includes("::") ? val.split("::")[0] : val;
  let decoded;
  try {
    decoded = Buffer.from(before, "base64").toString("utf8");
  } catch (_) {
    return null;
  }
  const jwt = decoded.includes("::") ? decoded.split("::")[0] : decoded;
  return jwt.split(".").length === 3 ? jwt : null;
}

function jobAgeDays(job) {
  const ts = Number(job.freshness || job.updatedAt || job.postedAt || 0);
  if (!ts) return null;
  return (Date.now() - ts) / 86400000;
}

function withinAge(job, maxDays) {
  const age = jobAgeDays(job);
  if (age == null) return true;
  return age <= maxDays;
}

async function ensureFoundit(page) {
  if (!/foundit\.in/i.test(page.url())) {
    await page.goto("https://www.foundit.in/seeker/dashboard", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await sleep(800);
  }
}

async function pageFetch(page, url, opts = {}) {
  await ensureFoundit(page);
  return page.evaluate(
    async ({ url, opts }) => {
      const res = await fetch(url, {
        method: opts.method || "GET",
        headers: opts.headers || {},
        credentials: "include",
        body: opts.body != null ? opts.body : undefined,
      });
      const text = await res.text();
      let json = null;
      try {
        json = JSON.parse(text);
      } catch (_) {}
      return {
        status: res.status,
        ok: res.ok,
        json,
        text: text.slice(0, 2000),
      };
    },
    { url, opts }
  );
}

async function ravenSearch(page, query, locations, start = 0, limit = 20) {
  const body = {
    query,
    locations: locations || [],
    start,
    limit,
    sort: 1,
  };
  const res = await pageFetch(
    page,
    "https://www.foundit.in/raven/api/public/search/v1/jobs",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "x-source-site-context": "rexmonster",
        "x-source-country": "IN",
      },
      body: JSON.stringify(body),
    }
  );
  const data = Array.isArray(res.json?.data) ? res.json.data : [];
  return { status: res.status, data };
}

async function jobDetail(page, jobId) {
  const res = await pageFetch(
    page,
    `https://www.foundit.in/home/api/jobDetail?jobId=${jobId}`,
    { headers: { Accept: "application/json" } }
  );
  return res.json && typeof res.json === "object" ? res.json : null;
}

async function alreadyApplied(page, jobId) {
  const uji = await pageFetch(page, "https://www.foundit.in/home/api/userJobInfo", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify([Number(jobId) || jobId]),
  });
  const row = Array.isArray(uji.json) ? uji.json[0] : null;
  if (row?.applied) return { applied: true, via: "userJobInfo" };

  const st = await pageFetch(
    page,
    `https://www.foundit.in/home/api/applicationStatus?jobId=${jobId}`,
    { headers: { Accept: "application/json" } }
  );
  if (st.json?.appliedAt) return { applied: true, via: "applicationStatus" };
  return { applied: false, uji: row, st: st.json };
}

async function falconApply(page, jwt, jobId) {
  return pageFetch(page, "https://www.foundit.in/falcon/api/users/v9/jobs/apply", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      Authorization: `Bearer ${jwt}`,
      "x-source-site-context": "rexmonster",
      "x-source-country": "IN",
    },
    body: JSON.stringify({ job: { jobId: Number(jobId) || jobId } }),
  });
}

async function readAppliedCount(page) {
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

function readLoginSignals() {
  const text = document.body?.innerText || "";
  // Prefer real greeting; ignore transient "Hi, Seeker" placeholders.
  const hits = [...text.matchAll(/Hi,\s*([^\n]+)/gi)].map((m) => m[1].trim());
  const hasRafi = hits.some((h) => /rafi/i.test(h));
  const loginWall = /sign in|log in|login/i.test(text) && !hasRafi;
  return { hits, hasRafi, loginWall };
}

async function confirmLogin(page) {
  const urls = [
    "https://www.foundit.in/seeker/dashboard",
    "https://www.foundit.in/home/user",
  ];
  let last = { hits: [], hasRafi: false, loginWall: true };
  for (const url of urls) {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
    // Header personalization can lag; poll so we do not false-fail on "Hi, Seeker".
    const deadline = Date.now() + 12000;
    while (Date.now() < deadline) {
      last = await page.evaluate(readLoginSignals);
      if (last.hasRafi && !last.loginWall) {
        last.url = url;
        return last;
      }
      await sleep(800);
    }
    last.url = url;
  }
  return last;
}

async function tryDismissScreening(page) {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    const clicked = await page.evaluate(() => {
      const buttons = [...document.querySelectorAll("button, a, [role=button]")];
      const prefer = (re) =>
        buttons.find((b) => re.test((b.innerText || b.textContent || "").trim()));
      const yes = prefer(/^(yes|y)$/i) || prefer(/\byes\b/i);
      const submit =
        prefer(/^submit$/i) ||
        prefer(/submit application/i) ||
        prefer(/^apply$/i);
      if (yes) {
        yes.click();
        return "yes";
      }
      if (submit) {
        submit.click();
        return "submit";
      }
      return null;
    });
    if (!clicked) break;
    await sleep(1000);
  }
}

async function handleExternalAts(context, resumePath, job, report) {
  const url = job.redirectUrl;
  if (!url) return { status: "no_redirect" };
  const page = await context.newPage();
  const started = Date.now();
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
    await sleep(2000);

    // LinkedIn Easy Apply
    if (/linkedin\.com/i.test(url)) {
      const easy = page
        .locator(
          "button.jobs-apply-button, button:has-text('Easy Apply'), button:has-text('Continue applying')"
        )
        .first();
      if (await easy.isVisible({ timeout: 5000 }).catch(() => false)) {
        await easy.click().catch(() => {});
        await sleep(1500);
        // Multi-step Easy Apply — advance until done or cap
        while (Date.now() - started < ATS_CAP_MS) {
          // Upload resume if file input present
          const fileInputs = page.locator('input[type="file"]');
          const n = await fileInputs.count();
          for (let i = 0; i < n; i++) {
            const input = fileInputs.nth(i);
            if (await input.isVisible().catch(() => false)) {
              await input.setInputFiles(resumePath).catch(() => {});
            }
          }
          // Fill CTC / notice common fields
          await page.evaluate(
            ({ cur, exp }) => {
              const fill = (el, val) => {
                if (!el || el.disabled) return;
                el.focus();
                el.value = String(val);
                el.dispatchEvent(new Event("input", { bubbles: true }));
                el.dispatchEvent(new Event("change", { bubbles: true }));
              };
              for (const el of document.querySelectorAll("input, textarea")) {
                const label = (
                  (el.getAttribute("aria-label") || "") +
                  " " +
                  (el.name || "") +
                  " " +
                  (el.placeholder || "")
                ).toLowerCase();
                if (/expected|current/.test(label) && /ctc|salary|compensation|pay/.test(label)) {
                  fill(el, /expected/.test(label) ? exp : cur);
                }
                if (/notice/.test(label)) fill(el, "Immediate");
                if (/phone|mobile/.test(label) && !el.value) fill(el, "8790251698");
              }
            },
            { cur: CURRENT_CTC_LPA, exp: EXPECTED_CTC_LPA }
          );

          const done = await page
            .locator(
              "text=/application submitted|applied|your application was sent/i"
            )
            .first()
            .isVisible()
            .catch(() => false);
          if (done) {
            return { status: "linkedin_easy_apply_ok", url };
          }

          const next = page
            .locator(
              "button:has-text('Submit application'), button:has-text('Review'), button:has-text('Next'), button:has-text('Continue'), button:has-text('Review your application')"
            )
            .first();
          if (!(await next.isVisible({ timeout: 2000 }).catch(() => false))) {
            break;
          }
          const label = ((await next.innerText().catch(() => "")) || "").toLowerCase();
          await next.click().catch(() => {});
          await sleep(1500);
          if (/submit/.test(label)) {
            await sleep(2000);
            const confirmed = await page
              .locator("text=/application submitted|applied|your application was sent/i")
              .first()
              .isVisible()
              .catch(() => false);
            return {
              status: confirmed ? "linkedin_easy_apply_ok" : "linkedin_submit_clicked",
              url,
            };
          }
        }
        return { status: "linkedin_ats_cap_or_incomplete", url };
      }
      // Sign-in wall
      if (/\/uas\/login|sign in/i.test(page.url() + (await page.title()))) {
        return { status: "linkedin_login_wall", url };
      }
      return { status: "linkedin_no_easy_apply", url };
    }

    // Workday / Greenhouse / generic ATS: open Apply, upload resume, fill CTC, submit
    const isWorkday = /myworkdayjobs\.com|workday\.com/i.test(url);
    let applyOpened = false;
    while (Date.now() - started < ATS_CAP_MS) {
      const body = await page.evaluate(() =>
        (document.body?.innerText || "").slice(0, 1200)
      );
      if (/captcha|hcaptcha|recaptcha|verify you are human/i.test(body)) {
        return { status: "ats_captcha", url: page.url() };
      }
      if (
        (/sign in|log in|create account|sso/i.test(body) &&
          /password/i.test(body) &&
          !/apply manually|autofill with resume/i.test(body)) ||
        (/create account\/sign in|create account\/sign-in/i.test(body) &&
          /current step/i.test(body))
      ) {
        return { status: "ats_login_wall", url: page.url() };
      }
      if (/thank you for (your )?appl|application submitted|successfully submitted|we have received your application/i.test(body)) {
        return { status: "ats_submitted", url: page.url() };
      }

      // Job posting landings (Workday/Greenhouse/etc.) → open Apply once before form fill
      if (!applyOpened) {
        const applyBtn = page
          .locator(
            'a[data-automation-id="adventureButton"], button[data-automation-id="adventureButton"], a:has-text("Apply Manually"), button:has-text("Apply Manually"), a:has-text("Apply"), button:has-text("Apply"), a:has-text("Apply for this job"), button:has-text("Apply for this job")'
          )
          .first();
        if (await applyBtn.isVisible({ timeout: 2500 }).catch(() => false)) {
          await applyBtn.click().catch(() => {});
          applyOpened = true;
          await sleep(2000);
          const manual = page
            .locator(
              'a[data-automation-id="applyManually"], button:has-text("Apply Manually"), a:has-text("Apply Manually")'
            )
            .first();
          if (await manual.isVisible({ timeout: 3000 }).catch(() => false)) {
            await manual.click().catch(() => {});
            await sleep(2000);
          }
          continue;
        }
        applyOpened = true;
      }

      const fileInputs = page.locator('input[type="file"]');
      const n = await fileInputs.count();
      for (let i = 0; i < n; i++) {
        await fileInputs.nth(i).setInputFiles(resumePath).catch(() => {});
      }
      // Workday "Autofill with Resume" / Select Files
      const autofill = page
        .locator(
          'button:has-text("Autofill with Resume"), button:has-text("Select Files"), label:has-text("Select Files")'
        )
        .first();
      if (await autofill.isVisible({ timeout: 800 }).catch(() => false)) {
        // If a hidden file input exists near autofill, set it; else click opens picker (CDP may not)
        if (n === 0) {
          await autofill.click().catch(() => {});
          await sleep(800);
        }
      }

      await page.evaluate(
        ({ cur, exp }) => {
          const fill = (el, val) => {
            if (!el || el.disabled) return;
            el.focus();
            el.value = String(val);
            el.dispatchEvent(new Event("input", { bubbles: true }));
            el.dispatchEvent(new Event("change", { bubbles: true }));
          };
          for (const el of document.querySelectorAll("input, textarea, select")) {
            const label = (
              (el.getAttribute("aria-label") || "") +
              " " +
              (el.name || "") +
              " " +
              (el.id || "") +
              " " +
              (el.placeholder || "") +
              " " +
              (el.getAttribute("data-automation-id") || "")
            ).toLowerCase();
            if (/expected/.test(label) && /ctc|salary|compensation|pay|annual/.test(label))
              fill(el, exp);
            else if (/current/.test(label) && /ctc|salary|compensation|pay|annual/.test(label))
              fill(el, cur);
            if (/notice/.test(label)) fill(el, "Immediate");
            if (/phone|mobile/.test(label) && !el.value) fill(el, "8790251698");
            if (/email/.test(label) && !el.value) fill(el, "rafi.success@gmail.com");
            if (/first\s*name|givenname/i.test(label) && !el.value) fill(el, "Mohammed Abdul Rafi");
            if (/last\s*name|familyname|surname/i.test(label) && !el.value) fill(el, "Ahmed");
          }
        },
        { cur: CURRENT_CTC_LPA, exp: EXPECTED_CTC_LPA }
      );

      const submit = page
        .locator(
          'button[data-automation-id="bottom-navigation-next-button"]:has-text("Submit"), button:has-text("Submit Application"), button:has-text("Submit"), button[type=submit], input[type=submit]'
        )
        .first();
      if (await submit.isVisible({ timeout: 1500 }).catch(() => false)) {
        const label = ((await submit.innerText().catch(() => "")) || "").toLowerCase();
        await submit.click().catch(() => {});
        await sleep(2000);
        const ok = /thank|submitted|application received|successfully applied|we have received/i.test(
          await page.evaluate(() => document.body?.innerText || "")
        );
        if (ok || /submit/.test(label)) {
          return {
            status: ok ? "ats_submitted" : "ats_submit_clicked",
            url: page.url(),
          };
        }
      }
      const next = page
        .locator(
          'button[data-automation-id="bottom-navigation-next-button"], button:has-text("Next"), button:has-text("Continue"), button:has-text("Save and Continue")'
        )
        .first();
      if (await next.isVisible({ timeout: 1000 }).catch(() => false)) {
        await next.click().catch(() => {});
        await sleep(1200);
        continue;
      }
      // No progress controls — avoid busy-spin; wait briefly then re-check body
      await sleep(1500);
      const body2 = await page.evaluate(() =>
        (document.body?.innerText || "").slice(0, 800)
      );
      if (/thank you for (your )?appl|application submitted|successfully submitted/i.test(body2)) {
        return { status: "ats_submitted", url: page.url() };
      }
      if (!isWorkday || applyOpened) break;
      applyOpened = true; // prevent infinite Apply-search loop
    }
    return { status: "ats_incomplete_or_cap", url: page.url() };
  } catch (e) {
    report.blocked.push({
      jobId: job.jobId,
      title: job.title,
      reason: "ats_error",
      error: String(e).slice(0, 300),
      url,
    });
    return { status: "ats_error", url, error: String(e).slice(0, 200) };
  } finally {
    await page.close().catch(() => {});
  }
}

async function collectCandidates(page, maxDays, seen) {
  const out = [];
  const locationSets = [
    ["hyderabad / secunderabad", "remote"],
    [], // unrestricted — local filter via classifyJob / JD enrich
  ];

  for (const query of QUERIES) {
    for (const locs of locationSets) {
      for (let start = 0; start < 60; start += 20) {
        const { data } = await ravenSearch(page, query, locs, start, 20);
        if (!data.length) break;
        for (const job of data) {
          const id = String(job.jobId || job.id || "");
          if (!id || seen.has(id)) continue;
          if (!withinAge(job, maxDays)) continue;
          seen.add(id);
          // Normalize skills alias for classifyJob
          if (!job.skills && job.itSkills) job.skills = job.itSkills;
          out.push(job);
        }
        if (data.length < 20) break;
      }
    }
  }
  return out;
}

async function main() {
  const resume = findResume();
  const report = {
    ts: new Date().toISOString(),
    resume,
    expectedCtcLpa: EXPECTED_CTC_LPA,
    currentCtcLpa: CURRENT_CTC_LPA,
    forbiddenDryRun: FORBIDDEN_DRY_RUN,
    appliedBefore: null,
    appliedAfter: null,
    applied: [],
    skipped: [],
    blocked: [],
    duplicates: [],
    referralDrafts: [],
    queries: QUERIES,
    maxApplies: MAX_APPLIES,
  };

  if (!resume) {
    report.blocked.push({ reason: "resume_missing" });
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(2);
  }

  let browser;
  try {
    browser = await chromium.connectOverCDP(CDP);
  } catch (e) {
    report.blocked.push({
      reason: "cdp_connect_failed",
      error: String(e).slice(0, 300),
    });
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(2);
  }

  try {
    const context = browser.contexts()[0] || (await browser.newContext());
    const page = await context.newPage();

    const login = await confirmLogin(page);
    report.login = login;
    if (!login.hasRafi || login.loginWall) {
      report.blocked.push({ reason: "foundit_login_required" });
      fs.mkdirSync(path.dirname(OUT), { recursive: true });
      fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
      console.error(JSON.stringify(report, null, 2));
      process.exit(3);
    }
    report.loggedIn = true;

    report.appliedBefore = await readAppliedCount(page);

    const cookies = await context.cookies("https://www.foundit.in");
    const jwt = jwtFromMssoat(cookies.find((c) => c.name === "MSSOAT")?.value);
    if (!jwt) {
      report.blocked.push({ reason: "mssoat_jwt_missing" });
      fs.mkdirSync(path.dirname(OUT), { recursive: true });
      fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
      console.error(JSON.stringify(report, null, 2));
      process.exit(3);
    }
    report.jwtOk = true;

    await ensureFoundit(page);
    const seen = new Set();
    let applies = 0;

    for (const maxDays of AGE_WINDOWS) {
      if (applies >= MAX_APPLIES) break;
      report.ageWindowUsed = maxDays;
      const candidates = await collectCandidates(page, maxDays, seen);
      report[`candidates_d${maxDays}`] = candidates.length;

      for (const raw of candidates) {
        if (applies >= MAX_APPLIES) break;
        let job = raw;
        let verdict = classifyJob(job);

        if (!verdict.pass && verdict.needsEnrich) {
          const detail = await jobDetail(page, job.jobId || job.id);
          if (detail) {
            job = { ...job, ...detail, skills: detail.skills || detail.itSkills || job.skills };
            verdict = classifyJob(job);
          }
        } else if (verdict.pass && !job.description) {
          // Enrich for redirectUrl / questionnaire when applying
          const detail = await jobDetail(page, job.jobId || job.id);
          if (detail) {
            job = {
              ...job,
              ...detail,
              skills: job.skills || detail.skills || detail.itSkills,
              redirectUrl: job.redirectUrl || detail.redirectUrl,
            };
            verdict = classifyJob(job);
            if (!verdict.pass) {
              report.skipped.push({
                jobId: String(job.jobId || job.id),
                title: job.title,
                company: job.companyName || job.company?.name,
                reason: verdict.reason,
                stage: "post-enrich",
              });
              continue;
            }
          }
        }

        if (!verdict.pass) {
          report.skipped.push({
            jobId: String(job.jobId || job.id),
            title: job.title || "",
            company: job.companyName || job.company?.name || "",
            reason: verdict.reason,
          });
          continue;
        }

        const companyName = job.companyName || job.company?.name || verdict.company || "";
        if (allowlistActive() && !companyAllowed(companyName)) {
          report.skipped.push({
            jobId: String(job.jobId || job.id),
            title: job.title || "",
            company: companyName,
            reason: "hitechcity_campus_allowlist",
          });
          continue;
        }

        const jobId = String(verdict.jobId || job.jobId || job.id);
        const elig = await alreadyApplied(page, jobId);
        if (elig.applied) {
          report.duplicates.push({
            jobId,
            title: verdict.title,
            company: verdict.company,
            via: elig.via,
          });
          continue;
        }

        // Prefer Foundit native apply first (registers on Foundit even for some externals)
        const applyRes = await falconApply(page, jwt, jobId);
        const bodyStr = JSON.stringify(applyRes.json || {});

        await tryDismissScreening(page);

        const duplicate =
          /DUPLICATE_APPLY/i.test(bodyStr) || /already\s*applied/i.test(bodyStr);
        if (duplicate) {
          report.duplicates.push({
            jobId,
            title: verdict.title,
            company: verdict.company,
            via: "falcon_DUPLICATE_APPLY",
          });
          continue;
        }

        const screeningBlock = /SCREENING_QUESTIONNAIRE|CANNOT_APPLY/i.test(bodyStr);
        const falconOk =
          applyRes.ok &&
          !screeningBlock &&
          (/SUCCESS|APPLIED|"status"\s*:\s*"OK"|applyStatus":"SUCCESS/i.test(bodyStr) ||
            (applyRes.status === 200 &&
              applyRes.json != null &&
              !/error|fail|cannot/i.test(bodyStr)));

        let pathLabel = "Foundit Falcon";
        let ats = null;
        const redirectUrl = job.redirectUrl || verdict.redirectUrl;
        if (redirectUrl && !/foundit\.in/i.test(redirectUrl)) {
          ats = await handleExternalAts(
            context,
            resume,
            { ...verdict, jobId, redirectUrl },
            report
          );
          pathLabel = `Foundit + ATS ${redirectUrl}`;
          await ensureFoundit(page);
        }

        if (falconOk || (ats && /_ok|_submitted|submit_clicked/i.test(ats.status))) {
          const entry = {
            jobId,
            title: verdict.title,
            company: verdict.company,
            loc: verdict.loc,
            path: pathLabel,
            falconStatus: applyRes.status,
            falconNext: applyRes.json?.next || applyRes.json?.responseType || null,
            ats,
            ageDays: jobAgeDays(job),
          };
          // Count intentional applies only when Falcon accepted or ATS progressed
          if (
            falconOk ||
            (ats &&
              /linkedin_easy_apply_ok|ats_submitted|linkedin_submit_clicked|ats_submit_clicked/i.test(
                ats.status
              ))
          ) {
            report.applied.push(entry);
            applies += 1;
            if (report.referralDrafts.length < 3) {
              report.referralDrafts.push({
                company: verdict.company,
                title: verdict.title,
                draft: `Hi — I'm applying for ${verdict.title} at ${verdict.company}. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)`,
              });
            }
          } else if (screeningBlock) {
            report.blocked.push({
              jobId,
              title: verdict.title,
              company: verdict.company,
              reason: "screening_questionnaire",
              falcon: applyRes.json,
            });
          } else {
            report.blocked.push({
              jobId,
              title: verdict.title,
              company: verdict.company,
              reason: "apply_uncertain",
              falconStatus: applyRes.status,
              falcon: applyRes.json,
              ats,
            });
          }
        } else if (screeningBlock) {
          report.blocked.push({
            jobId,
            title: verdict.title,
            company: verdict.company,
            reason: "screening_questionnaire",
            falcon: applyRes.json,
          });
        } else if (ats && /login_wall|captcha/i.test(ats.status)) {
          report.blocked.push({
            jobId,
            title: verdict.title,
            company: verdict.company,
            reason: ats.status,
            url: redirectUrl,
            falconStatus: applyRes.status,
            falcon: applyRes.json,
          });
        } else {
          report.blocked.push({
            jobId,
            title: verdict.title,
            company: verdict.company,
            reason: "falcon_apply_failed",
            falconStatus: applyRes.status,
            falcon: applyRes.json,
            text: applyRes.text,
          });
        }

        // Persist incremental progress
        fs.mkdirSync(path.dirname(OUT), { recursive: true });
        fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
      }

      // Expand age window only if we still have apply budget and few new applies from fresher days
      if (applies > 0 && maxDays >= 14 && applies >= Math.min(10, MAX_APPLIES)) {
        // keep going while inventory remains — do not soft-stop
      }
    }

    report.appliedAfter = await readAppliedCount(page);
    report.appliedDelta =
      report.appliedBefore != null && report.appliedAfter != null
        ? report.appliedAfter - report.appliedBefore
        : null;
    report.intentionalApplies = report.applied.length;

    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close().catch(() => {});
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
