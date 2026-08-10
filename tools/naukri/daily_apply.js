/**
 * Daily Naukri TopTier apply worker for Mohammed Abdul Rafi Ahmed.
 * Connects to Chrome CDP on 9222. Confirms applies only via Applied CTA / ATS thank-you.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const {
  findResume,
  hasDotNet,
  shouldSkipTitle,
  EXPECTED_CTC_LPA,
  CURRENT_CTC_LPA,
} = require("./resume_and_filters");

const CDP = process.env.NAUKRI_CDP || "http://127.0.0.1:9222";
const REPORT =
  process.env.NAUKRI_APPLY_REPORT ||
  "/opt/cursor/artifacts/naukri-daily-apply.json";
const RESUME = findResume();

const QUERIES = [
  "solution architect .net",
  "technical architect .net",
  ".net technical lead",
  "engineering manager .net",
  "principal engineer .net",
  "azure architect .net",
  "cloud architect .net",
  "dotnet architect",
  "dotnet technical lead",
  "solutions architect csharp",
  "solution architect",
  "principal engineer dotnet",
  ".net architect hyderabad",
];

function parseJobAges() {
  const raw = process.env.NAUKRI_JOB_AGES || "1,3,7";
  const ages = raw
    .split(",")
    .map((s) => Number(String(s).trim()))
    .filter((n) => Number.isFinite(n) && n > 0);
  return ages.length ? ages : [1, 3, 7];
}

const JOB_AGES = parseJobAges();
const MAX_APPLIES = Number(process.env.NAUKRI_MAX_APPLIES || 40);
const MAX_EXTERNAL_MS = 3.5 * 60 * 1000;
const SKIP_PROFILE_REFRESH = process.env.NAUKRI_SKIP_PROFILE_REFRESH === "1";

/** STEP 0 — always refresh Naukri profile resume before applies. */
function runProfileResumeRefresh() {
  const script = path.join(__dirname, "update_profile_resume.js");
  const env = {
    ...process.env,
    // Soft: do not abort daily applies if UI scrape misses "Updated today"
    NAUKRI_RESUME_SOFT: process.env.NAUKRI_RESUME_SOFT || "1",
  };
  const r = spawnSync(process.execPath, [script], {
    env,
    encoding: "utf8",
    timeout: 180000,
  });
  let report = null;
  try {
    report = JSON.parse(
      fs.readFileSync("/opt/cursor/artifacts/naukri-profile-resume.json", "utf8")
    );
  } catch (_) {
    report = {
      ok: false,
      reason: "profile_resume_report_missing",
      exitCode: r.status,
      stderr: (r.stderr || "").slice(0, 500),
      stdout: (r.stdout || "").slice(0, 500),
    };
  }
  return report;
}

const SENIORITY_RE =
  /\b(architect|technical lead|tech lead|engineering manager|principal|staff|director|avp|head of|solution architect|cloud architect|azure architect|\.net lead|dotnet lead)\b/i;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function parseMaxCtcLpa(text) {
  const m = String(text || "").match(
    /₹?\s*([\d.]+)\s*L\s*[-–]\s*₹?\s*([\d.]+)\s*L/i
  );
  if (m) return Number(m[2]);
  const m2 = String(text || "").match(/([\d.]+)\s*[-–]\s*([\d.]+)\s*LPA/i);
  if (m2) return Number(m2[2]);
  const m3 = String(text || "").match(/up to\s*₹?\s*([\d.]+)\s*L/i);
  if (m3) return Number(m3[1]);
  return null;
}

function locationAllowed(locText, blob) {
  const t = `${locText || ""} ${blob || ""}`;
  if (/\b(remote|wfh|work from home|india remote)\b/i.test(t)) return true;
  if (/\b(hyderabad|secunderabad|telangana)\b/i.test(t)) return true;
  if (/hybrid[^\n]{0,40}hyderabad/i.test(t)) return true;
  return false;
}

