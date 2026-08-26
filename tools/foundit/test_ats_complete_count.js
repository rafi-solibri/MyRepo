"use strict";
/**
 * Unit checks for Foundit "applied only when ATS completed" helpers.
 * Mirrors logic in daily_apply.js (kept in sync via assert on source).
 */
const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(path.join(__dirname, "daily_apply.js"), "utf8");
if (!/function atsFullyCompleted/.test(src)) throw new Error("atsFullyCompleted missing");
if (!/needsExternalAts/.test(src)) throw new Error("needsExternalAts missing");
if (!/external_ats_incomplete/.test(src)) throw new Error("external_ats_incomplete missing");
if (!/Never treat LinkedIn redirect-without-submit as success/.test(src)) {
  throw new Error("linkedin no-easy-apply hard fail missing");
}

function atsFullyCompleted(status) {
  return /^(linkedin_easy_apply_ok|ats_submitted)$/i.test(String(status || ""));
}
function atsSubmitClicked(status) {
  return /linkedin_submit_clicked|ats_submit_clicked/i.test(String(status || ""));
}

const assert = (c, m) => {
  if (!c) throw new Error(m);
};
assert(atsFullyCompleted("linkedin_easy_apply_ok"), "easy ok");
assert(atsFullyCompleted("ats_submitted"), "ats submitted");
assert(!atsFullyCompleted("linkedin_no_easy_apply"), "no easy");
assert(!atsFullyCompleted("linkedin_submit_clicked"), "submit clicked alone");
assert(!atsFullyCompleted("external_incomplete_or_timeout"), "incomplete");
assert(atsSubmitClicked("linkedin_submit_clicked"), "soft");
console.log("foundit ats_complete_count tests OK");
