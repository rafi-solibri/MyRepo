#!/usr/bin/env node
/** Unit checks for tools/hirist/apply_response.js */
"use strict";

const assert = require("assert");
const {
  parseApplyMultipleResponse,
  extractAppliedJobIds,
  searchHitAlreadyApplied,
} = require("./apply_response");

assert.deepStrictEqual(
  parseApplyMultipleResponse({
    status: 200,
    json: [{ success: true, message: { message: "Applied" } }],
  }),
  { ok: true, reason: "Applied" }
);

const already = parseApplyMultipleResponse({
  status: 200,
  json: [{ success: false, message: { message: "Job is already applied" } }],
});
assert.strictEqual(already.ok, false);
assert.strictEqual(already.alreadyApplied, true);

const assess = parseApplyMultipleResponse({
  status: 200,
  json: [
    {
      success: false,
      message: { message: "Assessment/ screening is required to apply for this Job" },
    },
  ],
});
assert.strictEqual(assess.ok, false);
assert.strictEqual(assess.assessmentRequired, true);
assert.ok(/assessment/i.test(assess.reason));

// Legacy object error still works
const unauth = parseApplyMultipleResponse({
  status: 401,
  json: { error: { name: "UNAUTHORISED_ACCESS" } },
});
assert.strictEqual(unauth.reason, "apply_401");

const ids = extractAppliedJobIds({
  data: {
    jobs: [
      { id: 76181840, jobDetail: { id: 1661575, title: "Full Stack Developer - .Net/Azure" } },
      { id: 9, jobDetail: { id: 1668077 } },
    ],
  },
});
assert.ok(ids.has(1661575));
assert.ok(ids.has(1668077));
assert.strictEqual(ids.size, 2);

assert.strictEqual(searchHitAlreadyApplied({ applied: 1, applyStatus: 1 }), true);
assert.strictEqual(searchHitAlreadyApplied({ applied: 0, applyStatus: 0, applyUrl: "" }), true);
assert.strictEqual(searchHitAlreadyApplied({ applied: 0, applyStatus: 1, applyUrl: "" }), false);

console.log("hirist apply_response ok");
