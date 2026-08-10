#!/usr/bin/env node
/**
 * Naukri helpers: resume path + login check patterns for TopTier UI.
 * Prefer cards as div.cursor-pointer; Quick Apply opens a popup.
 * Success = detail CTA shows Applied (sidebar Applied count is a filter chip, not status).
 */
"use strict";

const fs = require("fs");

const RESUME_CANDIDATES = [
  "/workspace/resumes/Rafi_Resume.docx",
  "/home/ubuntu/resumes/Rafi_Resume.docx",
  "/home/ubuntu/Documents/Rafi_Resume.docx",
  "/workspace/resumes/Rafi_Resume_Architect.docx",
];

function findResume() {
  for (const p of RESUME_CANDIDATES) {
    if (fs.existsSync(p) && fs.statSync(p).size > 1000) return p;
  }
  return null;
}

/**
 * Hard skip keywords (Coupa/Pega etc. - Mondelez false-apply fix).
 * Do NOT match bare "QA" — page chrome / "Software & QA" sidebars false-skip SA roles.
 * Only skip when title itself is a QA/SDET role.
 */
const SKIP_TITLE_RE =
  /\b(qa engineer|quality assurance|quality engineer|quality engineering|sdet|intern(?!et)|fresher|salesforce|servicenow|coupa|pega|guidewire|sap\b|dynamics|workday hms|revit|\bbarch\b|hubspot)\b/i;

/** Pure AI/data titles need .NET|C# on the TITLE (skills laundry lists are noisy). */
const PURE_AI_DATA_RE =
  /\b(ai\s+architect|ai\s+engineer|ml\s+engineer|genai|data\s+scientist|data\s+engineer)\b/i;

/** When scanning detail pages, use job panel text only — never document.body. */
function shouldSkipTitleFromDetail(detailText) {
  const t = String(detailText || "");
  // Prefer first heading-sized chunk if agent passes full panel.
  return shouldSkipTitle(t.slice(0, 400));
}

const DOTNET_RE = /(\.net|dotnet|asp\.?\s*net|c#|csharp)/i;

function normalizeAspNet(text) {
  return String(text || "").replace(/asp\.?\s*net/gi, "DOTNET");
}

function hasDotNet(title, skills) {
  const blob = normalizeAspNet(`${title || ""} ${skills || ""}`);
  return DOTNET_RE.test(blob);
}

function shouldSkipTitle(title) {
  const t = title || "";
  if (SKIP_TITLE_RE.test(t)) return true;
  // AI Architect without .NET on the title itself (Instahyre/Foundit parity)
  if (PURE_AI_DATA_RE.test(t) && !hasDotNet(t, "")) return true;
  return false;
}

module.exports = {
  findResume,
  hasDotNet,
  shouldSkipTitle,
  shouldSkipTitleFromDetail,
  normalizeAspNet,
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
