#!/usr/bin/env node
/** Quick unit checks for tools/hirist/filters.js */
"use strict";

const assert = require("assert");
const { skipReason, locationOk, hasDotNet } = require("./filters");

assert.strictEqual(
  skipReason("Technical Architect - .Net/Azure", {
    location: "Hyderabad",
    skills: ".Net Azure",
  }),
  null
);
assert.strictEqual(
  skipReason("AI Developer - Python", { location: "Hyderabad", skills: "Python" }),
  "pure_ai_data_without_dotnet"
);
assert.strictEqual(
  skipReason("Full Stack Lead (Java)", { location: "Hyderabad", skills: "Java" }),
  "java_primary"
);
assert.strictEqual(
  skipReason("Solutions Architect", { location: "Bangalore", skills: ".NET" }),
  "location_not_hyd_remote"
);
assert.ok(locationOk("Remote - India", "Staff Engineer", "Azure", 0));
assert.ok(locationOk("Pune", "Architect", ".NET", 1));
assert.ok(hasDotNet("Cloud SA", "C# ASP.NET"));

console.log("hirist filters ok");
