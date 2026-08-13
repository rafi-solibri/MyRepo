/**
 * Shared campus-company allowlist for Hitech City board browse
 * (Naukri / Foundit / Cutshort / Instahyre when HITECHCITY_COMPANY_ALLOWLIST is set).
 *
 * Env:
 *   HITECHCITY_COMPANY_ALLOWLIST  path to JSON array of company name strings
 *                                 OR path to companies.json ({ companies: [{name}] })
 *   When unset → allow all (normal portal daily behavior).
 */
"use strict";

const fs = require("fs");
const path = require("path");

let _cache = undefined;

function _norm(s) {
  return String(s || "")
    .toLowerCase()
    .replace(/j\.?\s*p\.?/g, "jp")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function _nameMatch(target, found) {
  const t = _norm(target);
  const f = _norm(found);
  if (!t || !f) return false;
  if (t.includes(f) || f.includes(t)) return true;
  const tc = t.replace(/\s/g, "");
  const fc = f.replace(/\s/g, "");
  if (tc && (tc.includes(fc) || fc.includes(tc))) return true;
  const tTok = new Set(t.split(" "));
  const fTok = new Set(f.split(" "));
  // JPMorgan / JP Morgan / Chase aliases
  const jpLeft = new Set(["jpmorgan", "jp", "chase", "jpmc", "jpmorganchase", "morgan"]);
  if ([...tTok].some((x) => jpLeft.has(x)) && [...fTok].some((x) => jpLeft.has(x))) return true;
  const overlap = [...tTok].filter((x) => fTok.has(x)).length;
  return overlap >= Math.min(2, tTok.size);
}

function _loadNames() {
  if (_cache !== undefined) return _cache;
  const p = process.env.HITECHCITY_COMPANY_ALLOWLIST;
  if (!p) {
    _cache = null;
    return _cache;
  }
  try {
    const raw = JSON.parse(fs.readFileSync(p, "utf8"));
    let names = [];
    if (Array.isArray(raw)) {
      names = raw.map((x) => (typeof x === "string" ? x : x?.name)).filter(Boolean);
    } else if (Array.isArray(raw.companies)) {
      names = raw.companies.map((c) => c?.name).filter(Boolean);
    } else if (Array.isArray(raw.names)) {
      names = raw.names.filter(Boolean);
    }
    _cache = names.filter(Boolean);
  } catch (e) {
    console.error("[hitechcity-allowlist] failed to load", p, e.message || e);
    _cache = null;
  }
  return _cache;
}

function companyAllowed(companyName) {
  const list = _loadNames();
  if (!list) return true;
  if (!list.length) return false;
  for (const target of list) {
    if (_nameMatch(target, companyName || "")) return true;
  }
  return false;
}

function allowlistActive() {
  return _loadNames() !== null;
}

function resetAllowlistCache() {
  _cache = undefined;
}

module.exports = {
  companyAllowed,
  allowlistActive,
  resetAllowlistCache,
  _norm,
};
