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

/** Hard skip keywords (Coupa/Pega etc. - Mondelez false-apply fix).
 *  QA/SDET only as role tokens — do not match "Software & QA" department chrome.
 *  Prefer shouldSkipTitle(role) over full page blobs. */
const SKIP_TITLE_RE =
  /\b((manual\s+)?qa(\s+engineer|\s+analyst|\s+lead|\s+manager|\s+tester)|\bquality assurance\b|sdet|intern(?!et)|fresher|salesforce|servicenow|coupa|pega|guidewire|(^|[^a-z])sap(\s|&|$)|dynamics\s*365|microsoft dynamics|workday hms)\b/i;

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
  hasDotNet,
  shouldSkipTitle,
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
