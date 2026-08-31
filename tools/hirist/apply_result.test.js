#!/usr/bin/env node
/** Unit checks for tools/hirist/apply_result.js */
"use strict";

const assert = require("assert");
const { parseApplyMultiple, jobAlreadyAppliedFlag } = require("./apply_result");

const fakeOk = parseApplyMultiple([
  { success: false, message: { message: "Assessment/ screening is required to apply for this Job" } },
]);
assert.strictEqual(fakeOk.applied, false);
assert.strictEqual(fakeOk.assessmentRequired, true);
assert.match(fakeOk.message, /assessment|screening/i);

const realOk = parseApplyMultiple([{ success: true, message: "Applied" }]);
assert.strictEqual(realOk.applied, true);
assert.strictEqual(realOk.assessmentRequired, false);

const already = parseApplyMultiple([{ success: false, message: "Already applied" }]);
assert.strictEqual(already.applied, false);
assert.strictEqual(already.alreadyApplied, true);

const already2 = parseApplyMultiple([{ success: false, message: "Successfully Applied to Job" }]);
assert.strictEqual(already2.alreadyApplied, true);
assert.strictEqual(already2.applied, false);

const httpErr = parseApplyMultiple({ error: { name: "UNAUTHORISED_ACCESS", message: "login" } });
assert.strictEqual(httpErr.applied, false);
assert.match(httpErr.message, /login/i);

assert.strictEqual(jobAlreadyAppliedFlag({ applied: 1 }), true);
assert.strictEqual(jobAlreadyAppliedFlag({ applied: 0 }), false);
assert.strictEqual(jobAlreadyAppliedFlag({ applied: false }), false);

console.log("hirist apply_result ok");
