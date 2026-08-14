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
  isArchLeadTitle,
  EXPECTED_CTC_LPA,
  CURRENT_CTC_LPA,
} = require("./resume_and_filters");
const { completeWorkdayApply, isSubmittedText } = require("./workday_apply");
const { fillCommonAtsQuestions } = require("./ats_form");
const { companyAllowed, allowlistActive } = require("../hitechcity/campus_allowlist");
const { artifactPaths, writeArtifactJson } = require("../artifact_path");

const CDP = process.env.NAUKRI_CDP || "http://127.0.0.1:9222";
const REPORT =
  process.env.NAUKRI_APPLY_REPORT ||
  artifactPaths("naukri-daily-apply.json")[0];
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
  "engineering manager",
  "technical lead",
  "software architect",
  "principal engineer",
  ".net lead",
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
const MAX_APPLIES = Number(process.env.NAUKRI_MAX_APPLIES || 60);
const MAX_EXTERNAL_MS = Number(process.env.NAUKRI_MAX_EXTERNAL_MS || 5 * 60 * 1000);
const MAX_WORKDAY_MS = Number(process.env.NAUKRI_MAX_WORKDAY_MS || 6.5 * 60 * 1000);
const SKIP_PROFILE_REFRESH = process.env.NAUKRI_SKIP_PROFILE_REFRESH === "1";
const EXPAND_BELOW = Number(process.env.NAUKRI_EXPAND_BELOW || 8);
const EARLY_EXPAND_BELOW = Number(process.env.NAUKRI_EARLY_EXPAND_BELOW || 3);
const AUTO_EXPAND_AGES =
  process.env.NAUKRI_AUTO_EXPAND_AGES !== "0"
    ? (process.env.NAUKRI_EXPAND_AGES || "15,30,60")
        .split(",")
        .map((s) => Number(String(s).trim()))
        .filter((n) => Number.isFinite(n) && n > 0)
    : [];
/** Extra query wave when primary+expand still thin. */
const EXTRA_QUERIES = [
  ".net azure architect",
  "solution architect azure",
  "dotnet engineering manager",
  "principal software engineer .net",
  "technical architect c#",
  "cloud architect .net",
];

function safeClose(page) {
  if (!page) return;
  page.close().catch(() => {});
}

function isJunkAtsUrl(url) {
  const u = String(url || "");
  return /careers\.infoedge\.com|infoedge\.in\/?$|infoedge\.com\/?$/i.test(u);
}

/** TopTier CTA copy varies: "On company site", "Go to company site", "Apply on company site". */
const COMPANY_SITE_CTA_RE =
  /Go to company site|On company site|Apply on company(?:\s+site)?|On hirist/i;

function isCompanySiteCta(text) {
  return COMPANY_SITE_CTA_RE.test(String(text || ""));
}

function preferAtsLinks(links) {
  const list = [...new Set((links || []).filter(Boolean))];
  const real = list.filter(
    (h) =>
      !isJunkAtsUrl(h) &&
      /myworkdayjobs|greenhouse|lever\.co|smartrecruiters|successfactors|icims|taleo|ashbyhq|phenom|oraclecloud|workdayjobs|jobs\.|careers\.|hirist/i.test(
        h
      )
  );
  // Prefer known ATS hosts first
  real.sort((a, b) => {
    const score = (u) =>
      /myworkdayjobs|greenhouse|lever\.co|smartrecruiters|ashbyhq|icims|hirist/i.test(
        u
      )
        ? 0
        : 1;
    return score(a) - score(b);
  });
  return real;
}

function isExternalAtsUrl(url) {
  const u = String(url || "");
  if (!/^https?:/i.test(u) || isJunkAtsUrl(u) || /naukri\.com/i.test(u))
    return false;
  return /myworkdayjobs|myworkdaysite|greenhouse|lever\.co|smartrecruiters|successfactors|icims|taleo|ashby|phenom|oraclecloud|hirist|careers\.|jobs\.|workdayjobs/i.test(
    u
  );
}

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
    const candidates = artifactPaths("naukri-profile-resume.json");
    let raw = null;
    for (const p of candidates) {
      try {
        if (fs.existsSync(p)) {
          raw = fs.readFileSync(p, "utf8");
          break;
        }
      } catch (_) {}
    }
    report = JSON.parse(raw);
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

/** Listed max CTC below this → skip. Postings often under-list; do not use 50. */
const MIN_LISTED_MAX_CTC_LPA = Number(process.env.NAUKRI_MIN_LISTED_MAX_CTC || 35);

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

/** Empty/unknown card location → allow (re-check on detail). Only hard-skip clear non-Hyd cities. */
function locationShouldSkip(locText, blob) {
  if (locationHardSkip(locText, blob)) return true;
  const locLine = ((locText || "").split("\n")[0] || "").trim();
  if (!locLine) return false;
  if (locationAllowed(locText, blob)) return false;
  // Non-empty location that is neither Hyd/remote nor a hard-skip city → skip
  return true;
}

function fingerprint(company, role) {
  return `${(company || "").toLowerCase().trim()}::${(role || "")
    .toLowerCase()
    .trim()}`;
}

/** TopTier sidebar filter chip "Applied (N)" is NOT per-job status. */
function isAppliedFilterChip(text) {
  const t = String(text || "")
    .replace(/\s+/g, " ")
    .trim();
  return /^Applied\s*\(\d+\)\s*$/i.test(t);
}

/**
 * TopTier Quick-apply buttons use dual absolute layers ("Quick apply" + "Applied").
 * button.innerText always concatenates to "Quick apply Applied" even when only one
 * layer is on-screen — the off state translates the Applied layer by ~button height.
 */
