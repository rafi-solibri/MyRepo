#!/usr/bin/env node
/**
 * Node wrapper around tools/naukri/tailor_resume.py
 * Produces a per-job Rafi_Resume.docx (truthful JD emphasis only).
 */
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { spawnSync } = require("child_process");
const { findResume } = require("./resume_and_filters");

const PY = path.join(__dirname, "tailor_resume.py");
const OUT_ROOT =
  process.env.NAUKRI_TAILORED_DIR ||
  path.join("/tmp", "naukri-tailored");

function resolvePython() {
  for (const cand of [
    process.env.PYTHON,
    process.env.PYTHON3,
    "python3",
    "python",
  ]) {
    if (!cand) continue;
    const r = spawnSync(cand, ["--version"], { encoding: "utf8" });
    if (r.status === 0) return cand;
  }
  return "python3";
}

/**
 * @param {{ role: string, company?: string, jdText?: string, base?: string }} opts
 * @returns {{ ok: boolean, out?: string, skills?: string[], headline?: string, reason?: string, meta?: object }}
 */
function tailorResumeForJob(opts = {}) {
  const role = String(opts.role || "").trim();
  const company = String(opts.company || "").trim();
  const jdText = String(opts.jdText || "").trim();
  const base = opts.base || findResume();
  if (!base || !fs.existsSync(base)) {
    return { ok: false, reason: "base_resume_missing" };
  }
  if (!role && !jdText) {
    return { ok: false, reason: "role_and_jd_empty", out: base };
  }

  const slug = crypto
    .createHash("sha1")
    .update(`${company}|${role}|${jdText.slice(0, 1500)}`)
    .digest("hex")
    .slice(0, 12);
  const outDir = path.join(OUT_ROOT, slug);
  const outPath = path.join(outDir, "Rafi_Resume.docx");
  fs.mkdirSync(outDir, { recursive: true });

  // Cache hit
  if (fs.existsSync(outPath) && fs.statSync(outPath).size > 1000) {
    let meta = null;
    try {
      meta = JSON.parse(
        fs.readFileSync(path.join(outDir, "Rafi_Resume.tailor.json"), "utf8")
      );
    } catch (_) {}
    return {
      ok: true,
      out: outPath,
      cached: true,
      skills: meta?.skills,
      headline: meta?.headline,
      meta,
    };
  }

  const jdFile = path.join(outDir, "jd.txt");
  fs.writeFileSync(jdFile, jdText || role, "utf8");

  const py = resolvePython();
  const r = spawnSync(
    py,
    [
      PY,
      "--role",
      role || "Solutions Architect",
      "--company",
      company,
      "--jd-file",
      jdFile,
      "--base",
      base,
      "--out",
      outPath,
    ],
    { encoding: "utf8", timeout: 60000 }
  );

  if (r.status !== 0 || !fs.existsSync(outPath)) {
    return {
      ok: false,
      reason: "tailor_failed",
      status: r.status,
      stderr: (r.stderr || "").slice(0, 500),
      stdout: (r.stdout || "").slice(0, 500),
      out: base,
    };
  }

  let meta = null;
  try {
    meta = JSON.parse(r.stdout || "{}");
  } catch (_) {
    try {
      meta = JSON.parse(
        fs.readFileSync(path.join(outDir, "Rafi_Resume.tailor.json"), "utf8")
      );
    } catch (__) {}
  }

  return {
    ok: true,
    out: outPath,
    cached: false,
    skills: meta?.skills,
    headline: meta?.headline,
    meta,
  };
}

module.exports = { tailorResumeForJob, OUT_ROOT };

if (require.main === module) {
  const role = process.argv[2] || "Solution Architect";
  const company = process.argv[3] || "TestCo";
  const jd = process.argv[4] || "Azure .NET Kafka microservices architect";
  const res = tailorResumeForJob({ role, company, jdText: jd });
  console.log(JSON.stringify(res, null, 2));
  process.exit(res.ok ? 0 : 1);
}
