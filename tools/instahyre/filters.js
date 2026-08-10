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

/**
 * Returns skip reason string or null if allowed.
 */
function skipReason(title, { company = "", location = "", skills = "" } = {}) {
  const t = title || "";
  const blob = `${t} ${company} ${skills}`;

  // QA / Quality Engineering slipped past bare "qa" filters previously
  if (
    /\b(quality engineering|quality assurance|qa engineer|qa lead|sdet|test engineer)\b/i.test(
      t
    )
  ) {
    return "qa_quality_engineering";
  }

  if (
    /\b(salesforce|servicenow|\bsap\b|coupa|pega|guidewire|hubspot|revit|\bbarch\b)\b/i.test(
      t
    )
  ) {
    return "wrong_stack_title";
  }

  if (
    /\b(ai architect|ai engineer|ml engineer|data scientist|data engineer|genai)\b/i.test(
      t
    ) &&
    !hasDotNet(t, skills)
  ) {
    return "pure_ai_data_without_dotnet";
  }

  // Java-primary IC (unless Staff/Lead/Architect with .NET also present)
  if (
    /\bjava\b/i.test(t) &&
    !hasDotNet(t, skills) &&
    !/\b(architect|engineering manager|staff|principal)\b/i.test(t)
  ) {
    return "java_primary";
  }

  if (location && !locationOk(location)) {
    return "location_not_hyd_remote";
  }

  return null;
}

module.exports = {
  hasDotNet,
  locationOk,
  skipReason,
};

if (require.main === module) {
  const samples = [
    "Quality Engineering Lead",
    "Full Stack Lead (Java)",
    "Staff Software Engineer .NET",
    "AI Architect",
  ];
  for (const title of samples) {
    console.log(title, "→", skipReason(title, { location: "Hyderabad" }));
  }
}
