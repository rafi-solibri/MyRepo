#!/usr/bin/env node
/** Shared Chrome CDP profile paths + auth cookie checks for job portals. */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const HOME = process.env.HOME || os.homedir();

const PROFILES = {
  source: process.env.CHROME_SOURCE_PROFILE || path.join(HOME, ".config/google-chrome"),
  linkedin: process.env.LINKEDIN_CHROME_PROFILE || "/home/ubuntu/chrome-cdp-profile",
  naukri: process.env.NAUKRI_CHROME_PROFILE || "/home/ubuntu/.naukri-chrome-profile",
  foundit: process.env.FOUNDIT_CHROME_PROFILE || "/home/ubuntu/.config/chrome-foundit",
  cutshort: process.env.CUTSHORT_CHROME_PROFILE || "/home/ubuntu/chrome-cutshort-profile",
  instahyre: process.env.INSTAHYRE_CHROME_PROFILE || "/home/ubuntu/chrome-instahyre-profile",
  indeed: process.env.INDEED_CHROME_PROFILE || "/home/ubuntu/chrome-indeed-profile",
};

const AUTH_COOKIES = {
  linkedin: ["li_at"],
  naukri: ["nauk_rt", "nauk_at"],
  foundit: ["MSSOAT"],
  cutshort: ["cutshort_authentication"],
  instahyre: ["sessionid"],
  indeed: ["__Secure-PassportAuthProxy-BearerToken", "CTK"],
};

function cookieNames(profileRoot) {
  const db = path.join(profileRoot, "Default", "Cookies");
  if (!fs.existsSync(db)) return [];
  const tmp = path.join(os.tmpdir(), `cookies-check-${process.pid}.db`);
  fs.copyFileSync(db, tmp);
  try {
    // Prefer python sqlite (always present); avoid adding better-sqlite3 dep.
    const out = execFileSync(
      "python3",
      ["-c", `import sqlite3; c=sqlite3.connect(${JSON.stringify(tmp)}); print("\\n".join(r[0] for r in c.execute("select name from cookies"))); c.close()`],
      { encoding: "utf8" }
    );
    return out.split("\n").map((s) => s.trim()).filter(Boolean);
  } catch {
    return [];
  } finally {
    try {
      fs.unlinkSync(tmp);
    } catch {
      /* ignore */
    }
  }
}

function hasAuth(portal, profileRoot = PROFILES[portal] || PROFILES.source) {
  const need = AUTH_COOKIES[portal] || [];
  const names = new Set(cookieNames(profileRoot));
  return need.some((n) => names.has(n));
}

function syncSessions() {
  const script = path.join(__dirname, "..", "scripts", "sync-chrome-sessions.sh");
  execFileSync("bash", [script], { stdio: "inherit" });
}

function statusReport() {
  const sourceNames = new Set(cookieNames(PROFILES.source));
  const report = { source: PROFILES.source, portals: {} };
  for (const [portal, need] of Object.entries(AUTH_COOKIES)) {
    const dest = PROFILES[portal];
    const destNames = new Set(cookieNames(dest));
    report.portals[portal] = {
      profile: dest,
      sourceHasAuth: need.some((n) => sourceNames.has(n)),
      destHasAuth: need.some((n) => destNames.has(n)),
      need,
    };
  }
  return report;
}

module.exports = { PROFILES, AUTH_COOKIES, cookieNames, hasAuth, syncSessions, statusReport };

if (require.main === module) {
  const cmd = process.argv[2] || "status";
  if (cmd === "sync") {
    syncSessions();
  }
  console.log(JSON.stringify(statusReport(), null, 2));
}
