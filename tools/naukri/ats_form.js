/**
 * Shared ATS form helpers (Greenhouse comboboxes, generic required fields).
 */
"use strict";

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function escapeRe(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Fill a Greenhouse react-select combobox by accessible label.
 */
async function fillOneCombobox(page, combo, answers) {
  if (!(await combo.isVisible().catch(() => false))) return false;
  await combo.click({ force: true }).catch(() => {});
  await sleep(300);

  for (const ans of answers) {
    await page.keyboard.press("Control+a").catch(() => {});
    await page.keyboard.press("Backspace").catch(() => {});
    if (!/^(Yes|No|N\/A)$/i.test(ans)) {
      await page.keyboard.type(String(ans), { delay: 20 });
      await sleep(400);
    } else {
      await sleep(200);
    }

    // Only visible options from the open menu (ignore hidden phone-code lists).
    const opts = page.locator("[role='option']:visible");
    const n = await opts.count();
    for (let i = 0; i < Math.min(n, 100); i++) {
      const t = ((await opts.nth(i).innerText().catch(() => "")) || "").trim();
      if (!t || /\+\d+/.test(t)) continue;
      if (new RegExp(`^${escapeRe(ans)}$`, "i").test(t)) {
        await opts.nth(i).click({ force: true }).catch(() => {});
        await sleep(250);
        return true;
      }
    }
    for (let i = 0; i < Math.min(n, 100); i++) {
      const t = ((await opts.nth(i).innerText().catch(() => "")) || "").trim();
      if (!t || /\+\d+/.test(t)) continue;
      if (new RegExp(`^${escapeRe(ans)}`, "i").test(t)) {
        await opts.nth(i).click({ force: true }).catch(() => {});
        await sleep(250);
        return true;
      }
    }
  }
  await page.keyboard.press("Escape").catch(() => {});
  return false;
}

async function fillLabeledCombobox(page, labelRegex, answer) {
  const answers = Array.isArray(answer) ? answer : [answer];
  // Greenhouse boards can render duplicate demographic question blocks — fill all.
  const labels = page.locator("label").filter({ hasText: labelRegex });
  const labelCount = await labels.count().catch(() => 0);
  let any = false;
  const seenIds = new Set();
  for (let i = 0; i < labelCount; i++) {
    const forId = await labels.nth(i).getAttribute("for").catch(() => null);
    if (!forId || seenIds.has(forId)) continue;
    seenIds.add(forId);
    const combo = page.locator(`[id="${forId}"]`);
    if (await fillOneCombobox(page, combo, answers)) any = true;
  }
  if (any) return true;

  const byLabel = page.getByLabel(labelRegex);
  const count = await byLabel.count().catch(() => 0);
  for (let i = 0; i < count; i++) {
    const el = byLabel.nth(i);
    const id = (await el.getAttribute("id").catch(() => "")) || "";
    if (id && seenIds.has(id)) continue;
    if (id) seenIds.add(id);
    if (await fillOneCombobox(page, el, answers)) any = true;
  }
  return any;
}

async function checkLabeledOption(page, legendRe, optionRe) {
  const fieldsets = page.locator("fieldset").filter({ hasText: legendRe });
  const fc = await fieldsets.count().catch(() => 0);
  let any = false;
  for (let f = 0; f < fc; f++) {
    const fieldset = fieldsets.nth(f);
    const inputs = fieldset.locator("input[type=checkbox], input[type=radio]");
    const n = await inputs.count();
    for (let i = 0; i < n; i++) {
      const id = await inputs.nth(i).getAttribute("id").catch(() => null);
      let text = "";
      if (id) {
        text = await page
          .locator("label")
          .filter({ has: page.locator(`[id="${id}"]`) })
          .innerText()
          .catch(() => "");
        if (!text) {
          text = await page
            .evaluate((fid) => {
              const lab = document.querySelector(`label[for="${fid}"]`);
              return lab?.innerText || "";
            }, id)
            .catch(() => "");
        }
      }
      if (!text) {
        text = await inputs
          .nth(i)
          .evaluate(
            (el) =>
              el.closest("label")?.innerText ||
              el.parentElement?.innerText ||
              ""
          )
          .catch(() => "");
      }
      if (optionRe.test(text || "")) {
        await inputs.nth(i).check({ force: true }).catch(() => {});
        any = true;
      }
    }
  }
  return any;
}

/** Best-effort Greenhouse / job-board required answers for Hyd candidate. */
async function fillCommonAtsQuestions(page) {
  const pairs = [
    [/Current country of residence/i, "India"],
    // Many GH boards keep US state lists after India; use N/A (not Telangana).
    [/^State/i, "N/A"],
    [/ever been employed/i, "No"],
    [/currently working/i, "No"],
    [/authorized to work/i, "Yes"],
    [/require sponsorship|visa sponsorship|immigration sponsorship/i, "No"],
    [/Applicant Privacy Policy/i, "Yes"],
    [/hybrid model|work from office|days from office/i, "Yes"],
    [/managing a team|people management|leadership perspective/i, "Yes"],
    [/join the team within|notice period|immediate/i, "Yes"],
    [/gender/i, "Male"],
    [/how did you hear/i, "Naukri"],
    [/years of experience|total experience/i, "15"],
    [/notice period|available to start|start date/i, "Immediate"],
    [/expected (ctc|salary|compensation)|desired salary/i, "6500000"],
    [/current (ctc|salary|compensation)|present ctc/i, "5200000"],
    [/willing to relocate/i, "Yes"],
  ];
  for (const [re, val] of pairs) {
    const ok = await fillLabeledCombobox(page, re, val).catch(() => false);
    if (/country of residence/i.test(String(re)) && ok) await sleep(1000);
  }

  // Checkbox / multi-select questions
  await checkLabeledOption(
    page,
    /willing to relocate/i,
    /I'm based in Hyderabad|^Yes$/i
  ).catch(() => {});
  await checkLabeledOption(page, /hybrid model|days from office/i, /^Yes$/i).catch(
    () => {}
  );

  // Phone "Country*" is a react-select (#country) — choose India +91 (allow +NNN here).
  const phoneCountry = page.locator("label").filter({ hasText: /^Country\*?$/i }).first();
  if (await phoneCountry.isVisible().catch(() => false)) {
    const forId = await phoneCountry.getAttribute("for").catch(() => "country");
    const combo = page.locator(`[id="${forId || "country"}"]`);
    await combo.click({ force: true }).catch(() => {});
    await sleep(300);
    await page.keyboard.type("India", { delay: 20 });
    await sleep(400);
    const opt = page
      .locator("[role='option']:visible")
      .filter({ hasText: /^India\s*\+91$/i })
      .first();
    if (await opt.isVisible().catch(() => false)) {
      await opt.click({ force: true }).catch(() => {});
    } else {
      const anyIndia = page
        .locator("[role='option']:visible")
        .filter({ hasText: /^India\b/i })
        .first();
      await anyIndia.click({ force: true }).catch(() => {});
    }
    await sleep(200);
  }

  const selects = page.locator("select");
  const n = await selects.count();
  for (let i = 0; i < n; i++) {
    const sel = selects.nth(i);
    const opts = await sel.locator("option").allTextContents().catch(() => []);
    const pick =
      opts.find((o) => /^India$/i.test(o.trim())) ||
      opts.find((o) => /Telangana/i.test(o)) ||
      opts.find((o) => /^N\/A$/i.test(o.trim())) ||
      opts.find((o) => /^No$/i.test(o.trim())) ||
      opts.find((o) => /^Yes$/i.test(o.trim()));
    if (pick) await sel.selectOption({ label: pick.trim() }).catch(() => {});
  }
}

module.exports = {
  fillLabeledCombobox,
  fillCommonAtsQuestions,
};
