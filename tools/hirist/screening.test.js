#!/usr/bin/env node
/** Unit checks for tools/hirist/screening.js */
"use strict";

const assert = require("assert");
const { answerScreeningQuestion, looksSubmitted } = require("./screening");

const azure = answerScreeningQuestion("Which Azure services have you worked extensively with?");
assert.match(azure, /App Service/i);
assert.ok(azure.length <= 500);

const years = answerScreeningQuestion(
  "How many years of experience do you have in designing and architecting enterprise applications using .NET Core and Azure?"
);
assert.match(years, /10\+/);

const owned = answerScreeningQuestion(
  "Have you independently owned the technical architecture of an application end-to-end?"
);
assert.match(owned, /^Yes/i);

assert.match(answerScreeningQuestion("Current CTC?"), /52/);
assert.match(answerScreeningQuestion("Expected CTC"), /65/);
assert.match(answerScreeningQuestion("Notice period"), /Immediate/i);
assert.match(answerScreeningQuestion("What is your current notice period?"), /Immediate/i);

assert.ok(looksSubmitted("https://www.hirist.tech/applied-jobs", ""));
assert.ok(looksSubmitted("https://www.hirist.tech/job/applied?jobId=1660067", ""));
assert.ok(looksSubmitted("https://www.hirist.tech/job/1/screening", "Application submitted"));
assert.ok(!looksSubmitted("https://www.hirist.tech/job/1/screening", "Submit a Form"));

console.log("hirist screening ok");
