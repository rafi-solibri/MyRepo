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
  let hasSpecificPlace = false;
  if (Array.isArray(locs)) {
    for (const l of locs) {
      if (typeof l === "string") {
        parts.push(l);
        if (l.trim() && !/^(india|in)$/i.test(l.trim())) hasSpecificPlace = true;
      } else if (l) {
        const place = l.text || l.name || l.city || l.label || "";
        if (place) {
          parts.push(place);
          if (!/^(india|in)$/i.test(String(place).trim())) hasSpecificPlace = true;
        }
        // Country-only rows still expose country; keep for debugging but city may be empty.
        // Only India/empty cards may pick up JD Remote/Hyd. Singapore/Thailand/etc.
        // country-only must not inherit marketing "remote-first" / WFH copy.
        if (!l.city && !l.text && !l.name && l.country) {
          parts.push(String(l.country));
          if (!/^(india|in)$/i.test(String(l.country).trim())) hasSpecificPlace = true;
        }
      }
    }
  }
  if (job.location) {
    parts.push(String(job.location));
    if (!/^(india|in)$/i.test(String(job.location).trim())) hasSpecificPlace = true;
  }
  // JD body Remote/Hyd only when card locations are empty or country-only (India).
  // Do NOT let marketing "remote-first" override an explicit Noida/Bangalore city.
  if (!hasSpecificPlace && job.description) {
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
  // Raven often emits 0-0 when experience is undisclosed — treat as unknown,
  // then overlay title bands like "6-9 Yrs" / "8 to 12 years" when present.
  const ravenUndisclosed =
    (Number.isNaN(min) && Number.isNaN(max)) || (min === 0 && max === 0);
  if (ravenUndisclosed) {
    const fromTitle = parseTitleExperience(title || job.title);
    if (fromTitle) {
      min = fromTitle.min;
      max = fromTitle.max == null ? NaN : fromTitle.max;
      return {
        min,
        max,
        undisclosed: Number.isNaN(min) && Number.isNaN(max),
      };
    }
    // No title band → stay undisclosed (do NOT keep 0-0 as a junior/mid band).
    return { min: NaN, max: NaN, undisclosed: true };
  }
  return { min, max, undisclosed: false };
}

/** Underscore / pipe titles ("Technical Architect_.NET", "IN_Senior_…") need word breaks. */
function titleForMatch(title) {
  return String(title || "").replace(/[_|/]+/g, " ");
}

function hasDotNetProof(text) {
  const norm = String(text || "").replace(/asp\.?\s*net/gi, "DOTNET");
  // Do NOT use `\bc#\b` — `#` is non-word so trailing `\b` never matches "C#" / "C#," / "C# &".
  // Cutshort parity: bare `c#` + `\bcsharp\b`.
  return /\.net|\bdotnet\b|\bdot\s*net\b|c#|\bcsharp\b/i.test(norm);
}

function hasDotNet(title, skills) {
  // Do NOT use \b before .net — space+dot is not a word boundary.
  return hasDotNetProof(`${titleForMatch(title)} ${skills || ""}`);
}

function hasSeniority(title) {
  // Accept Senior/.NET Senior/Senior Backend (not only "Senior .NET …" word-order).
  // Apply bias: uncertain → apply; still gated by .NET + Hyd/remote + exp elsewhere.
  // architect(?:ure)? covers "Solution Architecture …" titles (not only "Architect").
  return /\b(architect(?:ure)?|principal|staff\s+(software|engineer)|engineering\s+manager|\bem\b|director|avp|head\s+of|tech(?:nology)?\s+lead|technical\s+lead|\blead\b|manager|\bsenior\b|\bsr\.?\b)\b/i.test(
    titleForMatch(title)
  );
}

/** Architect / Tech Lead / EM band — Naukri parity: may apply without .NET on skills laundry list. */
function isArchLeadTitle(title) {
  return /\b(architect(?:ure)?|principal|staff\s+(software|engineer)|engineering\s+manager|\bem\b|tech(?:nology)?\s+lead|technical\s+lead|solution\s+architect(?:ure)?|software\s+architect(?:ure)?)\b/i.test(
    titleForMatch(title)
  );
}

