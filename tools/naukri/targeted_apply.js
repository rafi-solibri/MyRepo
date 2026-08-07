/**
 * Targeted re-apply for Hyd/Remote .NET senior roles after false skip_title fix.
 * Does not invent success — only records Applied CTA / thank-you.
 */
"use strict";

const fs = require("fs");
const { findResume, hasDotNet, shouldSkipTitle, EXPECTED_CTC_LPA, CURRENT_CTC_LPA } = require("./resume_and_filters");

const CDP = process.env.NAUKRI_CDP || "http://127.0.0.1:9222";
const RESUME = findResume();
const REPORT = "/opt/cursor/artifacts/naukri-targeted-apply.json";

const TARGETS = [
  { q: "solution architect .net", age: 7, roleRe: /solution architect.*\.net|microsoft \.net\/azure/i },
  { q: "engineering manager .net", age: 7, roleRe: /engineering manager/i, companyRe: /isolved/i },
  { q: ".net technical lead", age: 7, roleRe: /\.net lead|technical lead/i },
  { q: "principal engineer .net", age: 7, roleRe: /principal|engineering manager/i },
  { q: "dotnet technical lead", age: 7, roleRe: /\.net lead|technical lead|architect/i },
];

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function searchUrl(q, age) {
  const slug = q.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase();
  return `https://www.naukri.com/${slug}-jobs-in-hyderabad-secunderabad?k=${encodeURIComponent(q)}&l=${encodeURIComponent("hyderabad/secunderabad, remote")}&experience=12&jobAge=${age}`;
}

function parseMaxCtcLpa(text) {
  const m = String(text || "").match(/₹?\s*([\d.]+)\s*L\s*[-–]\s*₹?\s*([\d.]+)\s*L/i);
  return m ? Number(m[2]) : null;
}

async function dismiss(page) {
  for (const sel of ["button:has-text('Later')", "button:has-text('Not now')", "[aria-label='Close']", ".crossIcon"]) {
    const el = page.locator(sel).first();
    if (await el.isVisible().catch(() => false)) await el.click().catch(() => {});
  }
}

