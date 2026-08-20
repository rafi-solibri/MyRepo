#!/usr/bin/env node
/**
 * Instahyre daily apply — CDP login check + job_search + apply API.
 *
 * Usage:
 *   bash scripts/preflight-portal-run.sh instahyre
 *   bash scripts/launch-chrome-cdp.sh instahyre
 *   node tools/instahyre/daily_apply.js
 *
 * Env:
 *   INSTAHYRE_CDP            default http://127.0.0.1:9222
 *   INSTAHYRE_REPORT         default /opt/cursor/artifacts/instahyre-apply-report.json
 *   INSTAHYRE_MAX_APPLIES    default 50
 *   INSTAHYRE_DRY_RUN=1      search/filter only (no POST apply)
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const { skipReason, locationOk, hasDotNet } = require("./filters");
const { findResume } = require("./resume");
const { uploadProfileResume } = require("./update_profile_resume");
const { tailorResumeForJob } = require("../resume_tailor");
const { completeExternalPage } = require("../ats/complete_page");
const { companyAllowed, allowlistActive } = require("../hitechcity/campus_allowlist");

const CDP = process.env.INSTAHYRE_CDP || "http://127.0.0.1:9222";
const OUT =
  process.env.INSTAHYRE_REPORT ||
  "/opt/cursor/artifacts/instahyre-apply-report.json";
const MAX_APPLIES = Number(process.env.INSTAHYRE_MAX_APPLIES || 50);
const DRY_RUN = process.env.INSTAHYRE_DRY_RUN === "1";
/** Per-job JD-tailored resume → Instahyre profile upload + ATS file. Default ON. */
const TAILOR = process.env.INSTAHYRE_TAILOR !== "0";
/** After the run, optionally re-upload canonical resume (off by default so last tailored stays). */
const RESTORE_CANONICAL = process.env.INSTAHYRE_RESTORE_RESUME === "1";

