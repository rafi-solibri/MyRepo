#!/usr/bin/env node
"use strict";

const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const {
  shouldSkipLinkedinForRestriction,
  linkedinBlockedUntil,
} = require("./restriction");

function withTempFlag(liftIso, fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "li-restr-"));
  const flag = path.join(dir, "flag.json");
  const prev = process.env.LINKEDIN_RESTRICTION_FLAG;
  const prevRepo = process.env.LINKEDIN_RESTRICTION_REPO_FLAG;
  process.env.LINKEDIN_RESTRICTION_FLAG = flag;
  process.env.LINKEDIN_RESTRICTION_REPO_FLAG = path.join(dir, "missing-repo.json");
  fs.writeFileSync(
    flag,
    JSON.stringify({
      lift_utc: liftIso,
      kind: "account_temporarily_restricted",
    }),
    "utf8"
  );
  try {
    fn();
  } finally {
    if (prev === undefined) delete process.env.LINKEDIN_RESTRICTION_FLAG;
    else process.env.LINKEDIN_RESTRICTION_FLAG = prev;
    if (prevRepo === undefined) delete process.env.LINKEDIN_RESTRICTION_REPO_FLAG;
    else process.env.LINKEDIN_RESTRICTION_REPO_FLAG = prevRepo;
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

const future = new Date(Date.now() + 3 * 24 * 3600 * 1000).toISOString();
withTempFlag(future, () => {
  const skip = shouldSkipLinkedinForRestriction();
  assert.ok(skip, "expected skip while restriction active");
  assert.strictEqual(skip.reason, "linkedin_temporarily_restricted");
  assert.ok(linkedinBlockedUntil());
});

const past = new Date(Date.now() - 60_000).toISOString();
withTempFlag(past, () => {
  assert.strictEqual(shouldSkipLinkedinForRestriction(), null);
  assert.strictEqual(linkedinBlockedUntil(), null);
});

console.log("ok - tools/linkedin/restriction.js");
