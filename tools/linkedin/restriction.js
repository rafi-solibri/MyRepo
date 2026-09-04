/**
 * LinkedIn temporary-restriction memory (Node mirror of restriction.py).
 *
 * Used by Foundit (and any Node runner) so LinkedIn Easy Apply redirects
 * are skipped while a known account restriction is still active — avoids
 * a second portal re-hitting LinkedIn and extending the ban.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const REPO_ROOT = path.resolve(__dirname, "../..");

function flagPaths() {
  return [
    process.env.LINKEDIN_RESTRICTION_FLAG || "/tmp/linkedin-restriction-until.json",
    "/opt/cursor/artifacts/linkedin-restriction-until.json",
    process.env.LINKEDIN_RESTRICTION_REPO_FLAG ||
      path.join(REPO_ROOT, ".portal-sessions", "linkedin-restriction-until.json"),
  ];
}

function readRestrictionMemory() {
  for (const p of flagPaths()) {
    try {
      if (!fs.existsSync(p)) continue;
      const data = JSON.parse(fs.readFileSync(p, "utf8"));
      if (data && typeof data === "object") return data;
    } catch (_) {
      /* try next */
    }
  }
  return null;
}

function linkedinBlockedUntil() {
  const mem = readRestrictionMemory();
  if (!mem || !mem.lift_utc) return null;
  const lift = new Date(String(mem.lift_utc).replace(/Z$/, "+00:00"));
  if (Number.isNaN(lift.getTime())) return null;
  // 30s buffer after lift (parity with Python helper).
  if (Date.now() + 30_000 < lift.getTime()) return lift;
  return null;
}

/**
 * @returns {null | { reason: string, lift_utc: string, seconds_until_lift: number, hint: string }}
 */
function shouldSkipLinkedinForRestriction() {
  const lift = linkedinBlockedUntil();
  if (!lift) return null;
  const secs = Math.max(0, Math.floor((lift.getTime() - Date.now()) / 1000));
  return {
    reason: "linkedin_temporarily_restricted",
    lift_utc: lift.toISOString(),
    seconds_until_lift: secs,
    hint: "Wait until lift_utc; do not open linkedin.com from other portals (profile-data volume ban).",
  };
}

module.exports = {
  flagPaths,
  readRestrictionMemory,
  linkedinBlockedUntil,
  shouldSkipLinkedinForRestriction,
};
