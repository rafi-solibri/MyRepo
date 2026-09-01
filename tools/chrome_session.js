#!/usr/bin/env node
/** Shared Chrome CDP profile paths + auth cookie checks for job portals. */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const HOME = process.env.HOME || os.homedir();
const IS_WIN =
  process.platform === "win32" ||
  process.env.OS === "Windows_NT" ||
  Boolean(process.env.MSYSTEM);

function windowsLocalAppData() {
  if (process.env.LOCALAPPDATA) return process.env.LOCALAPPDATA;
  const up = process.env.USERPROFILE || HOME;
  return path.join(up, "AppData", "Local");
}

function defaultSourceProfile() {
  if (process.env.CHROME_SOURCE_PROFILE) return process.env.CHROME_SOURCE_PROFILE;
  if (IS_WIN) {
    return path.join(windowsLocalAppData(), "Google", "Chrome", "User Data");
  }
  return path.join(HOME, ".config", "google-chrome");
}

function useSystemChromeProfile() {
  // Windows home: App-Bound Encryption prevents copying Default cookies into a
  // separate --user-data-dir. Reuse the real Chrome User Data so sessions work.
  if (process.env.CHROME_CDP_MODE) {
    return process.env.CHROME_CDP_MODE === "system";
  }
  return IS_WIN;
}

function defaultPortalProfile(portal) {
  const envKey = {
    linkedin: "LINKEDIN_CHROME_PROFILE",
    naukri: "NAUKRI_CHROME_PROFILE",
    foundit: "FOUNDIT_CHROME_PROFILE",
    cutshort: "CUTSHORT_CHROME_PROFILE",
    instahyre: "INSTAHYRE_CHROME_PROFILE",
    indeed: "INDEED_CHROME_PROFILE",
    hirist: "HIRIST_CHROME_PROFILE",
    linkedin_alt: "LINKEDIN_CHROME_PROFILE_ALT",
    hitechcity: "HITECHCITY_CHROME_PROFILE",
  }[portal];
  if (envKey && process.env[envKey]) return process.env[envKey];

  if (useSystemChromeProfile()) {
    // Same absolute path as interactive Chrome → ABE cookies decrypt.
    return defaultSourceProfile();
  }

  if (IS_WIN) {
    const root = path.join(HOME, ".cursor", "chrome-cdp-profiles");
    // Prefer linkedin-alt when primary CDP profile has no li_at name but alt does.
    // Live session may still need headed login (ABE / stale encrypted blobs).
    if (portal === "linkedin" || portal === "hitechcity") {
      const primary = path.join(root, "linkedin");
      const alt = path.join(root, "linkedin-alt");
      // cookieNames is hoisted; avoid AUTH_COOKIES here (defined after PROFILES).
      const primaryOk = cookieNames(primary).includes("li_at");
      const altOk = cookieNames(alt).includes("li_at");
      if (!primaryOk && altOk) return alt;
      return primary;
    }
    return path.join(root, portal === "linkedin_alt" ? "linkedin-alt" : portal);
  }

  const linux = {
    linkedin: "/home/ubuntu/chrome-cdp-profile",
    naukri: "/home/ubuntu/.naukri-chrome-profile",
    foundit: "/home/ubuntu/.config/chrome-foundit",
    cutshort: "/home/ubuntu/chrome-cutshort-profile",
    instahyre: "/home/ubuntu/chrome-instahyre-profile",
    indeed: "/home/ubuntu/chrome-indeed-profile",
    hirist: "/home/ubuntu/chrome-hirist-profile",
    linkedin_alt: "/home/ubuntu/chrome-linkedin-profile",
    hitechcity: "/home/ubuntu/chrome-cdp-profile",
  };
  return linux[portal];
}

const PROFILES = {
  source: defaultSourceProfile(),
  linkedin: defaultPortalProfile("linkedin"),
  // Hitech City campus flow reuses LinkedIn CDP (careers browse + referrals).
  hitechcity:
    process.env.HITECHCITY_CHROME_PROFILE ||
    process.env.LINKEDIN_CHROME_PROFILE ||
    defaultPortalProfile("hitechcity"),
  naukri: defaultPortalProfile("naukri"),
  foundit: defaultPortalProfile("foundit"),
  cutshort: defaultPortalProfile("cutshort"),
  instahyre: defaultPortalProfile("instahyre"),
  indeed: defaultPortalProfile("indeed"),
  hirist: defaultPortalProfile("hirist"),
};

