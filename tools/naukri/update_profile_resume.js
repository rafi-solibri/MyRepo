#!/usr/bin/env node
/**
 * Daily Naukri profile resume refresh.
 *
 * Uploads resumes/Rafi_Resume.docx to https://www.naukri.com/mnjuser/profile
 * so recruiters see "Updated today" and the latest CV.
 *
 * Prerequisites:
 * - Logged-in Naukri Chrome CDP on http://127.0.0.1:9222
 * - bash scripts/bootstrap-job-assets.sh already run
 *
 * Usage:
 *   node tools/naukri/update_profile_resume.js
 *
 * Exit codes:
 *   0 — upload + verify today (or soft success with warning if NAUKRI_RESUME_SOFT=1)
 *   2 — missing resume / playwright
 *   3 — login required
 *   4 — file input / upload path failed
 *   5 — upload ran but "Updated today" not confirmed after retries
 *   1 — unexpected exception
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { hasAuth } = require("../chrome_session");
const { writeArtifactJson } = require("../artifact_path");
const {
  findResume,
  CHROME_PROFILE,
  RESUME_HEADLINE,
  PROFILE_URL: DEFAULT_PROFILE_URL,
} = require("./resume_and_filters");

const CDP = process.env.NAUKRI_CDP || "http://127.0.0.1:9222";
const PROFILE_URL = process.env.NAUKRI_PROFILE_URL || DEFAULT_PROFILE_URL;
const REPORT =
  process.env.NAUKRI_RESUME_REPORT ||
  require("../artifact_path").artifactPaths("naukri-profile-resume.json")[0];
const SOFT = process.env.NAUKRI_RESUME_SOFT === "1";
const MAX_ATTEMPTS = Number(process.env.NAUKRI_RESUME_ATTEMPTS || 3);
const SKIP_HEADLINE = process.env.NAUKRI_SKIP_HEADLINE === "1";

/** Prefer explicit per-job tailored path, else canonical Rafi_Resume.docx. */
function resolveResumePath() {
  const envPath =
    process.env.NAUKRI_RESUME_FILE || process.env.NAUKRI_RESUME_PATH || "";
  if (envPath && fs.existsSync(envPath) && fs.statSync(envPath).size > 1000) {
    return path.resolve(envPath);
  }
  return findResume();
}

/** Prefer resume-specific inputs — never random page file inputs (photo/etc). */
const RESUME_FILE_SELECTORS = [
  "#attachCV",
  "#lazyAttachCV",
  "input#attachCV",
  "input#lazyAttachCV",
  "input[name='attachCV']",
  "input[id*='attachCV' i]",
  "input[id*='resume' i][type='file']",
  "input[name*='resume' i][type='file']",
  "input[name*='cv' i][type='file']",
];

/** Naukri dates the profile in IST. Cloud VMs are UTC — local Date() is wrong near midnight IST. */
const NAUKRI_TZ = "Asia/Kolkata";

function todayPartsIst(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: NAUKRI_TZ,
    year: "numeric",
    month: "short",
    day: "numeric",
  }).formatToParts(now);
  const get = (type) => parts.find((p) => p.type === type)?.value;
  const monthNum = Number(
    new Intl.DateTimeFormat("en-US", {
      timeZone: NAUKRI_TZ,
      month: "numeric",
    }).format(now)
  );
  return {
    y: Number(get("year")),
    m: get("month"),
    day: Number(get("day")),
    monthNum,
  };
}

function todayTokens(now = new Date()) {
  const { y, m, day, monthNum } = todayPartsIst(now);
  const dd = String(day).padStart(2, "0");
  const mm = String(monthNum).padStart(2, "0");
  const yy = String(y).slice(-2);
  return [
    "Updated today",
    "updated today",
    "Today",
    "today",
    `${m} ${day}, ${y}`,
    `${m} ${dd}, ${y}`,
    `${day} ${m} ${y}`,
    `${dd} ${m} ${y}`,
    `${day} ${m}`,
    `${dd} ${m}`,
    `${m} ${day}`,
    `${m} ${dd}`,
    // Naukri resume card: "Uploaded on 24/08/2026"
    `${dd}/${mm}/${y}`,
    `${day}/${monthNum}/${y}`,
    `${dd}/${mm}/${yy}`,
    `${dd}-${mm}-${y}`,
    `${dd}.${mm}.${y}`,
    `Uploaded on ${dd}/${mm}/${y}`,
    `Uploaded on ${day}/${monthNum}/${y}`,
  ];
}