/**
 * Naukri NON_DOTNET_PRIMARY_RE parity — title-only (skills laundry lists are noisy).
 * Blocks Arch/Lead exception and forces skip when .NET|C# is absent from the title.
 */
const NON_DOTNET_PRIMARY_RE =
  /\b(java|j2ee|spring\s*boot|golang|go\s*lang|python|mean\b|mern\b|ruby\s+on\s+rails|\bphp\b|oracle\s+apps|oracle\s+fusion|oracle\s+dba|oracle\s+cloud|abap|mainframe|cobol|\bas400\b|ibm\s*i|c\s*\+\+|c\s*plus(?:\s*plus)?)\b/i;

function isNonDotNetPrimaryTitle(title) {
  const t = titleForMatch(title);
  return NON_DOTNET_PRIMARY_RE.test(t) && !hasDotNet(t, "");
}

function isJavaOrSalesforcePrimary(title, skills) {
  const t = titleForMatch(title);
  const blob = `${t} ${skills || ""}`;
  if (/\b(salesforce|agentforce|sfdc)\b/i.test(t)) return true;
  // Skills-only Salesforce without .NET on TITLE (Hitachi CPQ / Agentforce-adjacent).
  if (/\b(salesforce|agentforce|sfdc)\b/i.test(skills || "") && !hasDotNetProof(t)) return true;
  if (/\bjava\b(?!\s*script)/i.test(blob) && !hasDotNet(title, skills)) return true;
  // Python/Go/MEAN/… on TITLE without .NET — same as Java for Arch/Lead exception.
  if (isNonDotNetPrimaryTitle(title)) return true;
  return false;
}

function isTechLeadBand(title) {
  return /\b(architect(?:ure)?|principal|staff|tech(?:nology)?\s+lead|technical\s+lead)\b/i.test(
    titleForMatch(title)
  );
}

function isStaffPrincipal(title) {
  return /\b(staff|principal)\b/i.test(titleForMatch(title));
}

