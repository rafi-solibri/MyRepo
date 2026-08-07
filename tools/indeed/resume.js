/**
 * Shared constants for Indeed agents.
 */
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
  CHROME_INDEED: process.env.INDEED_CHROME_PROFILE || "/home/ubuntu/chrome-indeed-profile",
  CHROME_INSTAHYRE: process.env.INSTAHYRE_CHROME_PROFILE || "/home/ubuntu/chrome-instahyre-profile",
};

if (require.main === module) {
  const resume = findResume();
  console.log(JSON.stringify({ resume, label: RESUME_LABEL }, null, 2));
  if (!resume) process.exit(2);
}