function blobHitsToday(blob, now = new Date()) {
  const text = String(blob || "");
  return todayTokens(now).find((t) => text.includes(t)) || null;
}

async function dismissPopups(page) {
  for (const sel of [
    "button:has-text('Later')",
    "button:has-text('Not now')",
    "button:has-text('Skip')",
    "button:has-text('No thanks')",
    "[aria-label='Close']",
    ".crossIcon",
    "button:has-text('Close')",
    ".lightbox .close",
  ]) {
    const el = page.locator(sel).first();
    if (await el.isVisible().catch(() => false)) {
      await el.click().catch(() => {});
      await page.waitForTimeout(400);
    }
  }
}

async function ensureLoggedIn(page) {
  let lastErr = null;
  for (let i = 0; i < 3; i++) {
    try {
      await page.goto(PROFILE_URL, {
        waitUntil: "domcontentloaded",
        timeout: 60000,
      });
      lastErr = null;
      break;
    } catch (e) {
      lastErr = e;
      await page.waitForTimeout(1500).catch(() => {});
    }
  }
  if (lastErr) throw lastErr;
  await page.waitForTimeout(2500);
  await dismissPopups(page);
  const url = page.url();
  if (/nlogin|login/i.test(url)) {
    return { ok: false, reason: "naukri_login_required", url };
  }
  const body = await page.evaluate(() => document.body.innerText.slice(0, 1500));
  if (
    /login to continue|sign in|otp for logging/i.test(body) &&
    !/attach|resume|profile/i.test(body)
  ) {
    return { ok: false, reason: "naukri_login_required", url };
  }
  return { ok: true, url };
}

async function scrollResumeSection(page) {
  await page
    .evaluate(() => {
      const nodes = [...document.querySelectorAll("div, section, span, h1, h2, h3")];
      const hit = nodes.find((n) =>
        /resume|attach cv|upload cv|update resume/i.test(
          (n.innerText || "").slice(0, 80)
        )
      );
      if (hit) hit.scrollIntoView({ block: "center" });
      else window.scrollTo(0, Math.min(900, document.body.scrollHeight / 3));
    })
    .catch(() => {});
  await page.waitForTimeout(800);
}

async function findResumeFileInput(page) {
  for (const sel of RESUME_FILE_SELECTORS) {
    const loc = page.locator(sel);
    const n = await loc.count().catch(() => 0);
    for (let i = 0; i < n; i++) {
      const input = loc.nth(i);
      // Hidden inputs are OK — Naukri uses display:none attachCV
      const handle = await input.elementHandle().catch(() => null);
      if (!handle) continue;
      const meta = await handle.evaluate((el) => ({
        id: el.id || "",
        name: el.name || "",
        accept: el.getAttribute("accept") || "",
        type: el.type || "",
      }));
      if (meta.type && meta.type !== "file") continue;
      // Reject photo/avatar-ish inputs
      if (/photo|avatar|profile.?image|display.?pic/i.test(`${meta.id} ${meta.name}`)) {
        continue;
      }
      return { input, selector: sel, meta };
    }
  }
  return null;
}

async function clickUpdateResume(page) {
  const labels = [
    "text=/^Update resume$/i",
    "text=/Update resume/i",
    "text=/Upload resume/i",
    "text=/Replace resume/i",
    "text=/Update CV/i",
    "text=/Upload CV/i",
    "a:has-text('Update resume')",
    "button:has-text('Update resume')",
    ".updateResume, .uploadResume, [class*='updateResume'], [class*='attachCV']",
  ];
  for (const sel of labels) {
    const el = page.locator(sel).first();
    if (await el.isVisible().catch(() => false)) {
      await el.click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(1000);
      return sel;
    }
  }
  return null;
}