async function main() {
  const { chromium } = require("playwright-core");
  const browser = await chromium.connectOverCDP(CDP);
  const context = browser.contexts()[0];
  // Reuse an existing page when possible to avoid tab explosion / close hangs
  let page = context.pages().find((p) => /naukri\.com/i.test(p.url())) || context.pages()[0];
  if (!page) page = await context.newPage();
  page.setDefaultTimeout(45000);

  const report = {
    startedAt: new Date().toISOString(),
    resume: RESUME,
    applied: [],
    blocked: [],
    skipped: [],
    seen: [],
  };
  const seen = new Set();

  try {
    for (const t of TARGETS) {
      const url = searchUrl(t.q, t.age);
      console.log("SEARCH", t.q, t.age);
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90000 }).catch(() => {});
      await sleep(2500);
      await dismiss(page);

      const cards = await page.evaluate(() => {
        return [...document.querySelectorAll("div.cursor-pointer")]
          .filter((c) => /Quick apply|Applied|On company site/i.test(c.innerText || ""))
          .map((c, idx) => {
            const text = (c.innerText || "").trim();
            const lines = text.split("\n").map((x) => x.trim()).filter(Boolean);
            let company = (lines[0] || "").replace(/\s+\d\.\d.*$/, "").trim();
            const applyIdx = lines.findIndex((l) => /Quick apply|Applied|On company site/i.test(l));
            const role = applyIdx >= 0 ? lines[applyIdx + 1] || "" : "";
            const location = applyIdx >= 0 ? lines[applyIdx + 2] || "" : "";
            return {
              idx,
              company,
              role,
              location,
              text: text.slice(0, 500),
              already: /\bApplied\b/i.test(text) && !/Quick apply/i.test(text),
              companySite: /On company site/i.test(text),
              quick: /Quick apply/i.test(text),
            };
          });
      });

      for (const card of cards) {
        const key = `${card.company}::${card.role}`.toLowerCase();
        if (seen.has(key)) continue;
        seen.add(key);
        report.seen.push(card);

        if (t.roleRe && !t.roleRe.test(card.role) && !t.roleRe.test(card.text)) {
          continue;
        }
        if (t.companyRe && !t.companyRe.test(card.company)) continue;
        if (shouldSkipTitle(card.role)) {
          report.skipped.push({ ...card, reason: "skip_title" });
          continue;
        }
        if (!hasDotNet(card.role, card.text)) {
          report.skipped.push({ ...card, reason: "skip_no_dotnet" });
          continue;
        }
        if (!/\b(hyderabad|secunderabad|remote|wfh|hybrid)/i.test(`${card.location} ${card.text}`)) {
          report.skipped.push({ ...card, reason: "skip_location" });
          continue;
        }
        const maxCtc = parseMaxCtcLpa(card.text);
        if (maxCtc !== null && maxCtc < 50) {
          report.skipped.push({ ...card, reason: `skip_ctc_${maxCtc}` });
          continue;
        }
        if (card.already) {
          report.skipped.push({ ...card, reason: "already_applied_card" });
          continue;
        }

        console.log("OPEN", card.company, card.role);
        const locator = page.locator("div.cursor-pointer").filter({
          hasText: /Quick apply|Applied|On company site/i,
        });
        await locator.nth(card.idx).click().catch(() => {});
        await sleep(2200);
        await dismiss(page);

        // Read CTA from visible buttons near apply
        const state = await page.evaluate(() => {
          const buttons = [...document.querySelectorAll("button, a, div[role='button']")]
            .map((e) => (e.innerText || "").trim())
            .filter((t) => t && t.length < 60);
          const applyish = buttons.filter((t) => /apply|applied/i.test(t));
          return {
            applyish,
            url: location.href,
            head: document.body.innerText.slice(0, 800),
          };
        });
        console.log("STATE", card.company, state.applyish);

        if (state.applyish.some((t) => /^Applied$/i.test(t) || /Quick apply Applied/i.test(t))) {
          report.skipped.push({ ...card, reason: "already_applied_detail", applyish: state.applyish });
          await page.keyboard.press("Escape").catch(() => {});
          await sleep(500);
          continue;
        }

        if (card.companySite || state.applyish.some((t) => /company site/i.test(t))) {
          report.blocked.push({
            company: card.company,
            role: card.role,
            location: card.location,
            reason: "external_needs_manual_followup_in_burst",
            path: "company_ATS",
            naukriUrl: page.url(),
          });
          // Still try click + short ATS attempt
          const popupPromise = context.waitForEvent("page", { timeout: 8000 }).catch(() => null);
          const cta = page.locator("text=/On company site/i").first();
          if (await cta.isVisible().catch(() => false)) await cta.click().catch(() => {});
          const popup = await popupPromise;
          if (popup) {
            await sleep(3000);
            const purl = popup.url();
            const ptext = await popup.evaluate(() => (document.body?.innerText || "").slice(0, 1500)).catch(() => "");
            if (/thank you for appl|application (has been )?submitted|successfully submitted/i.test(ptext)) {
              report.applied.push({
                company: card.company,
                role: card.role,
                location: card.location,
                path: "company_ATS",
                atsUrl: purl,
                resume: RESUME,
              });
            } else {
              report.blocked.push({
                company: card.company,
                role: card.role,
                reason: "external_incomplete",
                atsUrl: purl,
                path: "company_ATS",
              });
            }
            // don't await close forever
            popup.close().catch(() => {});
          }
          await page.keyboard.press("Escape").catch(() => {});
          continue;
        }

        // Quick apply
        const qa = page.locator("button:has-text('Quick apply'), button:has-text('Quick Apply')").first();
        if (!(await qa.isVisible().catch(() => false))) {
          report.blocked.push({ ...card, reason: "quick_apply_missing", applyish: state.applyish });
          await page.keyboard.press("Escape").catch(() => {});
          continue;
        }
        await qa.click().catch(() => {});
        await sleep(2500);
        await dismiss(page);

        // Fill CTC chat if present
        await page
          .evaluate(
            ({ cur, exp }) => {
              for (const inp of document.querySelectorAll("input, textarea")) {
                if (inp.offsetParent === null) continue;
                const ctx = `${inp.placeholder || ""} ${inp.name || ""} ${inp.closest("div,li,section")?.innerText || ""}`.slice(0, 200);
                if (/expected/i.test(ctx) && /ctc|salary|lpa/i.test(ctx)) {
                  inp.value = String(exp);
                  inp.dispatchEvent(new Event("input", { bubbles: true }));
                } else if (/current/i.test(ctx) && /ctc|salary|lpa/i.test(ctx)) {
                  inp.value = String(cur);
                  inp.dispatchEvent(new Event("input", { bubbles: true }));
                } else if (/notice/i.test(ctx)) {
                  inp.value = "0";
                  inp.dispatchEvent(new Event("input", { bubbles: true }));
                }
              }
            },
            { cur: CURRENT_CTC_LPA, exp: EXPECTED_CTC_LPA }
          )
          .catch(() => {});
        for (const sel of ["button:has-text('Submit')", "button:has-text('Save')", "button:has-text('Continue')"]) {
          const b = page.locator(sel).first();
          if (await b.isVisible().catch(() => false)) {
            await b.click().catch(() => {});
            await sleep(1200);
          }
        }

        await sleep(1500);
        const after = await page.evaluate(() => {
          const buttons = [...document.querySelectorAll("button, a, div[role='button']")]
            .map((e) => (e.innerText || "").trim())
            .filter((t) => /apply|applied/i.test(t) && t.length < 60);
          const body = document.body.innerText || "";
          return {
            buttons,
            success: /applied successfully|application sent|successfully applied|Quick apply Applied/i.test(body),
          };
        });

        const confirmed =
          after.success ||
          after.buttons.some((t) => /Quick apply Applied|^Applied$/i.test(t));

        if (confirmed) {
          // recruiter note attempt
          let recruiterNote = false;
          const chat = page.locator("text=/Contact recruiter|Chat with recruiter|Message recruiter/i").first();
          if (await chat.isVisible().catch(() => false)) {
            await chat.click().catch(() => {});
            await sleep(800);
            const box = page.locator("textarea:visible").first();
            if (await box.isVisible().catch(() => false)) {
              await box
                .fill(
                  "Hi — Solutions Architect / Tech Lead (.NET, Azure/AWS, microservices), Hyderabad, immediate, expected 65 LPA. Open to a 15–20 min screen. — Mohammed Abdul Rafi Ahmed"
                )
                .catch(() => {});
              const send = page.locator("button:has-text('Send')").first();
              if (await send.isVisible().catch(() => false)) {
                await send.click().catch(() => {});
                recruiterNote = true;
              }
            }
          }
          report.applied.push({
            company: card.company,
            role: card.role,
            location: card.location,
            path: "Naukri",
            naukriUrl: page.url(),
            query: t.q,
            resume: RESUME,
            recruiterNote,
            confirmButtons: after.buttons,
          });
          console.log("APPLIED", card.company, card.role);
        } else {
          report.blocked.push({
            company: card.company,
            role: card.role,
            location: card.location,
            reason: "apply_unconfirmed",
            buttons: after.buttons,
            path: "Naukri",
            naukriUrl: page.url(),
          });
          console.log("UNCONFIRMED", card.company, after.buttons);
        }
        await page.keyboard.press("Escape").catch(() => {});
        await sleep(700);
      }
    }
  } finally {
    report.finishedAt = new Date().toISOString();
    report.counts = {
      applied: report.applied.length,
      blocked: report.blocked.length,
      skipped: report.skipped.length,
      seen: report.seen.length,
    };
    fs.writeFileSync(REPORT, JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
