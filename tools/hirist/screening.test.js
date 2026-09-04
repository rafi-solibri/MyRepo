#!/usr/bin/env node
/** Unit checks for Hirist screening answer picker. */
"use strict";

const assert = require("assert");
const { pickScreeningAnswer, screeningSuccess } = require("./screening");

assert.strictEqual(
  pickScreeningAnswer("What is your current notice period?", ["Immediately Available", "1 month"]).value,
  "Immediately Available"
);
assert.strictEqual(
  pickScreeningAnswer("What is your current annual salary? (in LPA, e.g., 45)", null).value,
  52
);
assert.strictEqual(
  pickScreeningAnswer("What is your expected CTC?", null).value,
  65
);
assert.strictEqual(
  pickScreeningAnswer("Are you currently living in Hyderabad?", ["No", "Yes"]).value,
  "Yes"
);
assert.ok(screeningSuccess("https://www.hirist.tech/job/applied?jobId=1667999", ""));
assert.ok(screeningSuccess("https://www.hirist.tech/job/1/screening", "Your application has been submitted successfully!"));
assert.ok(!screeningSuccess("https://www.hirist.tech/job/1/screening", "Submit a Form"));

console.log("hirist screening helpers ok");
