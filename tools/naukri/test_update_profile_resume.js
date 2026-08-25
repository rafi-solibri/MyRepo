#!/usr/bin/env node
"use strict";
const assert = require("assert");
const { todayTokens } = require("./update_profile_resume");

const tokens = todayTokens();
assert.ok(tokens.includes("Updated today"));
assert.ok(tokens.includes("Uploaded today"));
assert.ok(
  tokens.some((t) => /^Uploaded on \d{1,2}\/\d{1,2}\/\d{4}$/.test(t)),
  "TopTier Uploaded on D/M/YYYY"
);
assert.ok(
  tokens.some((t) => /^\d{2}\/\d{2}\/\d{4}$/.test(t)),
  "DD/MM/YYYY token"
);

const today = tokens.find((t) => /^\d{2}\/\d{2}\/\d{4}$/.test(t));
const blob = `Resume\nUpdate\nRafi_Resume.docx\nUploaded on ${today}`;
assert.ok(
  tokens.some((t) => t.length > 4 && blob.includes(t)),
  "must match TopTier uploaded-on line"
);

const stale = "Resume\nUploaded on 24/08/2025";
const staleHit = tokens.find((t) => t.length > 4 && stale.includes(t) && /\d{4}/.test(t));
assert.strictEqual(staleHit, undefined, "last-year DD/MM/YYYY must not count as today");

console.log("test_update_profile_resume.js OK");
