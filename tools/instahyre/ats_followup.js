#!/usr/bin/env node
/**
 * Follow-up: open already-interested job pages and complete company-site
 * ATS when a real external apply link exists.
 *
 * Does not POST in-app apply (skip already-applied). Never invents success.
 *
 *   CDP=http://127.0.0.1:9222 node tools/<portal>/ats_followup.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const { skipReason, locationOk, hasDotNet } = require("./filters");
const { findResume } = require("./resume");
const { completeExternalPage } = require("../ats/complete_page");

const CDP = process.env.CDP || "http://127.0.0.1:9222";
const OUT = process.env.ATS_REPORT || "/opt/cursor/artifacts/portal-ats-followup.json";
const MAX_COMPLETE = Number(process.env.ATS_MAX || 12);

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function isBrowserClosedError(e) {
  return /has been closed|Target closed|Browser closed|Connection closed|Session closed/i.test(
    String(e?.message || e)
  );
}

function absUrl(page, pathOrUrl) {
  if (!pathOrUrl) return pathOrUrl;
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl;
  return new URL(pathOrUrl, page.url()).href;
}

async function apiGet(page, url) {
  return page.evaluate(async (u) => {
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
}

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

function publicUrlFromJob(job) {
  const pathOrUrl =
    job.opportunity_url ||
    job.public_url ||
    job.job_url ||
    job.url ||
    "";
  if (pathOrUrl) {
    return pathOrUrl.startsWith("http") || pathOrUrl.startsWith("/")
      ? pathOrUrl
      : `/${pathOrUrl}`;
  }
  const id = job.id || job.job_id;
  if (!id) return null;
  return `/job-${id}/`;
}

async function findExternalLinks(page) {
  return page.evaluate(() => {
    const text = (document.body?.innerText || "").slice(0, 4000);
    const host = location.hostname;
    const anchors = [...document.querySelectorAll("a")]
      .map((a) => ({ href: a.href, text: (a.innerText || "").trim().slice(0, 80) }))
      .filter((a) => {
        if (!a.href) return false;
        if (a.href.includes(host)) return false;
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
      url: location.href,
      title: document.title,
      applicationSent: /application sent/i.test(text),
      interested: /interested|you have expressed interest/i.test(text),
      notFound: /page not found|404/i.test(text),
      external: anchors.slice(0, 6),
    };
  });
}

async function fetchInterested(page, report) {
  const jobs = [];
  let offset = 0;
  const limit = 50;
  const origin = new URL(page.url()).origin;
  for (let pages = 0; pages < 12; pages++) {
    const url =
      `${origin}/api/v1/candidate_opportunities/candidate_opportunity/` +
      `?status=1&limit=${limit}&offset=${offset}`;
    const res = await apiGet(page, url);
    if (res.status !== 200) {
      report.blocked.push({ reason: "interested_fetch_failed", status: res.status });
      break;
    }
    const objects = res.json?.objects || [];
    for (const opp of objects) {
      const job = opp.job || {};
      const employer = opp.employer || {};
      const id = job.id || job.job_id;
      if (!id) continue;
      jobs.push({
        id,
        title: job.title || job.candidate_title || "",
        locations: job.locations || "",
        keywords: Array.isArray(job.keywords) ? job.keywords.join(", ") : String(job.keywords || ""),
        company: employer.company_name || job.hiring_company_name || "",
        opportunity_url: job.opportunity_url || "",
        public_url: publicUrlFromJob({ ...job, id }),
      });
    }
    if (!res.json?.meta?.next || objects.length < limit) break;
    offset += limit;
    await sleep(400);
  }
  return jobs;
}

async function main() {
  const resume = findResume();
  const report = {
    ts: new Date().toISOString(),
    resume,
    applied: [],
    skipped: [],
    blocked: [],
    probed: [],
  };
  if (!resume) {
    report.blocked.push({ reason: "resume_missing" });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    process.exit(2);
  }

  const browser = await chromium.connectOverCDP(CDP);
  const context = browser.contexts()[0] || (await browser.newContext());
  const page = context.pages()[0] || (await context.newPage());
  if (!/candidate\/opportunities/i.test(page.url() || "")) {
    const seed = process.env.PORTAL_START_URL;
    if (seed) {
      await page.goto(seed, { waitUntil: "domcontentloaded", timeout: 60000 });
    } else {
      const origin = new URL(page.url() || "http://127.0.0.1").origin;
      await page.goto(`${origin}/candidate/opportunities/`, {
        waitUntil: "domcontentloaded",
        timeout: 60000,
      });
    }
  }
  await sleep(1500);

  let interested = await fetchInterested(page, report);
  report.interestedFetched = interested.length;

  if (interested.length < 20) {
    const artDir = "/opt/cursor/artifacts";
    const applyPath =
      process.env.APPLY_REPORT ||
      (fs.existsSync(artDir)
        ? fs
            .readdirSync(artDir)
            .filter((f) => f.endsWith("-apply-report.json"))
            .map((f) => path.join(artDir, f))[0]
        : null);
    try {
      if (!applyPath) throw new Error("apply_report_missing");
      const apply = JSON.parse(fs.readFileSync(applyPath, "utf8"));
      const extra = [];
      for (const row of apply.skipped || []) {
        if (row.reason !== "already_interested") continue;
        extra.push({
          id: row.id,
          title: row.title || "",
          locations: row.location || "",
          keywords: "",
          company: row.company || "",
          opportunity_url: "",
          public_url: `/job-${row.id}/`,
        });
      }
      report.applyReportFallback = extra.length;
      interested = extra;
    } catch (e) {
      report.blocked.push({ reason: "apply_report_fallback_failed", error: String(e).slice(0, 200) });
    }
  }

  const candidates = [];
  for (const job of interested) {
    if (!locationOk(job.locations, job.title, job.keywords)) {
      report.skipped.push({ id: job.id, title: job.title, company: job.company, reason: "location" });
      continue;
    }
    const reason = skipReason(job.title, {
      company: job.company,
      location: job.locations,
      skills: job.keywords,
    });
    if (reason) {
      report.skipped.push({ id: job.id, title: job.title, company: job.company, reason });
      continue;
    }
    candidates.push({ ...job, score: preferScore(job.title, job.keywords) });
  }
  candidates.sort((a, b) => b.score - a.score);
  report.candidates = candidates.length;
  console.error(`[ats] interested=${interested.length} hydEligible=${candidates.length}`);

  for (const job of candidates) {
    if (report.applied.length >= MAX_COMPLETE) break;
    const url = absUrl(page, job.public_url);
    console.error(`[ats] probe ${job.company} — ${job.title} ${url}`);
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
      await sleep(1000);
      const info = await findExternalLinks(page);
      const row = {
        id: job.id,
        title: job.title,
        company: job.company,
        location: job.locations,
        score: job.score,
        url: info.url,
        nExt: (info.external || []).length,
        sent: info.applicationSent,
        interested: info.interested,
        notFound: info.notFound,
        external: info.external,
      };
      report.probed.push(row);
      fs.writeFileSync(OUT, JSON.stringify(report, null, 2));

      if (info.applicationSent) {
        report.skipped.push({ ...row, reason: "already_application_sent" });
        continue;
      }
      if (!info.external?.length) {
        report.skipped.push({ ...row, reason: "no_company_ats_link" });
        continue;
      }

      const href = info.external[0].href;
      const atsPage = await context.newPage();
      try {
        await atsPage.goto(href, { waitUntil: "domcontentloaded", timeout: 60000 });
        const done = await completeExternalPage(atsPage, resume, { maxMs: 3.5 * 60 * 1000 });
        if (done.ok) {
          report.applied.push({
            id: job.id,
            title: job.title,
            company: job.company,
            location: job.locations,
            path: "company_ATS",
            atsUrl: done.url || href,
            confirmed: true,
            publicUrl: info.url,
          });
          console.error(`[ats] CONFIRMED ${job.company} — ${job.title}`);
        } else {
          report.blocked.push({
            reason: done.reason || "external_incomplete_or_timeout",
            id: job.id,
            title: job.title,
            company: job.company,
            url: done.url || href,
            path: "company_ATS",
          });
          console.error(`[ats] blocked ${done.reason} ${job.company}`);
        }
      } catch (e) {
        if (isBrowserClosedError(e)) throw e;
        report.blocked.push({
          reason: "external_ats_error",
          id: job.id,
          error: String(e).slice(0, 200),
        });
      } finally {
        await atsPage.close().catch(() => {});
      }
      fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
    } catch (e) {
      if (isBrowserClosedError(e)) {
        report.blocked.push({ reason: "browser_closed" });
        break;
      }
      report.blocked.push({
        reason: "probe_failed",
        id: job.id,
        error: String(e).slice(0, 200),
      });
    }
  }

  report.summary = {
    applied: report.applied.length,
    probed: report.probed.length,
    skipped: report.skipped.length,
    blocked: report.blocked.length,
    path: "already-interested pages → company ATS (complete_page.js)",
  };
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  process.exit(0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