function isAlreadyAppliedCta(text) {
  const t = String(text || "")
    .replace(/\s+/g, " ")
    .trim();
  if (!t) return false;
  if (isAppliedFilterChip(t)) return false;
  // Dual-layer buttons: do NOT treat concatenated "Quick apply Applied" as applied.
  // Callers must use readVisibleApplyCta(page) for live buttons.
  if (/Quick apply/i.test(t) && /Applied/i.test(t)) return false;
  if (/^Applied$/i.test(t)) return true;
  if (
    t.length < 48 &&
    /\bApplied\b/i.test(t) &&
    !/^Quick apply$/i.test(t) &&
    !/^Applied\s*\(/i.test(t)
  ) {
    return true;
  }
  return false;
}

/** Read the on-screen Quick apply / Applied state from dual-layer TopTier buttons. */
async function readVisibleApplyCta(page) {
  return page.evaluate(() => {
    function layerTranslateY(el) {
      const st = window.getComputedStyle(el);
      const m = /matrix\(([^)]+)\)/.exec(st.transform || "");
      if (!m) return 0;
      const parts = m[1].split(",").map((x) => Number(x.trim()));
      return parts[5] || 0;
    }
    function layerOnScreen(el) {
      const st = window.getComputedStyle(el);
      if (
        st.display === "none" ||
        st.visibility === "hidden" ||
        Number(st.opacity) < 0.2
      ) {
        return false;
      }
      const ty = layerTranslateY(el);
      const r = el.getBoundingClientRect();
      // Off-screen slide: |ty| ~= button height. Prefer transform over rect —
      // background tabs often report 0x0 rects while transforms stay correct.
      if (st.transform && st.transform !== "none") {
        if (Math.abs(ty) > 12) return false;
        return true;
      }
      if (r.width < 2 || r.height < 2) return false;
      return true;
    }

    const buttons = [
      ...document.querySelectorAll("button, a, [role='button']"),
    ];
    for (const btn of buttons) {
      const raw = (btn.innerText || btn.getAttribute("aria-label") || "")
        .replace(/\s+/g, " ")
        .trim();
      if (!raw || /^Applied\s*\(\d+\)\s*$/i.test(raw)) continue;
      if (!/Quick apply|Applied/i.test(raw)) continue;
      if (/company site|hirist/i.test(raw)) continue;

      // Only the absolute slide overlays decide state (nested text spans are always "on").
      const overlays = [...btn.querySelectorAll("span")].filter((s) => {
        const st = window.getComputedStyle(s);
        return st.position === "absolute" || /absolute|inset-0/i.test(s.className || "");
      });
      const layerPool = overlays.length ? overlays : [...btn.querySelectorAll("span")];
      const quickOn = layerPool.some(
        (s) =>
          /^Quick apply$/i.test((s.innerText || "").replace(/\s+/g, " ").trim()) &&
          layerOnScreen(s)
      );
      const appliedOn = layerPool.some(
        (s) =>
          /^Applied$/i.test((s.innerText || "").replace(/\s+/g, " ").trim()) &&
          layerOnScreen(s)
      );
      if (appliedOn && !quickOn) {
        return { state: "applied", label: "Applied", raw };
      }
      if (quickOn && !appliedOn) {
        return { state: "quick", label: "Quick apply", raw };
      }
      if (quickOn && appliedOn) {
        // Both claim on-screen — prefer Quick apply (try apply) unless disabled.
        return {
          state: btn.disabled ? "applied" : "quick",
          label: btn.disabled ? "Applied" : "Quick apply",
          raw,
        };
      }
      // No layered spans — fall back to plain label.
      if (/^Applied$/i.test(raw)) return { state: "applied", label: raw, raw };
      if (/^Quick apply$/i.test(raw)) return { state: "quick", label: raw, raw };
      // Dual-layer concatenates both words; if transforms were unreadable, try apply.
      if (/Quick apply/i.test(raw) && !btn.disabled) {
        return { state: "quick", label: "Quick apply", raw };
      }
    }
    return { state: "missing", label: "", raw: "" };
  });
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
    const siteRe =
      /Go to company site|On company site|Apply on company(?:\s+site)?|On hirist/i;
    const isFilterChip = (text) =>
      /^Applied\s*\(\d+\)\s*$/i.test(String(text || "").replace(/\s+/g, " ").trim());
    const nodes = [...document.querySelectorAll("div.cursor-pointer")].filter(
      (c) => {
        const text = (c.innerText || "").replace(/\s+/g, " ").trim();
        if (!text || text.length < 40) return false;
        if (isFilterChip(text)) return false;
        // Must look like a job card: apply CTA + role/years signal.
        if (
          !/Quick apply|Go to company site|On company site|Apply on company|On hirist/i.test(
            text
          )
        ) {
          return false;
        }
        // Exclude pure filter chrome even if it mentions Applied.
        if (/^Applied\b/i.test(text) && !/Quick apply|company site|hirist/i.test(text)) {
          return false;
        }
        return true;
      }
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
        /Quick apply|Go to company site|On company site|Apply on company|On hirist/i.test(
          l
        )
      );
      let role = "";
      let location = "";
      if (applyIdx >= 0) {
        role = lines[applyIdx + 1] || "";
        location = lines[applyIdx + 2] || "";
      }
      // Per-job already-applied is "Quick apply Applied" on the card CTA line only.
      const ctaLine = applyIdx >= 0 ? lines[applyIdx] : "";
      const companySite = siteRe.test(text);
      const quick = /Quick apply/i.test(text);
      return {
        idx,
        company,
        role,
        location,
        text: text.slice(0, 600),
        ctaLine,
        companySite,
        quick,
      };
    });
  });
  return raw.map((c) => {
    const already = isAlreadyAppliedCta(c.ctaLine || c.text);
    return {
      ...c,
      already,
      quick: c.quick && !already,
    };
  });
}

async function waitForDetailApplyReady(detailPage, { timeoutMs = 18000 } = {}) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    await detailPage.bringToFront().catch(() => {});
    const ready = await detailPage
      .evaluate(() =>
        [...document.querySelectorAll("button, a, [role='button']")].some((b) =>
          /Quick apply|Go to company site|On company site|Apply on company|On hirist|Applied/i.test(
            (b.innerText || b.getAttribute("aria-label") || "").replace(/\s+/g, " ")
          )
        )
      )
      .catch(() => false);
    if (ready) return true;
    await sleep(400);
  }
  return false;
}

function pruneStaleApplyTabs(context, keepPages = []) {
  const keep = new Set(keepPages.filter(Boolean));
  for (const p of context.pages()) {
    if (keep.has(p)) continue;
    const u = p.url() || "";
    if (
      /naukri\.com\/job-listings/i.test(u) ||
      /myworkdayjobs|myworkdaysite|greenhouse|lever\.co|smartrecruiters|successfactors|icims|ashbyhq/i.test(
        u
      )
    ) {
      safeClose(p);
    }
  }
}

async function openCard(context, page, idx) {
  // Click the same filtered job-card list as collectCards (never Applied (N) chips).
  pruneStaleApplyTabs(context, [page]);
  const beforeUrls = new Set(context.pages().map((p) => p.url()));
  const popupPromise = context
    .waitForEvent("page", { timeout: 8000 })
    .catch(() => null);
  const clicked = await page.evaluate((cardIdx) => {
    const isFilterChip = (text) =>
      /^Applied\s*\(\d+\)\s*$/i.test(String(text || "").replace(/\s+/g, " ").trim());
    const nodes = [...document.querySelectorAll("div.cursor-pointer")].filter((c) => {
      const text = (c.innerText || "").replace(/\s+/g, " ").trim();
      if (!text || text.length < 40) return false;
      if (isFilterChip(text)) return false;
      return /Quick apply|Go to company site|On company site|Apply on company|On hirist/i.test(
        text
      );
    });
    const el = nodes[cardIdx];
    if (!el) return false;
    el.scrollIntoView({ block: "center" });
    el.click();
    return true;
  }, idx);
  if (!clicked) throw new Error(`job card idx ${idx} not found`);
  let popup = await popupPromise;
  // Popup often starts as about:blank — wait for job-listings navigation.
  if (popup) {
    await popup
      .waitForURL(/naukri\.com\/job-listings/i, { timeout: 15000 })
      .catch(() => {});
    await popup.waitForLoadState("domcontentloaded").catch(() => {});
    await sleep(800);
  }
  let detailPage = page;
  if (popup && /naukri\.com\/job-listings/i.test(popup.url())) {
    detailPage = popup;
  } else {
    const fresh = context
      .pages()
      .find(
        (p) =>
          /naukri\.com\/job-listings/i.test(p.url()) && !beforeUrls.has(p.url())
      );
    if (fresh) detailPage = fresh;
  }
  await detailPage.bringToFront().catch(() => {});
  await waitForDetailApplyReady(detailPage, { timeoutMs: 18000 });
  await dismiss(detailPage);
  return detailPage;
}

