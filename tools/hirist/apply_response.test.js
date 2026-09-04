#!/usr/bin/env node
/** Unit checks for Hirist apply-multiple response parsing. */
"use strict";

const assert = require("assert");
const { interpretApplyResponse } = require("./apply_response");

assert.deepStrictEqual(
  interpretApplyResponse({
    status: 200,
    json: [{ data: { id: 1, jobId: 1663103 }, message: "Successfully Applied to Job" }],
  }),
  { kind: "ok", message: "Successfully Applied to Job" }
);

assert.strictEqual(
  interpretApplyResponse({
    status: 200,
    json: [{ success: false, message: { message: "Assessment/ screening is required to apply for this Job" } }],
  }).kind,
  "assessment"
);

assert.strictEqual(
  interpretApplyResponse({
    status: 200,
    json: [{ success: false, message: { message: "Job is already applied" } }],
  }).kind,
  "already"
);

assert.strictEqual(
  interpretApplyResponse({
    status: 200,
    json: [{ success: false, message: { message: "Assessment/ screening is required to apply for this Job" } }],
  }).kind !== "ok",
  true,
  "HTTP 200 + success:false must not count as applied"
);

assert.strictEqual(
  interpretApplyResponse({
    status: 401,
    json: { error: { name: "UNAUTHORISED_ACCESS" } },
  }).kind,
  "login"
);

assert.strictEqual(
  interpretApplyResponse({
    status: 200,
    json: [{ success: false, message: { message: "Recruiter closed this job" } }],
  }).kind,
  "rejected"
);

console.log("hirist apply_response ok");