function skipTitleReason(title) {
  const t = titleForMatch(title);
  if (/\b(qa\b|sdet|test\s+engineer)\b/i.test(t) && !hasDotNet(t, "")) return "QA/test";
  if (
    /\b(project\s+manager|program\s+manager|delivery\s+manager|technical\s+program\s+manager|\btpm\b)\b/i.test(
      t
    )
  )
    return "PM/TPM/delivery";
  if (/\bpresales|pre-sales\b/i.test(t)) return "presales";
  // Agentforce/SFDC titles are Salesforce-stack even when "Salesforce" is only the employer.
  if (/\b(salesforce|agentforce|sfdc)\b/i.test(t)) return "Salesforce";
  if (/\bservicenow\b/i.test(t)) return "ServiceNow";
  if (/\bpower\s*platform\b/i.test(t)) return "Power Platform";
  if (/\bduck\s*creek\b/i.test(t)) return "Duck Creek";
  // Naukri/LinkedIn/Instahyre parity — insurance P&C platforms are not .NET/cloud Arch targets.
  if (/\bguidewire\b/i.test(t)) return "Guidewire";
  // Pure AI / data titles need .NET|C#|dotnet on the TITLE (skills laundry lists are noisy).
  // Naukri/Instahyre parity: AI Solution Architect, Agentic/Generative AI Lead, Data Engineering Manager,
  // and trailing "Solutions Architect - AI" (ResultsCX 2026-08-25).
  // Arch/Lead exception must NOT apply — Socnet "Technical Lead - Agentic AI / Generative AI".
  // Do NOT match bare "Architecture … AI" (Microsoft "Solution Architecture Apps & AI" may still pass).
  // "Data Governance … Lead/Architect" (Macquarie 2026-08-28) — Arch/Lead must not waive .NET.
  // "Engineering Manager, AI Product Development" (Jobgether 2026-08-30) — EM + trailing AI Product.
  if (
    /\b(ai\s+(?:specialist\s+)?(?:solution\s+)?architect|ai\s+engineer(?:ing)?(?:\s+manager|\s+lead)?|engineering\s+manager[,\s:/|-]+ai|ai\s+product|ai\s+agent|ml\s+engineer|gen\s*-?\s*ai|genai|generative\s+ai|agentic\s+ai|\bgemini\b|\bllm\b|data\s+scientist|data\s+engineer(?:ing)?|data\s+architect|data\s+governance|architect\s*[-–:]?\s*ai|ai\s*[-–:]?\s*architect)\b/i.test(
      t
    ) &&
    !hasDotNet(t, "")
  )
    return "pure AI/data without .NET on title";
  // VoIP / Asterisk / telephony stacks — not .NET/cloud Arch targets (Jobgether 2026-08-25).
  if (/\b(asterisk|telephony|\bvoip\b)\b/i.test(t) && !hasDotNet(t, ""))
    return "Asterisk/telephony without .NET on title";
  // UI/frontend React|Angular|Vue Architect without .NET on TITLE (Infosys UI Technical Architect 2026-08-25).
  if (
    /\b(ui\s+(?:technical\s+)?architect|frontend|front[\s-]?end)\b/i.test(t) &&
    /\b(react|angular|vue\.?js|vue)\b/i.test(t) &&
    !hasDotNet(t, "")
  )
    return "UI/frontend React/Angular without .NET on title";
  // Infra / IT ops / helpdesk — .NET only in skills laundry lists is noise (NUS Analyst case).
  if (
    /\b(infrastructure|it\s+analyst|systems?\s+analyst|sysadmin|system\s+admin|network\s+engineer|desktop\s+support|help\s*desk|helpdesk|sre\b|site\s+reliability)\b/i.test(
      t
    ) &&
    !hasDotNet(t, "")
  )
    return "infra/ops without .NET on title";
  // Capgemini PU1 / AMS "Support- Architect" (job 64753771, 2026-08-30) — native Falcon
  // has no SAPBTP redirect, so the URL SAP check never fires. Title-only skip.
  if (/\b(pu1\s+support|support[\s-]+architect)\b/i.test(t) && !hasDotNet(t, ""))
    return "support architect without .NET on title";
  // Mobile-native EM/Arch (right advisors Android/iOS EM 64686483, 2026-08-30).
  if (
    /\b(android|\bios\b|mobile\s+application|mobile\s+app(?:lication)?s?)\b/i.test(t) &&
    !hasDotNet(t, "")
  )
    return "mobile Android/iOS without .NET on title";
  // EXTRA_QUERIES Arch/Lead wave pulled non-software EM/Principal titles (2026-08-15).
  // Specific EM titles first (Cyient "Manufacturing Engineering Manager" 2026-08-26).
  if (
    /\b(operations\s+engineering\s+manager|manufacturing\s+engineering\s+manager)\b/i.test(
      t
    ) &&
    !hasDotNet(t, "")
  )
    return "ops/manufacturing EM without .NET on title";
  if (
    /\b(facilities|electrical|mechanical|civil|structural|hvac|power\s+generation|wastewater|water|manufacturing)\b/i.test(
      t
    ) &&
    !hasDotNet(t, "")
  )
    return "non-software engineering without .NET on title";
  // Naukri NON_DOTNET_PRIMARY_RE parity — Oracle Fusion/Apps/ERP is not .NET.
  if (/\b(oracle\s+fusion|oracle\s+apps|oracle\s+erp)\b/i.test(t) && !hasDotNet(t, ""))
    return "Oracle Fusion/ERP without .NET on title";
  // Data-platform primary titles (Snowflake/Databricks) — Arch/Lead exception must not apply.
  if (/\b(snowflake|databricks)\b/i.test(t) && !hasDotNet(t, ""))
    return "Snowflake/Databricks without .NET on title";
  // Java/Python/Go/MEAN/… primary titles without .NET on TITLE — Arch/Lead must not apply
  // (S&P "Software Engineering Manager, Backend Development (Python)" false apply 2026-08-22).
  if (isNonDotNetPrimaryTitle(t)) return "non-.NET primary stack on title";
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
  // Reject clearly junior/mid bands (e.g. Capgemini "6-9 Yrs") but allow 8-12 / 10-15.
  if (!Number.isNaN(max) && max < 10 && (Number.isNaN(min) || min < 8)) {
    return { ok: false, reason: `maxExp ${max}<10 (junior/mid band)` };
  }
  if (!Number.isNaN(min) && min >= 6) return { ok: true, reason: `min ${min}≥6` };
  if (!Number.isNaN(max) && max >= 10) return { ok: true, reason: `max ${max}≥10` };
  if (isTechLeadBand(title) && !Number.isNaN(min) && min >= 8)
    return { ok: true, reason: `TL/Arch min ${min}≥8` };
  if (isStaffPrincipal(title) && !Number.isNaN(max) && max >= 10)
    return { ok: true, reason: `Staff/Principal max ${max}≥10` };
  return { ok: false, reason: `exp ${min}-${max} fails` };
}

