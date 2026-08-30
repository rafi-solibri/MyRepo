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
  skipReason("AI Solution Architect", { location: "Hyderabad", skills: "GenAI" }),
  "pure_ai_data_without_dotnet"
);
assert.strictEqual(
  skipReason("AI Solution Architect - RAG/Agentic AI", {
    location: "Hyderabad",
    skills: "RAG",
  }),
  "pure_ai_data_without_dotnet"
);
assert.strictEqual(
  skipReason("Solution Architect - Data Engineering", {
    location: "Hyderabad",
    skills: "Spark",
  }),
  "pure_ai_data_without_dotnet"
);
assert.strictEqual(
  skipReason("ETL Architect", { location: "Hyderabad", skills: "Informatica" }),
  "pure_ai_data_without_dotnet"
);
assert.strictEqual(
  skipReason("Senior Solution Architect - Google Cloud", {
    location: "Hyderabad",
    skills: "GCP",
  }),
  null
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