/** Instahyre public job pages are /job-{id}/, not /jobs/{id}/. */
function jobPublicUrl(job) {
  const id = job?.id || job?.job_id;
  const raw = job?.public_url || job?.opportunity_url || job?.job_url || "";
  if (raw) {
    if (/^https?:\/\//i.test(raw) || String(raw).startsWith("/")) return raw;
    return `/${raw}`;
  }
  return id ? `/job-${id}/` : "";
}

const SKILL_WAVES = [
  [".NET", "C#", "ASP.NET"],
  ["Azure", "AWS", "Microservices", "React", "Angular", "Node.js", "Python", "Java"],
  [
    "Engineering Manager",
    "Technical Architect",
    "Solution Architect",
    "Staff Engineer",
    "Principal Engineer",
    "Tech Lead",
    "Software Architect",
    "Backend",
    "Full Stack",
  ],
];

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function companyOf(job) {
  return (
    job?.employer?.company_name ||
    job?.company_name ||
    job?.company ||
    ""
  );
}

function locationsOf(job) {
  const loc = job?.locations;
  if (Array.isArray(loc)) return loc.join(",");
  return String(loc || "");
}

function skillsOf(job) {
  const kw = job?.keywords;
  if (Array.isArray(kw)) return kw.join(", ");
  return String(kw || job?.skills || "");
}

/** Prefer senior/.NET titles when ordering candidates; never used as hard skip. */
function preferScore(title, skills) {
  const t = title || "";
  let s = 0;
  if (/\b(principal|staff|architect|engineering manager|tech(?:nical)?\s+lead|em\b)\b/i.test(t))
    s += 40;
  if (/\b(lead|manager|head)\b/i.test(t)) s += 20;
  if (/\bsenior\b|\bsr\.?\b/i.test(t)) s += 10;
  if (hasDotNet(t, skills)) s += 25;
  if (/\b(azure|aws|cloud|\.net|c#|asp\.?net)\b/i.test(`${t} ${skills}`)) s += 5;
  return s;
}

function shouldHardSkipTitle(title) {
  // Extra title gates beyond skipReason (still title-first)
  if (/\b(intern|trainee|fresher|associate software|junior)\b/i.test(title || "")) {
    return "junior_title";
  }
  return null;
}

function isBrowserClosedError(e) {
  return /has been closed|Target closed|Browser closed|Connection closed|Session closed/i.test(
    String(e?.message || e)
  );
}

async function apiGet(page, url) {
  try {
    return await page.evaluate(async (u) => {
      const r = await fetch(u, {
        credentials: "include",
        headers: { "X-Requested-With": "XMLHttpRequest", Accept: "application/json" },
      });
      const text = await r.text();
      let json = null;
      try {
        json = JSON.parse(text);
      } catch {
        json = { raw: text.slice(0, 500) };
      }
      return { status: r.status, json };
    }, url);
  } catch (e) {
    if (isBrowserClosedError(e)) {
      return { status: 0, json: null, error: "browser_closed" };
    }
    throw e;
  }
}

async function apiPost(page, url, body) {
  return page.evaluate(
    async ({ u, body }) => {
      const csrf = document.cookie
        .split(";")
        .map((x) => x.trim())
        .find((x) => x.startsWith("csrftoken="))
        ?.split("=")[1];
      const r = await fetch(u, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          Accept: "application/json",
          ...(csrf ? { "X-CSRFToken": csrf } : {}),
        },
        body: JSON.stringify(body),
      });
      const text = await r.text();
      let json = null;
      try {
        json = JSON.parse(text);
      } catch {
        json = { raw: text.slice(0, 500) };
      }
      return { status: r.status, json };
    },
    { u: url, body }
  );
}

async function fetchFilterCounts(page) {
  const url =
    "https://www.instahyre.com/api/v1/candidate_opportunities/candidate_opportunity/fetch_filter_counts/";
  const res = await apiGet(page, url);
  return res.json?.status_counts || res.json || null;
}

/**
 * Recommended / undecided opportunities (status=0) are NOT always in job_search.
 * e.g. Uber Hyd Senior Staff Engineer only appeared on /candidate/opportunities/.
 */
function normalizeOpportunity(opp) {
  const job = opp?.job || {};
  const employer = opp?.employer || {};
  const id = job.id || job.job_id;
  if (!id) return null;
  const public_url = jobPublicUrl({
    id,
    public_url: job.opportunity_url || job.public_url || job.job_url || "",
  });
  return {
    id,
    title: job.title || job.candidate_title || "",
    job_title: job.title || job.candidate_title || "",
    locations: job.locations || "",
    keywords: job.keywords || [],
    employer: { company_name: employer.company_name || job.hiring_company_name || "" },
    company_name: employer.company_name || job.hiring_company_name || "",
    public_url,
    interview_status: opp.interview_status,
    is_interested: opp.is_interested || opp.interview_status === 1,
    opportunity_id: opp.id,
    _source: "opportunities",
  };
}

async function fetchUndecidedOpportunities(page, report) {
  const jobs = [];
  let offset = 0;
  const limit = 50;
  let pages = 0;
  while (pages < 6) {
    const url =
      `https://www.instahyre.com/api/v1/candidate_opportunities/candidate_opportunity/` +
      `?status=0&limit=${limit}&offset=${offset}`;
    let res;
    for (let attempt = 0; attempt < 4; attempt++) {
      res = await apiGet(page, url);
      if (res.error === "browser_closed") {
        report.blocked.push({ reason: "browser_closed", where: "opportunities" });
        return jobs;
      }
      if (res.status !== 429) break;
      report.rateLimited = (report.rateLimited || 0) + 1;
      await sleep(4000 + attempt * 2000);
    }
    if (res.status !== 200) {
      report.searchErrors.push({ skill: "opportunities:undecided", status: res.status });
      break;
    }
    const objects = res.json?.objects || [];
    for (const opp of objects) {
      const job = normalizeOpportunity(opp);
      if (job) jobs.push(job);
    }
    pages += 1;
    const next = res.json?.meta?.next;
    if (!next || objects.length < limit) break;
    offset += limit;
    await sleep(800);
  }
  return jobs;
}

function enqueueJob(job, seen, candidates, report) {
  const id = job.id || job.job_id;
  if (!id || seen.has(id)) return;
  seen.add(id);
  if (!job.public_url) job.public_url = jobPublicUrl(job);
  const title = job.title || job.job_title || "";
  const location = locationsOf(job);
  const skills = skillsOf(job);
  const company = companyOf(job);
  const salary = String(job.salary || job.ctc || "");

  if (job.interview_status === 1 || job.is_interested) {
    report.skipped.push({
      id,
      title,
      company,
      location,
      reason: "already_interested",
      source: job._source || "job_search",
    });
    return;
  }

  if (allowlistActive() && !companyAllowed(company)) {
    report.skipped.push({
      id,
      title,
      company,
      location,
      reason: "hitechcity_campus_allowlist",
      source: job._source || "job_search",
    });
    return;
  }

  if (!locationOk(location)) {
    report.skipped.push({
      id,
      title,
      company,
      location,
      reason: "location_not_hyd_remote",
      source: job._source || "job_search",
    });
    return;
  }

  const hard = shouldHardSkipTitle(title);
  if (hard) {
    report.skipped.push({
      id,
      title,
      company,
      location,
      reason: hard,
      source: job._source || "job_search",
    });
    return;
  }

  const reason = skipReason(title, { company, location, skills, salary });
  if (reason) {
    report.skipped.push({
      id,
      title,
      company,
      location,
      reason,
      source: job._source || "job_search",
    });
    return;
  }

  candidates.push({
    job,
    id,
    title,
    company,
    location,
    skills,
    score: preferScore(title, skills) + (job._source === "opportunities" ? 15 : 0),
  });
}

async function searchSkill(page, skill, location, report) {
  const jobs = [];
  let offset = 0;
  const limit = 50;
  let pages = 0;
  while (pages < 8) {
    const url =
      `https://www.instahyre.com/api/v1/job_search/?skills=${encodeURIComponent(skill)}` +
      `&location=${encodeURIComponent(location)}&limit=${limit}&offset=${offset}`;
    let res;
    for (let attempt = 0; attempt < 4; attempt++) {
      res = await apiGet(page, url);
      if (res.error === "browser_closed") {
        report.blocked.push({ reason: "browser_closed", where: `search:${skill}:${location}` });
        return jobs;
      }
      if (res.status !== 429) break;
      const wait = 4000 + attempt * 2000;
      report.rateLimited = (report.rateLimited || 0) + 1;
      await sleep(wait);
    }
    if (res.status !== 200) {
      report.searchErrors.push({ skill, location, status: res.status });
      break;
    }
    const objects = res.json?.objects || res.json?.results || [];
    for (const job of objects) jobs.push(job);
    pages += 1;
    const next = res.json?.meta?.next;
    if (!next || objects.length < limit) break;
    offset += limit;
    await sleep(1500);
  }
  return jobs;
}

async function applyJob(page, jobId) {
  return apiPost(
    page,
    "https://www.instahyre.com/api/v1/candidate_opportunities/candidate_opportunity/apply",
    { id: null, job_id: jobId, is_interested: true }
  );
}

/** Scrape public job page for JD text (API job_search detail has no description). */
async function fetchJdText(page, job) {
  const raw = jobPublicUrl(job);
  const url = /^https?:\/\//i.test(raw)
    ? raw
    : new URL(raw || `/job-${job.id || job.job_id}/`, "https://www.instahyre.com").href;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await sleep(1200);
    return await page.evaluate(() => {
      const text = document.body?.innerText || "";
      const start = text.search(/job description|responsibilities|requirements|about the (role|job)/i);
      const slice = (start >= 0 ? text.slice(start) : text).slice(0, 6000);
      return slice;
    });
  } catch {
    return "";
  }
}

