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
  /\b(qa engineer|quality assurance|quality engineer|quality engineering|quality architect|quality solution architect|\bqe architect\b|sdet|tosca|test automation architect|embedded\b|firmware|intern(?!et)|fresher|salesforce|agentforce|servicenow|coupa|pega|appian|anaplan|celonis|power platform|guidewire|sap\b|dynamics|workday hms|revit|\bbarch\b|hubspot|\bsre\b|site reliability|devops engineer|devops lead|platform sre|network operations|network ops|network support|civil\b|structural|substation|attack surface|cyber\s*security|cybersecurity|infosec|penetration|red team|soc analyst|security operations|threat hunter|\bmdr\b|\bedr\b)\b/i;

/** Pure AI/data titles need .NET|C# on the TITLE (skills laundry lists are noisy). */
const PURE_AI_DATA_RE =
  /\b(ai\s+architect|artificial\s+intelligence\s+architect|ai\s+agent|ai\s+engineer|ai\s+solution\s+architect|architect[^.\n]{0,48}\b(ai|ml)\b|data\s*&\s*ai|ml\s+engineer|gen\s*-?\s*ai|genai|agentic\s+ai|data\s+scientist|data\s+engineer|data\s+engineering)\b/i;

/**
 * Primary non-.NET stacks in the TITLE — skip to avoid Java/MEAN ATS dead-ends.
 * Do not use on full JD blobs (skills lists are noisy).
 */
const NON_DOTNET_PRIMARY_RE =
  /\b(java|j2ee|spring boot|golang|go lang|python|mean\b|mern\b|ruby on rails|php|oracle apps|oracle fusion|oracle\s+dba|oracle cloud|abap)\b/i;

/** When scanning detail pages, use job panel text only — never document.body. */
function shouldSkipTitleFromDetail(detailText) {
  const t = String(detailText || "");
  // Prefer first heading-sized chunk if agent passes full panel.
  return shouldSkipTitle(t.slice(0, 400));
}

const DOTNET_RE = /(\.net|dotnet|asp\.?\s*net|c#|csharp)/i;

/** Architect / Lead / EM / Principal / Staff / Director — apply even if card omits .NET. */
const ARCH_LEAD_RE =
  /\b(architect|technical lead|tech lead|technology lead|engineering manager|engineering lead|engineer manager|software engineer manager|principal|staff|director|avp|head of|solution architect|cloud architect|azure architect|\.net lead|dotnet lead|lead (software|development|engineer)|software (engineering )?manager|senior manager|manager[, -]?\s*(software|engineering|technology|platform)|senior engineering)\b/i;

function normalizeAspNet(text) {
  return String(text || "").replace(/asp\.?\s*net/gi, "DOTNET");
}

function hasDotNet(title, skills) {
  const blob = normalizeAspNet(`${title || ""} ${skills || ""}`);
  return DOTNET_RE.test(blob);
}

function isArchLeadTitle(title) {
  return ARCH_LEAD_RE.test(title || "");
}

function shouldSkipTitle(title) {
  const t = title || "";
  if (SKIP_TITLE_RE.test(t)) return true;
  // AI Architect without .NET on the title itself (Instahyre/Foundit parity)
  if (PURE_AI_DATA_RE.test(t) && !hasDotNet(t, "")) return true;
  // Java/MEAN/Python-primary titles without .NET|C# — do not burn ATS time
  if (NON_DOTNET_PRIMARY_RE.test(t) && !hasDotNet(t, "")) return true;
  return false;
}

module.exports = {
  findResume,
  hasDotNet,
  shouldSkipTitle,
  shouldSkipTitleFromDetail,
  isArchLeadTitle,
  normalizeAspNet,
  ARCH_LEAD_RE,
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
