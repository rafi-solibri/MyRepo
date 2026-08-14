/**
 * Instahyre eligibility helpers — keep Hyd/Remote .NET/architect focus.
 * Prefer calling skipReason(title, company, location, skills) before Apply.
 */
"use strict";

function hasDotNet(title, skills) {
  const norm = `${title || ""} ${skills || ""}`.replace(/asp\.?\s*net/gi, "DOTNET");
  return /\.net|\bdotnet\b|\bc#\b|\bcsharp\b/i.test(norm);
}

function locationOk(loc, title = "", skills = "") {
  const l = loc || "";
  if (/\b(hyderabad|secunderabad|\bhyd\b|remote|wfh|work\s*from\s*home)\b/i.test(l)) {
    return true;
  }
  // Soften: pan-India / anywhere / multi-city when senior .NET/cloud title
  if (
    /\b(pan[\s-]?india|anywhere(\s+in\s+india)?|work\s*from\s*anywhere|multiple\s+locations?|india\s*\(?\s*remote\s*\)?|remote[\s-]?india|locations?\s+across\s+india)\b/i.test(
      l
    ) &&
    (hasDotNet(title, skills) || hasTargetSeniority(title) || hasCloudPlatform(title, skills))
  ) {
    return true;
  }
  return false;
}

function hasCloudPlatform(title, skills) {
  return /\b(azure|aws|cloud|microservices|kubernetes|k8s|distributed|platform|backend)\b/i.test(
    `${title || ""} ${skills || ""}`
  );
}

function hasTargetSeniority(title) {
  return /\b(architect|engineering manager|tech(?:nical)?\s+lead|staff|principal)\b/i.test(
    title || ""
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
    /\b(ai architect|ai engineer|ai scientist|ai developer|ml engineer|ml scientist|machine learning|data scientist|data science|data engineer|data analyst|data specialist|genai|architect\s*[-–:]?\s*ai|ai\s*[-–:]?\s*architect)\b/i.test(
      t
    ) &&
    !hasDotNet(t, "") // title-only .NET proof for pure AI/data (skills laundry lists are noisy)
  ) {
    return "pure_ai_data_without_dotnet";
  }

  if (/\b(front[\s-]?end|ui engineer|ui developer)\b/i.test(t) && !hasDotNet(t, skills)) {
    return "frontend_without_dotnet";
  }

  // Cloud/sysadmin ops IC — not SA/TL/EM/Staff product engineering
  if (
    /\b(administrator|sysadmin|system admin|desktop support|help\s*desk|virtualisation engineer|virtualization engineer)\b/i.test(
      t
    ) &&
    !hasTargetSeniority(t)
  ) {
    return "ops_admin_title";
  }

  if (
    /\b(software engineer|backend engineer|full[\s-]?stack|developer)\b/i.test(t) &&
    !hasDotNet(t, skills) &&
    !hasTargetSeniority(t) &&
    !hasCloudPlatform(t, skills)
  ) {
    return "generic_engineering_without_dotnet_cloud";
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

  if (location && !locationOk(location, t, skills)) {
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
  hasCloudPlatform,
  hasTargetSeniority,
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
    "AI Scientist",
    "Frontend Engineer",
    "Fullstack Engineer",
    "Operations Manager",
    "AWS Administrator",
    "AWS - Data Specialist",
    "Azure Virtualisation Engineer",
    "Tech Lead",
  ];
  for (const title of samples) {
    console.log(title, "→", skipReason(title, { location: "Hyderabad" }));
  }
}
