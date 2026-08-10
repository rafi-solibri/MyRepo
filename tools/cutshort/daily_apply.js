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

const SEEKER_ID = "6a3e4526cc1fad8f39dccc0f";
const CDP = process.env.CUTSHORT_CDP || "http://127.0.0.1:9222";
const OUT_DIR = process.env.CUTSHORT_OUT || "/tmp/cutshort-run";
const TODAY = new Date().toISOString().slice(0, 10);
const REPORT_DIR = process.env.CUTSHORT_REPORT || path.join("/workspace/reports", TODAY);

const SKIP_RE =
  /\b(qa|sdet|test engineer|quality architect|intern|trainee|associate(?!\s+director)|junior|workday|dynamics|[\s/]sap[\s/]|shoppay|shopify|business development|\bbdm\b|recruiter|data architect|data engineer|analytics engineer|penetration|product manager|ios developer|android developer|flutter|php developer|wordpress|game developer|mobile engineer)\b/i;

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
  const hyd = locs.some((l) => l.includes("hyderabad"));
  const rt = String(job?.remoteType || "").toLowerCase();
  return hyd || rt === "remote_okay" || rt === "remote_only";
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
  if (SKIP_RE.test(title)) return null;
  if (job?.expRange?.max != null && job.expRange.max < 8) return null;
  if (ctc != null && ctc < 50) return null;
  if (!isHydOrRemote(job)) return null;

  if (
    /\b(solutions?\s*architect|technical\s*architect|cloud\s*architect|platform\s*architect|enterprise\s*architect|application\s*architect|tech(?:nical)?\s*lead|engineering\s*manager|principal|staff|head of eng|director of eng|delivery lead|engineering lead|architect)\b/i.test(
      title
    )
  ) {
    if (!/\b(workday|sap|salesforce)\b/i.test(skills)) return { tier: 1, reason: "tier1" };
  }
  if (
    /\b(\.net|c#|csharp|azure)\b/i.test(blob) &&
    /\b(senior|lead|principal|staff|architect|full\s*-?\s*stack|backend)\b/i.test(title + " " + blob)
  ) {
    return { tier: 2, reason: "tier2-net" };
  }
  if (
    /\b(senior\s*(full\s*-?\s*stack|fullstack|backend|software)|full\s*-?\s*stack|platform lead|backend lead|lead (engineer|developer))\b/i.test(
      title
    ) &&
    /\b(\.net|c#|csharp|azure|aws|react|microservices)\b/i.test(blob)
  ) {
    return { tier: 2, reason: "tier2-senior-stack" };
  }
  if (
    /\b(node\.?js|nodejs|typescript|java\b|genai|gen ai|llm|platform engineer)\b/i.test(blob) &&
    /\b(lead|staff|principal|architect|manager|head|senior)\b/i.test(title) &&
    (ctc == null ? !!job?.salaryRange?.hideSalary : ctc >= 55)
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

async function api(page, method, urlPath, body) {
  if (!String(page.url()).includes("cutshort.io")) {
    await page.goto("https://cutshort.io/profile/candidate-dashboard", {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await sleep(800);
  }
  return page.evaluate(
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
}

function pickOption(q) {
  const text = `${q.questionString || q.question?.questionString || q.questionText || ""}`.toLowerCase();
  const options = q.responseOptions || q.options || [];
  const ot = (o) => String(o.responseString || o.optionString || o.text || "").toLowerCase();
  const find = (p) => options.find((o) => p(ot(o)));
  if (/notice|availab|join|how soon|immediate/.test(text)) {
    return (
      find((t) => /immediate|served|already|0 day|available now/.test(t)) ||
      find((t) => /15|serving|less than/.test(t)) ||
      options[0]
    );
  }
  if (/salary|ctc|compensation|budget|band|range|pay/.test(text)) {
    const m = text.match(/(\d+)\s*[–\-to]+\s*(\d+)\s*lpa/) || text.match(/(\d+)\s*lpa/);
    const maxBand = m ? Number(m[2] || m[1]) : null;
    const yes = find((t) => /^(yes|y|ok|okay|works)/.test(t));
    const no = find((t) => /^(no|n\b|not)/.test(t));
    if (maxBand != null) return maxBand >= 55 ? yes || options[0] : no || options[options.length - 1];
    if (yes && /does this work|comfortable|acceptable|ok/.test(text)) return yes;
  }
  if (/location|city|relocat|wfh|remote|hybrid/.test(text)) {
    return (
      find((t) => /hyderabad/.test(t)) ||
      find((t) => /remote|wfh|anywhere/.test(t)) ||
      find((t) => /prefer|open|relocat/.test(t)) ||
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
  const text = `${q.questionString || q.question?.questionString || ""}`.toLowerCase();
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
          const options = q.responseOptions || q.options || [];
          const answerRowId = q._id;
          const questionId = q.question?._id || q.question || q.questionId;
          if (!answerRowId || questionId == null) continue;
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
  if (/Candidate login/i.test(body)) return { status: "login_required" };
  if (/view conversation/i.test(body) || /already applied/i.test(body)) {
    return { status: "already_applied" };
  }
  const hasApply = await page.evaluate(() =>
    [...document.querySelectorAll("button, a, [role=button]")].some((b) =>
      /^apply now$/i.test((b.innerText || "").trim())
    )
  );
  if (!hasApply) {
    const external = /company website|external apply|apply on company/i.test(body);
    return external ? { status: "external" } : { status: "blocked_no_apply" };
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
  if (!ta) return { status: "failed_no_textarea" };

  const firstName = (job.createdBy?.name || "").split(/\s+/)[0] || null;
  const note = noteFor(job, firstName);
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

  const apiRes = await api(page, "POST", "/sendreply/jobsignal", {
    signalid: jobId,
    message: note,
    seekerSignalContext: SEEKER_ID,
    type: "jobsignal",
    source: "all_jobs",
    urlParams: { jobid: jobId },
  });
  if (apiRes.ok) return { status: "applied", firstName, via: "api" };
  if (apiRes.status === 400 && /already/i.test(apiRes.text || "")) {
    return { status: "already_applied", via: "api" };
  }
  return { status: "failed_apply", apiStatus: apiRes.status };
}

async function scan(page) {
  const byId = new Map();
  async function pull(query, maxPages, label) {
    for (let p = 1; p <= maxPages; p++) {
      const qs = new URLSearchParams({ page: String(p), ...query }).toString();
      const res = await api(page, "GET", `/findjobs/q?${qs}`);
      const results = res.json?.results || [];
      if (!results.length) break;
      for (const j of results) byId.set(j._id, j);
      if (p === 1) console.log(`[scan:${label}] ${res.json?.total_count}`);
      if (res.json?.totalPages && p >= res.json.totalPages) break;
      await sleep(60);
    }
  }
  await pull({}, 350, "newest");
  await pull({ locations: "Hyderabad" }, 61, "hyd");
  for (const skills of ["00001", "00075", "00486", "00054", "00368"]) {
    await pull({ skills }, 50, skills);
  }
  return [...byId.values()];
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.mkdirSync(REPORT_DIR, { recursive: true });
  console.log("resume:", findResume());

  const browser = await chromium.connectOverCDP(CDP);
  const context = browser.contexts()[0] || (await browser.newContext());
  const page = await context.newPage();
  await page.goto("https://cutshort.io/profile/candidate-dashboard", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await sleep(1500);
  if (await page.evaluate(() => /Candidate login/i.test(document.body?.innerText || ""))) {
    console.log("LOGIN_REQUIRED");
    fs.writeFileSync(
      path.join(REPORT_DIR, "cutshort-daily.md"),
      `# Cutshort daily ${TODAY}\n\n**STOP: Cutshort login/session missing.**\n`
    );
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

  const jobs = await scan(page);
  stats.scanned = jobs.length;
  const qual = [];
  for (const job of jobs) {
    const c = classify(job);
    if (c) qual.push({ job, row: { id: job._id, title: titleOf(job), company: job.company, tier: c.tier, reason: c.reason, ctc: maxCtcLpa(job), remoteType: job.remoteType } });
  }
  qual.sort((a, b) => a.row.tier - b.row.tier || (b.row.ctc || 0) - (a.row.ctc || 0));
  stats.qualifying = qual.map((q) => q.row);
  console.log(`[filter] scanned=${jobs.length} qualifying=${qual.length}`);

  for (const { job, row } of qual) {
    console.log(`\n[apply] T${row.tier} ${row.title} @ ${row.company} ctc=${row.ctc}`);
    let result;
    try {
      result = await applyOne(page, job);
    } catch (e) {
      result = { status: "exception", error: String(e).slice(0, 200) };
    }
    console.log(" =>", result.status);
    if (result.status === "login_required") {
      stats.failed.push({ ...row, result });
      break;
    }
    if (result.status === "applied") {
      stats.applied.push({ ...row, result });
      // Answer questionnaires after each successful apply batch
      await answerPendingQuestionnaires(page, stats);
    } else if (result.status === "already_applied") stats.already.push({ ...row, result });
    else if (result.status === "external") stats.external.push({ ...row, result });
    else stats.failed.push({ ...row, result });
    await sleep(500);
  }

  // Final questionnaire sweep (also covers zero-apply days)
  await answerPendingQuestionnaires(page, stats);

  const report = `# Cutshort daily ${TODAY}

## Counts
- Scanned: **${stats.scanned}**
- Qualifying: **${stats.qualifying.length}**
- Applied: **${stats.applied.length}**
- Already: ${stats.already.length}
- Failed/blocked: ${stats.failed.length}
- External: ${stats.external.length}
- Q answered: **${stats.q.answered}** | already: ${stats.q.alreadySubmitted} | locked-empty: ${stats.q.lockedEmpty}
- Awaiting listed: ${stats.q.awaitingListed}

## Applied
${stats.applied.map((a) => `- T${a.tier} ${a.title} @ ${a.company} (${a.ctc}L) \`${a.id}\``).join("\n") || "_None_"}
`;
  fs.writeFileSync(path.join(REPORT_DIR, "cutshort-daily.md"), report);
  fs.writeFileSync(path.join(OUT_DIR, "stats.json"), JSON.stringify(stats, null, 2));
  console.log(report);
  await page.close().catch(() => {});
  await browser.close().catch(() => {});
}

if (require.main === module) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}

module.exports = { classify, isHydOrRemote, maxCtcLpa, titleOf };