function locationHardSkip(locText, blob) {
  if (locationAllowed(locText, blob)) return false;
  const locLine = (locText || "").split("\n")[0] || "";
  if (
    /\b(bengaluru|bangalore|pune|chennai|mumbai|delhi|gurgaon|gurugram|noida)\b/i.test(
      locLine
    ) &&
    !/\b(hyderabad|secunderabad|remote|wfh)\b/i.test(locLine)
  ) {
    return true;
  }
  return false;
}

function fingerprint(company, role) {
  return `${(company || "").toLowerCase().trim()}::${(role || "")
    .toLowerCase()
    .trim()}`;
}

/** TopTier often shows multiline CTA text: "Quick apply\\nApplied". */
function isAlreadyAppliedCta(text) {
  const t = String(text || "")
    .replace(/\s+/g, " ")
    .trim();
  if (!t) return false;
  if (/Quick apply\s*Applied/i.test(t)) return true;
  if (/^Applied$/i.test(t)) return true;
  if (/\bApplied\b/i.test(t) && !/^Quick apply$/i.test(t)) return true;
  return false;
}

async function dismiss(page) {
  for (const sel of [
    "button:has-text('Later')",
    "button:has-text('Not now')",
    "button:has-text('Skip')",
    "[aria-label='Close']",
    ".crossIcon",
    "button:has-text('Close')",
  ]) {
    const el = page.locator(sel).first();
    if (await el.isVisible().catch(() => false)) {
      await el.click().catch(() => {});
      await sleep(300);
    }
  }
}

function searchUrls(q, age) {
  const slug = q
    .replace(/[^a-z0-9]+/gi, "-")
    .replace(/^-|-$/g, "")
    .toLowerCase();
  const k = encodeURIComponent(q);
  // Combined "hyd + remote" location often returns 0 on TopTier — search separately.
  return [
    {
      label: "hyderabad",
      url: `https://www.naukri.com/${slug}-jobs-in-hyderabad?k=${k}&l=${encodeURIComponent(
        "hyderabad"
      )}&experience=12&jobAge=${age}`,
    },
    {
      label: "remote",
      url: `https://www.naukri.com/jobs-in-remote?k=${k}&experience=12&jobAge=${age}`,
    },
  ];
}

async function collectCards(page) {
  const raw = await page.evaluate(() => {
    const nodes = [...document.querySelectorAll("div.cursor-pointer")].filter(
      (c) =>
        /Quick apply|Applied|On company site|On hirist/i.test(c.innerText || "")
    );
    return nodes.map((c, idx) => {
      const text = (c.innerText || "").replace(/\r/g, "").trim();
      const lines = text
        .split("\n")
        .map((x) => x.trim())
        .filter(Boolean);
      let company = lines[0] || "";
      company = company.replace(/\s+\d\.\d.*$/, "").trim();
      const applyIdx = lines.findIndex((l) =>
        /Quick apply|Applied|On company site|On hirist/i.test(l)
      );
      let role = "";
      let location = "";
      if (applyIdx >= 0) {
        role = lines[applyIdx + 1] || "";
        location = lines[applyIdx + 2] || "";
      }
      const companySite = /On company site|On hirist/i.test(text);
      const quick = /Quick apply/i.test(text);
      return {
        idx,
        company,
        role,
        location,
        text: text.slice(0, 600),
        companySite,
        quick,
      };
    });
  });
  return raw.map((c) => {
    const already = isAlreadyAppliedCta(c.text);
    return {
      ...c,
      already,
      quick: c.quick && !already,
    };
  });
}

