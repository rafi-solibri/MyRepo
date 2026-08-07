/** Shared resume path helpers for Node portal automations. */
"use strict";

const fs = require("fs");
const path = require("path");

const CANONICAL_NAME = "Rafi_Resume_Technical_Architect.docx";
const LEGACY_ALIASES = ["Rafi_Resume.docx", "Rafi_Resume_Architect.docx"];
const RESUME_LABEL = "Rafi_Resume_Technical_Architect";

const SEARCH_DIRS = [
  "/workspace/resumes",
  path.join(__dirname, "..", "resumes"),
  "/home/ubuntu/resumes",
  "/home/ubuntu/Documents",
  "/home/ubuntu/Downloads",
  "/opt/cursor/artifacts",
  path.join(process.cwd(), "resumes"),
  process.cwd(),
];

function findResume() {
  for (const name of [CANONICAL_NAME, ...LEGACY_ALIASES]) {
    for (const dir of SEARCH_DIRS) {
      const p = path.join(dir, name);
      try {
        if (fs.existsSync(p) && fs.statSync(p).size > 1000) return p;
      } catch (_) {
        /* ignore */
      }
    }
  }
  return null;
}

function ensureResumeAliases() {
  const src = findResume();
  if (!src) {
    throw new Error(
      `Missing ${CANONICAL_NAME}. Expected under /workspace/resumes/ (run scripts/bootstrap-job-assets.sh).`
    );
  }
  const canonical =
    path.basename(src) === CANONICAL_NAME
      ? src
      : path.join(path.dirname(src), CANONICAL_NAME);
  if (src !== canonical) fs.copyFileSync(src, canonical);

  for (const dir of [
    "/workspace/resumes",
    "/home/ubuntu/resumes",
    "/home/ubuntu/Documents",
    "/home/ubuntu/Downloads",
    "/opt/cursor/artifacts",
  ]) {
    try {
      fs.mkdirSync(dir, { recursive: true });
      for (const name of [CANONICAL_NAME, ...LEGACY_ALIASES]) {
        const dest = path.join(dir, name);
        fs.copyFileSync(canonical, dest);
      }
    } catch (_) {
      /* ignore unwritable dirs */
    }
  }
  return canonical;
}

function resumeUploadPath() {
  return ensureResumeAliases();
}

module.exports = {
  CANONICAL_NAME,
  LEGACY_ALIASES,
  RESUME_LABEL,
  SEARCH_DIRS,
  findResume,
  ensureResumeAliases,
  resumeUploadPath,
};

if (require.main === module) {
  const p = ensureResumeAliases();
  console.log(p);
  console.log("label:", RESUME_LABEL);
  console.log("size:", fs.statSync(p).size);
}
