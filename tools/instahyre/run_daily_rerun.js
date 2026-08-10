#!/usr/bin/env node
/**
 * Instahyre daily apply runner — search + apply via CDP session APIs.
 * Writes report to INSTAHYRE_REPORT (default daily-rerun path).
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const { skipReason, locationOk } = require("./filters");
const { findResume } = require("./resume");

const CDP = process.env.INSTAHYRE_CDP || "http://127.0.0.1:9222";
const OUT =
  process.env.INSTAHYRE_REPORT ||
  "/opt/cursor/artifacts/instahyre-daily-rerun.json";
const MAX_APPLIES = Number(process.env.INSTAHYRE_MAX_APPLIES || 50);

const SKILLS = [
  ".NET",
  "C#",
  "ASP.NET",
  "Azure",
  "Architect",
  "Technical Lead",
  "Engineering Manager",
  "Staff Engineer",
  "Principal Engineer",
  "Solutions Architect",
  "Cloud Architect",
  "Full Stack",
  "Microservices",
];
const LOCATIONS = ["Hyderabad", "Work From Home"];

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function companyOf(job) {
  return (
    job?.employer?.company_name ||
    job?.company_name ||
    job?.employer?.name ||
    ""
  );
}

function skillsOf(job) {
  const kw = job?.keywords;
  if (Array.isArray(kw)) return kw.map(String).join(" ");
  return String(kw || "");
}

function isAlreadyInterested(job) {
  return Number(job?.interview_status) === 1;
}

function preferTier(job) {
  const title = job.title || "";
  const skills = skillsOf(job);
  const blob = `${title} ${skills}`;
  if (
    /\b(solutions?\s*architect|technical\s*architect|cloud\s*architect|platform\s*architect|enterprise\s*architect|tech(?:nical)?\s*lead|engineering\s*manager|principal|staff)\b/i.test(
      title
    )
  ) {
    return 1;
  }
  if (/\b(\.net|c#|asp\.?\s*net|azure)\b/i.test(blob)) return 2;
  if (
    /\b(senior|lead|architect|fullstack|full\s*-?\s*stack|backend)\b/i.test(title)
  ) {
    return 3;
  }
  return 4;
}

async function apiGet(page, url) {
  return page.evaluate(async (u) => {
    const r = await fetch(u, {
      credentials: "include",
      headers: {
        Accept: "application/json",
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

async function apiApply(page, jobId) {
  return page.evaluate(async (id) => {
    const csrf = document.cookie
      .split(";")
      .map((s) => s.trim())
      .find((c) => c.startsWith("csrftoken="))
      ?.split("=")
      .slice(1)
      .join("=");
    const r = await fetch(
      "/api/v1/candidate_opportunities/candidate_opportunity/apply",
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf || "",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ id: null, job_id: id, is_interested: true }),
      }
    );
    const text = await r.text();
    let json = null;
    try {
      json = JSON.parse(text);
    } catch {
      json = { raw: text.slice(0, 500) };
    }
    return { status: r.status, json };
  }, jobId);
}

async function dismissModals(page) {
  for (const s of [
    "text=/No thanks.*non-premium/i",
    ".application-modal-close",
  ]) {
    try {
      const el = page.locator(s).first();
      if (await el.isVisible({ timeout: 500 }).catch(() => false)) {
        await el.click({ timeout: 1500 }).catch(() => {});
        await sleep(300);
      }
    } catch {}
  }
}

async function checkExternal(context, job) {
  if (!job.public_url) return { path: "instahyre", external: false };
  const p = await context.newPage();
  try {
    await p.goto(job.public_url, {
      waitUntil: "domcontentloaded",
      timeout: 45000,
    });
    await sleep(1200);
    await dismissModals(p);
    const info = await p.evaluate(() => {
      const t = document.body?.innerText || "";
      const anchors = [...document.querySelectorAll("a")].map((a) => ({
        text: (a.innerText || "").trim().slice(0, 80),
        href: a.href || "",
      }));
      const ext = anchors.find((a) =>
        /apply on company|continue to company|company website|external apply|greenhouse|lever\.co|workday|ashbyhq|myworkdayjobs|boards\.greenhouse|jobs\.lever/i.test(
          `${a.text} ${a.href}`
        )
      );
      return {
        applicationSent: /application sent/i.test(t),
        companySite: /apply on company site|continue to company|external apply|company website/i.test(
          t
        ),
        snippet: t.replace(/\s+/g, " ").slice(0, 350),
        extHref: ext?.href || null,
        extText: ext?.text || null,
      };
    });
    return {
      path: info.companySite || info.extHref ? "external_ats" : "instahyre",
      external: !!(info.companySite || info.extHref),
      applicationSent: info.applicationSent,
      extHref: info.extHref,
      snippet: info.snippet,
    };
  } catch (e) {
    return {
      path: "instahyre",
      external: false,
      checkError: String(e).slice(0, 200),
    };
  } finally {
    await p.close().catch(() => {});
  }
}

async function tryCompleteExternal(context, job, check, resume) {
  if (!check.extHref) {
    return { status: "blocked", reason: "external_link_missing", ...check };
  }
  const p = await context.newPage();
  const started = Date.now();
  try {
    await p.goto(check.extHref, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await sleep(1500);
    const url = p.url();
    // Best-effort common ATS fields; 3–4 min cap
    const filled = await p.evaluate(() => {
      const set = (el, val) => {
        if (!el) return false;
        el.focus();
        el.value = val;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
        return true;
      };
      const fillBy = (re, val) => {
        const inputs = [...document.querySelectorAll("input, textarea")];
        const hit = inputs.find((i) => {
          const blob = `${i.name} ${i.id} ${i.placeholder} ${i.getAttribute("aria-label") || ""} ${i.type}`;
          return re.test(blob) && i.type !== "file" && i.type !== "hidden";
        });
        return set(hit, val);
      };
      return {
        email: fillBy(/email/i, "rafi.success@gmail.com"),
        phone: fillBy(/phone|mobile|tel/i, "8790251698"),
        first: fillBy(/first.?name/i, "Mohammed Abdul Rafi"),
        last: fillBy(/last.?name/i, "Ahmed"),
        name: fillBy(/^name$|full.?name|candidate.?name/i, "Mohammed Abdul Rafi Ahmed"),
        currentCtc: fillBy(/current.*(ctc|salary|comp)/i, "52"),
        expectedCtc: fillBy(/expected.*(ctc|salary|comp)|ctc|salary/i, "65"),
        notice: fillBy(/notice|joining|availability/i, "Immediate"),
      };
    });

    // Resume upload if present
    const fileInputs = p.locator('input[type="file"]');
    const n = await fileInputs.count();
    let uploaded = false;
    for (let i = 0; i < n; i++) {
      try {
        await fileInputs.nth(i).setInputFiles(resume);
        uploaded = true;
      } catch {}
    }

    // Attempt submit if clearly labeled and still within time
    let submitted = false;
    if (Date.now() - started < 180000) {
      const submit = p
        .locator(
          "button:has-text('Submit'), button:has-text('Apply'), input[type=submit][value*='Apply'], input[type=submit][value*='Submit']"
        )
        .first();
      if (await submit.isVisible({ timeout: 1500 }).catch(() => false)) {
        await submit.click({ timeout: 3000 }).catch(() => {});
        await sleep(2000);
        const body = await p.evaluate(() =>
          (document.body?.innerText || "").slice(0, 500)
        );
        submitted = /thank you|application (received|submitted|sent)|successfully applied/i.test(
          body
        );
      }
    }

    return {
      status: submitted ? "submitted" : "attempted",
      url,
      filled,
      uploaded,
      elapsedMs: Date.now() - started,
    };
  } catch (e) {
    return {
      status: "blocked",
      reason: "external_ats_error",
      error: String(e).slice(0, 300),
      elapsedMs: Date.now() - started,
    };
  } finally {
    await p.close().catch(() => {});
  }
}

async function collectJobs(page) {
  const seen = new Set();
  const candidates = [];
  for (const skill of SKILLS) {
    for (const loc of LOCATIONS) {
      let next = `/api/v1/job_search/?skills=${encodeURIComponent(skill)}&location=${encodeURIComponent(loc)}&limit=50`;
      let pages = 0;
      while (next && pages < 6) {
        pages++;
        let res = await apiGet(page, next);
        if (res.status === 429) {
          await sleep(3000);
          res = await apiGet(page, next);
        }
        if (res.status !== 200) {
          console.error("SEARCH_FAIL", skill, loc, res.status);
          break;
        }
        const objs = res.json?.objects || res.json?.results || [];
        for (const job of objs) {
          if (!job?.id || seen.has(job.id)) continue;
          seen.add(job.id);
          candidates.push(job);
        }
        next = res.json?.meta?.next || null;
        if (next && next.startsWith("http")) {
          try {
            const u = new URL(next);
            next = u.pathname + u.search;
          } catch {}
        }
        await sleep(700);
      }
    }
  }
  return candidates;
}

async function interestedCount(page) {
  // scrape opportunities page filter counts if present
  try {
    await page.goto("https://www.instahyre.com/candidate/opportunities/?matching=true", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await sleep(1200);
    await dismissModals(page);
    return page.evaluate(() => {
      const t = document.body?.innerText || "";
      const m = t.match(/Interested\s*\((\d+)\)/i);
      const u = t.match(/Undecided\s*\((\d+)\)/i);
      return {
        interested: m ? Number(m[1]) : null,
        undecided: u ? Number(u[1]) : null,
      };
    });
  } catch {
    return { interested: null, undecided: null };
  }
}

async function main() {
  const resume = findResume();
  const report = {
    ts: new Date().toISOString(),
    portal: "instahyre",
    resume,
    maxApplies: MAX_APPLIES,
    loggedIn: false,
    inventoryBefore: null,
    inventoryAfter: null,
    applied: [],
    external: [],
    skipped: [],
    blocked: [],
    highlights: [],
    searched: 0,
    openConsidered: 0,
  };

  const write = () => {
    fs.mkdirSync(path.dirname(OUT), { recursive: true });
    fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
  };

  if (!resume) {
    report.blocked.push({ reason: "resume_missing" });
    write();
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
    write();
    process.exit(2);
  }

  const context = browser.contexts()[0] || (await browser.newContext());
  let page =
    context.pages().find((p) => p.url().includes("instahyre.com")) ||
    context.pages()[0] ||
    (await context.newPage());
  await page.bringToFront();
  if (!String(page.url()).includes("instahyre.com")) {
    await page.goto("https://www.instahyre.com/candidate/opportunities/", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
  }
  await sleep(1000);
  await dismissModals(page);

  const body = await page.evaluate(() =>
    (document.body?.innerText || "").slice(0, 1500)
  );
  if (
    /log in|sign in|candidate login/i.test(body) &&
    !/opportunities|interested|search other jobs/i.test(body)
  ) {
    report.blocked.push({ reason: "instahyre_login_required" });
    write();
    process.exit(3);
  }
  report.loggedIn = true;
  report.inventoryBefore = await interestedCount(page);
  write();

  console.log("Collecting jobs…");
  const all = await collectJobs(page);
  report.searched = all.length;
  console.log("Collected", all.length);

  // Classify
  const open = [];
  for (const job of all) {
    const title = job.title || "";
    const company = companyOf(job);
    const location = String(job.locations || "");
    const skills = skillsOf(job);
    const reason = skipReason(title, {
      company,
      location,
      skills,
      salary: "",
    });
    if (reason) {
      report.skipped.push({
        id: job.id,
        title,
        company,
        location,
        reason,
      });
      continue;
    }
    // Extra location guard (API location param is imperfect)
    if (!locationOk(location)) {
      report.skipped.push({
        id: job.id,
        title,
        company,
        location,
        reason: "location_not_hyd_remote",
      });
      continue;
    }
    if (isAlreadyInterested(job)) {
      report.skipped.push({
        id: job.id,
        title,
        company,
        location,
        reason: "already_interested",
      });
      continue;
    }
    open.push(job);
  }

  open.sort((a, b) => preferTier(a) - preferTier(b) || b.id - a.id);
  report.openConsidered = open.length;
  write();
  console.log("Open qualifying", open.length);

  for (const job of open) {
    if (report.applied.length >= MAX_APPLIES) break;
    const title = job.title || "";
    const company = companyOf(job);
    const location = String(job.locations || "");
    console.log("APPLY", job.id, company, title, location);
    let res;
    try {
      res = await apiApply(page, job.id);
    } catch (e) {
      report.blocked.push({
        id: job.id,
        title,
        company,
        reason: "apply_exception",
        error: String(e).slice(0, 250),
      });
      continue;
    }
    if (res.status === 429) {
      await sleep(3500);
      res = await apiApply(page, job.id);
    }
    const ok =
      res.status >= 200 &&
      res.status < 300 &&
      !res.json?.error &&
      !/login|unauthorized/i.test(JSON.stringify(res.json || {}));
    if (!ok) {
      report.blocked.push({
        id: job.id,
        title,
        company,
        location,
        reason: "apply_failed",
        status: res.status,
        body: JSON.stringify(res.json).slice(0, 300),
      });
      write();
      await sleep(800);
      continue;
    }

    const check = await checkExternal(context, job);
    const entry = {
      id: job.id,
      title,
      company,
      location,
      path: check.path,
      public_url: job.public_url,
      applicationSent: check.applicationSent || false,
      keywords: (job.keywords || []).slice(0, 10),
      tier: preferTier(job),
    };

    if (check.external) {
      const ext = await tryCompleteExternal(context, job, check, resume);
      entry.external = ext;
      if (ext.status === "submitted") {
        entry.path = "external_ats";
        report.external.push(entry);
      } else if (ext.status === "attempted") {
        entry.path = "external_ats_attempted";
        report.external.push(entry);
        report.blocked.push({
          id: job.id,
          title,
          company,
          reason: "external_ats_incomplete",
          url: ext.url,
        });
      } else {
        report.blocked.push({
          id: job.id,
          title,
          company,
          reason: ext.reason || "external_ats_blocked",
          detail: ext,
        });
      }
    }

    report.applied.push(entry);
    if (entry.tier <= 2) {
      report.highlights.push(`${company} — ${title} — ${location}`);
    }
    write();
    await sleep(report.applied.length % 12 === 0 ? 2500 : 900);
  }

  report.inventoryAfter = await interestedCount(page);
  report.summary = {
    applied: report.applied.length,
    external: report.external.length,
    skipped: report.skipped.length,
    blocked: report.blocked.length,
    searched: report.searched,
    openConsidered: report.openConsidered,
  };
  write();
  console.log(JSON.stringify(report.summary, null, 2));
  // Disconnect without closing Chrome
  try {
    browser.close = async () => {};
  } catch {}
  process.exit(0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
