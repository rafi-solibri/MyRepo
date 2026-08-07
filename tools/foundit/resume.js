/** Foundit: resume path + never use canJobApply as dry-run (it submits). */
"use strict";
const {
  findResume,
  resumeUploadPath,
  CANONICAL_NAME,
  RESUME_LABEL,
  LEGACY_ALIASES,
} = require("../resume_paths");

const RESUME_CANDIDATES = [
  `/workspace/resumes/${CANONICAL_NAME}`,
  `/home/ubuntu/resumes/${CANONICAL_NAME}`,
  `/home/ubuntu/Documents/${CANONICAL_NAME}`,
  ...LEGACY_ALIASES.map((n) => `/workspace/resumes/${n}`),
];

module.exports = {
  findResume,
  resumeUploadPath,
  RESUME_CANDIDATES,
  RESUME_LABEL,
  CANONICAL_NAME,
  EXPECTED_CTC_LPA: 65,
  CURRENT_CTC_LPA: 52,
  /** Eligibility: use userJobInfo / applicationStatus — NEVER canJobApply for dry-run. */
  FORBIDDEN_DRY_RUN: "/home/api/canJobApply",
  CHROME_PROFILE: process.env.FOUNDIT_CHROME_PROFILE || "/home/ubuntu/.config/chrome-foundit",
};
if (require.main === module) console.log(JSON.stringify({ resume: findResume(), label: RESUME_LABEL }));
