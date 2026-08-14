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
  "remote in description should satisfy location when card is country-only"
);

assert.strictEqual(
  classifyJob({
    jobId: 3.1,
    title: ".NET Technical Architect with Azure",
    companyName: "Example",
    locations: [{ city: "Noida", country: "India" }],
    description: "Our remote-first approach gives flexibility. .NET Core Azure.",
    skills: [{ text: ".NET Core" }],
    minimumExperience: { years: 15 },
    maximumExperience: { years: 17 },
  }).pass,
  false,
  "JD remote-first must not override explicit non-Hyd city"
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
  "maxExp 7 with min 5 must still fail (junior/mid band)"
);

assert.strictEqual(
  classifyJob({
    jobId: 5,
    title: ".NET Technical Lead",
    companyName: "Example",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET Core" }],
    minimumExperience: { years: 8 },
    maximumExperience: { years: 12 },
  }).pass,
  true,
  "8-12 TL band should pass"
);

assert.strictEqual(
  classifyJob({
    jobId: 6,
    title: "Solution Architect .NET",
    companyName: "Example",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: "C#" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
    maximumSalary: { absoluteValue: 4000000 },
  }).pass,
  true,
  "listed max 40 LPA should pass (forms still state 65 expected)"
);

assert.strictEqual(
  classifyJob({
    jobId: 7,
    title: "Senior .NET Developer",
    companyName: "Example",
    locations: [{ text: "Remote" }],
    skills: [{ text: ".NET" }],
    minimumExperience: { years: 8 },
    maximumExperience: { years: 12 },
  }).pass,
  true,
  "Senior .NET should count as seniority"
);

assert.strictEqual(
  classifyJob({
    jobId: 8,
    title: ".Net Senior Developer",
    companyName: "Infosys",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET" }],
    minimumExperience: { years: 8 },
    maximumExperience: { years: 12 },
  }).pass,
  true,
  ".Net Senior Developer word-order must count as seniority"
);

assert.strictEqual(
  classifyJob({
    jobId: 9,
    title: "Senior Backend Developer (.NET)",
    companyName: "Example",
    locations: [{ text: "Remote" }],
    skills: [{ text: ".NET Core" }],
    minimumExperience: { years: 8 },
    maximumExperience: { years: 12 },
  }).pass,
  true,
  "Senior Backend Developer (.NET) must count as seniority"
);

assert.strictEqual(
  classifyJob({
    jobId: 10,
    title: ".Net Developer",
    companyName: "Example",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET" }],
    minimumExperience: { years: 8 },
    maximumExperience: { years: 12 },
  }).pass,
  false,
  "plain .Net Developer still lacks seniority"
);

assert.strictEqual(
  experienceOk(
    { minimumExperience: { years: 0 }, maximumExperience: { years: 0 } },
    "Senior Software Architect - .NET"
  ).ok,
  true,
  "Raven 0-0 with no title band must be undisclosed (not maxExp 0 junior/mid)"
);

assert.strictEqual(
  classifyJob({
    jobId: 11,
    title: "Senior Software Architect - .NET",
    companyName: "Hyland",
    locations: [{ text: "Remote" }],
    skills: [{ text: ".NET" }],
    minimumExperience: { years: 0 },
    maximumExperience: { years: 0 },
  }).pass,
  true,
  "Senior .NET Architect remote with Raven 0-0 must pass"
);

const indiaEnrich = classifyJob({
  jobId: 12,
  title: "Senior .NET Architect",
  companyName: "Example",
  locations: [{ country: "India" }],
  skills: [{ text: ".NET" }],
  minimumExperience: { years: 10 },
  maximumExperience: { years: 15 },
});
assert.strictEqual(indiaEnrich.needsEnrich, true, "country-only India must request JD enrich");
assert.strictEqual(indiaEnrich.pass, false);

assert.strictEqual(
  classifyJob({
    jobId: 13,
    title: "Agentforce - Sucess Architect",
    companyName: "Salesforce",
    locations: [{ text: "Hyderabad / Secunderabad, Telangana" }],
    skills: [{ text: ".NET" }, { text: "Salesforce" }],
    minimumExperience: { years: 8 },
    maximumExperience: { years: 12 },
  }).pass,
  false,
  "Agentforce title must hard-skip even with .NET in skills laundry list"
);

assert.strictEqual(
  classifyJob({
    jobId: 14,
    title: "Solutions Architect",
    companyName: "Salesforce",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET" }, { text: "Azure" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  false,
  "Salesforce employer without .NET on title must skip"
);

assert.strictEqual(
  classifyJob({
    jobId: 15,
    title: "Senior .NET Architect",
    companyName: "Salesforce",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET Core" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  true,
  "explicit .NET title at Salesforce employer may still pass"
);

console.log("filters.test.js OK");