/**
 * Build JD-tailored docx and push it to the Instahyre profile so recruiters
 * reviewing this interest see a keyword-aligned resume (native apply has no file attach).
 * Uses shared tools/resume_tailor.py via tailorResumeForJob (same as Foundit/LinkedIn).
 */
async function prepareTailoredResume(page, c, report) {
  const base = findResume();
  const jdText = await fetchJdText(page, c.job || { id: c.id, public_url: c.publicUrl });
  const tailored = tailorResumeForJob({
    master: base,
    title: c.title,
    company: c.company,
    description: jdText,
    skills: c.skills || c.job?.keywords || [],
    jobId: c.id,
  });
  if (!tailored.ok || !tailored.out) {
    report.tailorErrors = report.tailorErrors || [];
    report.tailorErrors.push({
      id: c.id,
      title: c.title,
      error: tailored.error || "tailor_failed",
    });
    return { resumePath: base, tailored: null, upload: null };
  }

  let upload = null;
  try {
    const profilePage = await page.context().newPage();
    try {
      upload = await uploadProfileResume(profilePage, tailored.out);
    } finally {
      await profilePage.close().catch(() => {});
    }
  } catch (e) {
    upload = { ok: false, reason: "upload_exception", error: String(e).slice(0, 200) };
  }
  if (!upload?.ok) {
    report.blocked.push({
      reason: "profile_resume_upload_failed",
      id: c.id,
      title: c.title,
      company: c.company,
      detail: upload?.reason || upload?.error || "unknown",
    });
  }
  return {
    resumePath: tailored.out,
    tailored: {
      path: tailored.out,
      headline: tailored.headline,
      skills: tailored.matchedSkills,
      bytes: tailored.bytes,
    },
    upload,
  };
}

