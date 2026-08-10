#!/usr/bin/env node
"use strict";
const assert = require("assert");
const { shouldSkipTitle, hasDotNet } = require("./resume_and_filters");

assert.strictEqual(shouldSkipTitle("Solution Architect .NET"), false);
assert.strictEqual(shouldSkipTitle("QA Engineer"), true);
assert.strictEqual(shouldSkipTitle("AI Architect"), true, "pure AI title must skip");
assert.strictEqual(
  shouldSkipTitle("AI Architect .NET"),
  false,
  "AI Architect with .NET on title OK"
);
assert.strictEqual(shouldSkipTitle("Internet of Things Lead"), false, "intern must not match internet");
assert.strictEqual(hasDotNet("SA", "ASP.Net Core"), true);
console.log("resume_and_filters self-test OK");
