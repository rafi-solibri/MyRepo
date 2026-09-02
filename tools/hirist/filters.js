/**
 * Hirist eligibility helpers — Hyd/Remote .NET/architect focus.
 * Prefer skipReason(title, { company, location, skills, salary, expMax }) before Apply.
 */
"use strict";

function hasDotNet(title, skills) {
  const norm = `${title || ""} ${skills || ""}`.replace(/asp\.?\s*net/gi, "DOTNET");
  return /\.net|\bdotnet\b|\bc#\b|\bcsharp\b/i.test(norm);
}

function hasCloudPlatform(title, skills) {
  return /\b(azure|aws|cloud|microservices|kubernetes|k8s|distributed|platform|backend)\b/i.test(
    `${title || ""} ${skills || ""}`
  );
}

function hasTargetSeniority(title) {
  return /\b(architect|engineering manager|tech(?:nical)?\s+lead|staff|principal|solutions?\s*architect|sdm|software development manager)\b/i.test(
    title || ""
  );
}

function locationOk(loc, title = "", skills = "", workFromHome = 0) {
  if (Number(workFromHome) === 1) return true;
  const l = loc || "";
  if (/\b(hyderabad|secunderabad|\bhyd\b|telangana|remote|wfh|work\s*from\s*home)\b/i.test(l)) {
    return true;
  }
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
function skipReason(
  title,
  { company = "", location = "", skills = "", salary = "", expMax = null, workFromHome = 0 } = {}
) {
  const t = title || "";

  if (
    /\b(quality engineering|quality assurance|qa engineer|qa lead|sdet|test engineer)\b/i.test(t)
  ) {
    return "qa_quality_engineering";
  }

  if (
    /\b(salesforce|servicenow|\bsap\b|coupa|conga|cpq|pega|guidewire|hubspot|revit|\bbarch\b|anaplan|kinaxis|shopify|dynamics\s*365|\bd365\b|dynamics\s+f&o|\bf&o\b|finance\s*&\s*operations|jira|atlassian)\b/i.test(
      t
    )
  ) {
    return "wrong_stack_title";
  }

  if (
    (
      /\b(ai architect|ai engineer|ai scientist|ai developer|ml engineer|ml scientist|machine learning|data scientist|data science|data engineer(?:ing)?|data analyst|data specialist|data architect|genai|architect\s*[-–:]?\s*ai|ai\s*[-–:]?\s*architect|quality data|data analytics|etl architect)\b/i.test(
        t
      ) ||
      (/\bai\b/i.test(t) && /\barchitect\b/i.test(t))
    ) &&
    !hasDotNet(t, "")
  ) {
    return "pure_ai_data_without_dotnet";
  }

  if (/\b(front[\s-]?end|ui engineer|ui developer)\b/i.test(t) && !hasDotNet(t, skills)) {
    return "frontend_without_dotnet";
  }

  if (/\bjava\b/i.test(t) && !hasDotNet(t, "")) {
    return "java_primary";
  }

  // Title-first: Python/Groovy (and close cousins) without .NET on the TITLE —
  // skills laundry often lists Azure/AWS and previously leaked these through.
  if (
    /\b(python|groovy|golang|go\s+lang|node\.?js|ruby on rails|php|sas)\b/i.test(t) &&
    !hasDotNet(t, "")
  ) {
    return "non_dotnet_primary";
  }

  if (
    /\b(intern|trainee|fresher|associate software|junior)\b/i.test(t) &&
    !hasTargetSeniority(t)
  ) {
    return "junior_title";
  }

  if (
    /\b(software engineer|backend engineer|full[\s-]?stack|developer)\b/i.test(t) &&
    !hasDotNet(t, skills) &&
    !hasTargetSeniority(t) &&
    !hasCloudPlatform(t, skills)
  ) {
    return "generic_engineering_without_dotnet_cloud";
  }

  if (
    /\b(operations manager|office manager|hr manager|talent|recruiter|business analyst|scrum master)\b/i.test(
      t
    ) &&
    !/\b(software|engineer|engineering|architect|\.net|platform|devops|sre)\b/i.test(t)
  ) {
    return "non_engineering_title";
  }

  if (location && !locationOk(location, t, skills, workFromHome)) {
    return "location_not_hyd_remote";
  }

  const maxCtc = parseMaxCtcLpa(`${salary} ${location}`);
  if (maxCtc != null && maxCtc < 35) {
    return `ctc_max_${maxCtc}`;
  }

  // Soft exp gate: max < 6 only when not already senior title
  if (expMax != null && Number(expMax) < 6 && !hasTargetSeniority(t)) {
    return `exp_max_${expMax}`;
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
    ["Technical Architect - .Net/Azure", { location: "Hyderabad", skills: ".Net Azure" }],
    ["AI Developer - Python", { location: "Hyderabad", skills: "Python" }],
    ["Full Stack Lead (Java)", { location: "Hyderabad", skills: "Java" }],
    ["Solutions Architect", { location: "Bangalore", skills: ".NET", workFromHome: 0 }],
    ["Staff Engineer", { location: "Remote", skills: "Azure", workFromHome: 1 }],
  ];
  for (const [title, opts] of samples) {
    console.log(JSON.stringify({ title, skip: skipReason(title, opts) }));
  }
}