async function openCard(context, page, idx) {
  const cards = page.locator("div.cursor-pointer").filter({
    hasText: /Quick apply|Applied|On company site|On hirist/i,
  });
  const card = cards.nth(idx);
  await card.scrollIntoViewIfNeeded().catch(() => {});
  const before = new Set(context.pages().map((p) => p.url()));
  const popupPromise = context
    .waitForEvent("page", { timeout: 5000 })
    .catch(() => null);
  await card.click({ timeout: 10000 });
  const popup = await popupPromise;
  await sleep(2000);
  // TopTier often opens /job-listings-... in a new tab — apply there.
  let detailPage = page;
  if (popup && /naukri\.com\/job-listings/i.test(popup.url())) {
    detailPage = popup;
    await detailPage.waitForLoadState("domcontentloaded").catch(() => {});
    await sleep(1500);
  } else {
    const fresh = context
      .pages()
      .find(
        (p) =>
          /naukri\.com\/job-listings/i.test(p.url()) && !before.has(p.url())
      );
    if (fresh) {
      detailPage = fresh;
      await sleep(1000);
    }
  }
  await dismiss(detailPage);
  return detailPage;
}

async function readDetail(page) {
  return page.evaluate(() => {
    const body = document.body.innerText || "";
    const panel =
      document.querySelector(
        "[class*='detail'], [class*='Detail'], aside, [role='dialog']"
      ) || document.body;
    const ptext = panel.innerText || body;
    // Prefer real apply buttons; normalize multiline "Quick apply\\nApplied".
    const ctas = [...document.querySelectorAll("button, a, div[role='button']")]
      .map((e) =>
        (e.innerText || e.getAttribute("aria-label") || "")
          .replace(/\s+/g, " ")
          .trim()
      )
      .filter((t) =>
        /Quick apply|Apply|Applied|On company site|Apply on company/i.test(t)
      );
    const preferred =
      ctas.find((t) => /Quick apply\s*Applied|^Applied$/i.test(t)) ||
      ctas.find((t) => /On company site|Apply on company/i.test(t)) ||
      ctas.find((t) => /Quick apply/i.test(t)) ||
      ctas[0] ||
      "";
    const links = [...document.querySelectorAll("a[href]")]
      .map((a) => a.href)
      .filter((h) =>
        /myworkdayjobs|greenhouse|lever\.co|smartrecruiters|successfactors|icims|taleo|ashbyhq|phenom|oraclecloud|jobs\.|careers\.|hirist/i.test(
          h
        )
      );
    return {
      cta: preferred,
      links: [...new Set(links)].slice(0, 8),
      blob: ptext.slice(0, 4000),
      url: location.href,
    };
  });
}

async function fillApplyForm(page) {
  await page
    .evaluate(
      ({ cur, exp }) => {
        const inputs = [...document.querySelectorAll("input, textarea")];
        for (const inp of inputs) {
          if (inp.offsetParent === null) continue;
          const ctx = (
            (inp.getAttribute("placeholder") || "") +
            " " +
            (inp.getAttribute("name") || "") +
            " " +
            (inp.getAttribute("aria-label") || "") +
            " " +
            (inp.closest("label,div,li,section")?.innerText || "")
          ).slice(0, 200);
          if (/expected/i.test(ctx) && /ctc|salary|lpa/i.test(ctx)) {
            inp.focus();
            inp.value = String(exp);
            inp.dispatchEvent(new Event("input", { bubbles: true }));
            inp.dispatchEvent(new Event("change", { bubbles: true }));
          } else if (/current/i.test(ctx) && /ctc|salary|lpa/i.test(ctx)) {
            inp.focus();
            inp.value = String(cur);
            inp.dispatchEvent(new Event("input", { bubbles: true }));
            inp.dispatchEvent(new Event("change", { bubbles: true }));
          } else if (/notice/i.test(ctx)) {
            inp.focus();
            inp.value = "0";
            inp.dispatchEvent(new Event("input", { bubbles: true }));
            inp.dispatchEvent(new Event("change", { bubbles: true }));
          }
        }
      },
      { cur: CURRENT_CTC_LPA, exp: EXPECTED_CTC_LPA }
    )
    .catch(() => {});

  for (const sel of [
    "button:has-text('Submit')",
    "button:has-text('Save')",
    "button:has-text('Continue')",
    "button:has-text('Send')",
    "button:has-text('Apply')",
  ]) {
    const b = page.locator(sel).first();
    if (await b.isVisible().catch(() => false)) {
      const t = ((await b.innerText()) || "").trim();
      if (/Applied/i.test(t)) break;
      await b.click().catch(() => {});
      await sleep(1500);
    }
  }
}

