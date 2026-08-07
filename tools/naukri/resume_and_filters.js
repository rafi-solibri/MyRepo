#!/usr/bin/env node
/**
 * Naukri helpers: resume path + login check patterns for TopTier UI.
 * Prefer cards as div.cursor-pointer; Quick Apply opens a popup.
 * Success = detail CTA shows Applied (sidebar Applied count is a filter chip, not status).
 */
"use strict";

const {
  findResume,
  resumeUploadPath,
  CANONICAL_NAME,
  RESUME_LABEL,
  LEGACY_ALIASES,
} = require("../resume_paths");

const RESUME_CANDIDATES = [
  `/workspace/resumes/${CANONICAL_NAME}`,
  `/home/ubuntu/resumes/${CANONICAL_NAME}`,
  `/home/ubuntu/Documents/${CANONICAL_NAME}`,
  ...LEGACY_ALIASES.flatMap((name) => [
    `/workspace/resumes/${name}`,
    `/home/ubuntu/resumes/${name}`,
    `/home/ubuntu/Documents/${name}`,
  ]),
];

/**
 * Hard skip keywords (Coupa/Pega etc. - Mondelez false-apply fix).
 * Do NOT match bare "QA" — page chrome / "Software & QA" sidebars false-skip SA roles.
 * Only skip when title itself is a QA/SDET role.
 */
const SKIP_TITLE_RE =
  /\b(qa engineer|quality assurance|quality engineer|sdet|intern(?!et)|fresher|salesforce|servicenow|coupa|pega|guidewire|sap\b|dynamics|workday hms)\b/i;

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
  return SKIP_TITLE_RE.test(title || "");
}

module.exports = {
  findResume,
  resumeUploadPath,
  hasDotNet,
  shouldSkipTitle,
  shouldSkipTitleFromDetail,
  normalizeAspNet,
  RESUME_CANDIDATES,
  RESUME_LABEL,
  CANONICAL_NAME,
  EXPECTED_CTC_LPA: 65,
  CURRENT_CTC_LPA: 52,
  CHROME_PROFILE: process.env.NAUKRI_CHROME_PROFILE || "/home/ubuntu/.naukri-chrome-profile",
  PROFILE_URL: process.env.NAUKRI_PROFILE_URL || "https://www.naukri.com/mnjuser/profile",
  RESUME_HEADLINE:
    "Solutions Architect & Technical Lead - 15+ Yrs - .NET Core, Microservices, AWS&Azure, Kafka&RabbitMQ",
};

if (require.main === module) {
  console.log(JSON.stringify({ resume: findResume(), label: RESUME_LABEL }, null, 2));
}
