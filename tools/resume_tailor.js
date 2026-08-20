#!/usr/bin/env node
/**
 * Node wrapper around shared tools/resume_tailor.py (LinkedIn + Foundit).
 *
 *   const { tailorResumeForJob } = require("../resume_tailor");
 *   const r = tailorResumeForJob({ master, title, company, description, skills, jobId });
 *
 * Returns { ok, out, headline, matchedSkills, bytes } for Foundit daily_apply.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.join(__dirname, "..");

function skillText(skills) {
  if (!skills) return "";
  if (typeof skills === "string") return skills;
  if (Array.isArray(skills)) {
    return skills
      .map((s) => (typeof s === "string" ? s : s?.text || s?.name || ""))
      .filter(Boolean)
      .join(", ");
  }
  return String(skills);
}

function resolvePython() {
  const candidates = [process.env.PYTHON, process.env.PYTHON3, "python3", "python"].filter(
    Boolean
  );
  for (const bin of candidates) {
    const probe = spawnSync(
      bin,
      ["-c", "import docx; import tools.resume_tailor"],
      { encoding: "utf8", cwd: ROOT, env: { ...process.env, PYTHONPATH: ROOT } }
    );
    if (probe.status === 0) return bin;
  }
  spawnSync("python3", ["-m", "pip", "install", "-q", "python-docx"], {
    encoding: "utf8",
  });
  return "python3";
}

/**
 * @param {object} opts
 * @returns {{ ok: boolean, out?: string, matchedSkills?: string[], headline?: string, bytes?: number, error?: string }}
 */
function tailorResumeForJob(opts = {}) {
  const jobId = String(opts.jobId || "job");
  const title = String(opts.title || "");
  const company = String(opts.company || "");
  const description = String(opts.description || "").slice(0, 20000);
  const skills = skillText(opts.skills);
  const jd = [description, skills].filter(Boolean).join("\n");
  const master = opts.master || "";

  const py = resolvePython();
  const code = `
import json, sys
from pathlib import Path
from tools.resume_tailor import tailor_resume_for_job, tailor_document, extract_jd_skills, preferred_headline

payload = json.loads(sys.stdin.read())
src = Path(payload["master"]) if payload.get("master") else None
jd = payload.get("jd") or ""
title = payload.get("title") or ""
company = payload.get("company") or ""
job_id = payload.get("job_id") or "job"
try:
    path = tailor_resume_for_job(job_id=job_id, title=title, company=company, jd=jd, src=src)
    matched = extract_jd_skills(jd, title)
    headline = preferred_headline(title, matched)
    p = Path(path)
    print(json.dumps({
        "ok": True,
        "out": str(p),
        "matchedSkills": matched,
        "headline": headline,
        "bytes": p.stat().st_size if p.is_file() else 0,
    }))
except Exception as e:
    print(json.dumps({"ok": False, "error": str(e)[:400]}))
    sys.exit(1)
`;

  const run = spawnSync(py, ["-c", code], {
    encoding: "utf8",
    cwd: ROOT,
    env: { ...process.env, PYTHONPATH: ROOT },
    input: JSON.stringify({
      master: master && fs.existsSync(master) ? master : null,
      jd,
      title,
      company,
      job_id: jobId,
    }),
    maxBuffer: 4 * 1024 * 1024,
  });

  const line = (run.stdout || "").trim().split("\n").filter(Boolean).pop() || "";
  let parsed;
  try {
    parsed = JSON.parse(line);
  } catch (_) {
    return {
      ok: false,
      error: (run.stderr || run.stdout || "tailor_failed").slice(0, 400),
      status: run.status,
    };
  }
  if (!parsed?.ok || !parsed.out) {
    return { ok: false, error: parsed?.error || "tailor_output_missing", raw: parsed };
  }
  return parsed;
}

module.exports = {
  tailorResumeForJob,
  skillText,
};

if (require.main === module) {
  const master =
    process.argv[2] || path.join(ROOT, "resumes", "Rafi_Resume.docx");
  const r = tailorResumeForJob({
    master,
    title: process.argv[3] || "Solutions Architect .NET Azure",
    company: process.argv[4] || "Example",
    description:
      process.argv[5] ||
      "Looking for Solutions Architect with .NET Core, Azure, Microservices, Kafka",
    skills: ".NET, Azure, Microservices",
    jobId: "demo",
  });
  console.log(JSON.stringify(r, null, 2));
  process.exit(r.ok ? 0 : 1);
}