async function clickQuickApply(page) {
  const selectors = [
    "button:has-text('Quick apply')",
    "button:has-text('Quick Apply')",
    "a:has-text('Quick apply')",
    "[role='button']:has-text('Quick apply')",
    "button:has-text('Apply')",
  ];
  for (const sel of selectors) {
    const btn = page.locator(sel).first();
    if (await btn.isVisible().catch(() => false)) {
      const label = ((await btn.innerText().catch(() => "")) || "")
        .replace(/\s+/g, " ")
        .trim();
      if (isAlreadyAppliedCta(label)) {
        return { already: true, label };
      }
      if (/company site|on company/i.test(label)) continue;
      await btn.click().catch(() => {});
      await sleep(2500);
      await dismiss(page);
      await fillApplyForm(page);
      return { clicked: true, label };
    }
  }
  return { clicked: false };
}

async function confirmApplied(page) {
  const detail = await readDetail(page);
  const cta = (detail.cta || "").replace(/\s+/g, " ").trim();
  if (isAlreadyAppliedCta(cta)) {
    return { ok: true, cta };
  }
  const toast = await page
    .evaluate(() => {
      const t = document.body.innerText || "";
      if (/applied successfully|application sent|successfully applied/i.test(t))
        return "toast";
      const hit = [...document.querySelectorAll("button, a, div")]
        .map((e) => (e.innerText || "").replace(/\s+/g, " ").trim())
        .find(
          (x) =>
            /Quick apply\s*Applied|^Applied$/i.test(x) && x.length < 40
        );
      return hit || "";
    })
    .catch(() => "");
  if (toast) return { ok: true, cta: toast };
  return { ok: false, cta: detail.cta };
}

async function tryContactRecruiter(page) {
  const note =
    "Hi — I'm a Solutions Architect / Tech Lead (.NET, Azure/AWS, microservices) based in Hyderabad, immediate joiner, expected CTC 65 LPA. Open to a 15–20 min screen if this role is a fit. Thanks — Mohammed Abdul Rafi Ahmed";
  for (const sel of [
    "text=/Contact recruiter|Chat with recruiter|Message recruiter|Send message/i",
    "button:has-text('Chat')",
  ]) {
    const el = page.locator(sel).first();
    if (!(await el.isVisible().catch(() => false))) continue;
    await el.click().catch(() => {});
    await sleep(1000);
    const box = page.locator("textarea:visible, [contenteditable='true']").first();
    if (await box.isVisible().catch(() => false)) {
      await box.fill(note).catch(() => {});
      const send = page
        .locator("button:has-text('Send'), button:has-text('Submit')")
        .first();
      if (await send.isVisible().catch(() => false)) {
        await send.click().catch(() => {});
        await sleep(1000);
        return { sent: true };
      }
    }
  }
  return { sent: false };
}

