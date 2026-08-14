/**
 * Resolve and dual-write daily artifact JSON.
 *
 * On Windows home, Node maps "/opt/..." → "C:\opt\...", while Git Bash maps
 * "/opt/..." → "<Git>/opt/...". Always also write repo `artifacts/` so
 * portal-home-daily / publish-home-result see today's file.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const REPO_ROOT = path.join(__dirname, "..");

function cloudArtifactsDir() {
  return process.env.CURSOR_ARTIFACTS_DIR || path.join(path.sep, "opt", "cursor", "artifacts");
}

function repoArtifactsDir() {
  return path.join(REPO_ROOT, "artifacts");
}

/** Primary + mirror paths for a report filename (e.g. naukri-daily-apply.json). */
function artifactPaths(filename) {
  const name = String(filename || "").replace(/^[/\\]+/, "");
  const cloud = path.join(cloudArtifactsDir(), name);
  const repo = path.join(repoArtifactsDir(), name);
  const envKey = process.env.ARTIFACT_REPORT_PATH;
  if (envKey) return [envKey, repo].filter((p, i, a) => a.indexOf(p) === i);
  if (path.resolve(cloud) === path.resolve(repo)) return [repo];
  return [cloud, repo];
}

function writeArtifactJson(filename, data) {
  const body = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  const written = [];
  for (const p of artifactPaths(filename)) {
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, body);
    written.push(p);
  }
  return written;
}

module.exports = {
  REPO_ROOT,
  cloudArtifactsDir,
  repoArtifactsDir,
  artifactPaths,
  writeArtifactJson,
};