async function readDetail(page) {
  const base = await page.evaluate(() => {
    const body = document.body.innerText || "";
    const panel =
      document.querySelector(
        "[class*='detail'], [class*='Detail'], aside, [role='dialog']"
      ) || document.body;
    const ptext = panel.innerText || body;
    const ctas = [...document.querySelectorAll("button, a, div[role='button']")]
      .map((e) =>
        (e.innerText || e.getAttribute("aria-label") || "")
          .replace(/\s+/g, " ")
          .trim()
      )
      .filter((t) => {
        if (!t || /^Applied\s*\(\d+\)\s*$/i.test(t)) return false; // filter chip
        return /Quick apply|Apply|Applied|Go to company site|On company site|Apply on company|On hirist/i.test(
          t
        );
      });
    const preferred =
      ctas.find((t) => /Go to company site/i.test(t)) ||
      ctas.find((t) =>
        /On company site|Apply on company(?:\s+site)?|On hirist/i.test(t)
      ) ||
      ctas.find((t) => /^Quick apply$/i.test(t)) ||
      ctas.find((t) => /Quick apply/i.test(t)) ||
      ctas.find((t) => /^Applied$/i.test(t)) ||
      ctas[0] ||
      "";
    const links = [...document.querySelectorAll("a[href]")]
      .map((a) => a.href)
      .filter((h) =>
        /myworkdayjobs|greenhouse|lever\.co|smartrecruiters|successfactors|icims|taleo|ashbyhq|phenom|oraclecloud|jobs\.|careers\.|hirist/i.test(
          h
        )
      )
      // Footer "Careers" on Naukri is InfoEdge — never treat as job ATS.
      .filter((h) => !/careers\.infoedge\.com|infoedge\.in/i.test(h));
    return {
      cta: preferred,
      links: [...new Set(links)].slice(0, 8),
      blob: ptext.slice(0, 4000),
      url: location.href,
    };
  });
  const visible = await readVisibleApplyCta(page).catch(() => null);
  if (visible && visible.state === "applied") {
    return { ...base, cta: "Applied", ctaState: "applied" };
  }
  if (visible && visible.state === "quick") {
    return { ...base, cta: "Quick apply", ctaState: "quick" };
  }
  return { ...base, ctaState: visible?.state || "unknown" };
}

async function waitForVisibleApplyCta(page, { timeoutMs = 10000 } = {}) {
  const start = Date.now();
  let last = null;
  while (Date.now() - start < timeoutMs) {
    last = await readVisibleApplyCta(page).catch(() => null);
    if (last && (last.state === "quick" || last.state === "applied")) return last;
    await sleep(400);
  }
  return last;
}

async function clickChatbotSave(page) {
  await page
    .evaluate(() => {
      const root =
        document.querySelector(
          ".chatbot_Drawer, ._chatBotContainer, #desktopChatBotContainer"
        ) || document;
      root.querySelector(".chatbot_Overlay")?.classList.remove("show");
      for (const el of root.querySelectorAll(
        ".send.disabled, .sendMsgbtn_container.disabled, .disabled"
      )) {
        el.classList.remove("disabled");
      }
      const sendWrap = root.querySelector(".send");
      sendWrap?.classList.remove("disabled");
      root.querySelector(".sendMsg")?.click();
      const save = [
        ...root.querySelectorAll(
          "div.sendMsg, div.send, div.sendMsgbtn_container, button"
        ),
      ].find((e) => /^Save$/i.test((e.innerText || "").trim()));
      save?.click();
    })
    .catch(() => {});
  // Playwright force-click — evaluate click often no-ops under TopTier overlay.
  for (const sel of [
    ".chatbot_Drawer .sendMsg",
    "._chatBotContainer .sendMsg",
    "#desktopChatBotContainer .sendMsg",
    ".chatbot_Drawer div.send:has-text('Save')",
    "div.sendMsgbtn_container",
    "button:has-text('Save')",
  ]) {
    const b = page.locator(sel).first();
    if (await b.isVisible().catch(() => false)) {
      await b.click({ force: true }).catch(() => {});
      break;
    }
  }
}

function chatSuccessReason(chatText) {
  const t = String(chatText || "");
  if (
    /successfully applied|application sent|has been submitted|thank you for applying|application has been submitted/i.test(
      t
    )
  ) {
    return "success";
  }
  if (
    /thank you for your responses/i.test(t) &&
    !/How many years|Are you|Do you|\?/i.test(
      t.split(/thank you for your responses/i)[1] || ""
    )
  ) {
    return "responses_thanks";
  }
  return null;
}

