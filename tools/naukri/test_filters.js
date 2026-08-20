#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  shouldSkipTitle,
  shouldSkipCompany,
  hasDotNet,
  isArchLeadTitle,
  parseNaukriCardLines,
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
assert.strictEqual(
  shouldSkipTitle("TOSCA Automation Architect"),
  true,
  "TOSCA / test automation architect must skip"
);
assert.strictEqual(
  shouldSkipTitle("Embedded Technical Architect- SME"),
  true,
  "Embedded / firmware-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Artificial Intelligence Architect"),
  true,
  "Artificial Intelligence Architect without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("GCP Gemini Enterprise Platform Architect"),
  true,
  "Gemini / GenAI platform architect without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("LLM Platform Architect"),
  true,
  "LLM-primary architect without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Senior Technical Consultant D365"),
  true,
  "Dynamics 365 / D365 must skip"
);
assert.strictEqual(
  shouldSkipTitle("Manager Cyber Architecture, OT & Engineering"),
  true,
  "Cyber Architecture must skip"
);
assert.strictEqual(
  shouldSkipTitle("Lead System Architect"),
  true,
  "Pega LSA title must skip"
);
assert.strictEqual(
  shouldSkipTitle("AI Engineering Manager"),
  true,
  "AI Engineering Manager without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Data Architect"),
  true,
  "Data Architect without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("GCP Infra Architect - S"),
  true,
  "GCP Infra Architect without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle(
    "Mainframe Developer | Senior Mainframe Developer | Mainframe Architect"
  ),
  true,
  "Mainframe Architect without .NET must skip (false-apply 2026-08-20)"
);
assert.strictEqual(
  shouldSkipTitle("COBOL Technical Lead"),
  true,
  "COBOL-primary lead without .NET must skip"
);
assert.strictEqual(
  shouldSkipCompany("Pega"),
  true,
  "Pega employer must skip even if title omits Pega"
);
assert.strictEqual(
  shouldSkipCompany("Pegasystems Worldwide India Pvt Ltd"),
  true,
  "Pegasystems employer must skip"
);
assert.strictEqual(
  shouldSkipCompany("Redwood Software India"),
  false,
  "non-Pega employer must not company-skip"
);
assert.strictEqual(shouldSkipTitle("Senior .NET Architect"), false);
assert.strictEqual(isArchLeadTitle("Dot Net Fullstack Developer"), false);
assert.strictEqual(
  isArchLeadTitle("Solution Architecture Apps & AI"),
  true,
  "Architecture titles count as arch/lead band"
);
assert.strictEqual(
  isArchLeadTitle("Manager, SW Engineering"),
  true,
  "Manager, SW Engineering is an EM-class apply title"
);
assert.strictEqual(
  isArchLeadTitle("Chief Technology Officer"),
  true,
  "CTO is director-band apply title"
);
assert.strictEqual(
  isArchLeadTitle("CTO"),
  true,
  "Bare CTO title is director-band"
);
assert.strictEqual(
  isArchLeadTitle("Cloud Engineering, Senior Specialist CTO AI Ready Data/DTR"),
  false,
  "Product-string CTO must not count as arch/lead"
);
assert.strictEqual(
  shouldSkipTitle("Manager, SW Engineering"),
  false,
  "EM-class SW Engineering manager must not title-skip"
);
assert.strictEqual(
  parseNaukriCardLines([
    "Acme Corp",
    "Solutions Architect .NET",
    "Hyderabad",
    "Quick apply",
  ]).role,
  "Solutions Architect .NET",
  "homepage card: role before location before CTA"
);
const { workdayCompliantPassword } = require("./workday_apply");
assert.strictEqual(workdayCompliantPassword("GoodPass123!"), "GoodPass123!");
const weak = workdayCompliantPassword("short");
assert.ok(weak.length >= 12);
assert.ok(/[A-Z]/.test(weak) && /[0-9]/.test(weak) && /[^A-Za-z0-9]/.test(weak));
assert.strictEqual(workdayCompliantPassword("short"), workdayCompliantPassword("short"));
console.log("resume_and_filters self-test OK");