async function waitUploadSignals(page) {
  const started = Date.now();
  let signal = null;
  while (Date.now() - started < 20000) {
    const hit = await page.evaluate(() => {
      const t = document.body.innerText || "";
      const patterns = [
        /successfully uploaded/i,
        /resume (has been )?uploaded/i,
        /resume updated/i,
        /updated today/i,
        /upload successful/i,
        /rafi_resume/i,
      ];
      for (const p of patterns) {
        if (p.test(t)) return p.toString();
      }
      // Progress / spinner gone + updateOn present
      const updateOn = [...document.querySelectorAll(".updateOn, [class*='updateOn']")]
        .map((e) => e.innerText.trim())
        .filter(Boolean);
      if (updateOn.length) return `updateOn:${updateOn[0]}`;
      return null;
    });
    if (hit) {
      signal = hit;
      break;
    }
    await page.waitForTimeout(800);
  }
  return signal;
}

async function confirmSave(page) {
  for (const sel of [
    "button:has-text('Save')",
    "button:has-text('Submit')",
    "button:has-text('Update')",
    "button:has-text('Confirm')",
    "button[type='submit']",
    ".lightbox button:has-text('Save')",
  ]) {
    const btn = page.locator(sel).first();
    if (await btn.isVisible().catch(() => false)) {
      await btn.click().catch(() => {});
      await page.waitForTimeout(2000);
      return sel;
    }
  }
  return null;
}

async function uploadResume(page, resumePath) {
  await scrollResumeSection(page);
  await dismissPopups(page);

  let uploadedVia = null;
  let clicked = await clickUpdateResume(page);

  // Path A: dedicated resume file input
  let found = await findResumeFileInput(page);
  if (found) {
    try {
      await found.input.setInputFiles(resumePath, { timeout: 25000 });
      uploadedVia = found.selector;
    } catch (_) {
      // fall through
    }
  }

  // Path B: filechooser after clicking Update resume
  if (!uploadedVia) {
    clicked = clicked || (await clickUpdateResume(page));
    const [chooser] = await Promise.all([
      page.waitForEvent("filechooser", { timeout: 10000 }).catch(() => null),
      (async () => {
        if (!clicked) await clickUpdateResume(page);
        else {
          // re-click to open chooser if needed
          await clickUpdateResume(page);
        }
      })(),
    ]);
    if (chooser) {
      await chooser.setFiles(resumePath);
      uploadedVia = "filechooser";
    }
  }

  // Path C: retry finding resume inputs after click
  if (!uploadedVia) {
    found = await findResumeFileInput(page);
    if (found) {
      await found.input.setInputFiles(resumePath, { timeout: 25000 });
      uploadedVia = found.selector;
    }
  }

  if (!uploadedVia) {
    return { ok: false, reason: "resume_file_input_not_found", clicked };
  }

  const saveClicked = await confirmSave(page);
  const signal = await waitUploadSignals(page);
  await dismissPopups(page);

  return {
    ok: true,
    uploadedVia,
    clicked,
    saveClicked,
    signal,
  };
}

async function touchHeadline(page) {
  try {
    await scrollResumeSection(page);
    // Open headline editor — several Naukri UI variants
    const openers = [
      "[class*='resumeHeadline'] .edit, [class*='resumeHeadline'] button, [class*='resumeHeadline'] span.edit",
      "[class*='resume-headline'] button, [class*='resume-headline'] .edit",
      "text=/Resume headline/i",
      "text=/Edit resume headline/i",
      "#resumeHeadline .edit, #resumeHeadline button",
      "div.resumeHeadline span.edit, .widgetHead .edit",
    ];
    let opened = false;
    for (const sel of openers) {
      const el = page.locator(sel).first();
      if (await el.isVisible().catch(() => false)) {
        await el.click().catch(() => {});
        await page.waitForTimeout(1000);
        opened = true;
        break;
      }
    }
    if (!opened) {
      // Click nearby pencil icons in resume headline widget
      const pencil = page
        .locator(
          "section:has-text('Resume headline') button, section:has-text('Resume headline') .edit, div:has-text('Resume headline') >> .. >> .edit"
        )
        .first();
      if (await pencil.isVisible().catch(() => false)) {
        await pencil.click().catch(() => {});
        await page.waitForTimeout(1000);
        opened = true;
      }
    }

    const box = page
      .locator(
        "textarea#resumeHeadline, textarea[name*='headline' i], .resumeHeadline textarea, .lightbox textarea, .drawer textarea, textarea"
      )
      .first();
    if (!(await box.isVisible().catch(() => false))) {
      return { touched: false, reason: "headline_input_missing", opened };
    }

    const current = (await box.inputValue().catch(() => "")) || "";
    const next =
      current.trim().length >= 5 ? current.trim() : RESUME_HEADLINE;
    // Force a save even when identical: append/remove trailing period then restore
    await box.fill(next + " ");
    await page.waitForTimeout(200);
    await box.fill(next);

    const save = page
      .locator(
        ".lightbox button:has-text('Save'), .drawer button:has-text('Save'), button:has-text('Save changes'), button:has-text('Save')"
      )
      .first();
    if (await save.isVisible().catch(() => false)) {
      await save.click();
      await page.waitForTimeout(2000);
      await dismissPopups(page);
      return { touched: true, headline: next.slice(0, 120) };
    }
    return { touched: false, reason: "headline_save_missing", opened };
  } catch (e) {
    return { touched: false, reason: String(e).slice(0, 200) };
  }
}

