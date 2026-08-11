#!/usr/bin/env node
/** Foundit: resume path + never use canJobApply as dry-run (it submits). */
"use strict";
const fs = require("fs");
const path = require("path");
const { PROFILES } = require("../chrome_session");

const REPO_RESUMES = path.join(__dirname, "..", "..", "resumes");
const RESUME_CANDIDATES = [
  path.join(REPO_RESUMES, "Rafi_Resume.docx"),
  path.join(process.cwd(), "resumes", "Rafi_Resume.docx"),
  "/workspace/resumes/Rafi_Resume.docx",
  "/home/ubuntu/resumes/Rafi_Resume.docx",
  "/home/ubuntu/Documents/Rafi_Resume.docx",
];
function findResume() {
  for (const p of RESUME_CANDIDATES) {
    if (fs.existsSync(p) && fs.statSync(p).size > 1000) return p;
  }
  return null;
}
module.exports = {
  findResume,
  RESUME_CANDIDATES,
  EXPECTED_CTC_LPA: 65,
  CURRENT_CTC_LPA: 52,
  /** Eligibility: use userJobInfo / applicationStatus — NEVER canJobApply for dry-run. */
  FORBIDDEN_DRY_RUN: "/home/api/canJobApply",
  CHROME_PROFILE:
    process.env.FOUNDIT_CHROME_PROFILE ||
    PROFILES.foundit ||
    "/home/ubuntu/.config/chrome-foundit",
  /** Shared Raven/Falcon eligibility helpers (title+skills .NET, title exp bands, etc.). */
  filters: () => require("./filters"),
};
if (require.main === module) console.log(JSON.stringify({ resume: findResume() }));
