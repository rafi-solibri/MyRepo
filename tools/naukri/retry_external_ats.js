/**
 * Retry incomplete company-ATS redirects from naukri-daily-apply.json.
 * Only records confirmed thank-you / submitted outcomes — does not invent applies.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const {
  findResume,
  EXPECTED_CTC_LPA,
  CURRENT_CTC_LPA,
} = require("./resume_and_filters");

const CDP = process.env.NAUKRI_CDP || "http://127.0.0.1:9222";
const SOURCE =
  process.env.NAUKRI_APPLY_REPORT ||
  "/opt/cursor/artifacts/naukri-daily-apply.json";
const REPORT =
  process.env.NAUKRI_ATS_RETRY_REPORT ||
  "/opt/cursor/artifacts/naukri-ats-retry.json";
const RESUME = findResume();
const MAX_EXTERNAL_MS = Number(process.env.NAUKRI_MAX_EXTERNAL_MS || 4 * 60 * 1000);

const RETRYABLE =
  /greenhouse|lever\.co|smartrecruiters|myworkday|workdaysite|ashbyhq|applytojob|zohorecruit|oraclecloud|careers\.unitedhealth|accenture\.com\/.*careers|wsa\.com/i;
const SKIP_HOST =
  /infoedge\.com|ripplehire|paradox\.ai|hirist\.|doubleclick|cutshort/i;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function fillAndSubmit(page) {
  if (RESUME) {
    const files = page.locator("input[type='file']");
    const n = await files.count().catch(() => 0);
    for (let fi = 0; fi < Math.min(n, 3); fi++) {
      await files.nth(fi).setInputFiles(RESUME).catch(() => {});
    }
    if (n) await sleep(1000);
  }

  await page
    .evaluate(
      ({ cur, exp }) => {
        const setVal = (inp, val) => {
          if (inp.tagName === "SELECT") return;
          const proto = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype,
            "value"
          );
          if (proto && proto.set) proto.set.call(inp, val);
          else inp.value = val;
          inp.dispatchEvent(new Event("input", { bubbles: true }));
          inp.dispatchEvent(new Event("change", { bubbles: true }));
        };
        for (const inp of document.querySelectorAll("input, textarea, select")) {
          if (inp.type === "file" || inp.type === "hidden") continue;
          if (inp.offsetParent === null && inp.type !== "radio") continue;
          if (inp.disabled || inp.readOnly) continue;
          const ctx = (
            (inp.getAttribute("placeholder") || "") +
            " " +
            (inp.getAttribute("name") || "") +
            " " +
            (inp.getAttribute("id") || "") +
            " " +
            (inp.getAttribute("aria-label") || "") +
            " " +
            (inp.closest("label,div,fieldset,li")?.innerText || "")
          ).slice(0, 280);
          if (/expected/i.test(ctx) && /ctc|salary|compensation|lpa|pay/i.test(ctx))
            setVal(inp, String(exp * 100000));
          else if (/current/i.test(ctx) && /ctc|salary|compensation|lpa|pay/i.test(ctx))
            setVal(inp, String(cur * 100000));
          else if (/first\s*name|fname/i.test(ctx) && !/last/i.test(ctx))
            setVal(inp, "Mohammed Abdul Rafi");
          else if (/last\s*name|lname|surname/i.test(ctx)) setVal(inp, "Ahmed");
          else if (/full\s*name|candidate\s*name|your\s*name/i.test(ctx))
            setVal(inp, "Mohammed Abdul Rafi Ahmed");
          else if (/e-?mail/i.test(ctx) || inp.type === "email")
            setVal(inp, "rafi.success@gmail.com");
          else if (/phone|mobile|tel\b/i.test(ctx) || inp.type === "tel")
            setVal(inp, "8790251698");
          else if (/city|location|prefer.*loc/i.test(ctx) && !/url|email/i.test(ctx))
            setVal(inp, "Hyderabad");
          else if (/notice|joining|availability|immediate/i.test(ctx))
            setVal(inp, "Immediate");
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
    "button:has-text('Send application')",
    "a:has-text('Apply')",
    "input[type='submit']",
  ]) {
    const b = page.locator(sel).first();
    if (await b.isVisible().catch(() => false)) {
      await b.click().catch(() => {});
      await sleep(2500);
      break;
    }
  }
}

function isThankYou(text) {
  return /thank you for appl|application (has been )?submitted|successfully submitted|we have received your application|application received|thanks for applying|application was sent/i.test(
    text || ""
  );
}

async function attemptAts(context, job) {
  const url = job.url || job.atsUrl || job.redirectUrl;
  if (!url || SKIP_HOST.test(url)) {
    return { ...job, outcome: "skipped_non_ats", url };
  }
  if (!RETRYABLE.test(url)) {
    return { ...job, outcome: "skipped_low_yield", url };
  }
  if (/hirist/i.test(url)) {
    return { ...job, outcome: "hirist_login_required_skip", url };
  }

  const page = await context.newPage();
  const start = Date.now();
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90000 }).catch(() => {});
    await sleep(2000);

    while (Date.now() - start < MAX_EXTERNAL_MS) {
      const cur = page.url();
      const text = await page
        .evaluate(() => (document.body?.innerText || "").slice(0, 2500))
        .catch(() => "");

      if (/captcha|verify you are human|cloudflare/i.test(text)) {
        return { ...job, outcome: "captcha_wall", url: cur };
      }
      if (
        /sign in|log in|login/i.test(cur + " " + text) &&
        !/application|apply|thank/i.test(text)
      ) {
        if (/hirist/i.test(cur + text)) {
          return { ...job, outcome: "hirist_login_required_skip", url: cur };
        }
        const guest = page
          .locator("text=/Continue as guest|Apply without|Don't have an account/i")
          .first();
        if (await guest.isVisible().catch(() => false)) {
          await guest.click().catch(() => {});
          await sleep(1500);
        } else {
          return { ...job, outcome: "ats_login_wall", url: cur };
        }
      }

      if (isThankYou(text)) {
        return {
          ...job,
          outcome: "applied",
          url: cur,
          resume: RESUME,
          confirmed: true,
        };
      }

      // Greenhouse / Lever often need Apply click first
      const applyEntry = page
        .locator(
          "a:has-text('Apply'), button:has-text('Apply for this job'), button:has-text('Apply now'), a:has-text('Apply for this job')"
        )
        .first();
      if (await applyEntry.isVisible().catch(() => false)) {
        await applyEntry.click().catch(() => {});
        await sleep(2000);
      }

      await fillAndSubmit(page);

      const after = await page
        .evaluate(() => (document.body?.innerText || "").slice(0, 2500))
        .catch(() => "");
      if (isThankYou(after)) {
        return {
          ...job,
          outcome: "applied",
          url: page.url(),
          resume: RESUME,
          confirmed: true,
        };
      }

      const next = page
        .locator(
          "button:has-text('Next'), button:has-text('Continue'), button:has-text('Save and Continue'), button:has-text('Review')"
        )
        .first();
      if (await next.isVisible().catch(() => false)) {
        await next.click().catch(() => {});
        await sleep(1500);
        continue;
      }
      await sleep(2500);
    }
    return { ...job, outcome: "external_incomplete_or_timeout", url: page.url() };
  } catch (e) {
    return {
      ...job,
      outcome: "exception",
      error: String(e).slice(0, 300),
      url,
    };
  } finally {
    await page.close().catch(() => {});
  }
}

async function main() {
  const src = JSON.parse(fs.readFileSync(SOURCE, "utf8"));
  const blocked = (src.blocked || []).filter(
    (b) => b.reason === "external_incomplete_or_timeout" && (b.url || b.atsUrl)
  );
  // De-dupe by URL
  const seen = new Set();
  const targets = [];
  for (const b of blocked) {
    const u = b.url || b.atsUrl;
    if (seen.has(u)) continue;
    seen.add(u);
    targets.push(b);
  }

  const { chromium } = require("playwright-core");
  const browser = await chromium.connectOverCDP(CDP);
  const context = browser.contexts()[0];
  if (!context) throw new Error("no chrome context on CDP");

  const report = {
    startedAt: new Date().toISOString(),
    resume: RESUME,
    sourceBlocked: blocked.length,
    targets: targets.length,
    applied: [],
    blocked: [],
    skipped: [],
  };

  try {
    for (const job of targets) {
      console.log("RETRY", job.company, "|", (job.role || "").slice(0, 60), "|", (job.url || "").slice(0, 80));
      const result = await attemptAts(context, job);
      if (result.outcome === "applied") {
        report.applied.push(result);
        console.log("  OK applied");
      } else if (
        /skip|hirist/i.test(result.outcome || "")
      ) {
        report.skipped.push(result);
        console.log("  skip", result.outcome);
      } else {
        report.blocked.push(result);
        console.log("  blocked", result.outcome);
      }
    }
  } finally {
    report.finishedAt = new Date().toISOString();
    report.counts = {
      applied: report.applied.length,
      blocked: report.blocked.length,
      skipped: report.skipped.length,
    };
    fs.mkdirSync(path.dirname(REPORT), { recursive: true });
    fs.writeFileSync(REPORT, JSON.stringify(report, null, 2));

    // Merge confirmed applies into daily report (honest append only).
    if (report.applied.length) {
      src.external = [...(src.external || []), ...report.applied];
      src.applied = [...(src.applied || []), ...report.applied];
      // Remove matching URLs from blocked
      const appliedUrls = new Set(report.applied.map((a) => a.url));
      src.blocked = (src.blocked || []).filter((b) => !appliedUrls.has(b.url));
      src.atsRetry = {
        finishedAt: report.finishedAt,
        counts: report.counts,
        report: REPORT,
      };
      src.counts = {
        profileUpdated: Boolean(src.profileResumeRefresh?.profileUpdated),
        applied: src.applied.length,
        externalCompleted: src.external.length,
        blocked: src.blocked.length,
        skipped: (src.skipped || []).length,
        seen: (src.seen || []).length,
      };
      src.finishedAt = new Date().toISOString();
      fs.writeFileSync(SOURCE, JSON.stringify(src, null, 2));
    }

    console.log(JSON.stringify({ counts: report.counts, applied: report.applied }, null, 2));
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
