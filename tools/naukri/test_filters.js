#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  shouldSkipTitle,
  hasDotNet,
  isArchLeadTitle,
} = require("./resume_and_filters");

assert.strictEqual(shouldSkipTitle("Solution Architect .NET"), false);
assert.strictEqual(shouldSkipTitle("QA Engineer"), true);
assert.strictEqual(shouldSkipTitle("AI Architect"), true, "pure AI title must skip");
assert.strictEqual(
  shouldSkipTitle("AI Architect .NET"),
  false,
  "AI Architect with .NET on title OK"
);
assert.strictEqual(
  shouldSkipTitle("Internet of Things Lead"),
  false,
  "intern must not match internet"
);
assert.strictEqual(hasDotNet("SA", "ASP.Net Core"), true);
assert.strictEqual(
  shouldSkipTitle("Aspire Systems - Solution Architect - Java (12-16 yrs)"),
  true,
  "Java-primary SA must skip"
);
assert.strictEqual(
  shouldSkipTitle("Full Stack Architect - MEAN Technologies"),
  true,
  "MEAN-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Solution Architect - Java/.NET"),
  false,
  "Java with .NET on title OK"
);
assert.strictEqual(
  isArchLeadTitle("Lead Software Engineer"),
  true,
  "Lead Software Engineer is senior apply title"
);
assert.strictEqual(
  isArchLeadTitle("Senior Manager Software Engineering"),
  true,
  "Senior Manager Software Engineering is senior apply title"
);
assert.strictEqual(
  isArchLeadTitle("Software Engineer Manager"),
  true,
  "Software Engineer Manager is senior apply title"
);
assert.strictEqual(
  isArchLeadTitle("Senior Manager - Technology"),
  true,
  "Senior Manager - Technology is senior apply title"
);
assert.strictEqual(
  shouldSkipTitle("SRE Engineering Manager"),
  true,
  "SRE-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Principal Engineer - SRE"),
  true,
  "SRE suffix must skip"
);
assert.strictEqual(
  shouldSkipTitle("Appian Technical Lead - II"),
  true,
  "Appian-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Technical Lead - Network Operations"),
  true,
  "Network Operations lead must skip"
);
assert.strictEqual(
  shouldSkipTitle("Oracle Fusion Finance Solution Architect"),
  true,
  "Oracle Fusion SA must skip"
);
assert.strictEqual(
  shouldSkipTitle(
    "Oracle Cloud Infra Admin-Oracle DBA Cloud Architect-Manager"
  ),
  true,
  "Oracle DBA Cloud Architect must skip"
);
assert.strictEqual(
  shouldSkipTitle("Data & AI Solution Architect"),
  true,
  "Data & AI SA without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Principal IS Architect, Anaplan"),
  true,
  "Anaplan-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Quality Solution Architect"),
  true,
  "Quality Architect must skip"
);
assert.strictEqual(
  shouldSkipTitle("Immediate Hiring For Power Platform Architect"),
  true,
  "Power Platform must skip"
);
assert.strictEqual(
  shouldSkipTitle("Solution Architect - Gen AI - Life Sciences"),
  true,
  "Gen AI SA without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("AI Agent Architect ( Agentic AI Systems)"),
  true,
  "AI Agent Architect without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Principal Architect- AI ,ML"),
  true,
  "Principal Architect AI/ML without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Agentforce Technical Lead"),
  true,
  "Agentforce/Salesforce must skip"
);
assert.strictEqual(
  shouldSkipTitle("Principal Network Support Engineer"),
  true,
  "Network Support must skip"
);
assert.strictEqual(
  shouldSkipTitle(
    "Project Engineering Manager Substation (Civil & Structural)- Riyadh"
  ),
  true,
  "Civil/Structural EM must skip"
);
assert.strictEqual(
  shouldSkipTitle("QE Architect"),
  true,
  "QE Architect must skip"
);
assert.strictEqual(
  shouldSkipTitle("Azure Data Engineering Manager"),
  true,
  "Data Engineering Manager without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Senior Manager - Attack Surface Reduction"),
  true,
  "Attack Surface / cyber primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Cyber Security Architect"),
  true,
  "Cyber Security Architect must skip"
);
assert.strictEqual(shouldSkipTitle("Senior .NET Architect"), false);
assert.strictEqual(isArchLeadTitle("Dot Net Fullstack Developer"), false);
console.log("resume_and_filters self-test OK");