async function answerNaukriChatbot(page) {
  // Drawer can mount a beat after Quick apply — wait before declaring no_chat.
  {
    const start = Date.now();
    while (Date.now() - start < 8000) {
      const ready = await page
        .evaluate(() => {
          const el = document.querySelector(
            ".chatbot_Drawer, ._chatBotContainer, #desktopChatBotContainer"
          );
          const t = (el?.innerText || "").trim();
          return t.length >= 20;
        })
        .catch(() => false);
      if (ready) break;
      await sleep(350);
    }
  }

  let lastFingerprint = "";
  let stuckCount = 0;
  for (let step = 0; step < 24; step++) {
    await page.bringToFront().catch(() => {});
    const chatText = await page
      .evaluate(
        () =>
          document.querySelector(
            ".chatbot_Drawer, ._chatBotContainer, #desktopChatBotContainer"
          )?.innerText || ""
      )
      .catch(() => "");
    if (!chatText || chatText.length < 20) return { done: true, reason: "no_chat" };
    const doneReason = chatSuccessReason(chatText);
    if (doneReason === "success") return { done: true, reason: "success" };
    if (doneReason === "responses_thanks") {
      await clickChatbotSave(page);
      await sleep(1500);
      return { done: true, reason: "responses_thanks" };
    }

    const fingerprint = chatText.replace(/\s+/g, " ").trim().slice(-500);
    const picked = await page
      .evaluate(() => {
        const root =
          document.querySelector(
            ".chatbot_Drawer, ._chatBotContainer, #desktopChatBotContainer"
          ) || document;
        root.querySelector(".chatbot_Overlay")?.classList.remove("show");

        const scoreBand = (v) => {
          const s = String(v || "").trim();
          if (/^yes$/i.test(s)) return 10_000;
          if (/immediate|serving notice|available/i.test(s)) return 9_000;
          if (/hyderabad|secunderabad|remote|work from home|wfh|any location/i.test(s))
            return 8_000;
          if (/^no$/i.test(s)) return -1;
          const nums = (s.match(/\d+/g) || []).map(Number);
          if (!nums.length) return 0;
          const top = Math.max(...nums);
          if (/>|plus|\+/i.test(s)) return top + 50;
          return top;
        };
        const setChecked = (inp) => {
          if (!inp) return;
          const native = Object.getOwnPropertyDescriptor(
            HTMLInputElement.prototype,
            "checked"
          );
          native?.set?.call(inp, true);
          inp.dispatchEvent(new MouseEvent("click", { bubbles: true }));
          inp.dispatchEvent(new Event("input", { bubbles: true }));
          inp.dispatchEvent(new Event("change", { bubbles: true }));
          try {
            const lab = root.querySelector(
              `label[for="${CSS.escape(inp.id)}"]`
            );
            lab?.click();
          } catch (_) {}
          inp.closest(".ssrc__radio-btn-container")?.click();
        };

        const radios = [...root.querySelectorAll('input[type="radio"]')].filter(
          (r) => r.offsetParent !== null || r.getClientRects().length
        );
        if (radios.length) {
          const yes = radios.find((r) => /^yes$/i.test(r.value || r.id));
          const target =
            yes ||
            [...radios].sort(
              (a, b) => scoreBand(b.value || b.id) - scoreBand(a.value || a.id)
            )[0];
          setChecked(target);
          return target.value || target.id || "radio";
        }

        // Native <select> questions.
        const sel = [...root.querySelectorAll("select")].find(
          (s) => s.offsetParent !== null && s.options && s.options.length > 1
        );
        if (sel) {
          const opts = [...sel.options].filter((o) => o.value || o.text);
          const ranked = opts.sort(
            (a, b) => scoreBand(b.text || b.value) - scoreBand(a.text || a.value)
          );
          const best = ranked[0];
          if (best) {
            sel.value = best.value;
            sel.dispatchEvent(new Event("input", { bubbles: true }));
            sel.dispatchEvent(new Event("change", { bubbles: true }));
            return `select:${(best.text || best.value || "").trim()}`;
          }
        }

        // Free-text / contenteditable years questions.
        const box = root.querySelector(
          '.textArea[contenteditable="true"], [contenteditable="true"].textArea, div.textArea[contenteditable="true"], textarea:not([type="hidden"])'
        );
        if (box && box.offsetParent !== null) {
          const q = (root.innerText || "").slice(-400);
          let answer = "15";
          if (/relocat|hyderabad|willing|immediate|join/i.test(q)) answer = "Yes";
          else if (/ctc|salary|lpa|compensation|expected/i.test(q)) answer = "65";
          else if (/current.*ctc|current.*salary/i.test(q)) answer = "52";
          else if (/notice/i.test(q)) answer = "0";
          box.focus();
          if (box.tagName === "TEXTAREA" || box.tagName === "INPUT") {
            box.value = answer;
          } else {
            box.textContent = answer;
          }
          box.dispatchEvent(new InputEvent("input", { bubbles: true, data: answer }));
          box.dispatchEvent(new Event("change", { bubbles: true }));
          return `text:${answer}`;
        }

        const chips = [
          ...root.querySelectorAll(
            "label, button, [role='button'], div[class*='chip'], span[class*='chip'], span.ssrc__label, li[role='option']"
          ),
        ].filter((e) => {
          const t = (e.innerText || "").replace(/\s+/g, " ").trim();
          return (
            t &&
            t.length < 48 &&
            /^(Yes|No|Immediate|Serving notice|Available|>?\d+.*years|\d+\s*-\s*\d+\s*years|Hyderabad|Secunderabad|Remote|Work from home|WFH|Any location|15\+|Agree|Proceed)$/i.test(
              t
            )
          );
        });
        if (chips.length) {
          const ranked = [...chips].sort(
            (a, b) =>
              scoreBand((b.innerText || "").trim()) -
              scoreBand((a.innerText || "").trim())
          );
          ranked[0].click();
          return (ranked[0].innerText || "").trim();
        }

        // Last-resort: click an unchecked checkbox / agree.
        const agree = [...root.querySelectorAll('input[type="checkbox"]')].find(
          (c) => !c.checked && /agree|confirm|authorize|consent/i.test(
            (c.closest("label,div,li")?.innerText || c.id || "") + " " + (c.value || "")
          )
        );
        if (agree) {
          setChecked(agree);
          return "checkbox:agree";
        }
        return null;
      })
      .catch(() => null);

    if (fingerprint === lastFingerprint) stuckCount += 1;
    else stuckCount = 0;
    lastFingerprint = fingerprint;

    if (!picked) {
      // Nothing to pick — try Save once in case prior answer enabled it, then stop.
      await clickChatbotSave(page);
      await sleep(1800);
      const after = await page
        .evaluate(
          () =>
            document.querySelector(
              ".chatbot_Drawer, ._chatBotContainer, #desktopChatBotContainer"
            )?.innerText || ""
        )
        .catch(() => "");
      const late = chatSuccessReason(after);
      if (late) return { done: true, reason: late };
      break;
    }
    await sleep(400);
    await clickChatbotSave(page);
    await sleep(2200);
    if (stuckCount >= 3) {
      // Same drawer text after repeated answers — Save may be stuck; one more force Save then exit.
      await clickChatbotSave(page);
      await sleep(2000);
      break;
    }
  }
  // Final pass: drawer may already show thanks / applied after last Save.
  const finalText = await page
    .evaluate(
      () =>
        document.querySelector(
          ".chatbot_Drawer, ._chatBotContainer, #desktopChatBotContainer"
        )?.innerText || ""
    )
    .catch(() => "");
  const finalReason = chatSuccessReason(finalText);
  if (finalReason) {
    if (finalReason === "responses_thanks") {
      await clickChatbotSave(page);
      await sleep(1000);
    }
    return { done: true, reason: finalReason };
  }
  return { done: false, reason: "chat_steps_exhausted" };
}

async function fillApplyForm(page) {
  // TopTier recruiter chatbot (Yes/No + experience bands) — must answer to finish apply.
  const chat = await answerNaukriChatbot(page).catch(() => null);
  if (chat?.reason === "success" || chat?.reason === "responses_thanks") {
    await sleep(1000);
    return chat;
  }
  // Recruiter Yes/No questions (TopTier uses label[for=Yes]/No] chips).
  await page
    .evaluate(() => {
      const setChecked = (inp) => {
        if (!inp) return;
        const native = Object.getOwnPropertyDescriptor(
          HTMLInputElement.prototype,
          "checked"
        );
        native?.set?.call(inp, true);
        inp.dispatchEvent(new Event("click", { bubbles: true }));
        inp.dispatchEvent(new Event("input", { bubbles: true }));
        inp.dispatchEvent(new Event("change", { bubbles: true }));
      };
      const yes = document.querySelector('#Yes, input[value="Yes"]');
      setChecked(yes);
      document.querySelector('label[for="Yes"]')?.click();
    })
    .catch(() => {});
  await sleep(400);

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
    ".sendMsgbtn_container",
    ".sendMsg",
    "div.send:has-text('Save')",
    "button:has-text('Apply')",
  ]) {
    const b = page.locator(sel).first();
    if (await b.isVisible().catch(() => false)) {
      const t = ((await b.innerText().catch(() => "")) || "").trim();
      if (/Applied/i.test(t) && /Quick apply/i.test(t)) continue;
      if (/^Applied$/i.test(t)) break;
      await b.click({ force: true }).catch(() => {});
      await sleep(1500);
    }
  }
  // Fallback: click TopTier chat/save div by exact text.
  await page
    .evaluate(() => {
      const el = [...document.querySelectorAll("div.sendMsg, div.send, div.sendMsgbtn_container")]
        .find((e) => /^Save$/i.test((e.innerText || "").trim()));
      if (el) el.click();
    })
    .catch(() => {});
  await sleep(1200);
  return chat || { done: false, reason: "form_fill" };
}