function ctcOk(job) {
  const abs = job.maximumSalary?.absoluteValue;
  if (abs == null || abs === 0) return { ok: true, lpa: null };
  const lpa = Number(abs) / 1e5;
  if (Number.isNaN(lpa)) return { ok: true, lpa: null };
  // Listed max often understates; only skip clearly low bands. Forms still state 65 expected.
  if (lpa < 35) return { ok: false, lpa, reason: `max CTC ${lpa} LPA < 35` };
  return { ok: true, lpa };
}

function classifyJob(job) {
  const title = job.title || job.jobTitle || "";
  const skills = skillTexts(job);
  const loc = locationsFrom(job);
  const jobId = String(job.jobId || job.id || "");

  const archLead = isArchLeadTitle(title);
  // Naukri parity: Arch/Lead/EM Hyd/remote may pass without .NET on skills when not Java/SF-primary.
  if (!hasDotNet(title, skills)) {
    if (!(archLead && !isJavaOrSalesforcePrimary(title, skills))) {
      return { pass: false, reason: "no .NET on title+skills" };
    }
  }
  const norm = `${titleForMatch(title)} ${skills}`.replace(/asp\.?\s*net/gi, "DOTNET");
  if (/\bsap\b/i.test(norm) && !hasDotNetProof(norm))
    return { pass: false, reason: "SAP without .NET" };
  // Capgemini SAPBTP URLs omit "SAP" from the display title — treat redirect as SAP signal.
  // Require .NET on TITLE only: skills laundry lists are noisy (PU1 Support Architect 2026-08-26).
  const redirect = String(job.redirectUrl || job.applyUrl || "");
  if (/sapbtp|\bsap\b/i.test(redirect) && !hasDotNet(title, ""))
    return { pass: false, reason: "SAP without .NET" };
  if (/\bjava\b(?!\s*script)/i.test(norm) && !hasDotNetProof(norm))
    return { pass: false, reason: "Java-only" };
  const skip = skipTitleReason(title);
  if (skip) return { pass: false, reason: skip };
  // Employer Salesforce + no .NET on TITLE → Salesforce-stack (skills laundry lists are noisy).
  const company = job.companyName || job.company?.name || "";
  if (/\bsalesforce\b/i.test(company) && !hasDotNet(title, "")) {
    return { pass: false, reason: "Salesforce" };
  }
  if (!hasSeniority(title))
    return { pass: false, reason: "no seniority keyword on title" };
  if (!locationOk(loc, title)) {
    // Empty or country-only (India) cards need JD body for Remote/Hyd signals.
    const countryOnly = !loc || /^(india|in)(\s*\|\s*(india|in))*$/i.test(loc.trim());
    if (!loc || (countryOnly && !job.description)) {
      return {
        pass: false,
        reason: "needs JD location enrich",
        needsEnrich: true,
      };
    }
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
    archLeadWithoutDotNetProof: archLead && !hasDotNet(title, skills),
  };
}

module.exports = {
  skillTexts,
  locationsFrom,
  parseTitleExperience,
  experienceBounds,
  titleForMatch,
  hasDotNetProof,
  hasDotNet,
  hasSeniority,
  isArchLeadTitle,
  isJavaOrSalesforcePrimary,
  isNonDotNetPrimaryTitle,
  NON_DOTNET_PRIMARY_RE,
  experienceOk,
  ctcOk,
  classifyJob,
  FORBIDDEN_DRY_RUN: "/home/api/canJobApply",
};
