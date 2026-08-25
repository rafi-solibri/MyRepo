#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  isFalseApplyCta,
  looksLikeApplyCta,
  isBrochureOrDeadEnd,
  extractHopDestinationFromUrl,
} = require("./apply_cta");

assert.strictEqual(isFalseApplyCta("View applied jobs (20+)"), true);
assert.strictEqual(isFalseApplyCta("Applied jobs"), true);
assert.strictEqual(isFalseApplyCta("Apply now"), false);
assert.strictEqual(looksLikeApplyCta("View applied jobs (20+)"), false);
assert.strictEqual(looksLikeApplyCta("Quick apply"), true);
assert.strictEqual(looksLikeApplyCta("Apply for this job"), true);
assert.strictEqual(looksLikeApplyCta("Apply with Indeed"), false);

assert.strictEqual(
  isBrochureOrDeadEnd({
    url: "https://www.mihira.ai/careers.html",
    text: "Join our growing team. See all open roles.",
  }),
  true
);
assert.strictEqual(
  isBrochureOrDeadEnd({
    url: "https://boards.greenhouse.io/acme/jobs/1",
    text: "Apply for this job. First name. Upload resume.",
    hasFile: true,
  }),
  false
);
assert.strictEqual(
  extractHopDestinationFromUrl(
    "https://www.indeed.com/applystart?jk=abc&continueUrl=https%3A%2F%2Facme.wd1.myworkdayjobs.com%2Fen-US%2Fjob"
  ),
  "https://acme.wd1.myworkdayjobs.com/en-US/job"
);
assert.strictEqual(
  extractHopDestinationFromUrl("https://www.indeed.com/rc/clk?jk=abc"),
  ""
);

const { ATS_OVERLAY_SELECTORS } = require("./complete_page");
assert.ok(ATS_OVERLAY_SELECTORS.some((s) => /Not [Nn]ow/.test(s)));
assert.ok(ATS_OVERLAY_SELECTORS.some((s) => /Accept All Cookies/.test(s)));

console.log("tools/ats/test_apply_cta.js OK");