async function clickQuickApply(page) {
  await page.bringToFront().catch(() => {});
  let visible = await waitForVisibleApplyCta(page, { timeoutMs: 12000 });
  if (visible?.state === "applied") {
    return { already: true, label: visible.label || "Applied" };
  }
  const selectors = [
    "button:has-text('Quick apply')",
    "button:has-text('Quick Apply')",
    "a:has-text('Quick apply')",
    "[role='button']:has-text('Quick apply')",
    "button:has-text('Apply')",
  ];
  let clicked = false;
  let label = visible?.label || "";
  for (const sel of selectors) {
    const btn = page.locator(sel).first();
    if (await btn.isVisible().catch(() => false)) {
      label = ((await btn.innerText().catch(() => "")) || "")
        .replace(/\s+/g, " ")
        .trim();
      if (/company site|on company/i.test(label)) continue;
      // Dual-layer buttons always include both words — click unless visible state is applied.
      if (/^Applied$/i.test(label) && !/Quick apply/i.test(label)) {
        return { already: true, label };
      }
      await btn.click({ force: true }).catch(() => {});
      clicked = true;
      break;
    }
  }
  // Evaluate fallback: Playwright text match can miss dual-layer / nested spans.
  if (!clicked) {
    const viaEval = await page
      .evaluate(() => {
        const layerOnScreen = (el) => {
          const st = window.getComputedStyle(el);
          if (
            st.display === "none" ||
            st.visibility === "hidden" ||
            Number(st.opacity) < 0.2
          ) {
            return false;
          }
          const r = el.getBoundingClientRect();
          if (r.width < 2 || r.height < 2) return false;
          let ty = 0;
          const m = /matrix\(([^)]+)\)/.exec(st.transform || "");
          if (m) {
            const parts = m[1].split(",").map((x) => Number(x.trim()));
            ty = parts[5] || 0;
          }
          if (Math.abs(ty) > Math.max(12, r.height * 0.35)) return false;
          return true;
        };
        const buttons = [
          ...document.querySelectorAll("button, a, [role='button']"),
        ];
        for (const btn of buttons) {
          const raw = (btn.innerText || btn.getAttribute("aria-label") || "")
            .replace(/\s+/g, " ")
            .trim();
          if (!/Quick apply/i.test(raw)) continue;
          if (/company site|hirist/i.test(raw)) continue;
          const overlays = [...btn.querySelectorAll("span")].filter((s) => {
            const st = window.getComputedStyle(s);
            return (
              st.position === "absolute" ||
              /absolute|inset-0/i.test(s.className || "")
            );
          });
          const pool = overlays.length ? overlays : [...btn.querySelectorAll("span")];
          const quickOn = pool.some(
            (s) =>
              /^Quick apply$/i.test((s.innerText || "").replace(/\s+/g, " ").trim()) &&
              layerOnScreen(s)
          );
          if (quickOn || /^Quick apply$/i.test(raw)) {
            btn.scrollIntoView({ block: "center" });
            btn.click();
            return raw || "Quick apply";
          }
        }
        return "";
      })
      .catch(() => "");
    if (viaEval) {
      clicked = true;
      label = viaEval;
    }
  }
  if (!clicked) return { clicked: false };
  await sleep(2500);
  await dismiss(page);
  const chat = await fillApplyForm(page);
  return {
    clicked: true,
    label: visible?.label || label || "Quick apply",
    chat,
  };
}

async function waitForAppliedCta(page, { timeoutMs = 12000 } = {}) {
  const start = Date.now();
  let last = null;
  while (Date.now() - start < timeoutMs) {
    await page.bringToFront().catch(() => {});
    last = await readVisibleApplyCta(page).catch(() => null);
    if (last?.state === "applied") return last;
    const toast = await page
      .evaluate(() => {
        const t = document.body.innerText || "";
        if (
          /applied successfully|application sent|successfully applied|thank you for your responses|thank you for applying/i.test(
            t
          )
        )
          return "toast";
        return "";
      })
      .catch(() => "");
    if (toast) return { state: "applied", label: toast, raw: toast };
    await sleep(400);
  }
  return last;
}

