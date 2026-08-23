#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  todayTokens,
  datePartsInZone,
  blobLooksUpdatedToday,
} = require("./update_profile_resume");

// 2026-08-23 19:30 UTC == 2026-08-24 01:00 IST
const overnight = new Date("2026-08-23T19:30:00Z");
const ist = datePartsInZone(overnight, "Asia/Kolkata");
const utc = datePartsInZone(overnight, "UTC");
assert.deepStrictEqual(ist, { year: 2026, month: 8, day: 24 });
assert.deepStrictEqual(utc, { year: 2026, month: 8, day: 23 });

const tokens = todayTokens(overnight);
assert.ok(tokens.includes("24/08/2026"), "IST DD/MM/YYYY");
assert.ok(tokens.includes("Uploaded on 24/08/2026"), "Naukri Uploaded on IST");
assert.ok(tokens.includes("Aug 24, 2026"), "IST Aug D, YYYY");
assert.ok(tokens.includes("Aug 23, 2026"), "UTC date still present");
assert.ok(tokens.includes("Updated today"));

const naukriResumeName =
  "Resume\nUpdate\n\nMohammed_Abdul_Rafi_Ahmed_Resume.docx\n\nUploaded on 24/08/2026";
assert.strictEqual(
  blobLooksUpdatedToday(naukriResumeName, overnight),
  true,
  "2026-08-24 IST Uploaded on must count as todayHit"
);
assert.strictEqual(
  blobLooksUpdatedToday("Uploaded on 23/08/2026", overnight),
  true,
  "UTC calendar date still accepted"
);
assert.strictEqual(
  blobLooksUpdatedToday("Uploaded on 22/08/2026", overnight),
  false,
  "yesterday must not count"
);

console.log("update_profile_resume todayTokens self-test OK");