async function handleExternal(context, page, detail, jobMeta, report) {
  const start = Date.now();
  let atsUrl = detail.links[0] || null;
  const cta = page
    .locator(
      "a:has-text('On company site'), button:has-text('On company site'), a:has-text('Apply on company'), button:has-text('Apply on company')"
    )
    .first();
  let newPage = null;
  if (await cta.isVisible().catch(() => false)) {
    const popupPromise = context
      .waitForEvent("page", { timeout: 8000 })
      .catch(() => null);
    await cta.click().catch(() => {});
    newPage = await popupPromise;
    await sleep(2000);
  }
  if (!newPage) {
    if (
      /workday|greenhouse|lever|smartrecruiters|icims|taleo|ashby|phenom|careers|hirist/i.test(
        page.url()
      )
    ) {
      newPage = page;
    } else if (atsUrl) {
      newPage = await context.newPage();
      await newPage
        .goto(atsUrl, { waitUntil: "domcontentloaded", timeout: 60000 })
        .catch(() => {});
    }
  }
  if (!newPage) {
    report.blocked.push({
      ...jobMeta,
      reason: "external_link_not_opened",
      path: "company_ATS",
    });
    return;
  }
  atsUrl = newPage.url();

  // Hirist is a secondary board — skip login walls instead of hard-blocking the day.
  if (/hirist\.tech|hirist\.com|\/hirist/i.test(atsUrl)) {
    const hText = await newPage
      .evaluate(() => (document.body?.innerText || "").slice(0, 1500))
      .catch(() => "");
    if (/login|sign in|register|otp/i.test(atsUrl + " " + hText)) {
      report.skipped.push({
        ...jobMeta,
        reason: "hirist_login_required_skip",
        url: atsUrl,
        path: "hirist",
      });
      if (newPage !== page) await newPage.close().catch(() => {});
      return;
    }
  }

  while (Date.now() - start < MAX_EXTERNAL_MS) {
    const url = newPage.url();
    const text = await newPage
      .evaluate(() => (document.body?.innerText || "").slice(0, 2000))
      .catch(() => "");
    if (/captcha|verify you are human|cloudflare/i.test(text)) {
      report.blocked.push({
        ...jobMeta,
        reason: "captcha_wall",
        url,
        path: "company_ATS",
      });
      if (newPage !== page) await newPage.close().catch(() => {});
      return;
    }
    if (
      /sign in|log in|login/i.test(url + text) &&
      !/application|apply|thank/i.test(text)
    ) {
      // Hirist login wall → skip (not a hard blocker)
      if (/hirist/i.test(url + text)) {
        report.skipped.push({
          ...jobMeta,
          reason: "hirist_login_required_skip",
          url,
          path: "hirist",
        });
        if (newPage !== page) await newPage.close().catch(() => {});
        return;
      }
      const guest = newPage
        .locator("text=/Continue as guest|Apply without|Don't have an account/i")
        .first();
      if (await guest.isVisible().catch(() => false)) {
        await guest.click().catch(() => {});
      } else {
        report.blocked.push({
          ...jobMeta,
          reason: "ats_login_wall",
          url,
          path: "company_ATS",
        });
        if (newPage !== page) await newPage.close().catch(() => {});
        return;
      }
    }

    if (RESUME) {
      const file = newPage.locator("input[type='file']").first();
      if (await file.count()) {
        await file.setInputFiles(RESUME).catch(() => {});
        await sleep(1000);
      }
    }

    await newPage
      .evaluate(
        ({ cur, exp }) => {
          const inputs = [
            ...document.querySelectorAll("input, textarea, select"),
          ];
          for (const inp of inputs) {
            if (inp.offsetParent === null && inp.type !== "file") continue;
            const ctx = (
              (inp.getAttribute("placeholder") || "") +
              " " +
              (inp.getAttribute("name") || "") +
              " " +
              (inp.getAttribute("aria-label") || "") +
              " " +
              (inp.closest("label,div,fieldset,li")?.innerText || "")
            ).slice(0, 240);
            if (
              /expected/i.test(ctx) &&
              /ctc|salary|compensation|lpa|pay/i.test(ctx)
            ) {
              if (inp.tagName === "SELECT") continue;
              inp.value = String(exp * 100000);
              inp.dispatchEvent(new Event("input", { bubbles: true }));
            } else if (
              /current/i.test(ctx) &&
              /ctc|salary|compensation|lpa|pay/i.test(ctx)
            ) {
              if (inp.tagName === "SELECT") continue;
              inp.value = String(cur * 100000);
              inp.dispatchEvent(new Event("input", { bubbles: true }));
            }
          }
        },
        { cur: CURRENT_CTC_LPA, exp: EXPECTED_CTC_LPA }
      )
      .catch(() => {});

    for (const sel of [
      "button:has-text('Submit application')",
      "button:has-text('Submit Application')",
      "button:has-text('Submit')",
      "button:has-text('Apply')",
      "input[type='submit']",
    ]) {
      const b = newPage.locator(sel).first();
      if (await b.isVisible().catch(() => false)) {
        await b.click().catch(() => {});
        await sleep(2000);
      }
    }

    const after = await newPage
      .evaluate(() => (document.body?.innerText || "").slice(0, 2500))
      .catch(() => "");
    if (
      /thank you for appl|application (has been )?submitted|successfully submitted|we have received your application|application received/i.test(
        after
      )
    ) {
      report.external.push({
        ...jobMeta,
        path: "company_ATS",
        atsUrl: newPage.url(),
        resume: RESUME,
        confirmed: true,
      });
      report.applied.push({
        ...jobMeta,
        path: "company_ATS",
        atsUrl: newPage.url(),
        resume: RESUME,
      });
      if (newPage !== page) await newPage.close().catch(() => {});
      return;
    }

    const next = newPage
      .locator(
        "button:has-text('Next'), button:has-text('Continue'), button:has-text('Save and Continue')"
      )
      .first();
    if (await next.isVisible().catch(() => false)) {
      await next.click().catch(() => {});
      await sleep(1500);
      continue;
    }
    await sleep(2000);
    break;
  }

  report.blocked.push({
    ...jobMeta,
    reason: "external_incomplete_or_timeout",
    url: newPage.url(),
    path: "company_ATS",
  });
  if (newPage !== page) await newPage.close().catch(() => {});
}