async function confirmApplied(page, chatHint = null) {
  if (
    chatHint?.reason === "success" ||
    chatHint?.reason === "responses_thanks"
  ) {
    // Chatbot completion often precedes CTA layer flip — count as applied.
    const visibleEarly = await waitForAppliedCta(page, { timeoutMs: 5000 });
    if (visibleEarly?.state === "applied") {
      return { ok: true, cta: "Applied" };
    }
    return { ok: true, cta: `chatbot:${chatHint.reason}` };
  }
  // Instant Quick Apply (no chatbot): CTA animates Quick→Applied. Do NOT
  // return early on "quick" — wait specifically for Applied / toast.
  // Also covers chat_steps_exhausted when Save eventually flipped CTA.
  const visible = await waitForAppliedCta(page, {
    timeoutMs: chatHint?.reason === "chat_steps_exhausted" ? 8000 : 12000,
  });
  if (visible?.state === "applied") {
    return { ok: true, cta: visible.label || "Applied" };
  }
  // Late chatbot thanks after exhausted loop / overlay lag.
  const lateChat = await page
    .evaluate(() => {
      const t =
        document.querySelector(
          ".chatbot_Drawer, ._chatBotContainer, #desktopChatBotContainer"
        )?.innerText ||
        document.body.innerText ||
        "";
      if (/thank you for your responses|successfully applied|application sent/i.test(t))
        return "late_thanks";
      return "";
    })
    .catch(() => "");
  if (lateChat) return { ok: true, cta: `chatbot:${lateChat}` };
  const detail = await readDetail(page);
  return { ok: false, cta: detail.cta || visible?.label || "" };
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
  const candidateLinks = preferAtsLinks(detail.links || []);
  let atsUrl = candidateLinks[0] || null;

  // Naukri "Go to company site" opens via window.open — hook to capture URL if popup is missed.
  await page
    .evaluate(() => {
      if (window.__naukriOpenHooked) return;
      window.__naukriOpenHooked = true;
      window.__naukriOpenedUrls = window.__naukriOpenedUrls || [];
      const orig = window.open;
      window.open = function (url, ...rest) {
        try {
          if (url) window.__naukriOpenedUrls.push(String(url));
        } catch (_) {}
        return orig.apply(this, [url, ...rest]);
      };
    })
    .catch(() => {});

  // Prefer "Go to company site" — "Apply on company site" is often disabled ("Apply attempted").
  const ctaSelectors = [
    "button:has-text('Go to company site')",
    "a:has-text('Go to company site')",
    "button:has-text('On company site'):not([disabled])",
    "a:has-text('On company site')",
    "button:has-text('Apply on company site'):not([disabled])",
    "button:has-text('Apply on company'):not([disabled])",
    "a:has-text('Apply on company site')",
    "a:has-text('Apply on company')",
  ];

  let newPage = null;
  const beforePages = new Set(context.pages());
  const beforeUrls = new Set(context.pages().map((p) => p.url()));

  for (const sel of ctaSelectors) {
    const cta = page.locator(sel).first();
    if (!(await cta.isVisible().catch(() => false))) continue;
    if (await cta.isDisabled().catch(() => false)) continue;

    const popupPromise = context
      .waitForEvent("page", { timeout: 12000 })
      .catch(() => null);
    await cta.click({ force: true }).catch(() => {});
    newPage = await popupPromise;
    await sleep(2500);

    if (!newPage) {
      // Prefer truly new Page objects, then new non-Naukri / ATS URLs.
      newPage =
        context.pages().find((p) => !beforePages.has(p)) ||
        context.pages().find((p) => {
          const u = p.url();
          return !beforeUrls.has(u) && isExternalAtsUrl(u);
        }) ||
        null;
    }

    if (newPage) break;

    const opened = await page
      .evaluate(() => window.__naukriOpenedUrls || [])
      .catch(() => []);
    if (opened && opened.length) {
      atsUrl =
        preferAtsLinks(opened)[0] ||
        opened.find((u) => isExternalAtsUrl(u)) ||
        opened[opened.length - 1] ||
        atsUrl;
      break;
    }
  }

  if (!newPage) {
    if (isExternalAtsUrl(page.url())) {
      newPage = page;
    } else if (atsUrl) {
      newPage = await context.newPage();
      await newPage
        .goto(atsUrl, { waitUntil: "domcontentloaded", timeout: 60000 })
        .catch(() => {});
    }
  }
  if (!newPage) {
    // Hirist "Apply on hirist.com Apply attempted" — soft-skip (owner Hirist login optional).
    const ctaBlob = String(detail.cta || jobMeta.cta || "");
    if (/hirist/i.test(ctaBlob)) {
      report.skipped.push({
        ...jobMeta,
        reason: "hirist_login_required_skip",
        path: "hirist",
        cta: detail.cta,
      });
      return;
    }
    report.blocked.push({
      ...jobMeta,
      reason: "external_link_not_opened",
      path: "company_ATS",
      cta: detail.cta,
    });
    return;
  }

  // InfoEdge marketing false-link — fail fast; try alternate real ATS URLs.
  if (isJunkAtsUrl(newPage.url())) {
    let rescued = false;
    for (const alt of candidateLinks) {
      if (isJunkAtsUrl(alt)) continue;
      await newPage
        .goto(alt, { waitUntil: "domcontentloaded", timeout: 60000 })
        .catch(() => {});
      await sleep(1500);
      if (!isJunkAtsUrl(newPage.url())) {
        rescued = true;
        break;
      }
    }
    if (!rescued) {
      report.blocked.push({
        ...jobMeta,
        reason: "infoedge_false_link",
        url: newPage.url(),
        path: "company_ATS",
      });
      if (newPage !== page) safeClose(newPage);
      return;
    }
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
      if (newPage !== page) safeClose(newPage);
      return;
    }
  }

  // Workday dedicated flow (Apply → Autofill/Manual → account → steps)
  // Also catch branded hosts that redirect into Workday Candidate Home UI.
  const looksWorkdayUrl = /myworkdayjobs\.com|myworkdaysite\.com|workdayjobs/i.test(
    newPage.url()
  );
  const looksWorkdayUi = await newPage
    .evaluate(() =>
      /Autofill with Resume|Apply Manually|data-automation-id/i.test(
        document.body?.innerText || ""
      ) || !!document.querySelector("[data-automation-id]")
    )
    .catch(() => false);
  if (looksWorkdayUrl || looksWorkdayUi) {
    const wd = await completeWorkdayApply(newPage, RESUME, {
      maxMs: Math.max(60_000, MAX_WORKDAY_MS - (Date.now() - start)),
    });
    if (wd.ok) {
      report.external.push({
        ...jobMeta,
        path: "company_ATS",
        atsUrl: wd.url || newPage.url(),
        resume: RESUME,
        confirmed: true,
      });
      report.applied.push({
        ...jobMeta,
        path: "company_ATS",
        atsUrl: wd.url || newPage.url(),
        resume: RESUME,
      });
    } else {
      report.blocked.push({
        ...jobMeta,
        reason: wd.reason || "external_incomplete_or_timeout",
        url: wd.url || newPage.url(),
        path: "company_ATS",
      });
    }
    if (newPage !== page) safeClose(newPage);
    return;
  }

  while (Date.now() - start < MAX_EXTERNAL_MS) {
    const url = newPage.url();
    if (isJunkAtsUrl(url)) {
      report.blocked.push({
        ...jobMeta,
        reason: "infoedge_false_link",
        url,
        path: "company_ATS",
      });
      if (newPage !== page) safeClose(newPage);
      return;
    }
    const text = await newPage
      .evaluate(() => (document.body?.innerText || "").slice(0, 2500))
      .catch(() => "");
    const hasRecaptcha =
      /captcha|verify you are human|cloudflare|hcaptcha|datadome/i.test(text) ||
      (await newPage.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha'], .g-recaptcha, #g-recaptcha-response").count()) >
        0;
    if (hasRecaptcha) {
      report.blocked.push({
        ...jobMeta,
        reason: "captcha_wall",
        url,
        path: "company_ATS",
      });
      if (newPage !== page) safeClose(newPage);
      return;
    }

    // Real auth wall = password field / create-account step — NOT header "Sign In".
    const hasPassword = (await newPage.locator("input[type='password']").count()) > 0;
    const hasApplyCta = await newPage
      .locator(
        "a[data-automation-id='adventureButton'], button:has-text('Apply'), a:has-text('Apply'), text=/Autofill with Resume|Apply Manually|Submit application/i"
      )
      .first()
      .isVisible()
      .catch(() => false);
    if (hasPassword && !hasApplyCta && !/thank you for appl|application submitted/i.test(text)) {
      if (/hirist/i.test(url + text)) {
        report.skipped.push({
          ...jobMeta,
          reason: "hirist_login_required_skip",
          url,
          path: "hirist",
        });
        if (newPage !== page) safeClose(newPage);
        return;
      }
      // Accenture / Azure B2C and similar SSO walls — do not burn the full external budget.
      if (
        /b2clogin\.com|login\.microsoftonline\.com|accounts\.google\.com|okta\.com|auth0\.com/i.test(
          url
        )
      ) {
        report.blocked.push({
          ...jobMeta,
          reason: "ats_login_wall",
          url,
          path: "company_ATS",
        });
        if (newPage !== page) safeClose(newPage);
        return;
      }
      const guest = newPage
        .locator("text=/Continue as guest|Apply without|Don't have an account/i")
        .first();
      if (await guest.isVisible().catch(() => false)) {
        await guest.click().catch(() => {});
        await sleep(1000);
      } else {
        report.blocked.push({
          ...jobMeta,
          reason: "ats_login_wall",
          url,
          path: "company_ATS",
        });
        if (newPage !== page) safeClose(newPage);
        return;
      }
    }

    // Prefer clicking Apply before declaring defeat on careers pages
    for (const sel of [
      "a:has-text('Apply for this job')",
      "button:has-text('Apply for this job')",
      "a:has-text('Apply')",
      "button:has-text('Apply')",
      "button:has-text('Apply Now')",
    ]) {
      const b = newPage.locator(sel).first();
      if (await b.isVisible().catch(() => false)) {
        const label = ((await b.innerText().catch(() => "")) || "").trim();
        if (/Applied|Sign In|Log In/i.test(label) && !/^Apply/i.test(label)) continue;
        await b.click().catch(() => {});
        await sleep(2000);
        break;
      }
    }

    if (RESUME) {
      const files = newPage.locator("input[type='file']");
      const nFiles = await files.count();
      for (let fi = 0; fi < Math.min(nFiles, 3); fi++) {
        await files.nth(fi).setInputFiles(RESUME).catch(() => {});
      }
      if (nFiles) await sleep(1200);
    }

    // Greenhouse / Infor / generic ATS named fields
    for (const [sel, val] of [
      [
        "input[name='first_name'], #first_name, input[name*='first_name'], input[placeholder='First name' i]",
        "Mohammed Abdul Rafi",
      ],
      [
        "input[name='last_name'], #last_name, input[name*='last_name'], input[placeholder='Last name' i]",
        "Ahmed",
      ],
      [
        "input[name='email'], #email, input[type='email'], input[name*='[email]']",
        "rafi.success@gmail.com",
      ],
      [
        "input[name='phone'], #phone, input[type='tel'], input[name*='[phone]']",
        "8790251698",
      ],
      ["#address1, input[name*='[address1]']", "Hyderabad"],
      ["#town, input[name*='[town]']", "Hyderabad"],
      ["#postcode, input[name*='[postcode]']", "500032"],
    ]) {
      const el = newPage.locator(sel).first();
      if (await el.isVisible().catch(() => false)) {
        await el.fill(val).catch(() => {});
      }
    }
    // Infor / Phenom-style Yes/No radios + acknowledgement.
    for (const [qRe, yes] of [
      [/at least 18/i, true],
      [/legally authorised|legally authorized|authorised to work|authorized to work/i, true],
      [/relatives who are currently employed/i, false],
      [/non-compete|previously worked for/i, false],
    ]) {
      const block = newPage.locator("fieldset, div, li, section").filter({ hasText: qRe }).first();
      if (!(await block.isVisible().catch(() => false))) continue;
      const choice = block
        .locator(yes ? "label:has-text('Yes'), input[value='true']" : "label:has-text('No'), input[value='false']")
        .first();
      await choice.click({ force: true }).catch(() => {});
    }
    const ack = newPage.locator("select").filter({ hasText: /I confirm/i }).first();
    if (await ack.count().catch(() => 0)) {
      await ack.selectOption({ label: "I confirm" }).catch(() => {});
    }
    const ackText = newPage
      .locator("#application_form_application_answers_attributes_5_text_answer, input[aria-label*='Acknowledgement' i]")
      .first();
    if (await ackText.isVisible().catch(() => false)) {
      await ackText.fill("I confirm").catch(() => {});
    }
    const countrySel = newPage.locator("select[aria-label='Country'], select#application_form\\[application\\]\\[country\\]").first();
    if (await countrySel.isVisible().catch(() => false)) {
      await countrySel.selectOption({ label: "India" }).catch(() => {});
    }

    // Greenhouse / SmartRecruiters / generic boards — required comboboxes & selects.
    if (
      /greenhouse\.io|job-boards\.greenhouse|smartrecruiters\.com|lever\.co|ashbyhq\.com/i.test(
        newPage.url()
      )
    ) {
      await fillCommonAtsQuestions(newPage).catch(() => {});
    }

    // SmartRecruiters often needs an explicit "Submit" after consent checkbox.
    if (/smartrecruiters\.com/i.test(newPage.url())) {
      const consent = newPage
        .locator(
          "input[type='checkbox'], [role='checkbox']"
        )
        .first();
      if (await consent.isVisible().catch(() => false)) {
        await consent.check({ force: true }).catch(() => {});
        await consent.click({ force: true }).catch(() => {});
      }
    }

    await newPage
      .evaluate(
        ({ cur, exp }) => {
          const setVal = (inp, val) => {
            inp.focus();
            inp.value = String(val);
            inp.dispatchEvent(new Event("input", { bubbles: true }));
            inp.dispatchEvent(new Event("change", { bubbles: true }));
          };
          const inputs = [
            ...document.querySelectorAll("input, textarea, select"),
          ];
          for (const inp of inputs) {
            if (inp.offsetParent === null && inp.type !== "file") continue;
            if (inp.type === "password" || inp.type === "hidden") continue;
            const ctx = (
              (inp.getAttribute("placeholder") || "") +
              " " +
              (inp.getAttribute("name") || "") +
              " " +
              (inp.getAttribute("aria-label") || "") +
              " " +
              (inp.id || "") +
              " " +
              (inp.closest("label,div,fieldset,li")?.innerText || "")
            ).slice(0, 240);
            if (
              /expected/i.test(ctx) &&
              /ctc|salary|compensation|lpa|pay/i.test(ctx)
            ) {
              if (inp.tagName === "SELECT") continue;
              setVal(inp, exp * 100000);
            } else if (
              /current/i.test(ctx) &&
              /ctc|salary|compensation|lpa|pay/i.test(ctx)
            ) {
              if (inp.tagName === "SELECT") continue;
              setVal(inp, cur * 100000);
            } else if (/email/i.test(ctx) && !inp.value) {
              setVal(inp, "rafi.success@gmail.com");
            } else if (/phone|mobile/i.test(ctx) && !inp.value) {
              setVal(inp, "8790251698");
            } else if (/first[_ ]?name/i.test(ctx) && !inp.value) {
              setVal(inp, "Mohammed Abdul Rafi");
            } else if (/last[_ ]?name/i.test(ctx) && !inp.value) {
              setVal(inp, "Ahmed");
            } else if (/location|city|hyderabad/i.test(ctx) && !inp.value) {
              setVal(inp, "Hyderabad");
            }
          }
        },
        { cur: CURRENT_CTC_LPA, exp: EXPECTED_CTC_LPA }
      )
      .catch(() => {});

    for (const sel of [
      "button:has-text('Submit application')",
      "button:has-text('Submit Application')",
      "input[type='submit'][value*='Submit' i]",
      "button:has-text('Submit')",
      "button:has-text('Apply')",
      "input[type='submit']",
    ]) {
      const b = newPage.locator(sel).first();
      if (await b.isVisible().catch(() => false)) {
        const label = ((await b.innerText().catch(() => "")) || "").trim();
        if (/sign in|log in|create account/i.test(label)) continue;
        await b.click({ force: true }).catch(() => {});
        await sleep(2500);
      }
    }

    const after = await newPage
      .evaluate(() => (document.body?.innerText || "").slice(0, 2500))
      .catch(() => "");
    if (isSubmittedText(after)) {
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
      if (newPage !== page) safeClose(newPage);
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
    await sleep(1500);
    break;
  }

  report.blocked.push({
    ...jobMeta,
    reason: "external_incomplete_or_timeout",
    url: newPage.url(),
    path: "company_ATS",
  });
  if (newPage !== page) safeClose(newPage);
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
  const seniorTitle =
    isArchLeadTitle(role) ||
    /\b(lead|manager|architect|principal|staff|director)\b/i.test(role);
  if (!seniorTitle && !isArchLeadTitle(blob)) {
    return "skip_seniority";
  }
  // Architect / Tech Lead / EM / Principal / Staff / Senior Manager: allow without
  // .NET on the card snippet (JD often buries it). Still require .NET for weaker titles.
  if (!hasDotNet(role, blob) && !isArchLeadTitle(role)) return "skip_no_dotnet";
  if (locationShouldSkip(loc, blob)) return "skip_location";
  const maxCtc = parseMaxCtcLpa(blob);
  if (maxCtc !== null && maxCtc < MIN_LISTED_MAX_CTC_LPA)
    return `skip_ctc_max_${maxCtc}`;
  return null;
}

async function processCard(context, page, card, i, jobMeta, report) {
  const detailPage = await openCard(context, page, card.idx != null ? card.idx : i);
  const openedTab = detailPage !== page;
  await detailPage.bringToFront().catch(() => {});
  // Detail CTA layers can mount late — wait before already/missing decisions.
  await waitForVisibleApplyCta(detailPage, { timeoutMs: 12000 });
  let detail = await readDetail(detailPage);
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
      safeClose(detailPage);
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
  const detailApplied =
    detail.ctaState === "applied" ||
    (detail.ctaState !== "quick" &&
      detail.ctaState !== "unknown" &&
      detail.ctaState !== "missing" &&
      isAlreadyAppliedCta(detail.cta));
  if (detailApplied) {
    report.skipped.push({
      ...jobMeta,
      reason: "already_applied_detail",
      naukriJobUrl: detail.url,
      cta: detail.cta,
      ctaState: detail.ctaState,
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

  if (card.companySite || isCompanySiteCta(detail.cta)) {
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
    // One more CTA poll — slow TopTier detail tabs.
    detail = await readDetail(detailPage);
    if (card.companySite || isCompanySiteCta(detail.cta)) {
      await handleExternal(context, detailPage, detail, jobMeta, report);
      await page.bringToFront().catch(() => {});
      await closeDetail();
      return;
    }
    report.blocked.push({
      ...jobMeta,
      reason: "quick_apply_not_found",
      path: "Naukri",
      naukriJobUrl: detail.url,
      cta: detail.cta,
      ctaState: detail.ctaState,
    });
    await closeDetail();
    return;
  }
  await sleep(2000);
  const conf = await confirmApplied(detailPage, click.chat);
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
      chat: click.chat || null,
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
      const candidates = artifactPaths("naukri-profile-resume.json");
      let raw = null;
      for (const p of candidates) {
        try {
          if (fs.existsSync(p)) {
            raw = fs.readFileSync(p, "utf8");
            break;
          }
        } catch (_) {}
      }
      report.profileResumeRefresh = JSON.parse(raw);
    } catch (_) {}
  }

  const { chromium } = require("playwright-core");
  const browser = await chromium.connectOverCDP(CDP);
  const context = browser.contexts()[0];
  const page = await context.newPage();
  page.setDefaultTimeout(45000);

  const seen = new Set();

  async function runSearchPass(ages, passLabel, queries = QUERIES) {
    for (const age of ages) {
      if (report.applied.length >= MAX_APPLIES) break;
      for (const q of queries) {
        if (report.applied.length >= MAX_APPLIES) break;
        for (const loc of searchUrls(q, age)) {
          if (report.applied.length >= MAX_APPLIES) break;
          const url = loc.url;
          report.queriesRun.push({
            q,
            age,
            loc: loc.label,
            url,
            pass: passLabel,
          });
          await page
            .goto(url, { waitUntil: "domcontentloaded", timeout: 90000 })
            .catch(() => {});
          await sleep(2200);
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

            if (allowlistActive() && !companyAllowed(card.company)) {
              report.skipped.push({
                company: card.company,
                role: card.role,
                location: card.location,
                reason: "hitechcity_campus_allowlist",
                query: q,
                age,
                loc: loc.label,
              });
              continue;
            }

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
  }

  try {
    // Freshest age first; early-expand when still thin after age-1.
    const primaryAges = [...JOB_AGES];
    const firstAge = primaryAges.length ? [primaryAges[0]] : [1];
    const restAges = primaryAges.slice(1);
    await runSearchPass(firstAge, "primary-fresh");

    if (
      report.applied.length < EARLY_EXPAND_BELOW &&
      restAges.length &&
      report.applied.length < MAX_APPLIES
    ) {
      console.log(
        `Early age expand (applied=${report.applied.length} < ${EARLY_EXPAND_BELOW}):`,
        restAges.join(",")
      );
      report.earlyExpandedAges = restAges;
      await runSearchPass(restAges, "primary-early-rest");
    } else if (restAges.length) {
      await runSearchPass(restAges, "primary");
    }

    // Auto-expand older inventory in the same run when fresh ages are thin.
    if (
      report.applied.length < EXPAND_BELOW &&
      AUTO_EXPAND_AGES.length &&
      !JOB_AGES.some((a) => AUTO_EXPAND_AGES.includes(a))
    ) {
      const expand = AUTO_EXPAND_AGES.filter((a) => !JOB_AGES.includes(a));
      if (expand.length) {
        report.expandedAges = expand;
        console.log("Expanding job ages:", expand.join(","));
        await runSearchPass(expand, "expand");
      }
    }

    // Extra query wave when still thin after age expands
    if (report.applied.length < EXPAND_BELOW && EXTRA_QUERIES.length) {
      const agesForExtra =
        report.expandedAges && report.expandedAges.length
          ? [...new Set([...JOB_AGES, ...report.expandedAges])]
          : JOB_AGES;
      console.log(
        `Extra queries (applied=${report.applied.length} < ${EXPAND_BELOW}):`,
        EXTRA_QUERIES.join(" | ")
      );
      report.extraQueries = EXTRA_QUERIES;
      await runSearchPass(agesForExtra, "extra-queries", EXTRA_QUERIES);
    }

    // Recommended + homepage inventory pass when search burst is thin
    if (report.applied.length < EXPAND_BELOW) {
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
        for (let i = 0; i < Math.min(cards.length, 50); i++) {
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
    const written = writeArtifactJson("naukri-daily-apply.json", report);
    if (process.env.NAUKRI_APPLY_REPORT) {
      fs.mkdirSync(path.dirname(REPORT), { recursive: true });
      fs.writeFileSync(REPORT, JSON.stringify(report, null, 2));
      written.push(REPORT);
    }
    console.log(
      JSON.stringify(
        {
          counts: report.counts,
          applied: report.applied,
          blocked: report.blocked,
          skippedSample: report.skipped.slice(0, 40),
          reportPaths: [...new Set(written)],
        },
        null,
        2
      )
    );
    // Avoid awaiting page.close() — CDP close can hang on TopTier tabs.
    safeClose(page);
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
