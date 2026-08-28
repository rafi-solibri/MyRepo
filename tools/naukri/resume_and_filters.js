#!/usr/bin/env node
/**
 * Naukri helpers: resume path + login check patterns for TopTier UI.
 * Prefer cards as div.cursor-pointer; Quick Apply opens a popup.
 * Success = detail CTA shows Applied (sidebar Applied count is a filter chip, not status).
 */
"use strict";

const fs = require("fs");

const path = require("path");
const RESUME_CANDIDATES = [
  path.join(__dirname, "..", "..", "resumes", "Rafi_Resume.docx"),
  "/workspace/resumes/Rafi_Resume.docx",
  "/home/ubuntu/resumes/Rafi_Resume.docx",
  "/home/ubuntu/Documents/Rafi_Resume.docx",
  path.join(__dirname, "..", "..", "resumes", "Rafi_Resume_Architect.docx"),
  "/workspace/resumes/Rafi_Resume_Architect.docx",
];

function findResume() {
  for (const p of RESUME_CANDIDATES) {
    try {
      if (fs.existsSync(p) && fs.statSync(p).size > 1000) return p;
    } catch (_) {}
  }
  return null;
}

/**
 * Hard skip keywords (Coupa/Pega etc. - Mondelez false-apply fix).
 * Do NOT match bare "QA" — page chrome / "Software & QA" sidebars false-skip SA roles.
 * Only skip when title itself is a QA/SDET role.
 */
const SKIP_TITLE_RE =
  /\b(qa engineer|quality assurance|quality engineer|quality engineering|quality architect|quality solution architect|\bqe architect\b|sdet|tosca|test automation architect|embedded\b|firmware|intern(?!et)|fresher|salesforce|agentforce|servicenow|coupa|pega|lead system architect|\blsa\b|appian|anaplan|celonis|power platform|guidewire|sap\b|dynamics|\bd365\b|workday hms|revit|\bbarch\b|hubspot|\bsre\b|site reliability|devops engineer|devops lead|devops architect|platform sre|network operations|network ops|network support|network cisco|cisco\s+meraki|\bmeraki\b|sd-?\s*wan|l2\s*\/\s*l3|civil\b|structural|substation|attack surface|cyber\s*security|cybersecurity|cyber architecture|infosec|penetration|red team|soc analyst|security operations|threat hunter|\bmdr\b|\bedr\b|security\s+engineer|security\s+architecture|observability|\bdatadog\b|infrastructure engineer|analog\s*ic|\bvlsi\b|digital verification|\basic\b|\bfpga\b|mulesoft|mule\s*soft|ms\s*fabric|microsoft\s*fabric|\bsynapse\b|\bdatabricks\b|datalake|data\s*lake|\bnetcool\b|big\s*data|bigdata|oracle\s+epm|\bepm\b|\bpbcs\b|\bepbcs\b|sharepoint|\btableau\b|\bcopilot\s+architect\b|ms\s+copilot|\bui\s+architect\b)\b/i;

/**
 * Employer names that are Coupa/Pega/Salesforce/SAP-primary even when the
 * card title omits the stack keyword (recommended/homepage inventory).
 */
const SKIP_COMPANY_RE =
  /\b(pega(?:systems)?|coupa|salesforce|sap(?:\s*labs)?|cadence)\b/i;

/** Pure AI/data titles need .NET|C# on the TITLE (skills laundry lists are noisy). */
const PURE_AI_DATA_RE =
  /\b(ai\s+architect|artificial\s+intelligence\s+architect|ai\s+agent|ai\s+engineer(?:ing)?(?:\s+manager|\s+lead)?|ai\s+engineering\s+manager|ai\s+solution\s+architect|full\s*stack\s+ai\s+manager|ai\s+manager|architect[^.\n]{0,48}\b(ai|ml)\b|data\s*(?:&|and)\s*ai|ml\s+engineer|gen\s*-?\s*ai|genai|agentic\s+ai|\bgemini\b|\bllm\b|enterprise\s+platform\s+architect[^.\n]{0,24}\b(ai|ml|gemini|llm)\b|data\s+scientist|data\s+engineer|data\s+engineering|data\s+architect|gcp\s+infra(?:structure)?(?:\s+architect)?)\b/i;

/**
 * Primary non-.NET stacks in the TITLE — skip to avoid Java/MEAN ATS dead-ends.
 * Do not use on full JD blobs (skills lists are noisy).
 */
const NON_DOTNET_PRIMARY_RE =
  /\b(java|j2ee|spring boot|golang|go lang|python|node\.?js|mean\b|mern\b|ruby on rails|php|oracle apps|oracle fusion|oracle\s+dba|oracle cloud|oracle\s+epm|abap|mainframe|cobol|\bas400\b|ibm\s*i)\b/i;