function decideSkip(card, { detailMode = false } = {}) {
  const blob = card.text || "";
  const role = card.role || "";
  const loc = card.location || "";

  if (card.already) return "already_applied";
  // Title/role keyword skips only — never scan full page chrome (false "QA" hits).
  if (shouldSkipTitle(role)) return "skip_title_keyword";
  if (!detailMode && shouldSkipTitle(blob.split("\n").slice(0, 8).join(" ")))
    return "skip_title_keyword";
  if (!SENIORITY_RE.test(role) && !SENIORITY_RE.test(blob)) {
    if (!/\b(lead|manager|architect|principal|staff)\b/i.test(role))
      return "skip_seniority";
  }
  if (!hasDotNet(role, blob)) return "skip_no_dotnet";
  if (locationHardSkip(loc, blob)) return "skip_location";
  if (!locationAllowed(loc, blob)) return "skip_location";
  const maxCtc = parseMaxCtcLpa(blob);
  if (maxCtc !== null && maxCtc < 50) return `skip_ctc_max_${maxCtc}`;
  return null;
}

async function processCard(context, page, card, i, jobMeta, report) {
  const detailPage = await openCard(context, page, i);
  const openedTab = detailPage !== page;
  const detail = await readDetail(detailPage);
  // Detail re-check: location/CTC/.NET only — skip_title already decided from card role.
  const detailSkip = decideSkip(
    {
      ...card,
      text: `${card.role}\n${card.location}\n${detail.blob.slice(0, 1200)}`,
      role: card.role,
      location: card.location,
    },
    { detailMode: true }
  );
  const closeDetail = async () => {
    if (openedTab) {
      detailPage.close().catch(() => {});
      await page.bringToFront().catch(() => {});
    } else {
      await page.keyboard.press("Escape").catch(() => {});
    }
  };
  if (
    detailSkip &&
    detailSkip !== "already_applied" &&
    !String(detailSkip).startsWith("skip_title")
  ) {
    report.skipped.push({ ...jobMeta, reason: detailSkip + "_detail" });
    await closeDetail();
    return;
  }
  if (isAlreadyAppliedCta(detail.cta)) {
    report.skipped.push({
      ...jobMeta,
      reason: "already_applied_detail",
      naukriJobUrl: detail.url,
      cta: detail.cta,
    });
    // Interview-call maximization: still try recruiter note on prior applies.
    const rec = await tryContactRecruiter(detailPage);
    if (rec.sent) {
      report.recruiterNotes = report.recruiterNotes || [];
      report.recruiterNotes.push({
        company: jobMeta.company,
        role: jobMeta.role,
        naukriJobUrl: detail.url,
      });
    }
    await closeDetail();
    return;
  }

  if (card.companySite || /On company site|Apply on company/i.test(detail.cta)) {
    await handleExternal(context, detailPage, detail, jobMeta, report);
    await page.bringToFront().catch(() => {});
    await closeDetail();
    await sleep(800);
    return;
  }

  const click = await clickQuickApply(detailPage);
  if (click.already) {
    report.skipped.push({
      ...jobMeta,
      reason: "already_applied_cta",
      naukriJobUrl: detail.url,
      cta: click.label,
    });
    await closeDetail();
    return;
  }
  if (!click.clicked) {
    report.blocked.push({
      ...jobMeta,
      reason: "quick_apply_not_found",
      path: "Naukri",
      naukriJobUrl: detail.url,
      cta: detail.cta,
    });
    await closeDetail();
    return;
  }
  await sleep(2000);
  const conf = await confirmApplied(detailPage);
  if (conf.ok) {
    const rec = await tryContactRecruiter(detailPage);
    report.applied.push({
      ...jobMeta,
      path: "Naukri",
      cta: conf.cta,
      recruiterNote: rec.sent,
      naukriJobUrl: detail.url || detailPage.url(),
    });
  } else {
    report.blocked.push({
      ...jobMeta,
      reason: "apply_unconfirmed",
      cta: conf.cta,
      path: "Naukri",
      naukriJobUrl: detail.url,
    });
  }
  await closeDetail();
  await sleep(700);
}

