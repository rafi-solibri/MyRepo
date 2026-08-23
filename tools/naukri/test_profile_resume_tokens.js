#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  todayTokens,
  todayPartsIst,
  blobHitsToday,
} = require("./update_profile_resume");

// 2026-08-24 00:16 IST == 2026-08-23 18:46 UTC (cloud VM local date is still the 23rd).
const NEAR_MIDNIGHT_IST = new Date("2026-08-23T18:46:46.730Z");
const AFTERNOON_IST = new Date("2026-08-24T08:30:00.000Z"); // 14:00 IST 24 Aug

const midnightParts = todayPartsIst(NEAR_MIDNIGHT_IST);
assert.strictEqual(midnightParts.y, 2026);
assert.strictEqual(midnightParts.m, "Aug");
assert.strictEqual(midnightParts.day, 24);
assert.strictEqual(midnightParts.monthNum, 8);

const midnightTokens = todayTokens(NEAR_MIDNIGHT_IST);
assert.ok(midnightTokens.includes("24/08/2026"), "IST DD/MM/YYYY required");
assert.ok(midnightTokens.includes("Aug 24, 2026"), "IST month-day required");
assert.ok(midnightTokens.includes("Uploaded on 24/08/2026"));
assert.ok(
  !midnightTokens.includes("Aug 23, 2026"),
  "must not use UTC calendar day near IST midnight"
);

const naukriCard =
  "Resume\nUpdate\n\nRafi_Resume.docx\n\nUploaded on 24/08/2026";
assert.strictEqual(
  blobHitsToday(naukriCard, NEAR_MIDNIGHT_IST),
  "24/08/2026"
);
assert.strictEqual(
  blobHitsToday(naukriCard, AFTERNOON_IST),
  "24/08/2026"
);
assert.strictEqual(
  blobHitsToday("Last updated Aug 23, 2026", NEAR_MIDNIGHT_IST),
  null,
  "yesterday UTC date is not today IST"
);

console.log("test_profile_resume_tokens: ok");
