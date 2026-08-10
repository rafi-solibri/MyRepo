/**
 * Shared Foundit eligibility filters for Mohammed Abdul Rafi Ahmed daily apply.
 * .NET proof = title + skills only (never the search query).
 */
"use strict";

function skillTexts(job) {
  const out = [];
  for (const key of ["skills", "itSkills", "keySkills"]) {
    const arr = job[key];
    if (!Array.isArray(arr)) continue;
    for (const s of arr) {
      if (typeof s === "string") out.push(s);
      else if (s?.text) out.push(s.text);
      else if (s?.name) out.push(s.name);
    }
  }
  return out.join(" ");
}

function locationsFrom(job) {
  const parts = [];
  const locs = job.locations || job.jobLocations || [];
  if (Array.isArray(locs)) {
    for (const l of locs) {
      if (typeof l === "string") parts.push(l);
      else if (l) {
        parts.push(l.text || l.name || l.city || l.label || "");
        // Country-only rows still expose country; keep for debugging but city may be empty.
        if (!l.city && !l.text && !l.name && l.country) parts.push(String(l.country));
      }
    }
  }
  if (job.location) parts.push(String(job.location));
  // Many external cards leave locations=[] / India-only; JD body often has Remote/Hyderabad.
  if (job.description) {
    const desc = String(job.description).replace(/<[^>]+>/g, " ");
    const hits = desc.match(/\b(hyderabad|secunderabad|remote|wfh|work\s*from\s*home)\b/gi);
    if (hits) parts.push(...hits);
  }
  return parts.filter(Boolean).join(" | ");
}

/** Parse "6-9 Yrs" / "8 to 12 years" style bands from title when Raven is 0-0. */
function parseTitleExperience(title) {
  const t = title || "";
  let m = t.match(/(\d+)\s*[-–to]+\s*(\d+)\s*(?:\+)?\s*(?:yrs?|years?)/i);
  if (m) return { min: Number(m[1]), max: Number(m[2]) };
  m = t.match(/(\d+)\s*\+\s*(?:yrs?|years?)/i);
  if (m) return { min: Number(m[1]), max: null };
  return null;
}

function experienceBounds(job, title) {
  let min = Number(job.minimumExperience?.years ?? job.minExperience ?? NaN);
  let max = Number(job.maximumExperience?.years ?? job.maxExperience ?? NaN);
  const undisclosed =
    (Number.isNaN(min) && Number.isNaN(max)) || (min === 0 && max === 0);
  if (undisclosed) {
    const fromTitle = parseTitleExperience(title || job.title);
    if (fromTitle) {
      min = fromTitle.min;
      max = fromTitle.max == null ? NaN : fromTitle.max;
    }
  }
  return { min, max, undisclosed: Number.isNaN(min) && Number.isNaN(max) };
}

function hasDotNet(title, skills) {
  // Do NOT use \b before .net — space+dot is not a word boundary.
  const norm = `${title || ""} ${skills || ""}`.replace(/asp\.?\s*net/gi, "DOTNET");
  return /\.net|\bdotnet\b|\bc#\b/i.test(norm);
}

function hasSeniority(title) {
  return /\b(architect|principal|staff\s+(software|engineer)|engineering\s+manager|\bem\b|director|avp|head\s+of|tech(?:nology)?\s+lead|technical\s+lead|\blead\b|manager)\b/i.test(
    title || ""
  );
}

function isTechLeadBand(title) {
  return /\b(architect|principal|staff|tech(?:nology)?\s+lead|technical\s+lead)\b/i.test(
    title || ""
  );
}

function isStaffPrincipal(title) {
  return /\b(staff|principal)\b/i.test(title || "");
}