async function main() {
  const report = {
    startedAt: new Date().toISOString(),
    resume: RESUME,
    jobAges: JOB_AGES,
    profileResumeRefresh: null,
    applied: [],
    external: [],
    blocked: [],
    skipped: [],
    seen: [],
    recruiterNotes: [],
    queriesRun: [],
  };

  if (!SKIP_PROFILE_REFRESH) {
    report.profileResumeRefresh = runProfileResumeRefresh();
    if (!report.profileResumeRefresh?.profileUpdated) {
      console.error(
        "WARN: Naukri profile resume not confirmed Updated today:",
        JSON.stringify({
          ok: report.profileResumeRefresh?.ok,
          profileUpdated: report.profileResumeRefresh?.profileUpdated,
          warning: report.profileResumeRefresh?.warning,
          reason: report.profileResumeRefresh?.reason,
          verify: report.profileResumeRefresh?.verify,
        })
      );
    } else {
      console.log(
        "Naukri profile resume refreshed:",
        report.profileResumeRefresh.verify?.matchedToken ||
          report.profileResumeRefresh.verify?.updateOn ||
          "ok"
      );
    }
  } else {
    try {
      report.profileResumeRefresh = JSON.parse(
        fs.readFileSync("/opt/cursor/artifacts/naukri-profile-resume.json", "utf8")
      );
    } catch (_) {}
  }

  const { chromium } = require("playwright-core");
  const browser = await chromium.connectOverCDP(CDP);
  const context = browser.contexts()[0];
  const page = await context.newPage();
  page.setDefaultTimeout(45000);

  const seen = new Set();

  try {
    for (const age of JOB_AGES) {
      if (report.applied.length >= MAX_APPLIES) break;
      for (const q of QUERIES) {
        if (report.applied.length >= MAX_APPLIES) break;
        for (const loc of searchUrls(q, age)) {
          if (report.applied.length >= MAX_APPLIES) break;
          const url = loc.url;
          report.queriesRun.push({ q, age, loc: loc.label, url });
          await page
            .goto(url, { waitUntil: "domcontentloaded", timeout: 90000 })
            .catch(() => {});
          await sleep(2500);
          await dismiss(page);

          const noJobs = await page.evaluate(() =>
            /No jobs found/i.test(document.body.innerText || "")
          );
          let cards = await collectCards(page);
          if (noJobs || !cards.length) continue;

          for (let i = 0; i < cards.length; i++) {
            if (report.applied.length >= MAX_APPLIES) break;
            cards = await collectCards(page);
            const card = cards[i];
            if (!card) continue;
            const fp = fingerprint(card.company, card.role);
            if (seen.has(fp)) {
              report.skipped.push({
                company: card.company,
                role: card.role,
                reason: "duplicate_in_run",
                query: q,
                age,
                loc: loc.label,
              });
              continue;
            }
            seen.add(fp);
            report.seen.push({
              company: card.company,
              role: card.role,
              location: card.location,
              query: q,
              age,
              loc: loc.label,
            });

            const reason = decideSkip(card);
            if (reason) {
              report.skipped.push({
                company: card.company,
                role: card.role,
                location: card.location,
                reason,
                query: q,
                age,
                loc: loc.label,
              });
              continue;
            }

            const jobMeta = {
              company: card.company,
              role: card.role,
              location: card.location,
              naukriUrl: page.url(),
              query: q,
              age,
              loc: loc.label,
              resume: RESUME,
            };

            try {
              await processCard(context, page, card, i, jobMeta, report);
            } catch (e) {
              report.blocked.push({
                ...jobMeta,
                reason: "exception",
                error: String(e).slice(0, 300),
              });
              await page.keyboard.press("Escape").catch(() => {});
            }
          }
        }
      }
    }

    // Recommended + homepage inventory pass when search burst is thin
    if (report.applied.length < 15) {
      for (const inventoryUrl of [
        "https://www.naukri.com/mnjuser/recommendedjobs",
        "https://www.naukri.com/mnjuser/homepage",
      ]) {
        if (report.applied.length >= MAX_APPLIES) break;
        await page
          .goto(inventoryUrl, {
            waitUntil: "domcontentloaded",
            timeout: 90000,
          })
          .catch(() => {});
        await sleep(3000);
        await dismiss(page);
        let cards = await collectCards(page);
        const queryLabel = inventoryUrl.includes("recommended")
          ? "recommended"
          : "homepage";
        for (let i = 0; i < Math.min(cards.length, 30); i++) {
          if (report.applied.length >= MAX_APPLIES) break;
          cards = await collectCards(page);
          const card = cards[i];
          if (!card) continue;
          const fp = fingerprint(card.company, card.role);
          if (seen.has(fp)) continue;
          seen.add(fp);
          const reason = decideSkip(card);
          if (reason) {
            report.skipped.push({
              company: card.company,
              role: card.role,
              location: card.location,
              reason,
              query: queryLabel,
            });
            continue;
          }
          const jobMeta = {
            company: card.company,
            role: card.role,
            location: card.location,
            naukriUrl: page.url(),
            query: queryLabel,
            resume: RESUME,
          };
          try {
            await processCard(context, page, card, i, jobMeta, report);
          } catch (e) {
            report.blocked.push({
              ...jobMeta,
              reason: "exception",
              error: String(e).slice(0, 300),
            });
            await page.keyboard.press("Escape").catch(() => {});
          }
        }
      }
    }
  } finally {
    report.finishedAt = new Date().toISOString();
    report.counts = {
      profileUpdated: Boolean(report.profileResumeRefresh?.profileUpdated),
      applied: report.applied.length,
      externalCompleted: report.external.length,
      blocked: report.blocked.length,
      skipped: report.skipped.length,
      seen: report.seen.length,
    };
    fs.mkdirSync(path.dirname(REPORT), { recursive: true });
    fs.writeFileSync(REPORT, JSON.stringify(report, null, 2));
    console.log(
      JSON.stringify(
        {
          counts: report.counts,
          applied: report.applied,
          blocked: report.blocked,
          skippedSample: report.skipped.slice(0, 40),
        },
        null,
        2
      )
    );
    // Avoid awaiting page.close() — CDP close can hang on TopTier tabs.
    page.close().catch(() => {});
  }
}

if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((e) => {
      console.error(e);
      process.exit(1);
    });
}
