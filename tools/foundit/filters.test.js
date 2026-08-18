#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  parseTitleExperience,
  experienceOk,
  classifyJob,
  hasDotNet,
  hasSeniority,
  isArchLeadTitle,
  isJavaOrSalesforcePrimary,
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

// Arch/EM without .NET on skills — Naukri parity (not Java/SF primary)
assert.strictEqual(
  classifyJob({
    jobId: 16,
    title: "Solution Architect",
    companyName: "Example Corp",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: "Azure" }, { text: "Microservices" }, { text: "API" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  true,
  "Arch title Hyd without .NET skills laundry may pass"
);

assert.strictEqual(
  classifyJob({
    jobId: 17,
    title: "Engineering Manager",
    companyName: "Example Corp",
    locations: [{ text: "Remote" }],
    skills: [{ text: "Java" }, { text: "Spring" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  false,
  "EM with Java-only skills must still fail"
);

assert.strictEqual(
  classifyJob({
    jobId: 18,
    title: "Backend Developer",
    companyName: "Example Corp",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: "Azure" }],
    minimumExperience: { years: 8 },
    maximumExperience: { years: 12 },
  }).pass,
  false,
  "non-arch title without .NET must still fail"
);

assert.strictEqual(
  classifyJob({
    jobId: 19,
    title: "Senior IT Analyst (Infrastructure)",
    companyName: "National University Of Singapore",
    locations: [{ text: "Singapore | Remote" }],
    skills: [{ text: ".NET" }, { text: "Azure" }, { text: "Windows" }],
    minimumExperience: { years: 8 },
    maximumExperience: { years: 12 },
  }).pass,
  false,
  "infra/IT Analyst must skip when .NET is only in skills laundry list"
);

assert.strictEqual(
  classifyJob({
    jobId: 20,
    title: "Senior .NET Infrastructure Architect",
    companyName: "Example",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET Core" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  true,
  "Infrastructure + .NET on title may still pass"
);

assert.strictEqual(
  isArchLeadTitle("Solution Architecture Apps & AI"),
  true,
  "Architecture (not only Architect) is arch/lead band"
);
assert.strictEqual(
  classifyJob({
    jobId: 21,
    title: "Solution Architecture Apps & AI",
    companyName: "Microsoft Corp",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: "Azure" }, { text: "Apps" }],
  }).pass,
  true,
  "Solution Architecture Hyd titles may apply without .NET skills laundry"
);

assert.strictEqual(
  classifyJob({
    jobId: 22,
    title: "Facilities Engineering Manager",
    companyName: "Shell",
    locations: [{ text: "Singapore | remote" }],
    skills: [{ text: "Azure" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).reason,
  "non-software engineering without .NET on title",
  "Facilities EM must skip"
);

assert.strictEqual(
  classifyJob({
    jobId: 23,
    title: "Principal Electrical Engineer - Power Generation",
    companyName: "Jacobs",
    locations: [{ text: "Philippines | remote" }],
    skills: [{ text: "Azure" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  false,
  "electrical/power Principal must skip"
);

assert.strictEqual(
  classifyJob({
    jobId: 24,
    title: "Principal Engineer - Mechanical (UK Water)",
    companyName: "Arcadis",
    locations: [{ text: "Hyderabad / Secunderabad, Telangana" }],
    skills: [{ text: "Azure" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  false,
  "mechanical Principal Hyd must skip"
);

assert.strictEqual(
  classifyJob({
    jobId: 25,
    title: "Operations Engineering Manager 2",
    companyName: "Celestica",
    locations: [{ text: "Thailand | Remote" }],
    skills: [{ text: "Azure" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).reason,
  "ops/manufacturing EM without .NET on title",
  "operations engineering manager must skip"
);

assert.strictEqual(
  classifyJob({
    jobId: 26,
    title: "Oracle Fusion Apps Principal Solutions Engineer (ERP)",
    companyName: "Oracle",
    locations: [{ text: "Saudi Arabia | remote" }],
    skills: [{ text: ".NET" }, { text: "Oracle Fusion" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).reason,
  "Oracle Fusion/ERP without .NET on title",
  "Oracle Fusion title must skip even with .NET in skills laundry"
);

assert.strictEqual(
  classifyJob({
    jobId: 26.1,
    title: "Snowflake Solutions Architect",
    companyName: "INFOTRON",
    locations: [{ text: "India" }, { text: "Remote" }],
    skills: [{ text: "Snowflake" }, { text: "AWS" }, { text: "Azure" }],
    minimumExperience: { years: 8 },
    maximumExperience: { years: 15 },
  }).reason,
  "Snowflake/Databricks without .NET on title",
  "Snowflake Architect must hard-skip even via Arch/Lead without .NET"
);

assert.strictEqual(
  classifyJob({
    jobId: 26.2,
    title: "Databricks Solutions Architect",
    companyName: "Example",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET" }, { text: "Databricks" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).reason,
  "Snowflake/Databricks without .NET on title",
  "Databricks title must skip even with .NET in skills laundry"
);

assert.strictEqual(
  classifyJob({
    jobId: 26.3,
    title: "Principal Engineer - SoC RTL Design",
    companyName: "tylsemi",
    locations: [{ text: "India" }, { text: "Remote" }],
    skills: [{ text: "RTL" }, { text: "Verilog" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).reason,
  "SoC/RTL/silicon hardware without .NET on title",
  "SoC RTL Principal must hard-skip even via Arch/Lead without .NET"
);

assert.strictEqual(
  classifyJob({
    jobId: 26.4,
    title: "Senior FPGA Engineer",
    companyName: "Example",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET" }, { text: "FPGA" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).reason,
  "SoC/RTL/silicon hardware without .NET on title",
  "FPGA title must skip even with .NET in skills laundry"
);

assert.strictEqual(
  classifyJob({
    jobId: 27,
    title: "AI Solution Architect",
    companyName: "hire feed",
    locations: [{ text: "United Arab Emirates | Remote" }],
    skills: [{ text: ".NET" }, { text: "Azure" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).reason,
  "pure AI/data without .NET on title",
  "AI Solution Architect must skip like AI Architect"
);

assert.strictEqual(
  classifyJob({
    jobId: 28,
    title: "Data Engineering Manager",
    companyName: "Reap",
    locations: [{ text: "Singapore | Remote" }],
    skills: [{ text: "Azure" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).reason,
  "pure AI/data without .NET on title",
  "Data Engineering Manager must skip"
);

assert.strictEqual(
  classifyJob({
    jobId: 29,
    title: "Application Architect",
    companyName: "RealPage",
    locations: [{ text: "Hyderabad / Secunderabad, Telangana" }],
    skills: [{ text: "Azure" }, { text: "Microservices" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  true,
  "Hyd Application Architect without .NET skills laundry may still pass"
);

assert.strictEqual(
  classifyJob({
    jobId: 30,
    title: "Engineering Manager, Water",
    companyName: "Jacobs",
    locations: [{ text: "Singapore | remote" }],
    skills: [{ text: "Azure" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  false,
  "Water/civil EM must skip"
);

assert.strictEqual(
  classifyJob({
    jobId: 31,
    title: "AI Specialist Solution Architect, Southeast Asia (Singapore)",
    companyName: "Red Hat",
    locations: [{ text: "Singapore | remote" }],
    skills: [{ text: "Azure" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).reason,
  "pure AI/data without .NET on title",
  "AI Specialist Solution Architect must skip"
);

assert.strictEqual(
  hasSeniority("Technical Architect_.NET Core"),
  true,
  "underscore before .NET must not hide Architect seniority"
);
assert.strictEqual(
  hasSeniority("IN_Senior Associate_Azure Dot Net Developer_GCC_Advisory_Bangalore"),
  true,
  "IN_Senior underscore title must count as seniority"
);
assert.strictEqual(
  hasDotNet("IN_Senior Associate_Azure Dot Net Developer", ""),
  true,
  "Dot Net (two words) on title is .NET proof"
);
assert.strictEqual(
  isJavaOrSalesforcePrimary("CPQ/Digital Commerce Solution architect", "Salesforce Conga CPQ"),
  true,
  "Salesforce in skills without .NET on title is SF-primary"
);
assert.strictEqual(
  classifyJob({
    jobId: 32,
    title: "CPQ/Digital Commerce Solution architect",
    companyName: "Hitachi Energy",
    locations: [{ city: "Remote", country: "India" }],
    skills: [{ text: "Salesforce" }, { text: "Conga CPQ" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  false,
  "Salesforce-stack architect without .NET on title must skip"
);
assert.strictEqual(
  classifyJob({
    jobId: 33,
    title: "Technical Architect_.NET Core",
    companyName: "Example",
    locations: [{ text: "Hyderabad" }],
    skills: [{ text: ".NET Core" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 12 },
  }).pass,
  true,
  "Technical Architect_.NET Core Hyd must pass"
);
assert.strictEqual(
  classifyJob({
    jobId: 34,
    title: "Solutions Architect",
    companyName: "Allianz Technology",
    locations: [{ country: "Thailand" }],
    description: "Work from home. Remote-first culture across APAC.",
    skills: [{ text: "software architecture" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  false,
  "country-only Thailand must not inherit JD WFH/remote-first"
);
assert.strictEqual(
  classifyJob({
    jobId: 35,
    title: "Software Engineering Manager, AI i18n and Evaluations",
    companyName: "Google India",
    locations: [{ country: "Singapore" }],
    description: "This is a remote-first role based in Singapore.",
    skills: [{ text: "AI" }, { text: "i18n" }],
    minimumExperience: { years: 10 },
    maximumExperience: { years: 15 },
  }).pass,
  false,
  "country-only Singapore must not inherit JD remote-first"
);

console.log("filters.test.js OK");
