/**
 * Complete Hirist in-app screening (/job/{id}/screening) after apply-multiple
 * returns "Assessment/ screening is required".
 */
"use strict";

const { CURRENT_CTC_LPA, EXPECTED_CTC_LPA } = require("./resume");

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function pickScreeningAnswer(
  question,
  options,
  { currentCtc = CURRENT_CTC_LPA, expectedCtc = EXPECTED_CTC_LPA } = {}
) {
  const q = String(question || "").toLowerCase();
  const opts = (options || []).map((o) => String(o));

  if (/notice period/.test(q)) {
    const imm = opts.findIndex((o) => /immediately/i.test(o));
    if (imm >= 0) return { kind: "option", index: imm, value: opts[imm] };
    if (opts.length) return { kind: "option", index: 0, value: opts[0] };
  }

  if (/expected/.test(q) && /salary|ctc|lpa|annual/.test(q)) {
    return { kind: "number", value: expectedCtc };
  }
  if ((/current/.test(q) || /annual salary/.test(q)) && /salary|ctc|lpa|annual/.test(q)) {
    return { kind: "number", value: currentCtc };
  }
  if (/salary|ctc|lpa/.test(q)) {
    return { kind: "number", value: currentCtc };
  }

  if (/hyderabad|secunderabad|\bhyd\b|relocate|willing to|work from home|remote/.test(q)) {
    const yes = opts.findIndex((o) => /^yes\b/i.test(o.trim()));
    if (yes >= 0) return { kind: "option", index: yes, value: opts[yes] };
    return { kind: "option", value: "Yes" };
  }

  return null;
}

function screeningSuccess(url, body) {
  const u = String(url || "");
  const text = String(body || "");
  return /\/job\/applied/i.test(u) || /submitted successfully/i.test(text);
}

async function fillVisibleScreening(page) {
  return page.evaluate(
    ({ currentCtc, expectedCtc }) => {
      const clickExact = (re, maxLen = 80) => {
        const els = [...document.querySelectorAll("button, [role=button], label, li, div, span")];
        const el = els.find((e) => {
          const t = (e.innerText || "").trim();
          return t && t.length <= maxLen && re.test(t);
        });
        if (el) el.click();
        return el ? (el.innerText || "").trim() : null;
      };

      const clicks = [];
      const imm = clickExact(/^immediately available$/i);
      if (imm) clicks.push(imm);

      const yes = clickExact(/^yes$/i, 8);
      if (yes) clicks.push(yes);

      const blockText = (el) => {
        let n = el;
        for (let i = 0; i < 6 && n; i++) {
          const t = (n.innerText || "").trim();
          if (t && t.length < 400) return t;
          n = n.parentElement;
        }
        return "";
      };

      for (const num of document.querySelectorAll("input[type=number], input[inputmode=decimal], input[inputmode=numeric]")) {
        const ctx = `${blockText(num)} ${num.placeholder || ""} ${num.getAttribute("aria-label") || ""}`;
        const expected = /expected/i.test(ctx);
        const val = String(expected ? expectedCtc : currentCtc);
        num.focus();
        num.value = val;
        num.dispatchEvent(new Event("input", { bubbles: true }));
        num.dispatchEvent(new Event("change", { bubbles: true }));
        clicks.push(`num:${val}`);
      }

      return clicks;
    },
    { currentCtc: CURRENT_CTC_LPA, expectedCtc: EXPECTED_CTC_LPA }
  );
}

async function clickContinue(page) {
  return page.evaluate(() => {
    const els = [...document.querySelectorAll("button, [role=button], a")];
    const n = els.find((el) => /^(next|submit|apply|continue)$/i.test((el.innerText || "").trim()));
    if (n) {
      n.click();
      return (n.innerText || "").trim();
    }
    return null;
  });
}

/**
 * Fill notice/CTC/Hyd screening and wait for apply confirmation.
 * @returns {{ ok: boolean, url?: string, reason?: string, preview?: string }}
 */
async function completeScreening(page, jobId, { timeoutMs = 180000 } = {}) {
  const id = String(jobId || "").trim();
  if (!id) return { ok: false, reason: "screening_missing_job_id" };

  await page.goto(`https://www.hirist.tech/job/${id}/screening?`, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await sleep(2000);

  const started = Date.now();
  let lastClick = null;
  while (Date.now() - started < timeoutMs) {
    const url = page.url();
    const body = await page.evaluate(() => (document.body && document.body.innerText) || "");
    if (screeningSuccess(url, body)) {
      return { ok: true, url };
    }
    await fillVisibleScreening(page);
    lastClick = await clickContinue(page);
    await sleep(1800);
    if (!lastClick) break;
  }

  const url = page.url();
  const body = await page.evaluate(() => (document.body && document.body.innerText) || "");
  if (screeningSuccess(url, body)) {
    return { ok: true, url };
  }
  return {
    ok: false,
    reason: "screening_incomplete",
    url,
    preview: body.slice(0, 220),
  };
}

module.exports = {
  pickScreeningAnswer,
  screeningSuccess,
  completeScreening,
};

if (require.main === module) {
  const samples = [
    ["What is your current notice period?", ["Immediately Available", "1 month"]],
    ["What is your current annual salary? (in LPA, e.g., 45)", null],
    ["Are you currently living in Hyderabad?", ["No", "Yes"]],
  ];
  for (const [q, opts] of samples) {
    console.log(JSON.stringify({ q, pick: pickScreeningAnswer(q, opts) }));
  }
}
