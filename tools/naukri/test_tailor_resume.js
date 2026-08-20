#!/usr/bin/env node
"use strict";
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { tailorResumeForJob } = require("./tailor_resume");

const out = tailorResumeForJob({
  role: "Solution Architect",
  company: "Epam Systems",
  jdText:
    "We need a Solution Architect with deep .NET Core, Azure, Kafka, and microservices experience.",
});
assert.strictEqual(out.ok, true, "tailor should succeed");
assert.ok(out.out && fs.existsSync(out.out), "output docx exists");
assert.strictEqual(path.basename(out.out), "Rafi_Resume.docx");
assert.ok(
  (out.skills || []).some((s) => /\.NET|Azure|Kafka/i.test(s)),
  "skills should reflect JD"
);
assert.ok(/Architect/i.test(out.headline || ""), "headline should target role");

const cached = tailorResumeForJob({
  role: "Solution Architect",
  company: "Epam Systems",
  jdText:
    "We need a Solution Architect with deep .NET Core, Azure, Kafka, and microservices experience.",
});
assert.strictEqual(cached.ok, true);
assert.strictEqual(cached.cached, true, "second call should hit cache");

// Must not invent stacks not on the CV allow-list (Salesforce etc. ignored).
const sf = tailorResumeForJob({
  role: "Technical Lead",
  company: "Acme",
  jdText: "Must have Salesforce and Pega experience plus .NET Core",
});
assert.strictEqual(sf.ok, true);
assert.ok(
  !(sf.skills || []).some((s) => /salesforce|pega/i.test(s)),
  "must not invent Salesforce/Pega skills"
);
assert.ok(
  (sf.skills || []).some((s) => /\.NET/i.test(s)),
  "still keep .NET from JD"
);

console.log("tailor_resume self-test OK");