/** When scanning detail pages, use job panel text only — never document.body. */
function shouldSkipTitleFromDetail(detailText) {
  const t = String(detailText || "");
  // Prefer first heading-sized chunk if agent passes full panel.
  return shouldSkipTitle(t.slice(0, 400));
}

/**
 * Generic Architect/Lead titles whose JD/skills panel is clearly AI/ML or
 * Java/Python-primary (no .NET|C#) — e.g. Globallogic "Senior Architect"
 * with Tensorflow/Pytorch/Java laundry list (false-apply 2026-08-23).
 * Only for detail blobs; never run on short card snippets.
 */
function shouldSkipNonDotNetPrimaryJd(role, detailText) {
  const title = String(role || "").trim();
  const blob = String(detailText || "");
  if (!title || blob.length < 280) return false;
  if (hasDotNet(title, "")) return false;
  if (!isArchLeadTitle(title)) return false;
  // Title already caught by PURE_AI_DATA / NON_DOTNET_PRIMARY — no need.
  if (shouldSkipTitle(title)) return false;
  const head = blob.slice(0, 2200);
  if (hasDotNet("", head)) return false;
  const low = head.toLowerCase();
  const aiHits = (
    low.match(
      /\b(tensorflow|pytorch|deep learning|machine learning|\bml\b|gen\s*-?\s*ai|genai|agentic|llm|artificial intelligence|large language)\b/g
    ) || []
  ).length;
  const javaPyHits = (
    low.match(/\b(java|spring boot|python|node\.?js|mean\b|mern\b)\b/g) || []
  ).length;
  // Multiple AI/ML signals in skills/overview → not a .NET arch role.
  if (aiHits >= 2) return true;
  if (aiHits >= 1 && javaPyHits >= 2) return true;
  return false;
}

