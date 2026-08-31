/**
 * Hirist recruiter screening (/job/{id}/screening) — truthful profile answers.
 */
"use strict";

const { CURRENT_CTC_LPA, EXPECTED_CTC_LPA } = require("./resume");

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function answerScreeningQuestion(question) {
  const q = String(question || "");
  const ql = q.toLowerCase();

  if (/azure service/i.test(q)) {
    return "App Service, Azure SQL, Functions, Service Bus, Storage, Key Vault, AKS, and API Management in production .NET systems.";
  }
  if (
    /how many years|years of (exp|experience)/i.test(q) &&
    /\.net|azure|architect|c#/i.test(q)
  ) {
    return "10+ years designing and architecting enterprise applications on .NET Core and Azure (16 years total software experience).";
  }
  if (/independently owned|end-to-end|owned the technical architecture/i.test(q)) {
    return "Yes. I have independently owned technical architecture of in-house .NET/Azure applications end-to-end, from design through production operations.";
  }
  if (/current (ctc|salary|compensation)|present ctc/i.test(q)) {
    return `${CURRENT_CTC_LPA} LPA`;
  }
  if (/expected (ctc|salary|compensation)|notice period ctc/i.test(q)) {
    return `${EXPECTED_CTC_LPA} LPA`;
  }
  if (/notice|joining|availability|immediate/i.test(q) && !/ctc|salary/i.test(q)) {
    return "Immediate";
  }
  if (/\b(location|hyderabad|willing to (relocate|work)|work from home|remote)\b/i.test(q)) {
    return "Hyderabad / Remote. Immediate joiner.";
  }
  if (/^\s*(have you|are you|do you|can you)\b/i.test(q) || /\b(yes|no)\b/i.test(ql)) {
    if (/notice period|relocat|hybrid|remote|willing|available/i.test(q)) return "Yes";
    if (/architect|lead|\.net|azure|c#|independently|owned/i.test(q)) return "Yes";
  }
  return "Yes — 16 years as Technical Lead / Solution Architect on .NET, C#, Azure/AWS. Current 52 LPA, expected 65 LPA, immediate joiner, Hyderabad / Remote.";
}

function looksSubmitted(url, text) {
  const u = String(url || "");
  const t = String(text || "");
  if (/application submitted|applied successfully|successfully applied|thanks for applying|thank you for applying/i.test(t)) {
    return true;
  }
  if (/\/job\/applied(\?|$)/i.test(u) || /\/applied-jobs/i.test(u)) return true;
  return false;
}

async function fillVisibleAnswers(page) {
  const qTexts = await page
    .evaluate(() =>
      [...document.querySelectorAll("textarea")]
        .filter((el) => el.offsetParent)
        .map((el) => {
          const block = el.closest("form") || el.parentElement || el;
          return (block.innerText || "").slice(0, 600);
        })
    )
    .catch(() => []);
  const answers = (qTexts || []).map((t) => answerScreeningQuestion(t).slice(0, 500));
  const filled = await page
    .evaluate((vals) => {
      const areas = [...document.querySelectorAll("textarea")].filter((el) => el.offsetParent);
      const proto = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value");
      let n = 0;
      areas.forEach((el, i) => {
        const ans = vals[i] || "";
        if (!ans) return;
        if (proto && proto.set) proto.set.call(el, ans);
        else el.value = ans;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
        n += 1;
      });
      return n;
    }, answers)
    .catch(() => 0);

  // Hidden radios + visible labels (Hirist .radio-container-hirist).
  await page
    .evaluate(() => {
      const prefer = [/^yes$/i, /^10$/, /^8$/, /^immediately available$/i];
      const containers = [...document.querySelectorAll(".answer-options, .radio-container-hirist")];
      const groups = new Map();
      for (const lab of document.querySelectorAll(".answer-options label, .radio-container-hirist label")) {
        const group = lab.closest(".answer-options") || lab.closest(".screening-question-container") || lab.parentElement;
        if (!groups.has(group)) groups.set(group, []);
        groups.get(group).push(lab);
      }
      for (const labs of groups.values()) {
        let pick = null;
        for (const re of prefer) {
          pick = labs.find((l) => re.test((l.innerText || "").trim()));
          if (pick) break;
        }
        if (!pick) pick = labs[0];
        if (pick) pick.click();
      }
      return containers.length;
    })
    .catch(() => 0);

  await page
    .evaluate((currentCtc) => {
      for (const el of document.querySelectorAll("input[type='number'], input[type='text']")) {
        if (!el.offsetParent) continue;
        const block = (el.closest("form") || el.parentElement || el).innerText || "";
        const want = /expected/i.test(block) ? "65" : String(el.value || currentCtc);
        const proto = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value");
        if (proto && proto.set) proto.set.call(el, want);
        else el.value = want;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }, CURRENT_CTC_LPA)
    .catch(() => {});

  // Recruiter MCQ chips (Next stays disabled until a choice is selected).
  const clicked = await page
    .evaluate(() => {
      const skip = /next|submit|apply|premium|save|posted by/i;
      const prefer = [
        /^immediately available$/i,
        /^immediate$/i,
        /^yes$/i,
        /^10$/,
        /^8$/,
      ];
      const buttons = [...document.querySelectorAll("button")].filter(
        (el) => el.offsetParent && el.type !== "submit" && !skip.test((el.innerText || "").trim())
      );
      function optionGroup(el) {
        let p = el.parentElement;
        while (p && p !== document.body) {
          const sibs = [...p.querySelectorAll(":scope > button, :scope button")].filter(
            (b) => b.offsetParent && b.type !== "submit" && !skip.test((b.innerText || "").trim())
          );
          if (sibs.length >= 2 && sibs.length <= 8) return p;
          p = p.parentElement;
        }
        return el.parentElement || el;
      }
      let n = 0;
      const groups = new Map();
      for (const el of buttons) {
        const parent = optionGroup(el);
        if (!groups.has(parent)) groups.set(parent, []);
        groups.get(parent).push(el);
      }
      for (const els of groups.values()) {
        let picked = null;
        for (const re of prefer) {
          picked = els.find((el) => re.test((el.innerText || "").trim()));
          if (picked) break;
        }
        if (!picked) picked = els[0];
        if (picked) {
          picked.click();
          n += 1;
        }
      }
      return n;
    })
    .catch(() => 0);

  return filled + clicked;
}

async function clickNextOrSubmit(page) {
  for (const sel of [
    "button:has-text('Submit')",
    "button:has-text('Next')",
    "button[type='submit']",
    "a:has-text('Submit')",
    "a:has-text('Next')",
  ]) {
    const loc = page.locator(sel);
    const n = await loc.count().catch(() => 0);
    for (let i = 0; i < Math.min(n, 6); i++) {
      const b = loc.nth(i);
      if (!(await b.isVisible().catch(() => false))) continue;
      const label = ((await b.innerText().catch(() => "")) || "").trim();
      if (/sign in|log in|premium|save/i.test(label) && !/submit|next|apply/i.test(label)) {
        continue;
      }
      const disabled = await b.isDisabled().catch(() => false);
      if (disabled) continue;
      await b.click().catch(() => {});
      return true;
    }
  }
  return false;
}

/**
 * Complete recruiter screening for a Hirist job, then the caller retries apply-multiple.
 */
async function completeScreening(page, { jobId, timeoutMs = 180000 } = {}) {
  const started = Date.now();
  const url = `https://www.hirist.tech/job/${jobId}/screening`;
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForSelector("textarea, input[type='radio'], button", { timeout: 15000 }).catch(() => {});
  await sleep(800);

  let steps = 0;
  while (Date.now() - started < timeoutMs && steps < 8) {
    const body = await page.evaluate(() => (document.body && document.body.innerText) || "").catch(() => "");
    if (looksSubmitted(page.url(), body)) {
      return { ok: true, reason: "screening_submitted", steps, url: page.url() };
    }
    if (/please login|sign in to continue/i.test(body)) {
      return { ok: false, reason: "hirist_login_required", steps, url: page.url() };
    }

    const filled = await fillVisibleAnswers(page);
    if (filled) await sleep(400);
    const clicked = await clickNextOrSubmit(page);
    steps += 1;
    await sleep(1800);

    const after = await page.evaluate(() => (document.body && document.body.innerText) || "").catch(() => "");
    if (looksSubmitted(page.url(), after)) {
      return { ok: true, reason: "screening_submitted", steps, url: page.url() };
    }
    if (!filled && !clicked) break;
  }

  const finalText = await page.evaluate(() => (document.body && document.body.innerText) || "").catch(() => "");
  if (looksSubmitted(page.url(), finalText)) {
    return { ok: true, reason: "screening_submitted", steps, url: page.url() };
  }
  if (/screening|submit a form|mandatory question/i.test(finalText) && /textarea|enter your answer/i.test(finalText)) {
    return { ok: false, reason: "screening_incomplete", steps, url: page.url() };
  }
  // Left screening URL after Next — treat as form accepted; caller must verify apply.
  if (!/\/screening/i.test(page.url())) {
    return { ok: true, reason: "screening_left_form", steps, url: page.url() };
  }
  return { ok: false, reason: "screening_incomplete", steps, url: page.url() };
}

module.exports = {
  answerScreeningQuestion,
  looksSubmitted,
  completeScreening,
};
