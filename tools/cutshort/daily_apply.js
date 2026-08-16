#!/usr/bin/env node
/**
 * Cutshort daily apply + questionnaire runner (Rafi Ahmed).
 * Requires Chrome CDP on :9222 with cutshort profile logged in.
 *
 * Usage:
 *   bash scripts/preflight-portal-run.sh cutshort
 *   bash scripts/launch-chrome-cdp.sh cutshort
 *   node tools/cutshort/daily_apply.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");
const {
  buildAnswerPayload,
  answersNonEmpty,
  EXPECTED_CTC_LPA,
  CURRENT_CTC_LPA,
  findResume,
} = require("./questionnaire.js");
const { companyAllowed, allowlistActive } = require("../hitechcity/campus_allowlist");
const { completeExternalPage } = require("../ats/complete_page");

const SEEKER_ID = "6a3e4526cc1fad8f39dccc0f";
const CDP = process.env.CUTSHORT_CDP || "http://127.0.0.1:9222";
const MAX_APPLIES = Number(process.env.CUTSHORT_MAX_APPLIES || process.env.HITECHCITY_CUTSHORT_MAX || 40);
const OUT_DIR = process.env.CUTSHORT_OUT || "/tmp/cutshort-run";
const TODAY = new Date().toISOString().slice(0, 10);
const REPORT_DIR = process.env.CUTSHORT_REPORT || path.join("/workspace/reports", TODAY);
const HOME_REPORT =
  process.env.CUTSHORT_HOME_REPORT ||
  (fs.existsSync("/opt/cursor/artifacts")
    ? "/opt/cursor/artifacts/cutshort-daily-run.json"
    : path.join(process.cwd(), "artifacts", "cutshort-daily-run.json"));

function writeHomeReport(partial) {
  const finishedAt = new Date().toISOString();
  const applied = (partial.applied || []).map((a) => ({
    id: a.id,
    title: a.title,
    company: a.company,
    tier: a.tier,
    ctc: a.ctc,
  }));
  const external = (partial.external || []).map((a) => ({
    id: a.id,
    title: a.title,
    company: a.company,
    reason: "external_ats",
  }));
  const rejected = (partial.failed || [])
    .filter((a) => a.result?.status !== "login_required")
    .map((a) => ({
      id: a.id,
      title: a.title,
      company: a.company,
      reason: a.result?.status || "failed",
    }));
  const blocked = [];
  if (partial.loginRequired) {
    blocked.push({
      reason: "cutshort_login_required",
      detail:
        partial.loginDetail ||
        "Candidate dashboard redirected to login; re-auth CDP profile",
    });
  }
  const skipped = (partial.already || []).map((a) => ({
    id: a.id,
    title: a.title,
    company: a.company,
    reason: "already_applied",
  }));
  const q = partial.q || {};
  // Historical locked-empty questionnaires are not same-day apply failures —
  // keep them in notes/counts but do not treat as rejected applications.
  const report = {
    portal: "cutshort",
    source: process.env.CUTSHORT_SOURCE || "home-local",
    date: TODAY,
    finishedAt,
    ok: blocked.length === 0 && (applied.length > 0 || Number(partial.scanned || 0) > 0),
    counts: {
      applied: applied.length,
      external: external.length,
      rejected: rejected.length,
      blocked: blocked.length,
      skipped: skipped.length,
      seen: Number(partial.scanned || 0),
      questionnairesAnswered: Number(q.answered || 0),
      questionnairesLockedEmpty: Number(q.lockedEmpty || 0),
    },
    applied,
    external,
    rejected,
    blocked,
    skipped,
    seen: (partial.qualifying || []).map((qrow) => ({
      id: qrow.id,
      title: qrow.title,
      company: qrow.company,
      tier: qrow.tier,
    })),
    blockerSummary: blocked[0]
      ? `${blocked[0].reason} — ${blocked[0].detail || "re-login via launch-chrome-cdp.sh cutshort"}`
      : null,
    notes: [
      `qualifying=${(partial.qualifying || []).length}`,
      `q_answered=${q.answered || 0}`,
      `q_locked_empty=${q.lockedEmpty || 0}`,
      `q_already_submitted=${q.alreadySubmitted || 0}`,
    ],
  };
  fs.mkdirSync(path.dirname(HOME_REPORT), { recursive: true });
  fs.writeFileSync(HOME_REPORT, JSON.stringify(report, null, 2) + "\n");
  return HOME_REPORT;
}

function isLoggedOut(url, bodyText) {
  const u = String(url || "");
  const text = String(bodyText || "");
  if (/[?&]redirect_url=/.test(u) || /cutshort\.io\/?\?/.test(u)) return true;
  if (/\/login|\/signin|\/candidate-login/i.test(u)) return true;
  // Marketing homepage nav always says "Candidate login"; require logout cues.
  if (
    /Candidate login/i.test(text) &&
    /Employer login/i.test(text) &&
    /Get started/i.test(text)
  ) {
    return true;
  }
  return false;
}

const SKIP_RE =
  /\b(qa engineer|quality assurance|quality engineer|sdet|test engineer|intern|trainee|associate(?!\s+(director|technical|architect|principal|lead|vice))|junior|workday|dynamics|\bsap\b|shoppay|shopify|business development|\bbdm\b|recruiter|data architect|data engineer|analytics engineer|penetration|product manager|ios developer|android developer|flutter|php developer|wordpress|game developer|mobile engineer)\b/i;

/** C# / .NET need non-\b patterns: `\bc#\b` never matches "C#" (# is non-word). */
const NET_STACK_RE = /(\.net|\bdotnet\b|asp\.?\s*net|c#|\bcsharp\b|\bazure\b)/i;
const STACK_SIGNAL_RE =
  /(\.net|\bdotnet\b|asp\.?\s*net|c#|\bcsharp\b|\bazure\b|\baws\b|\breact\b|microservices|\bnode\.?js\b|\bnodejs\b|\btypescript\b|\bjava\b|genai|gen\s*ai|generative\s*ai|\bllm\b|platform engineer)/i;
const TIER1_TITLE_RE =
  /\b(solutions?\s*architect|technical\s*architect|cloud\s*architect|platform\s*architect|enterprise\s*architect|application\s*architect|tech(?:nical)?\s*lead|engineering\s*manager|engineering\s*leader|principal|staff|head of eng(?:ineering)?|director of eng(?:ineering)?|delivery lead|engineering lead|architect)\b/i;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function titleOf(job) {
  return (job?.aiGeneratedData?.jobHeadline || job?.headline || "").trim();
}

function maxCtcLpa(job) {
  const r = job?.salaryRange || {};
  const max = r.maxVanity ?? r.max ?? null;
  if (max == null || max === 0) return null;
  return max > 1000 ? max / 1e5 : max;
}

function isHydOrRemote(job) {
  const locs = (job?.locations || []).map((l) => String(l).toLowerCase());
  const hyd = locs.some(
    (l) =>
      l.includes("hyderabad") ||
      l.includes("telangana") ||
      l.includes("hitec") ||
      l.includes("madhapur") ||
      /\bhyd\b/.test(l)
  );
  const rt = String(job?.remoteType || "").toLowerCase();
  if (hyd || rt === "remote_okay" || rt === "remote_only") return true;
  // Country-only / empty location cards often hide Hyd/remote in headline.
  const title = titleOf(job).toLowerCase();
  if (/hyderabad|\bhyd\b|telangana|remote|wfh|work from home/.test(title)) return true;
  // Cutshort often lists only "India" for remote/WFH roles — allow when title is senior/.NET/architect.
  const indiaOnly =
    locs.length > 0 &&
    locs.every((l) => l === "india" || l === "in" || l.includes("india")) &&
    !locs.some((l) =>
      /bengaluru|bangalore|pune|mumbai|chennai|noida|gurgaon|gurugram|delhi|kolkata/.test(l)
    );
  if (
    indiaOnly &&
    (/\b(architect|engineering manager|tech(?:nical)?\s*lead|principal|staff|senior|lead)\b/i.test(
      title
    ) ||
      NET_STACK_RE.test(title) ||
      NET_STACK_RE.test(skillsText(job)))
  ) {
    return true;
  }
  if (
    locs.length === 0 &&
    (rt === "" || rt === "remote_not_okay" || rt === "unknown") &&
    /remote|wfh|work from home/.test(String(job?.aiGeneratedData?.jobDescription || job?.description || "").toLowerCase())
  ) {
    return true;
  }
  return false;
}

function skillsText(job) {
  const obj = job?.allSkillsObj;
  if (obj && typeof obj === "object" && !Array.isArray(obj)) {
    return Object.values(obj).map(String).join(" ").toLowerCase();
  }
  return "";
}

function classify(job) {
  const title = titleOf(job);
  const ctc = maxCtcLpa(job);
  const skills = skillsText(job);
  const blob = `${title} ${skills}`;
  const company =
    (typeof job.company === "string" && job.company) ||
    job.companyDetails?.name ||
    job.companyId?.name ||
    "";
  if (allowlistActive() && !companyAllowed(company)) return null;
  if (SKIP_RE.test(title)) return null;
  // Tier-1 Architect/EM/Lead: allow listed max exp ≥6 (was 8 — missed 5–7 bands).
  // Tier-2 .NET titles: also allow max ≥6 so 5–7 yr senior/.NET bands are not dropped.
  const expMax = job?.expRange?.max;
  const isTier1Title = TIER1_TITLE_RE.test(title);
  const isNetTitle = NET_STACK_RE.test(title) || NET_STACK_RE.test(blob);
  const minMax = isTier1Title || isNetTitle ? 6 : 8;
  if (expMax != null && expMax < minMax) return null;
  if (ctc != null && ctc < 35) return null;
  if (!isHydOrRemote(job)) return null;

  if (isTier1Title) {
    // Title-first only — SKIP_RE already drops Workday/SAP/Dynamics/QA/data titles.
    // Do not drop Architect/EM when JD casually lists Salesforce/Java/data skills.
    return { tier: 1, reason: "tier1" };
  }
  if (
    NET_STACK_RE.test(blob) &&
    /\b(senior|lead|principal|staff|architect|full\s*-?\s*stack|backend)\b/i.test(title + " " + blob)
  ) {
    return { tier: 2, reason: "tier2-net" };
  }
  if (
    /\b(senior\s*(full\s*-?\s*stack|fullstack|backend|software)|full\s*-?\s*stack|platform lead|backend lead|lead (engineer|developer))\b/i.test(
      title
    ) &&
    STACK_SIGNAL_RE.test(blob)
  ) {
    return { tier: 2, reason: "tier2-senior-stack" };
  }
  // Tier 3 stretch: Hyd/remote with band ≥35L — senior/lead + cloud/stack signal.
  // Prefer APPLY when uncertain (title-first hard-skips already applied above).
  if (
    /\b(lead|staff|principal|architect|manager|head|senior|fullstack|full\s*-?\s*stack)\b/i.test(
      title
    ) &&
    STACK_SIGNAL_RE.test(blob) &&
    (ctc == null ? !!job?.salaryRange?.hideSalary : ctc >= 35)
  ) {
    return { tier: 3, reason: "tier3-stretch" };
  }
  return null;
}

function noteFor(job, firstName) {
  const role = titleOf(job) || "this";
  const company =
    (typeof job.company === "string" && job.company) ||
    job.companyDetails?.name ||
    job.companyId?.name ||
    "the company";
  const hi = firstName ? `Hi ${firstName},` : "Hi,";
  return `${hi}

I'm applying for the ${role} role at ${company} — strong overlap with my Solutions Architect / Technical Lead background leading .NET/React/cloud platforms.

15+ years across Nemetschek/Solibri, Infosys, and EPAM: architecture + delivery for large product platforms (.NET/C#, React, AWS/Azure, microservices).

Hyderabad-based (remote/WFH preferred), immediate joinee. Current CTC 52 LPA → expected 65 LPA.

Could we do a 15–20 min screening call this week, or please refer me to the hiring manager?

Thanks,
Rafi Ahmed`;
}

function isBrowserClosedError(e) {
  return /has been closed|Target closed|Browser closed|Connection closed|Session closed|ECONNREFUSED|cdp_connect/i.test(
    String(e?.message || e)
  );
}

/** CDP session that can reconnect when Chrome drops the page mid-scan. */
function createCdpSession() {
  let browser = null;
  let context = null;
  let page = null;

  async function connect() {
    browser = await chromium.connectOverCDP(CDP, { timeout: 60000 });
    context = browser.contexts()[0] || (await browser.newContext());
    page = context.pages().find((p) => /cutshort\.io/i.test(p.url())) || (await context.newPage());
    if (!String(page.url()).includes("cutshort.io")) {
      await page.goto("https://cutshort.io/profile/candidate-dashboard", {
        waitUntil: "domcontentloaded",
        timeout: 60000,
      });
      await sleep(800);
    }
    return page;
  }

  async function ensurePage() {
    try {
      if (page && !page.isClosed()) {
        void page.url();
        return page;
      }
    } catch {
      /* reconnect below */
    }
    console.log("[cdp] reconnecting…");
    await sleep(1500);
    return connect();
  }

  async function disconnect() {
    // Never browser.close() on Windows home — Playwright can tear down Chrome CDP.
    // page.close() can hang on a dying CDP target — bound it.
    // Must browser.disconnect() or the CDP WebSocket keeps Node alive forever.
    if (page) {
      await Promise.race([page.close().catch(() => {}), sleep(3000)]);
    }
    page = null;
    context = null;
    if (browser) {
      try {
        browser.disconnect();
      } catch {
        /* already gone */
      }
    }
    browser = null;
  }

  return {
    connect,
    ensurePage,
    disconnect,
    getPage: () => page,
  };
}

async function api(pageOrSession, method, urlPath, body) {
  const session =
    pageOrSession && typeof pageOrSession.ensurePage === "function" ? pageOrSession : null;
  let page = session ? await session.ensurePage() : pageOrSession;
  const run = async (p) => {
    if (!String(p.url()).includes("cutshort.io")) {
      await p.goto("https://cutshort.io/profile/candidate-dashboard", {
        waitUntil: "domcontentloaded",
        timeout: 60000,
      });
      await sleep(800);
    }
    return p.evaluate(
      async ({ method, urlPath, body }) => {
        const cookies = document.cookie.split(";").map((s) => s.trim());
        const xsrf = cookies
          .find((c) => c.startsWith("XSRF-TOKEN="))
          ?.split("=")
          .slice(1)
          .join("=");
        const token = decodeURIComponent(xsrf || "");
        const headers = {
          Accept: "application/json",
          "x-requested-with": "XMLHttpRequest",
          "x-xsrf-token": token,
          "x-csrf-token": token,
        };
        if (body != null) headers["Content-Type"] = "application/json";
        const res = await fetch(urlPath, {
          method,
          headers,
          credentials: "include",
          body: body != null ? JSON.stringify(body) : undefined,
        });
        const text = await res.text();
        let json = null;
        try {
          json = JSON.parse(text);
        } catch {}
        return { status: res.status, ok: res.ok, json, text: text.slice(0, 1500) };
      },
      { method, urlPath, body }
    );
  };
  try {
    return await run(page);
  } catch (e) {
    if (!session || !isBrowserClosedError(e)) throw e;
    console.log("[cdp] api retry after closed page:", String(e.message || e).slice(0, 120));
    page = await session.ensurePage();
    return run(page);
  }
}

function questionText(q) {
  return `${
    q.questionString ||
    q.question?.questionString ||
    q.question?.title ||
    q.questionText ||
    q.title ||
    ""
  }`.toLowerCase();
}

function questionOptions(q) {
  return (
    q.responseOptions ||
    q.options ||
    q.question?.options ||
    q.question?.responseOptions ||
    []
  );
}

function optionText(o) {
  return String(o.responseString || o.optionString || o.label || o.text || "").toLowerCase();
}

function pickOption(q) {
  const text = questionText(q);
  const options = questionOptions(q);
  const find = (p) => options.find((o) => p(optionText(o)));
  if (/notice|availab|join|how soon|immediate/.test(text)) {
    return (
      find((t) => /immediate|served|already|0 day|available now/.test(t)) ||
      find((t) => /15|serving|less than/.test(t)) ||
      options[0]
    );
  }
  if (/salary|ctc|compensation|budget|band|range|pay|₹|rs\.?/.test(text)) {
    const m =
      text.match(/(\d+)\s*[–\-to]+\s*(\d+)\s*l(?:pa)?/) ||
      text.match(/₹\s*(\d+)\s*[l]?\s*[–\-to]+\s*₹?\s*(\d+)\s*l/) ||
      text.match(/(\d+)\s*lpa/);
    const maxBand = m ? Number(m[2] || m[1]) : null;
    const yes = find((t) => /^(yes|y\b|ok|okay|works)|yes, this works|this works/.test(t));
    const no = find((t) => /^(no|n\b|not)|does not work|doesn't work/.test(t));
    if (maxBand != null) return maxBand >= 35 ? yes || options[0] : no || options[options.length - 1];
    if (yes && /does this work|comfortable|acceptable|ok/.test(text)) return yes;
  }
  if (/location|city|relocat|wfh|remote|hybrid/.test(text)) {
    return (
      find((t) => /hyderabad/.test(t)) ||
      find((t) => /currently in this location|okay with it|remote|wfh|anywhere/.test(t)) ||
      find((t) => /can relocate|prefer|open|relocat/.test(t)) ||
      options[0]
    );
  }
  if (/year|experience|proficien|skill/.test(text)) {
    if (/sagemaker|mlops|sap\b|workday|dynamics|salesforce|golang|ruby|php|kotlin|swift/.test(text)) {
      return find((t) => /not much|none|no experience|fresher|0/.test(t)) || options[0];
    }
    return (
      find((t) => /5\+|more than 5|7\+|10\+|8\+|15\+|expert/.test(t)) ||
      find((t) => /\d+/.test(t) && parseFloat(t) >= 5) ||
      options[options.length - 1]
    );
  }
  return options[0] || null;
}

function freeText(q) {
  const text = questionText(q);
  if (/current.*ctc|present.*ctc|current.*salary/.test(text)) return `${CURRENT_CTC_LPA} LPA`;
  if (/expected.*ctc|expected.*salary|expectation/.test(text)) return `${EXPECTED_CTC_LPA} LPA`;
  if (/ctc|salary|compensation/.test(text))
    return `Current ${CURRENT_CTC_LPA} LPA; Expected ${EXPECTED_CTC_LPA} LPA. No active offers.`;
  if (/notice|availab|join/.test(text)) return "Served notice / immediately available.";
  if (/location|relocat/.test(text))
    return "Hyderabad / remote preferred. Can discuss relocation only for an exceptional role.";
  if (/offer/.test(text)) return "No active offers.";
  return `Hyderabad-based Solutions Architect / Technical Lead, immediate joinee. Current ${CURRENT_CTC_LPA} LPA, expected ${EXPECTED_CTC_LPA} LPA.`;
}

async function answerPendingQuestionnaires(page, stats) {
  for (let p = 1; p <= 50; p++) {
    const qs = new URLSearchParams({
      page: String(p),
      user_role: "candidate",
      context: SEEKER_ID,
      convo_status: "awaiting",
    }).toString();
    const res = await api(page, "GET", `/conversations-v2/candidate?${qs}`);
    const list = res.json?.results || [];
    if (p === 1) {
      stats.q.awaitingListed = res.json?.totalCount || 0;
      console.log(`[Q] awaiting=${stats.q.awaitingListed} pages=${res.json?.totalPages}`);
    }
    if (!list.length) break;

    for (const t of list) {
      const threadId = t._id;
      const last = String(t.lastMsgText || "");
      const looksLikeQ =
        /questionnaire|screening/i.test(last) ||
        (Array.isArray(t.questions) && t.questions.length > 0);
      if (!looksLikeQ) {
        stats.q.skipNotQuestionnaire++;
        continue;
      }

      const loaded = await api(page, "GET", `/loadthread-v2/${threadId}`);
      const thread = loaded.json?.thread || loaded.json;
      const msgs = thread?.messages || loaded.json?.messages || [];
      for (const msg of Array.isArray(msgs) ? msgs : []) {
        const questions = msg.questions || [];
        if (!questions.length) continue;
        if (msg.screeningSubmitted === true) {
          if (answersNonEmpty(questions)) stats.q.alreadySubmitted++;
          else stats.q.lockedEmpty++;
          continue;
        }
        const pending = questions.filter((q) => !q.responseStringArray?.length);
        if (!pending.length) {
          stats.q.alreadySubmitted++;
          continue;
        }

        const answers = [];
        for (const q of pending) {
          const options = questionOptions(q);
          const answerRowId = q._id;
          const questionId = q.question?._id || q.question || q.questionId;
          if (!answerRowId || questionId == null || typeof questionId === "object") continue;
          if (options.length) {
            const opt = pickOption(q);
            if (!opt) continue;
            answers.push({
              answerRowId,
              questionId: String(questionId),
              optionId: String(opt._id || opt.id),
            });
          } else {
            answers.push({
              answerRowId,
              questionId: String(questionId),
              optionId: freeText(q),
            });
          }
        }
        if (!answers.length) {
          stats.q.skippedNoAnswers++;
          continue;
        }

        const messageId = msg._id;
        const payload = buildAnswerPayload(messageId, answers);
        const save = await api(page, "POST", `/update-message/${messageId}`, payload);
        if (!save.ok) {
          if (/already been submitted/i.test(save.text || "")) stats.q.alreadySubmitted++;
          else stats.q.saveFailed++;
          continue;
        }
        const verify = await api(page, "GET", `/loadthread-v2/${threadId}`);
        const vthread = verify.json?.thread || verify.json;
        const vmsgs = vthread?.messages || verify.json?.messages || [];
        const vmsg = (Array.isArray(vmsgs) ? vmsgs : []).find((m) => m._id === messageId);
        if (!answersNonEmpty(vmsg?.questions || [])) {
          stats.q.verifyEmpty++;
          continue;
        }
        const sub = await api(page, "POST", `/update-message/${messageId}`, {
          ...payload,
          screeningSubmitted: true,
        });
        if (sub.ok) {
          stats.q.answered++;
          console.log(`[Q] submitted ${threadId} n=${answers.length}`);
        } else if (/already been submitted/i.test(sub.text || "")) {
          stats.q.alreadySubmitted++;
        } else {
          stats.q.submitFailed++;
        }
        await sleep(120);
      }
    }
    if (res.json?.totalPages && p >= res.json.totalPages) break;
  }
}

async function applyOne(page, job) {
  const jobId = job._id;
  await page.goto(`https://cutshort.io/profile/view/j/${jobId}`, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await sleep(2500);
  let body = await page.evaluate(() => document.body?.innerText || "");
  if (isLoggedOut(page.url(), body)) return { status: "login_required" };
  if (/view conversation/i.test(body) || /already applied/i.test(body)) {
    return { status: "already_applied" };
  }
  const hasApply = await page.evaluate(() =>
    [...document.querySelectorAll("button, a, [role=button]")].some((b) =>
      /^apply now$/i.test((b.innerText || "").trim())
    )
  );
  const firstName = (job.createdBy?.name || "").split(/\s+/)[0] || null;
  const note = noteFor(job, firstName);

  async function applyViaApi(via) {
    const apiRes = await api(page, "POST", "/sendreply/jobsignal", {
      signalid: jobId,
      message: note,
      seekerSignalContext: SEEKER_ID,
      type: "jobsignal",
      source: "all_jobs",
      urlParams: { jobid: jobId },
    });
    if (apiRes.ok) return { status: "applied", firstName, via };
    if (apiRes.status === 400 && /already/i.test(apiRes.text || "")) {
      return { status: "already_applied", via };
    }
    return {
      status: "failed_apply",
      via,
      apiStatus: apiRes.status,
      apiText: String(apiRes.text || "").slice(0, 240),
    };
  }

  if (!hasApply) {
    const external = /company website|external apply|apply on company/i.test(body);
    if (external) return { status: "external" };
    // UI often blocked by Cloudflare turnstile / partial render — try API.
    return applyViaApi("api_no_ui_button");
  }

  await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button, a, [role=button]")].find((b) =>
      /^apply now$/i.test((b.innerText || "").trim())
    );
    btn?.click();
  });
  let ta = null;
  for (let i = 0; i < 24; i++) {
    ta = await page.$("textarea");
    if (ta) break;
    await sleep(250);
  }
  if (!ta) return applyViaApi("api_no_textarea");

  await ta.click({ clickCount: 3 });
  await page.keyboard.press("Backspace");
  await page.keyboard.type(note, { delay: 6 });
  await sleep(300);
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button, a, [role=button]")].find((b) =>
      /^(send|apply|submit|send application)$/i.test((b.innerText || "").trim())
    );
    btn?.click();
  });
  await sleep(3000);
  body = await page.evaluate(() => document.body?.innerText || "");
  if (/view conversation/i.test(body) || /already applied/i.test(body)) {
    return { status: "applied", firstName, via: "ui" };
  }

  return applyViaApi("api_after_ui");
}