function skipTitleReason(title) {
  const t = title || "";
  if (/\b(qa\b|sdet|test\s+engineer)\b/i.test(t) && !hasDotNet(t, "")) return "QA/test";
  if (
    /\b(project\s+manager|program\s+manager|delivery\s+manager|technical\s+program\s+manager|\btpm\b)\b/i.test(
      t
    )
  )
    return "PM/TPM/delivery";
  if (/\bpresales|pre-sales\b/i.test(t)) return "presales";
  if (/\bsalesforce\b/i.test(t)) return "Salesforce";
  if (/\bservicenow\b/i.test(t)) return "ServiceNow";
  if (/\bpower\s*platform\b/i.test(t)) return "Power Platform";
  if (/\bduck\s*creek\b/i.test(t)) return "Duck Creek";
  // Pure AI / data titles need .NET|C#|dotnet on the TITLE (skills laundry lists are noisy).
  if (
    /\b(ai\s+architect|ai\s+engineer|ml\s+engineer|genai|data\s+scientist|data\s+engineer)\b/i.test(
      t
    ) &&
    !hasDotNet(t, "")
  )
    return "pure AI/data without .NET on title";
  if (/\bwpf\b/i.test(t) && !/\basp\.?\s*net|web\s*api|azure|\.net\s*core\b/i.test(t))
    return "WPF/hardware desktop";
  return null;
}

function locationOk(loc, title) {
  return /\b(hyderabad|secunderabad|\bhyd\b|remote|wfh|work\s*from\s*home)\b/i.test(
    `${loc || ""} ${title || ""}`
  );
}

function experienceOk(job, title) {
  const { min, max, undisclosed } = experienceBounds(job, title);
  if (undisclosed) return { ok: true, reason: "undisclosed" };
  if (!Number.isNaN(max) && max < 10) return { ok: false, reason: `maxExp ${max}<10` };
  if (!Number.isNaN(min) && min >= 7) return { ok: true, reason: `min ${min}≥7` };
  if (!Number.isNaN(max) && max >= 12) return { ok: true, reason: `max ${max}≥12` };
  if (isTechLeadBand(title) && min >= 8 && max >= 10)
    return { ok: true, reason: `TL/Arch band ${min}-${max}` };
  if (isStaffPrincipal(title) && max >= 10)
    return { ok: true, reason: `Staff/Principal max ${max}≥10` };
  return { ok: false, reason: `exp ${min}-${max} fails` };
}

function ctcOk(job) {
  const abs = job.maximumSalary?.absoluteValue;
  if (abs == null || abs === 0) return { ok: true, lpa: null };
  const lpa = Number(abs) / 1e5;
  if (Number.isNaN(lpa)) return { ok: true, lpa: null };
  if (lpa < 50) return { ok: false, lpa, reason: `max CTC ${lpa} LPA < 50` };
  return { ok: true, lpa };
}

function classifyJob(job) {
  const title = job.title || job.jobTitle || "";
  const skills = skillTexts(job);
  const loc = locationsFrom(job);
  const jobId = String(job.jobId || job.id || "");

  if (!hasDotNet(title, skills))
    return { pass: false, reason: "no .NET on title+skills" };
  const norm = `${title} ${skills}`.replace(/asp\.?\s*net/gi, "DOTNET");
  if (/\bsap\b/i.test(norm) && !/\.net|\bdotnet\b|\bc#\b/i.test(norm))
    return { pass: false, reason: "SAP without .NET" };
  if (/\bjava\b(?!\s*script)/i.test(norm) && !/\.net|\bdotnet\b|\bc#\b/i.test(norm))
    return { pass: false, reason: "Java-only" };
  const skip = skipTitleReason(title);
  if (skip) return { pass: false, reason: skip };
  if (!hasSeniority(title))
    return { pass: false, reason: "no seniority keyword on title" };
  if (!locationOk(loc, title)) {
    if (!loc) return { pass: false, reason: "needs JD location enrich", needsEnrich: true };
    return { pass: false, reason: `location not Hyd/remote: ${loc.slice(0, 80)}` };
  }
  const exp = experienceOk(job, title);
  if (!exp.ok) return { pass: false, reason: exp.reason };
  const ctc = ctcOk(job);
  if (!ctc.ok) return { pass: false, reason: ctc.reason };

  return {
    pass: true,
    jobId,
    title,
    skills: skills.slice(0, 200),
    loc: loc || "(from title)",
    company: job.companyName || job.company?.name || "Unknown",
    redirectUrl: job.redirectUrl || null,
    exp,
    ctcLpa: ctc.lpa,
  };
}

module.exports = {
  skillTexts,
  locationsFrom,
  parseTitleExperience,
  experienceBounds,
  hasDotNet,
  hasSeniority,
  experienceOk,
  ctcOk,
  classifyJob,
  FORBIDDEN_DRY_RUN: "/home/api/canJobApply",
};
