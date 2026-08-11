/**
 * Instahyre eligibility helpers — keep Hyd/Remote .NET/architect focus.
 * Prefer calling skipReason(title, company, location, skills) before Apply.
 */
"use strict";

function hasDotNet(title, skills) {
  const norm = `${title || ""} ${skills || ""}`.replace(/asp\.?\s*net/gi, "DOTNET");
  return /\.net|\bdotnet\b|\bc#\b|\bcsharp\b/i.test(norm);
}

function locationOk(loc) {
  return /\b(hyderabad|secunderabad|\bhyd\b|remote|wfh|work\s*from\s*home)\b/i.test(
    loc || ""
  );
}

/** Parse listed max CTC in LPA from free-text location/salary blurb. */
function parseMaxCtcLpa(text) {
  const t = String(text || "");
  let m = t.match(/₹?\s*([\d.]+)\s*L\s*[-–]\s*₹?\s*([\d.]+)\s*L/i);
  if (m) return Number(m[2]);
  m = t.match(/([\d.]+)\s*[-–]\s*([\d.]+)\s*LPA/i);
  if (m) return Number(m[2]);
  m = t.match(/up to\s*₹?\s*([\d.]+)\s*L/i);
  if (m) return Number(m[1]);
  return null;
}

/**
 * Returns skip reason string or null if allowed.
 */
function skipReason(title, { company = "", location = "", skills = "", salary = "" } = {}) {
  const t = title || "";

  // QA / Quality Engineering slipped past bare "qa" filters previously
  if (
    /\b(quality engineering|quality assurance|qa engineer|qa lead|sdet|test engineer)\b/i.test(
      t
    )
  ) {
    return "qa_quality_engineering";
  }

  if (
    /\b(salesforce|servicenow|\bsap\b|coupa|pega|guidewire|hubspot|revit|\bbarch\b|anaplan|kinaxis)\b/i.test(
      t
    )
  ) {
    return "wrong_stack_title";
  }

  // Pure AI/data titles — include "Solution/Technical Architect - AI" forms
  if (
    /\b(ai architect|ai engineer|ml engineer|data scientist|data engineer|data analyst|genai|architect\s*[-–:]?\s*ai|ai\s*[-–:]?\s*architect)\b/i.test(
      t
    ) &&
    !hasDotNet(t, "") // title-only .NET proof for pure AI/data (skills laundry lists are noisy)
  ) {
    return "pure_ai_data_without_dotnet";
  }

  // Non-engineering ops/people titles (title-first; not SA/TL/EM/Staff product eng)
  if (
    /\b(operations manager|office manager|hr manager|talent|recruiter|business analyst|scrum master)\b/i.test(
      t
    ) &&
    !/\b(software|engineer|engineering|architect|\.net|platform|devops|sre)\b/i.test(t)
  ) {
    return "non_engineering_title";
  }

  // Java-primary IC (unless Staff/Lead/Architect with .NET also present)
  if (
    /\bjava\b/i.test(t) &&
    !hasDotNet(t, skills) &&
    !/\b(architect|engineering manager|staff|principal|tech(?:nical)?\s+lead)\b/i.test(t)
  ) {
    return "java_primary";
  }

  if (location && !locationOk(location)) {
    return "location_not_hyd_remote";
  }

  const maxCtc = parseMaxCtcLpa(`${salary} ${location}`);
  if (maxCtc != null && maxCtc < 35) {
    return `ctc_max_${maxCtc}`;
  }

  return null;
}

module.exports = {
  hasDotNet,
  locationOk,
  parseMaxCtcLpa,
  skipReason,
};

if (require.main === module) {
  const samples = [
    "Quality Engineering Lead",
    "Full Stack Lead (Java)",
    "Staff Software Engineer .NET",
    "AI Architect",
    "Solution Architect - AI",
    "Lead Anaplan Solution Architect",
    "Senior Data Analyst",
    "Operations Manager",
  ];
  for (const title of samples) {
    console.log(title, "→", skipReason(title, { location: "Hyderabad" }));
  }
}