async function scan(pageOrSession) {
  const byId = new Map();
  async function pull(query, maxPages, label) {
    for (let p = 1; p <= maxPages; p++) {
      const qs = new URLSearchParams({ page: String(p), pageSize: "50", ...query }).toString();
      let res;
      try {
        res = await api(pageOrSession, "GET", `/findjobs/q?${qs}`);
      } catch (e) {
        if (!isBrowserClosedError(e)) throw e;
        console.error(`[scan:${label}] aborted page ${p}:`, String(e.message || e).slice(0, 160));
        break;
      }
      const results = res.json?.results || [];
      if (!results.length) break;
      for (const j of results) byId.set(j._id, j);
      if (p === 1) console.log(`[scan:${label}] ${res.json?.total_count}`);
      if (res.json?.totalPages && p >= res.json.totalPages) break;
      await sleep(60);
    }
  }
  // Cap pages so daily runs finish in-session; classify() decides quality.
  // Note: bare `q=`/`query=` params are ignored by /findjobs/q (same total as newest).
  await pull({}, 120, "newest");
  await pull({ matchesfor: SEEKER_ID }, 40, "matchesfor");
  await pull({ locations: "Hyderabad" }, 50, "hyd");
  await pull({ locations: "Telangana" }, 25, "telangana");
  await pull({ locations: "India", remoteType: "remote_okay" }, 40, "india-remote");
  await pull({ remoteType: "remote_okay" }, 40, "remote_okay");
  await pull({ remoteType: "remote_only" }, 25, "remote_only");
  for (const skills of ["00001", "00075", "00486", "00054", "00368", "00002", "00115"]) {
    await pull({ skills }, 35, skills);
  }
  return [...byId.values()];
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.mkdirSync(REPORT_DIR, { recursive: true });
  console.log("resume:", findResume());

  const session = createCdpSession();
  const page = await session.connect();
  await sleep(700);
  const loginProbe = await page.evaluate(() => ({
    url: location.href,
    text: (document.body?.innerText || "").slice(0, 2000),
  }));
  if (isLoggedOut(loginProbe.url, loginProbe.text)) {
    console.log("LOGIN_REQUIRED", loginProbe.url);
    fs.writeFileSync(
      path.join(REPORT_DIR, "cutshort-daily.md"),
      `# Cutshort daily ${TODAY}\n\n**STOP: Cutshort login/session missing.**\n\nURL: ${loginProbe.url}\n`
    );
    const homePath = writeHomeReport({
      loginRequired: true,
      loginDetail: `session rejected (url=${loginProbe.url}); cookie may exist but is stale — headed re-login required`,
      scanned: 0,
      applied: [],
      already: [],
      failed: [],
      external: [],
      qualifying: [],
      q: {},
    });
    console.log("home_report:", homePath);
    await session.disconnect();
    process.exit(2);
  }


  const stats = {
    scanned: 0,
    applied: [],
    already: [],
    failed: [],
    external: [],
    qualifying: [],
    q: {
      awaitingListed: 0,
      answered: 0,
      alreadySubmitted: 0,
      lockedEmpty: 0,
      saveFailed: 0,
      submitFailed: 0,
      verifyEmpty: 0,
      skippedNoAnswers: 0,
      skipNotQuestionnaire: 0,
    },
  };

  let jobs = [];
  try {
    jobs = await scan(session);
  } catch (e) {
    const msg = String(e?.message || e);
    console.error("[scan] fatal:", msg.slice(0, 240));
    stats.q.error = `scan_aborted: ${msg.slice(0, 200)}`;
    if (!isBrowserClosedError(e)) throw e;
  }
  stats.scanned = jobs.length;
  const qual = [];
  const skipReasons = Object.create(null);
  for (const job of jobs) {
    const c = classify(job);
    if (c) {
      qual.push({
        job,
        row: {
          id: job._id,
          title: titleOf(job),
          company: job.company,
          tier: c.tier,
          reason: c.reason,
          ctc: maxCtcLpa(job),
          remoteType: job.remoteType,
        },
      });
      continue;
    }
    // Lightweight skip taxonomy for volume debugging (not applied as rejects).
    const title = titleOf(job);
    let why = "no_tier_match";
    if (SKIP_RE.test(title)) why = "skip_title";
    else if (job?.expRange?.max != null && job.expRange.max < 6) why = "exp_max_low";
    else if (maxCtcLpa(job) != null && maxCtcLpa(job) < 35) why = "ctc_under_35";
    else if (!isHydOrRemote(job)) why = "location";
    skipReasons[why] = (skipReasons[why] || 0) + 1;
  }
  qual.sort((a, b) => a.row.tier - b.row.tier || (b.row.ctc || 0) - (a.row.ctc || 0));
  stats.qualifying = qual.map((q) => q.row);
  stats.skipReasons = skipReasons;
  console.log(`[filter] scanned=${jobs.length} qualifying=${qual.length} skips=${JSON.stringify(skipReasons)}`);

  for (const { job, row } of qual) {
    if (stats.applied.length >= MAX_APPLIES) {
      console.log(`[cutshort] hit CUTSHORT_MAX_APPLIES=${MAX_APPLIES}`);
      break;
    }
    console.log(`\n[apply] T${row.tier} ${row.title} @ ${row.company} ctc=${row.ctc}`);
    let result;
    try {
      const p = await session.ensurePage();
      result = await applyOne(p, job);
    } catch (e) {
      if (isBrowserClosedError(e)) {
        console.error("[apply] CDP closed:", String(e.message || e).slice(0, 160));
        stats.failed.push({ ...row, result: { status: "cdp_closed" } });
        try {
          await session.ensurePage();
        } catch {
          console.error("[apply] cannot reconnect — stopping");
          break;
        }
        continue;
      }
      result = { status: "exception", error: String(e).slice(0, 200) };
    }
    console.log(" =>", result.status);
    if (result.status === "login_required") {
      stats.failed.push({ ...row, result });
      stats.loginRequired = true;
      stats.loginDetail = "Candidate session lost mid-run";
      break;
    }
    if (result.status === "applied") {
      stats.applied.push({ ...row, result });
      // Answer questionnaires after each apply (per-apply pass; audit counts reset in final sweep)
      const perApplyQ = {
        awaitingListed: 0,
        answered: 0,
        alreadySubmitted: 0,
        lockedEmpty: 0,
        saveFailed: 0,
        submitFailed: 0,
        verifyEmpty: 0,
        skippedNoAnswers: 0,
        skipNotQuestionnaire: 0,
      };
      try {
        await answerPendingQuestionnaires(await session.ensurePage(), { q: perApplyQ });
        stats.q.answered += perApplyQ.answered;
        stats.q.saveFailed += perApplyQ.saveFailed;
        stats.q.submitFailed += perApplyQ.submitFailed;
        stats.q.verifyEmpty += perApplyQ.verifyEmpty;
        console.log(`[Q] per-apply answered+=${perApplyQ.answered}`);
      } catch (e) {
        const msg = String(e?.message || e);
        console.error("[Q] per-apply aborted:", msg.slice(0, 200));
        if (!/has been closed|Target closed|Browser closed|Connection closed/i.test(msg)) throw e;
      }
    }     else if (result.status === "already_applied") stats.already.push({ ...row, result });
    else if (result.status === "external") {
      const href = await (await session.ensurePage())
        .evaluate(() => {
          const a = [...document.querySelectorAll("a")].find((el) =>
            /company website|apply on company|greenhouse|myworkdayjobs|lever\.co|smartrecruiters|ashbyhq|careers\.|jobs\./i.test(
              `${el.innerText || ""} ${el.href || ""}`
            )
          );
          return a?.href || "";
        })
        .catch(() => "");
      if (href) {
        const ats = await (await session.ensurePage()).context().newPage();
        try {
          await ats.goto(href, { waitUntil: "domcontentloaded", timeout: 60000 });
          const done = await completeExternalPage(ats, findResume());
          if (done.ok) {
            stats.applied.push({
              ...row,
              result: { status: "applied", path: "company_ATS", atsUrl: done.url || href },
            });
            console.log(`[EXT] submitted ${href.slice(0, 80)}`);
          } else {
            stats.external.push({
              ...row,
              result: { ...result, reason: done.reason, atsUrl: done.url || href },
            });
            console.log(`[EXT] blocked ${done.reason} ${href.slice(0, 80)}`);
          }
        } catch (e) {
          stats.external.push({ ...row, result: { ...result, error: String(e).slice(0, 180) } });
        } finally {
          await ats.close().catch(() => {});
        }
      } else {
        stats.external.push({ ...row, result });
      }
    }
    else stats.failed.push({ ...row, result });
    await sleep(500);
  }

  // Final questionnaire audit (unique counts — do not sum across per-apply passes).
  // Historical locked-empty threads cannot be re-answered. Skip the 40+ page
  // sweep when this session applied 0 so the run does not burn ~10 min every day.
  if (!stats.applied.length) {
    stats.q.skippedAudit = "no_applies_this_session";
    console.log("[Q] skip final audit — 0 applies this session (historical locked-empty cannot be unlocked)");
  } else {
  const auditQ = {
    awaitingListed: 0,
    answered: 0,
    alreadySubmitted: 0,
    lockedEmpty: 0,
    saveFailed: 0,
    submitFailed: 0,
    verifyEmpty: 0,
    skippedNoAnswers: 0,
    skipNotQuestionnaire: 0,
  };
  try {
    await answerPendingQuestionnaires(await session.ensurePage(), { q: auditQ });
    stats.q.answered += auditQ.answered;
    stats.q.awaitingListed = auditQ.awaitingListed;
    stats.q.alreadySubmitted = auditQ.alreadySubmitted;
    stats.q.lockedEmpty = auditQ.lockedEmpty;
    stats.q.saveFailed += auditQ.saveFailed;
    stats.q.submitFailed += auditQ.submitFailed;
    stats.q.verifyEmpty += auditQ.verifyEmpty;
    stats.q.skippedNoAnswers = auditQ.skippedNoAnswers;
    stats.q.skipNotQuestionnaire = auditQ.skipNotQuestionnaire;
  } catch (e) {
    // Chrome/CDP often dies after long scans — do not lose the apply report.
    const msg = String(e?.message || e);
    stats.q.error = msg.slice(0, 240);
    console.error("[Q] audit aborted:", msg.slice(0, 200));
    if (!/has been closed|Target closed|Browser closed|Connection closed/i.test(msg)) {
      throw e;
    }
  }
  }

  const failedTotal = stats.failed.length + stats.q.lockedEmpty + stats.q.verifyEmpty;
  const report = `# Cutshort daily ${TODAY}

## Counts
- Scanned: **${stats.scanned}**
- Qualifying: **${stats.qualifying.length}**
- Applied: **${stats.applied.length}**
- Already: ${stats.already.length}
- Failed/blocked (apply): ${stats.failed.length}
- External: ${stats.external.length}
- Q answered: **${stats.q.answered}** | already-submitted: ${stats.q.alreadySubmitted} | locked-empty: **${stats.q.lockedEmpty}** | verify-empty: ${stats.q.verifyEmpty}
- Awaiting listed: ${stats.q.awaitingListed}
- Failures (apply + locked-empty + verify-empty): **${failedTotal}**
${stats.q.error ? `- Q audit note: ${stats.q.error}\n` : ""}
## Applied
${stats.applied.map((a) => `- T${a.tier} ${a.title} @ ${a.company} (${a.ctc}L) \`${a.id}\` via=${a.result?.via || "?"}`).join("\n") || "_None_"}

## Failed applies
${stats.failed.map((a) => `- T${a.tier} ${a.title} @ ${a.company} — ${a.result?.status}`).join("\n") || "_None_"}
`;
  fs.writeFileSync(path.join(REPORT_DIR, "cutshort-daily.md"), report);
  fs.writeFileSync(path.join(OUT_DIR, "stats.json"), JSON.stringify(stats, null, 2));
  const homePath = writeHomeReport(stats);
  console.log(report);
  console.log("home_report:", homePath);
  await session.disconnect();
  // Playwright CDP can leave sockets/handles open even after browser.disconnect().
  process.exit(0);
}

if (require.main === module) {
  main().catch((e) => {
    console.error(e);
    try {
      writeHomeReport({
        loginRequired: /login/i.test(String(e?.message || e)),
        loginDetail: String(e?.message || e).slice(0, 300),
        scanned: 0,
        applied: [],
        already: [],
        failed: [],
        external: [],
        qualifying: [],
        q: { error: String(e?.message || e).slice(0, 240) },
      });
    } catch {
      /* ignore */
    }
    process.exit(1);
  });
}

module.exports = { classify, isHydOrRemote, maxCtcLpa, titleOf };