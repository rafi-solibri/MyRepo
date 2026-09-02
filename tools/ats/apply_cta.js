/**
 * Shared Apply-CTA + brochure/hop helpers (no browser).
 * Used by complete_page.js and Naukri/Foundit so false "Apply" matches
 * (e.g. "View applied jobs") and marketing careers pages fail fast.
 */
"use strict";

const FALSE_APPLY_CTA_RE =
  /view applied|applied jobs|already applied|my applications|see (all )?applied|applications? sent/i;

const BROCHURE_URL_RE =
  /\/careers\.html(?:$|[?#])|\/about(?:-us)?(?:\/|$)|\/life-at|\/why[- ]join|\/join[- ]us(?:\.html)?(?:$|[?#])|\/our[- ]team|\/culture(?:\/|$)|\/careers\/?$|\/careers\/?[?#]|\/jobs\/?$|\/job-openings\/?$/i;

const JOB_DETAIL_URL_RE =
  /\/job\/|\/jobs\/\d|\/jobdetails\/|gh_jid=|requisition|reqid=|pid=\d|myworkdayjobs|greenhouse\.io|lever\.co|smartrecruiters|ashbyhq|icims|eightfold|darwinbox/i;

const BROCHURE_TEXT_RE =
  /join our (growing )?team|life at |why (work|join) (at|us)|we('re| are) hiring|see (all )?(open )?(roles|positions|jobs)|explore (our )?(careers|opportunities)|view (all )?openings/i;

const ATS_FORM_HINT_RE =
  /submit application|apply for this job|upload (your )?resume|cover letter|work history|autofill with resume|apply manually|first name|email address/i;

const BOARD_TRACKING_RE =
  /indeed\.com\/(?:applystart|rc\/clk|pagead|viewjob|clk)|linkedin\.com\/jobs\/(?:view|search)|naukri\.com\/job-listings|foundit\.in\/job\//i;

function normalizeLabel(label) {
  return String(label || "").replace(/\s+/g, " ").trim();
}

function isFalseApplyCta(label) {
  const t = normalizeLabel(label);
  if (!t) return false;
  if (FALSE_APPLY_CTA_RE.test(t)) return true;
  if (/sign in|log in|create account/i.test(t) && !/^apply/i.test(t)) return true;
  if (/with (indeed|linkedin|google|microsoft|facebook|apple)/i.test(t) && !/without indeed/i.test(t)) {
    return true;
  }
  return false;
}

function looksLikeApplyCta(label) {
  const t = normalizeLabel(label);
  if (!t || isFalseApplyCta(t)) return false;
  return /\bapply\b|i'?m interested|start application|submit application/i.test(t);
}

function isBrochureOrDeadEnd({
  url = "",
  text = "",
  hasFile = false,
  hasWd = false,
  hasEmail = false,
  hasPassword = false,
  hasApplyCta = false,
} = {}) {
  if (hasFile || hasWd || hasEmail || hasPassword) return false;
  if (hasApplyCta) return false;
  const u = String(url || "");
  const t = String(text || "");
  if (JOB_DETAIL_URL_RE.test(u) && ATS_FORM_HINT_RE.test(t)) return false;
  if (BROCHURE_URL_RE.test(u)) return true;
  if (BROCHURE_TEXT_RE.test(t) && !ATS_FORM_HINT_RE.test(t)) return true;
  if (/careers|jobs|join-us|about/i.test(u) && !ATS_FORM_HINT_RE.test(t) && !JOB_DETAIL_URL_RE.test(u)) {
    return true;
  }
  return false;
}

function extractHopDestinationFromUrl(url) {
  const raw = String(url || "");
  if (!raw) return "";
  let parsed;
  try {
    parsed = new URL(raw);
  } catch (_) {
    return "";
  }
  const keys = [
    "continueUrl",
    "continue_url",
    "dest",
    "destination",
    "redirect_url",
    "redirectUrl",
    "url",
    "u",
    "r",
    "continue",
    "target",
  ];
  for (const key of keys) {
    const val = parsed.searchParams.get(key);
    if (!val) continue;
    let dest = val;
    try {
      dest = decodeURIComponent(val);
    } catch (_) {}
    if (!/^https?:/i.test(dest)) continue;
    if (BOARD_TRACKING_RE.test(dest)) continue;
    if (/indeed\.com\/|linkedin\.com\/jobs|naukri\.com|foundit\.in/i.test(dest)) continue;
    return dest;
  }
  return "";
}

function isBoardTrackingUrl(url) {
  return BOARD_TRACKING_RE.test(String(url || ""));
}

module.exports = {
  isFalseApplyCta,
  looksLikeApplyCta,
  isBrochureOrDeadEnd,
  extractHopDestinationFromUrl,
  isBoardTrackingUrl,
  FALSE_APPLY_CTA_RE,
};
