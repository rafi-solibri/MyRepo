/**
 * Shared constants for Indeed / Instahyre agents.
 */
"use strict";
const fs = require("fs");
const RESUME_CANDIDATES = [
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
  EXPECTED_CTC_LPA: 60,
  CURRENT_CTC_LPA: 52,
  CHROME_INDEED: process.env.INDEED_CHROME_PROFILE || "/home/ubuntu/chrome-indeed-profile",
  CHROME_INSTAHYRE: process.env.INSTAHYRE_CHROME_PROFILE || "/home/ubuntu/chrome-instahyre-profile",
};

if (require.main === module) {
  const resume = findResume();
  console.log(JSON.stringify({ resume }, null, 2));
  if (!resume) process.exit(2);
}