async function spotCheckExternal(page, job, report) {
  const raw = jobPublicUrl(job);
  const url = /^https?:\/\//i.test(raw) ? raw : new URL(raw || `/job-${job.id}/`, page.url()).href;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await sleep(1200);
    const info = await page.evaluate(() => {
      const text = (document.body?.innerText || "").slice(0, 4000);
      const anchors = [...document.querySelectorAll("a")]
        .map((a) => ({ href: a.href, text: (a.innerText || "").trim().slice(0, 80) }))
        .filter((a) => {
          if (!a.href || /instahyre\.com/i.test(a.href)) return false;
          // Ignore social / share noise mistaken for ATS
          if (
            /facebook\.com|instagram\.com|twitter\.com|x\.com|linkedin\.com\/company|youtube\.com|t\.co/i.test(
              a.href
            )
          ) {
            return false;
          }
          return /apply (on|via|now)|company (site|website)|greenhouse|lever\.co|myworkdayjobs|ashbyhq|smartrecruiters|boards\.|jobs\.|careers\./i.test(
            `${a.text} ${a.href}`
          );
        });
      return {
        applicationSent: /application sent/i.test(text),
        interested: /interested|you have expressed interest/i.test(text),
        external: anchors.slice(0, 5),
      };
    });
    return info;
  } catch (e) {
    report.blocked.push({
      reason: "spot_check_failed",
      jobId: job.id,
      error: String(e).slice(0, 200),
    });
    return null;
  }
}

