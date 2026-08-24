/**
 * Hirist resume path helpers (shared with other portals).
 */
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
    try {
      if (fs.existsSync(p) && fs.statSync(p).size > 1000) return p;
    } catch {
      /* ignore */
    }
  }
  return null;
}

module.exports = {
  findResume,
  RESUME_CANDIDATES,
  EXPECTED_CTC_LPA: 65,
  CURRENT_CTC_LPA: 52,
  CHROME_HIRIST:
    process.env.HIRIST_CHROME_PROFILE ||
    PROFILES.hirist ||
    "/home/ubuntu/chrome-hirist-profile",
};

if (require.main === module) {
  const resume = findResume();
  console.log(
    JSON.stringify(
      {
        resume,
        CHROME_HIRIST: module.exports.CHROME_HIRIST,
      },
      null,
      2
    )
  );
  if (!resume) process.exit(2);
}
