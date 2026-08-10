#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  parseTitleExperience,
  experienceOk,
  classifyJob,
  hasDotNet,
} = require("./filters");

assert.deepStrictEqual(parseTitleExperience(".Net Lead|6-9 Yrs|Hyderabad"), {
  min: 6,
  max: 9,
});
assert.strictEqual(
  experienceOk(
    { minimumExperience: { years: 0 }, maximumExperience: { years: 0 } },
    ".Net Azure / AWS Lead|6-9 Yrs|Hyderabad"
  ).ok,
  false,
  "title-embedded 6-9 must fail max<10"
);

assert.strictEqual(hasDotNet("Solution Architect", "ASP.Net Core, Azure"), true);
assert.strictEqual(hasDotNet("SAP Architect", "SAP MM"), false);

const pass = classifyJob({
  jobId: 1,
  title: "Principal Engineer - .NET Core",
  companyName: "Example",
  locations: [{ text: "Hyderabad / Secunderabad" }],
  skills: [{ text: ".NET Core" }],
  minimumExperience: { years: 10 },
  maximumExperience: { years: 15 },
});
assert.strictEqual(pass.pass, true);

assert.strictEqual(
  classifyJob({
    jobId: 2,
    title: "AI Architect",
    companyName: "Example",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET" }, { text: "Python" }],
    minimumExperience: { years: 12 },
    maximumExperience: { years: 14 },
  }).pass,
  false,
  "pure AI title needs .NET on title"
);

assert.strictEqual(
  classifyJob({
    jobId: 3,
    title: "Tech Architect / Lead Developer (.NET)",
    companyName: "Example",
    locations: [{ country: "India" }],
    description: "Fully remote role building ASP.NET Core APIs",
    skills: [{ text: "ASP.NET Core" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  true,
  "remote in description should satisfy location"
);

assert.strictEqual(
  classifyJob({
    jobId: 4,
    title: "Tech Architect / Lead Developer (.NET)",
    companyName: "Example",
    locations: [{ country: "India" }],
    description: "Fully remote role",
    skills: [{ text: ".NET" }],
    minimumExperience: { years: 5 },
    maximumExperience: { years: 7 },
  }).pass,
  false,
  "maxExp 7 must still fail after location enrich"
);

console.log("filters.test.js OK");
