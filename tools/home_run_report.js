#!/usr/bin/env node
/**
 * Normalize / write home-local daily run JSON for any portal.
 *
 * Schema (counts used in daily mail):
 *   applied, external, rejected, blocked, skipped, seen
 *
 * Usage:
 *   node tools/home_run_report.js write --portal linkedin --in raw.json --out report.json
 *   node tools/home_run_report.js empty --portal naukri --reason "login" --out report.json
 */
const fs = require("fs");
const path = require("path");
const os = require("os");

function todayDate(d = new Date()) {
  return d.toISOString().slice(0, 10);
}

function asArray(v) {
  return Array.isArray(v) ? v : [];
}

function pickList(obj, keys) {
  for (const k of keys) {
    if (Array.isArray(obj[k])) return obj[k];
  }
  return [];
}

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i === -1 || i + 1 >= process.argv.length) return null;
  return process.argv[i + 1];
}

function defaultOut(portal) {
  const name = `${portal}-daily-run.json`;
  const { artifactPaths } = require("./artifact_path");
  return artifactPaths(name)[0];
}

function normalize(raw = {}, opts = {}) {
  const portal = opts.portal || raw.portal || "unknown";
  const applied = pickList(raw, ["applied", "submitted", "applications"]);
  const external = pickList(raw, [
    "external",
    "externalCompleted",
    "companySite",
    "ats",
  ]);
  const rejected = pickList(raw, ["rejected", "declined", "failed"]);
  const blocked = pickList(raw, ["blocked", "blockers"]);
  const skipped = pickList(raw, ["skipped", "skips"]);
  const seen = pickList(raw, ["seen", "scanned"]);

  const countsIn = raw.counts && typeof raw.counts === "object" ? raw.counts : {};
  const counts = {
    applied: Number(countsIn.applied ?? applied.length) || 0,
    external:
      Number(countsIn.external ?? countsIn.externalCompleted ?? external.length) ||
      0,
    rejected: Number(countsIn.rejected ?? rejected.length) || 0,
    blocked: Number(countsIn.blocked ?? blocked.length) || 0,
    skipped: Number(countsIn.skipped ?? skipped.length) || 0,
    seen: Number(countsIn.seen ?? seen.length) || 0,
  };

  const blockerSummary =
    raw.blockerSummary ||
    raw.blocker ||
    raw.reason ||
    (blocked[0] && (blocked[0].reason || blocked[0].message)) ||
    null;

  const finishedAt = raw.finishedAt || opts.finishedAt || new Date().toISOString();
  const date =
    raw.date ||
    (typeof finishedAt === "string" && finishedAt.slice(0, 10)) ||
    todayDate();

  return {
    portal,
    source: raw.source || opts.source || "home-local",
    date,
    startedAt: raw.startedAt || opts.startedAt || null,
    finishedAt,
    host: raw.host || opts.host || os.hostname(),
    ok:
      raw.ok !== undefined
        ? Boolean(raw.ok)
        : counts.blocked === 0 || counts.applied > 0,
    counts,
    applied,
    external,
    rejected,
    blocked,
    skipped,
    seen,
    blockerSummary,
    notes: asArray(raw.notes),
    preflight: raw.preflight || null,
    logPath: raw.logPath || opts.logPath || null,
  };
}

function writeReport(report, outPath) {
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2) + "\n");
  return outPath;
}

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function main() {
  const cmd = process.argv[2] || "normalize";
  const portal = (argValue("--portal") || "unknown").toLowerCase();
  const out = argValue("--out") || defaultOut(portal);
  const source = argValue("--source") || "home-local";
  const reason = argValue("--reason");
  const logPath = argValue("--log");

  if (cmd === "empty") {
    const report = normalize(
      {
        portal,
        ok: false,
        blockerSummary: reason || "no_result",
        blocked: reason ? [{ reason }] : [],
        counts: {
          applied: 0,
          external: 0,
          rejected: 0,
          blocked: reason ? 1 : 0,
          skipped: 0,
          seen: 0,
        },
      },
      { portal, source, logPath },
    );
    writeReport(report, out);
    console.log(JSON.stringify(report, null, 2));
    return;
  }

  const inPath = argValue("--in");
  let raw = {};
  if (inPath) {
    raw = readJson(inPath);
  } else if (cmd === "normalize" && !process.stdin.isTTY) {
    raw = JSON.parse(fs.readFileSync(0, "utf8"));
  } else if (fs.existsSync(defaultOut(portal))) {
    raw = readJson(defaultOut(portal));
  } else {
    console.error("No input JSON. Pass --in <path> or pipe JSON.");
    process.exit(2);
  }

  const report = normalize(raw, { portal, source, logPath });
  if (cmd === "write" || argValue("--out") || cmd === "normalize") {
    writeReport(report, out);
  }
  console.log(JSON.stringify(report, null, 2));
}

main();