const AUTH_COOKIES = {
  linkedin: ["li_at"],
  hitechcity: ["li_at"],
  naukri: ["nauk_rt", "nauk_at"],
  foundit: ["MSSOAT"],
  cutshort: ["cutshort_authentication"],
  instahyre: ["sessionid"],
  indeed: ["__Secure-PassportAuthProxy-BearerToken"],
  // Hirist seeker session is `hirist_seeker_enc` (older builds used `token` + XSRF-TOKEN).
  hirist: ["hirist_seeker_enc", "token"],
};

function cookiesDbPath(profileRoot) {
  const candidates = [
    path.join(profileRoot, "Default", "Network", "Cookies"),
    path.join(profileRoot, "Default", "Cookies"),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return candidates[0];
}

function resolvePython() {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  const candidates = IS_WIN
    ? ["py", "python", "python3", "C:\\Python314\\python.exe", "C:\\Python313\\python.exe"]
    : ["python3", "python"];
  for (const bin of candidates) {
    try {
      const args = bin === "py" ? ["-3", "-c", "print(1)"] : ["-c", "print(1)"];
      execFileSync(bin, args, { stdio: "ignore" });
      return bin;
    } catch {
      /* try next */
    }
  }
  return "python3";
}

function cookieNames(profileRoot) {
  const db = cookiesDbPath(profileRoot);
  if (!fs.existsSync(db)) return [];
  const tmp = path.join(os.tmpdir(), `cookies-check-${process.pid}-${Date.now()}.db`);
  try {
    fs.copyFileSync(db, tmp);
  } catch (err) {
    // Chrome locks Network/Cookies while running — caller must close Chrome or kill for sync.
    return [];
  }
  try {
    const py = resolvePython();
    const pyArgs =
      py === "py"
        ? [
            "-3",
            "-c",
            `import sqlite3; c=sqlite3.connect(${JSON.stringify(tmp)}); print("\\n".join(r[0] for r in c.execute("select name from cookies"))); c.close()`,
          ]
        : [
            "-c",
            `import sqlite3; c=sqlite3.connect(${JSON.stringify(tmp)}); print("\\n".join(r[0] for r in c.execute("select name from cookies"))); c.close()`,
          ];
    const out = execFileSync(py, pyArgs, { encoding: "utf8" });
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

function portalStatus(portal) {
  if (!AUTH_COOKIES[portal] || !PROFILES[portal]) {
    return {
      ok: false,
      portal,
      reason: "unknown_portal",
      knownPortals: Object.keys(AUTH_COOKIES),
    };
  }
  const sourceNames = new Set(cookieNames(PROFILES.source));
  const dest = PROFILES[portal];
  const destNames = new Set(cookieNames(dest));
  const need = AUTH_COOKIES[portal];
  const sourceHasAuth = need.some((n) => sourceNames.has(n));
  const destHasAuth = need.some((n) => destNames.has(n));
  const sourceDb = cookiesDbPath(PROFILES.source);
  const sourceLocked =
    fs.existsSync(sourceDb) && sourceNames.size === 0 && !destHasAuth;
  let reason = "login_required_sync_desktop_chrome_and_save_snapshot";
  if (destHasAuth) {
    // Name presence in SQLite ≠ live decryptable session on Windows ABE.
    reason = IS_WIN
      ? "sqlite_auth_cookie_present_verify_live_cdp"
      : "ok";
  } else if (sourceLocked) reason = "chrome_cookies_locked_close_chrome_and_resync";
  else if (IS_WIN)
    reason =
      "windows_abe_one_time_login_required_run_home_headed_login_sh";
  return {
    ok: destHasAuth,
    portal,
    profile: dest,
    source: PROFILES.source,
    sourceHasAuth,
    destHasAuth,
    sourceCookiesDb: sourceDb,
    sourcePossiblyLocked: sourceLocked,
    need,
    isWindows: IS_WIN,
    reason,
    liveHint: IS_WIN
      ? "bash scripts/home-headed-login.sh " +
        (portal === "hitechcity" ? "linkedin" : portal) +
        (portal === "hitechcity" ? "  # or: bash scripts/home-headed-login.sh hitechcity" : "")
      : undefined,
  };
}

/** Live CDP waiters — SQLite cookie names are unreliable on Windows ABE / locked DB. */
const LIVE_CDP_WAITERS = {
  linkedin: path.join(__dirname, "linkedin", "wait_for_cdp_login.js"),
  hitechcity: path.join(__dirname, "linkedin", "wait_for_cdp_login.js"),
  cutshort: path.join(__dirname, "cutshort", "wait_for_cdp_login.js"),
  foundit: path.join(__dirname, "foundit", "wait_for_cdp_login.js"),
  instahyre: path.join(__dirname, "instahyre", "wait_for_cdp_login.js"),
  naukri: path.join(__dirname, "naukri", "wait_for_cdp_login.js"),
  hirist: path.join(__dirname, "hirist", "wait_for_cdp_login.js"),
  indeed: path.join(__dirname, "indeed", "wait_for_cdp_login.js"),
};

/**
 * Cookie-name presence can outlive JWT/OauthExpires (Indeed 2026-09-01).
 * Optional Chrome probe via tools/portal_auth_freshness.py.
 */
function checkAuthFreshness(portal) {
  if (process.env.PORTAL_AUTH_FRESHNESS === "0") return null;
  const script = path.join(__dirname, "portal_auth_freshness.py");
  if (!fs.existsSync(script)) return null;
  // Fast path: only Indeed/Foundit currently decode exp claims. Others skip chrome
  // unless PORTAL_AUTH_FRESHNESS_ALL=1 (slower — launches headless Chrome).
  const heavy = new Set(["indeed", "foundit"]);
  if (!heavy.has(portal) && process.env.PORTAL_AUTH_FRESHNESS_ALL !== "1") {
    return null;
  }
  try {
    const py = resolvePython();
    const args =
      py === "py"
        ? ["-3", script, "check", portal]
        : [script, "check", portal];
    const bin = py === "py" ? "py" : py;
    const out = execFileSync(bin, args, {
      encoding: "utf8",
      timeout: Number(process.env.PORTAL_AUTH_FRESHNESS_TIMEOUT_MS || 90000),
      env: { ...process.env },
    });
    const start = out.lastIndexOf("{");
    if (start < 0) return { raw: out.slice(0, 300) };
    return JSON.parse(out.slice(start));
  } catch (err) {
    const stdout = String((err && err.stdout) || "");
    const stderr = String((err && err.stderr) || "");
    const blob = `${stdout}\n${stderr}`;
    const start = blob.lastIndexOf("{");
    if (start >= 0) {
      try {
        return JSON.parse(blob.slice(start));
      } catch {
        /* fall through */
      }
    }
    return {
      ok: false,
      portal,
      reason: "freshness_check_error",
      error: String((err && err.message) || err).slice(0, 240),
    };
  }
}

function runLiveCdpWaiter(portal, result) {
  const waiter = LIVE_CDP_WAITERS[portal];
  if (!waiter || !fs.existsSync(waiter)) return result;
  // Only when CDP is already up — launching Chrome belongs to launch-chrome-cdp.sh.
  try {
    execFileSync("curl", ["-fsS", "http://127.0.0.1:9222/json/version"], {
      stdio: "ignore",
      timeout: 3000,
    });
  } catch {
    result.liveSkipped = "cdp_not_up";
    return result;
  }
  try {
    execFileSync(process.execPath, [waiter], {
      stdio: ["ignore", "pipe", "pipe"],
      timeout: 45000,
      env: { ...process.env, NODE_PATH: path.join(__dirname, "node_modules") },
    });
    result.ok = true;
    result.destHasAuth = true;
    result.reason = `live_cdp_${portal}_ok`;
    result.liveVerified = true;
  } catch (err) {
    result.ok = false;
    result.liveVerified = false;
    const stdout = String((err && err.stdout) || "");
    const stderr = String((err && err.stderr) || "");
    const blob = `${stdout}\n${stderr}`;
    result.liveError = blob.slice(0, 400);
    let liveJson = null;
    for (const line of blob.split(/\r?\n/).reverse()) {
      const t = line.trim();
      if (!t.startsWith("{") || !t.includes('"ok"')) continue;
      try {
        liveJson = JSON.parse(t);
        break;
      } catch {
        /* keep scanning */
      }
    }
    if (liveJson && liveJson.reason) {
      result.reason = String(liveJson.reason);
      if (liveJson.url) result.liveUrl = String(liveJson.url).slice(0, 240);
    } else {
      result.reason = `${portal}_login_required`;
    }
  }
  return result;
}

function checkPortal(portal) {
  const result = portalStatus(portal);
  // Windows ABE / locked Cookies DB: SQLite names lie while Chrome is open.
  // Prefer a live CDP probe when the portal check would false-fail.
  if (
    !result.ok &&
    (result.sourcePossiblyLocked || result.isWindows)
  ) {
    runLiveCdpWaiter(portal, result);
  }

  // Every run: when names look OK, still verify JWT/OauthExpires for Indeed/Foundit.
  if (result.ok || process.env.PORTAL_AUTH_FRESHNESS_FORCE === "1") {
    const fresh = checkAuthFreshness(portal);
    if (fresh) {
      result.freshness = fresh;
      if (fresh.expired || fresh.reason === "indeed_session_expired" || fresh.reason === "foundit_session_expired") {
        result.ok = false;
        result.reason = String(fresh.reason || `${portal}_session_expired`);
        result.hint =
          fresh.hint ||
          `Session expired — bash scripts/home-headed-login.sh ${portal === "hitechcity" ? "linkedin" : portal} && bash scripts/refresh-portal-session-seed.sh ${portal === "hitechcity" ? "linkedin" : portal}`;
      } else if (fresh.ok === false && fresh.reason && !String(fresh.reason).includes("unverified") && !String(fresh.reason).includes("skipped")) {
        // Hard login_required from value probe
        if (fresh.reason.endsWith("_login_required")) {
          result.ok = false;
          result.reason = fresh.reason;
        }
      }
    }
  }

  // Optional: when CDP already running, live-verify even if SQLite names passed
  // (catches server-invalidated sessions). Default on for cron via env.
  if (
    result.ok &&
    process.env.PORTAL_LIVE_LOGIN_CHECK === "1" &&
    LIVE_CDP_WAITERS[portal]
  ) {
    runLiveCdpWaiter(portal, result);
  }

  console.log(JSON.stringify(result, null, 2));
  if (result.reason === "unknown_portal") return 2;
  return result.ok ? 0 : 3;
}

function syncSessions() {
  const script = path.join(__dirname, "..", "scripts", "sync-chrome-sessions.sh");
  execFileSync("bash", [script], { stdio: "inherit" });
}

function statusReport() {
  const sourceNames = new Set(cookieNames(PROFILES.source));
  const report = {
    source: PROFILES.source,
    sourceCookiesDb: cookiesDbPath(PROFILES.source),
    isWindows: IS_WIN,
    portals: {},
  };
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

module.exports = {
  PROFILES,
  AUTH_COOKIES,
  LIVE_CDP_WAITERS,
  cookiesDbPath,
  cookieNames,
  hasAuth,
  portalStatus,
  checkPortal,
  checkAuthFreshness,
  runLiveCdpWaiter,
  syncSessions,
  statusReport,
  resolvePython,
  IS_WIN,
  useSystemChromeProfile,
  defaultSourceProfile,
};

if (require.main === module) {
  const cmd = process.argv[2] || "status";
  if (cmd === "sync") {
    syncSessions();
  } else if (cmd === "check") {
    process.exit(checkPortal(process.argv[3] || ""));
  } else if (cmd === "path") {
    const key = process.argv[3] || "source";
    const p = PROFILES[key];
    if (!p) {
      console.error(`Unknown profile key: ${key}`);
      process.exit(2);
    }
    process.stdout.write(p);
  } else if (cmd === "cookies-db") {
    const key = process.argv[3] || "source";
    const root = PROFILES[key];
    if (!root) {
      console.error(`Unknown profile key: ${key}`);
      process.exit(2);
    }
    process.stdout.write(cookiesDbPath(root));
  } else {
    console.log(JSON.stringify(statusReport(), null, 2));
  }
}
