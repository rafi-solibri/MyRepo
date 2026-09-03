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
  skipReason("Technical Architect - Conga CPQ/CLM", {
    location: "Hyderabad",
    skills: "Conga CPQ",
  }),
  "wrong_stack_title"
);
assert.strictEqual(
  skipReason("Technical Architect - Microsoft Dynamics 365 Finance & Operations", {
    location: "Hyderabad",
    skills: "D365 F&O Azure",
  }),
  "wrong_stack_title"
);
assert.strictEqual(
  skipReason("Senior Technical Consultant D365", {
    location: "Hyderabad",
    skills: ".NET",
  }),
  "wrong_stack_title"
);
assert.strictEqual(
  skipReason("Full Stack Developer - Python/Groovy", {
    location: "Hyderabad",
    skills: "Python Groovy Azure",
  }),
  "non_dotnet_primary"
);
assert.strictEqual(
  skipReason("Principal/Senior SAS Programmer", {
    location: "Hyderabad",
    skills: "SAS Azure",
  }),
  "non_dotnet_primary"
);
assert.strictEqual(
  skipReason("Jira Architect/Atlassian Solution Architect", {
    location: "Hyderabad",
    skills: "Jira Atlassian",
  }),
  "wrong_stack_title"
);
assert.strictEqual(
  skipReason("E2Open GTM Architect", {
    location: "Hyderabad",
    skills: "E2Open GTM",
  }),
  "wrong_stack_title"
);
assert.strictEqual(
  skipReason("GTM Architect", { location: "Hyderabad", skills: "Go-To-Market" }),
  "wrong_stack_title"
);
assert.strictEqual(
  skipReason("Tech Lead .NET / SAS", { location: "Hyderabad", skills: "C# SAS" }),
  null
);
assert.strictEqual(
  skipReason("Tech Lead .NET / Python", { location: "Hyderabad", skills: "C# Python" }),
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
