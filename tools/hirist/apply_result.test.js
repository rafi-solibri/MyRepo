#!/usr/bin/env node
/** Unit checks for Hirist apply-multiple response parsing. */
"use strict";

const assert = require("assert");
const { interpretApplyMultiple, appliedJobIdFromRow } = require("./apply_result");

assert.deepStrictEqual(
  interpretApplyMultiple({
    status: 200,
    json: [{ success: false, message: { message: "Assessment/ screening is required to apply for this Job" } }],
  }),
  {
    kind: "rejected",
    reason: "assessment_required",
    message: "Assessment/ screening is required to apply for this Job",
  }
);

assert.strictEqual(
  interpretApplyMultiple({
    status: 200,
    json: [{ success: true, jobId: 1668422 }],
  }).kind,
  "applied"
);

assert.strictEqual(
  interpretApplyMultiple({
    status: 200,
    json: [{ success: false, message: "You have already applied" }],
  }).kind,
  "already"
);

assert.strictEqual(
  interpretApplyMultiple({
    status: 200,
    json: { status: { code: 200, message: "Success" } },
  }).kind,
  "applied"
);

assert.strictEqual(
  interpretApplyMultiple({
    status: 200,
    json: { error: { name: "UNAUTHORISED_ACCESS", message: "nope" } },
  }).kind,
  "login"
);

assert.strictEqual(
  interpretApplyMultiple({ status: 401, json: {} }).kind,
  "login"
);

assert.strictEqual(
  interpretApplyMultiple({ status: 200, json: { foo: 1 } }).kind,
  "rejected"
);

assert.strictEqual(appliedJobIdFromRow({ jobDetail: { id: 1668350 } }), 1668350);
assert.strictEqual(appliedJobIdFromRow({ jobId: "1667999" }), 1667999);

console.log("hirist apply_result ok");