const DOTNET_RE = /(\.net|dotnet|asp\.?\s*net|c#|csharp)/i;

/** Architect / Lead / EM / Principal / Staff / Director — apply even if card omits .NET. */
const ARCH_LEAD_RE =
  /\b(architect(?:ure|ing)?|technical lead|tech lead|technology lead|engineering manager|engineering lead|engineer manager|software engineer manager|principal|staff|director|avp|head of|chief technology|solution architect(?:ure|ing)?|cloud architect(?:ure|ing)?|azure architect(?:ure|ing)?|\.net lead|dotnet lead|lead (software|development|developer|engineer|fullstack|full[\s-]?stack)|(software|development|developer|fullstack|full[\s-]?stack)\s+lead|software\s+(engineering\s+|development\s+)?manager|development manager|senior manager|manager\b[^.\n]{0,32}\b(sw|software|engineering|technology|platform|development)|senior engineering)\b/i;

/** TopTier search cards: CTA then role. Homepage cards: role then location then CTA last. */
const CARD_CTA_RE =
  /Quick apply|Go to company site|On company site|Apply on company|On hirist/i;
const CARD_LOCATION_RE =
  /\b(remote|hybrid|wfh|work from home|hyderabad|secunderabad|telangana|bengaluru|bangalore|pune|chennai|mumbai|delhi|noida|gurgaon|gurugram|india)\b/i;
const CARD_META_RE =
  /^(?:\d+\.\d+|posted by\b|.*\bemployees\b|\d+\+?d ago\b|quick apply|not disclosed|₹|.*\bl\/year\b|.*\blpa\b|\d+\s*-\s*\d+\s*yrs)/i;

function isCardLocationLine(l) {
  const t = String(l || "").trim();
  if (!t || t.length >= 140 || CARD_CTA_RE.test(t)) return false;
  if (/^(hybrid\s*-?\s*)?(remote|wfh|work from home)\b/i.test(t)) return true;
  if (
    /^(hybrid\s*-)?\s*(hyderabad|secunderabad|bengaluru|bangalore|pune|chennai|mumbai|delhi|noida|gurgaon|gurugram)\b/i.test(
      t
    )
  ) {
    return true;
  }
  if (
    CARD_LOCATION_RE.test(t) &&
    !/\b(architect|engineer|manager|lead|developer|consultant|director|principal|staff)\b/i.test(
      t
    )
  ) {
    return true;
  }
  return false;
}

/**
 * Parse company / role / location from Naukri card lines.
 * Never treat company name or skills laundry as the job title.
 */
function parseNaukriCardLines(lines) {
  const ls = (lines || [])
    .map((x) => String(x || "").trim())
    .filter(Boolean);
  const company = ls[0] || "";
  let role = "";
  let location = "";
  const locIdx = ls.findIndex((l, i) => i > 0 && isCardLocationLine(l));
  if (locIdx > 0) {
    location = ls[locIdx];
    for (let i = locIdx - 1; i >= 1; i--) {
      if (CARD_CTA_RE.test(ls[i]) || CARD_META_RE.test(ls[i])) continue;
      role = ls[i];
      break;
    }
  }
  if (!role) {
    const applyIdx = ls.findIndex((l) => CARD_CTA_RE.test(l));
    if (applyIdx >= 0 && ls[applyIdx + 1] && !CARD_META_RE.test(ls[applyIdx + 1])) {
      role = ls[applyIdx + 1];
      if (!location) location = ls[applyIdx + 2] || "";
    } else if (applyIdx > 1) {
      for (let i = applyIdx - 1; i >= 1; i--) {
        if (CARD_META_RE.test(ls[i]) || isCardLocationLine(ls[i])) continue;
        if (CARD_CTA_RE.test(ls[i])) continue;
        role = ls[i];
        break;
      }
    }
  }
  return { company, role, location };
}

/** Title skip from the job title only — never company name / card chrome / skills. */
function shouldSkipTitleFromCard(role, cardText) {
  const r = String(role || "").trim();
  if (r) return shouldSkipTitle(r);
  const recovered = parseNaukriCardLines(String(cardText || "").split("\n")).role;
  if (recovered) return shouldSkipTitle(recovered);
  return false;
}

function normalizeAspNet(text) {
  return String(text || "").replace(/asp\.?\s*net/gi, "DOTNET");
}

function hasDotNet(title, skills) {
  const blob = normalizeAspNet(`${title || ""} ${skills || ""}`);
  return DOTNET_RE.test(blob);
}

function isArchLeadTitle(title) {
  const t = String(title || "").trim();
  if (ARCH_LEAD_RE.test(t)) return true;
  // Bare "CTO" only — do not match product strings like "Specialist CTO AI Ready".
  return /^cto\b/i.test(t);
}

function shouldSkipTitle(title) {
  const t = title || "";
  if (SKIP_TITLE_RE.test(t)) return true;
  // AI Architect without .NET on the title itself (Instahyre/Foundit parity)
  if (PURE_AI_DATA_RE.test(t) && !hasDotNet(t, "")) return true;
  // Java/MEAN/Python-primary titles without .NET|C# — do not burn ATS time
  if (NON_DOTNET_PRIMARY_RE.test(t) && !hasDotNet(t, "")) return true;
  // IC/EDA "Principal Design Engineer" (Cadence etc.) — not software/.NET SA
  if (
    /\bdesign\s+engineer\b/i.test(t) &&
    !/\bsoftware\b/i.test(t) &&
    !hasDotNet(t, "")
  ) {
    return true;
  }
  return false;
}

/** Skip Coupa/Pega/Salesforce/SAP employers even when title omits stack keyword. */
/** Recover the listing title from a Naukri job-listings URL slug. */
function titleFromNaukriJobUrl(url) {
  const m = String(url || "").match(/\/job-listings-([^/?#]+)/i);
  if (!m) return "";
  let slug = m[1];
  try {
    slug = decodeURIComponent(slug);
  } catch (_) {}
  return slug
    .replace(/-/g, " ")
    .replace(/\s+\d+\s+to\s+\d+\s+years.*$/i, "")
    .trim();
}

function shouldSkipCompany(company) {
  const c = String(company || "").trim();
  if (!c) return false;
  return SKIP_COMPANY_RE.test(c);
}

module.exports = {
  findResume,
  hasDotNet,
  shouldSkipTitle,
  shouldSkipTitleFromDetail,
  shouldSkipTitleFromCard,
  shouldSkipNonDotNetPrimaryJd,
  shouldSkipCompany,
  parseNaukriCardLines,
  isArchLeadTitle,
  titleFromNaukriJobUrl,
  normalizeAspNet,
  ARCH_LEAD_RE,
  CARD_CTA_RE,
  SKIP_COMPANY_RE,
  RESUME_CANDIDATES,
  EXPECTED_CTC_LPA: 65,
  CURRENT_CTC_LPA: 52,
  CHROME_PROFILE: process.env.NAUKRI_CHROME_PROFILE || "/home/ubuntu/.naukri-chrome-profile",
  PROFILE_URL: process.env.NAUKRI_PROFILE_URL || "https://www.naukri.com/mnjuser/profile",
  RESUME_HEADLINE:
    "Solutions Architect & Technical Lead - 15+ Yrs - .NET Core, Microservices, AWS&Azure, Kafka&RabbitMQ",
};

if (require.main === module) {
  console.log(JSON.stringify({ resume: findResume() }, null, 2));
}