async function main() {
  const resume = findResume();
  const report = {
    ts: new Date().toISOString(),
    resume,
    maxApplies: MAX_APPLIES,
    dryRun: DRY_RUN,
    tailor: TAILOR,
    applied: [],
    skipped: [],
    blocked: [],
    searchErrors: [],
    tailorErrors: [],
    filterSelfCheck: {
      qe: skipReason("Quality Engineering Lead", { location: "Hyderabad" }),
      net: skipReason("Staff Software Engineer .NET", { location: "Hyderabad" }),
      ai: skipReason("AI Architect", { location: "Hyderabad", skills: ".NET" }),
    },
    countsBefore: null,
    countsAfter: null,
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
    report.blocked.push({ reason: "cdp_connect_failed", error: String(e).slice(0, 300) });
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.error(JSON.stringify(report, null, 2));
    process.exit(2);
  }

  try {
    const context = browser.contexts()[0] || (await browser.newContext());
    // Always newPage — pages()[0] may be a foreign portal tab (Foundit/Naukri/
    // LinkedIn) left from an earlier home daily; goto then ERR_ABORTs.
    const page = await context.newPage();
    await page.goto("https://www.instahyre.com/candidate/opportunities/", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await sleep(2000);
    const body = await page.evaluate(() => (document.body?.innerText || "").slice(0, 1500));
    if (
      /log in|sign in|candidate login/i.test(body) &&
      !/opportunities|interested|matching/i.test(body)
    ) {
      report.blocked.push({ reason: "instahyre_login_required" });
      fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
      console.error(JSON.stringify(report, null, 2));
      process.exitCode = 3;
      return;
    }
    report.loggedIn = true;
    report.countsBefore = await fetchFilterCounts(page);
    console.error(
      `[instahyre] logged in; interested=${report.countsBefore?.["1"]} undecided=${report.countsBefore?.["0"]}`
    );

    const seen = new Set();
    const candidates = [];

    // Recommended feed first — job_search often omits these Hyd matches.
    console.error("[instahyre] fetch undecided opportunities");
    const oppJobs = await fetchUndecidedOpportunities(page, report);
    report.opportunitiesUndecided = oppJobs.length;
    for (const job of oppJobs) enqueueJob(job, seen, candidates, report);
    if (candidates.length > 0) {
      candidates.sort((a, b) => b.score - a.score);
      for (const c of candidates) {
        if (report.applied.length >= MAX_APPLIES) break;
        await maybeApply(page, c, report);
      }
      candidates.length = 0;
    }

    let browserDied = false;
    try {
      for (const wave of SKILL_WAVES) {
        if (report.applied.length >= MAX_APPLIES) break;
        for (const skill of wave) {
          for (const loc of ["Hyderabad", "Work From Home"]) {
            console.error(`[instahyre] search skill=${skill} loc=${loc}`);
            const jobs = await searchSkill(page, skill, loc, report);
            if (jobs.length === 0 && report.blocked.some((b) => b.reason === "browser_closed")) {
              browserDied = true;
              break;
            }
            for (const job of jobs) enqueueJob(job, seen, candidates, report);
            await sleep(2500);
          }
          if (browserDied) break;
        }
        if (browserDied) break;
        // After wave 1 (.NET), if we already have plenty of open candidates, still continue
        // but prefer applying those first before broader skills.
        if (wave === SKILL_WAVES[0] && candidates.length > 0) {
          candidates.sort((a, b) => b.score - a.score);
          for (const c of candidates) {
            if (report.applied.length >= MAX_APPLIES) break;
            await maybeApply(page, c, report);
          }
          candidates.length = 0;
        }
      }

      if (!browserDied) {
        candidates.sort((a, b) => b.score - a.score);
        for (const c of candidates) {
          if (report.applied.length >= MAX_APPLIES) break;
          await maybeApply(page, c, report);
        }

        // Follow company-site ATS links (do not stop at "detected").
        const toCheck = report.applied.filter((a) => a.path === "Instahyre").slice(0, 12);
        const fallbackResume = findResume();
        for (const a of toCheck) {
          const info = await spotCheckExternal(page, { id: a.id, public_url: a.publicUrl }, report);
          if (!info) continue;
          a.ui = info.applicationSent
            ? "application_sent"
            : info.interested
              ? "interested"
              : "unknown";
          if (info.external?.length) {
            a.externalLinks = info.external;
            const href = info.external[0].href;
            const atsResume =
              (a.tailoredResume && fs.existsSync(a.tailoredResume) && a.tailoredResume) ||
              fallbackResume;
            const atsPage = await page.context().newPage();
            try {
              await atsPage.goto(href, { waitUntil: "domcontentloaded", timeout: 60000 });
              const done = await completeExternalPage(atsPage, atsResume);
              if (done.ok) {
                report.applied.push({
                  ...a,
                  path: "company_ATS",
                  atsUrl: done.url || href,
                  confirmed: true,
                  resumeUsed: atsResume,
                });
              } else {
                report.blocked.push({
                  reason: done.reason || "external_incomplete_or_timeout",
                  id: a.id,
                  title: a.title,
                  company: a.company,
                  url: done.url || href,
                  path: "company_ATS",
                });
              }
            } catch (e) {
              report.blocked.push({
                reason: "external_ats_error",
                id: a.id,
                error: String(e).slice(0, 200),
              });
            } finally {
              await atsPage.close().catch(() => {});
            }
          }
        }

        // Restore canonical resume on profile so the account is not left on a stretch title.
        if (TAILOR && RESTORE_CANONICAL && report.applied.some((a) => a.tailoredResume)) {
          try {
            const canon = findResume();
            const restorePage = await page.context().newPage();
            try {
              report.canonicalResumeRestored = await uploadProfileResume(restorePage, canon);
            } finally {
              await restorePage.close().catch(() => {});
            }
          } catch (e) {
            report.canonicalResumeRestored = {
              ok: false,
              error: String(e).slice(0, 200),
            };
          }
        }

        report.countsAfter = await fetchFilterCounts(page);
      }
    } catch (e) {
      if (isBrowserClosedError(e)) {
        browserDied = true;
        report.blocked.push({ reason: "browser_closed", detail: String(e.message || e).slice(0, 200) });
        console.error("[instahyre] browser closed mid-run — writing partial report");
      } else {
        throw e;
      }
    }

    report.summary = {
      applied: report.applied.length,
      skipped: report.skipped.length,
      blocked: report.blocked.length,
      uniqueJobsSeen: seen.size,
      opportunitiesUndecided: report.opportunitiesUndecided || 0,
      path: "Instahyre opportunities feed + job_search API (candidate_opportunity/apply)",
      partial: browserDied || undefined,
    };

    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
  } finally {
    // Never browser.close() over CDP (kills shared Chrome). Avoid disconnect()
    // hang — exit after writing the report.
  }
  process.exit(process.exitCode || 0);
}

async function maybeApply(page, c, report) {
  if (DRY_RUN) {
    report.applied.push({
      id: c.id,
      title: c.title,
      company: c.company,
      location: c.location,
      path: "dry_run",
      score: c.score,
    });
    return;
  }

  let tailoredResume = null;
  let tailorMeta = null;
  let profileUpload = null;
  if (TAILOR) {
    console.error(`[instahyre] tailor+upload resume for ${c.company} — ${c.title}`);
    const prep = await prepareTailoredResume(page, c, report);
    tailoredResume = prep.resumePath;
    tailorMeta = prep.tailored
      ? { headline: prep.tailored.headline, skills: prep.tailored.skills, path: prep.tailored.path }
      : null;
    profileUpload = prep.upload
      ? { ok: !!prep.upload.ok, reason: prep.upload.reason || null }
      : null;
  }

  await sleep(800);
  console.error(`[instahyre] apply ${c.company} — ${c.title}`);
  const res = await applyJob(page, c.id);
  const ok =
    res.status === 200 &&
    (res.json?.success === true || res.json?.opp_id || /success/i.test(JSON.stringify(res.json)));
  if (ok) {
    report.applied.push({
      id: c.id,
      title: c.title,
      company: c.company,
      location: c.location,
      path: "Instahyre",
      score: c.score,
      publicUrl: c.job.public_url || null,
      oppId: res.json?.opp_id || null,
      appliedOn: res.json?.applied_on || null,
      tailoredResume: tailoredResume || null,
      tailor: tailorMeta,
      profileResumeUpload: profileUpload,
    });
    // Persist incrementally so a late hang still leaves a usable report
    try {
      fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    } catch {
      /* ignore */
    }
    return;
  }
  const msg = JSON.stringify(res.json || {}).slice(0, 300);
  if (/already applied|already interested/i.test(msg)) {
    report.skipped.push({
      id: c.id,
      title: c.title,
      company: c.company,
      location: c.location,
      reason: "already_applied_api",
    });
    return;
  }
  report.blocked.push({
    reason: "apply_failed",
    id: c.id,
    title: c.title,
    company: c.company,
    status: res.status,
    body: msg,
  });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