async function verifyUpdated(page) {
  await page.goto(PROFILE_URL, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(2500);
  await dismissPopups(page);
  await scrollResumeSection(page);
  await page.waitForTimeout(1000);

  const text = await page.evaluate(() => {
    const updateOn = [
      ...document.querySelectorAll(
        ".updateOn, [class*='updateOn'], [class*='update-on'], [class*='lastUpdated'], [class*='last-updated']"
      ),
    ]
      .map((e) => e.innerText.trim())
      .filter(Boolean)
      .join(" | ");

    const resumeBits = [...document.querySelectorAll("a, span, div, p")]
      .map((e) => (e.innerText || "").trim())
      .filter((t) => t && t.length < 100 && /Rafi_Resume|\.docx|\.pdf/i.test(t))
      .slice(0, 5);

    // Collect nearby "Updated …" / "Uploaded on …" phrases (Naukri resume card)
    const updatedLines = (document.body.innerText || "")
      .split("\n")
      .map((l) => l.trim())
      .filter(
        (l) =>
          /^updated\b/i.test(l) ||
          /\bupdated today\b/i.test(l) ||
          /\buploaded on\b/i.test(l)
      )
      .slice(0, 10);

    return {
      updateOn,
      updatedLines,
      resumeName: resumeBits[0] || "",
      resumeBits,
      bodySlice: document.body.innerText.slice(0, 6000),
    };
  });

  const tokens = todayTokens();
  const blob = [
    text.updateOn,
    text.updatedLines.join("\n"),
    text.resumeName,
    (text.resumeBits || []).join("\n"),
    text.bodySlice,
  ].join("\n");
  const matchedToken = blobHitsToday(blob);
  const todayHit = Boolean(matchedToken);
  const resumePresent = /Rafi_Resume|\.docx/i.test(
    `${text.resumeName} ${text.resumeBits.join(" ")}`
  );

  return {
    todayHit,
    resumePresent,
    matchedToken,
    updateOn: text.updateOn,
    updatedLines: text.updatedLines,
    resumeName: text.resumeName,
    tokensTried: tokens.filter((t) => /[0-9]|Uploaded|Updated today/i.test(t)).slice(0, 12),
  };
}

async function runRefresh(page, resumePath) {
  const attempts = [];
  let lastVerify = null;
  let lastUpload = null;
  let lastHeadline = null;

  for (let i = 1; i <= MAX_ATTEMPTS; i++) {
    const up = await uploadResume(page, resumePath);
    lastUpload = up;
    if (!up.ok) {
      attempts.push({ attempt: i, upload: up });
      continue;
    }
    lastHeadline = SKIP_HEADLINE
      ? { touched: false, reason: "skipped_for_per_job_tailor" }
      : await touchHeadline(page);
    // Give Naukri a moment to persist
    await page.waitForTimeout(2500);
    lastVerify = await verifyUpdated(page);
    attempts.push({
      attempt: i,
      upload: up,
      headline: lastHeadline,
      verify: {
        todayHit: lastVerify.todayHit,
        resumePresent: lastVerify.resumePresent,
        updateOn: lastVerify.updateOn,
        matchedToken: lastVerify.matchedToken,
      },
    });
    if (lastVerify.todayHit && lastVerify.resumePresent) break;
    if (lastVerify.todayHit) break;
    // Soft: resume filename visible after upload counts as progress; still retry for todayHit
    await page.waitForTimeout(1500);
  }

  return { attempts, lastUpload, lastHeadline, lastVerify };
}

async function main() {
  const resume = resolveResumePath();
  const result = {
    startedAt: new Date().toISOString(),
    resume,
    chromeProfileHint: CHROME_PROFILE,
    cdp: CDP,
    auth: {
      destHasAuth: hasAuth("naukri"),
    },
    ok: false,
    profileUpdated: false,
  };

  if (!resume) {
    result.reason = "Rafi_Resume.docx_missing";
    writeReport(result);
    console.error(JSON.stringify(result, null, 2));
    process.exit(2);
  }

  let chromium;
  try {
    ({ chromium } = require("playwright-core"));
  } catch {
    try {
      ({ chromium } = require("playwright"));
    } catch (e) {
      result.reason = "playwright_missing";
      result.error = String(e);
      writeReport(result);
      console.error(JSON.stringify(result, null, 2));
      process.exit(2);
    }
  }

  let page;
  try {
    const browser = await chromium.connectOverCDP(CDP);
    const context = browser.contexts()[0] || (await browser.newContext());
    // Reuse one profile tab and close extras — daily_apply mid-run uploads
    // otherwise leave 10+ mnjuser/profile tabs and page.goto times out.
    const existing = context
      .pages()
      .filter((p) => /naukri\.com\/mnjuser\/profile/i.test(p.url() || ""));
    for (const p of existing.slice(0, -1)) {
      p.close().catch(() => {});
    }
    page = existing[existing.length - 1] || (await context.newPage());
    page.setDefaultTimeout(45000);
  } catch (e) {
    result.reason = "cdp_unreachable";
    result.error = String(e).slice(0, 500);
    result.hint = "Run: bash scripts/launch-chrome-cdp.sh naukri";
    writeReport(result);
    console.error(JSON.stringify(result, null, 2));
    process.exit(2);
  }

  try {
    const login = await ensureLoggedIn(page);
    if (!login.ok) {
      Object.assign(result, login);
      writeReport(result);
      console.error(JSON.stringify(result, null, 2));
      process.exit(3);
    }

    const abs = path.resolve(resume);
    const refresh = await runRefresh(page, abs);
    result.attempts = refresh.attempts;
    result.upload = refresh.lastUpload;
    result.headline = refresh.lastHeadline;
    result.verify = refresh.lastVerify;
    result.finishedAt = new Date().toISOString();

    if (!refresh.lastUpload || !refresh.lastUpload.ok) {
      result.reason = (refresh.lastUpload && refresh.lastUpload.reason) || "upload_failed";
      writeReport(result);
      console.error(JSON.stringify(result, null, 2));
      process.exit(4);
    }

    result.profileUpdated = Boolean(refresh.lastVerify && refresh.lastVerify.todayHit);
    result.ok = result.profileUpdated || (SOFT && refresh.lastUpload.ok);

    if (!result.profileUpdated) {
      result.warning =
        "Upload attempted but 'Updated today' not confirmed after retries. Check Naukri profile UI / session.";
      result.reason = "updated_today_unconfirmed";
      writeReport(result);
      console.error(JSON.stringify(result, null, 2));
      process.exit(SOFT ? 0 : 5);
    }

    writeReport(result);
    console.log(JSON.stringify(result, null, 2));
    process.exit(0);
  } catch (e) {
    result.reason = "exception";
    result.error = String(e).slice(0, 500);
    writeReport(result);
    console.error(JSON.stringify(result, null, 2));
    process.exit(1);
  } finally {
    if (page) await page.close().catch(() => {});
  }
}

function writeReport(obj) {
  try {
    if (process.env.NAUKRI_RESUME_NO_ARTIFACT !== "1") {
      writeArtifactJson("naukri-profile-resume.json", obj);
    }
    if (process.env.NAUKRI_RESUME_REPORT) {
      fs.mkdirSync(path.dirname(REPORT), { recursive: true });
      fs.writeFileSync(REPORT, JSON.stringify(obj, null, 2));
    }
  } catch (_) {
    // ignore
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  uploadResume,
  ensureLoggedIn,
  touchHeadline,
  verifyUpdated,
  runRefresh,
  resolveResumePath,
  todayTokens,
  todayPartsIst,
  blobHitsToday,
  NAUKRI_TZ,
  PROFILE_URL,
};
