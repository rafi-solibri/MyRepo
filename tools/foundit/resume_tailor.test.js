#!/usr/bin/env node
/** Unit checks for Foundit JD resume tailor wrapper (shared tools/resume_tailor.py). */
"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { tailorResumeForJob } = require("../resume_tailor");

const master = path.join(__dirname, "..", "..", "resumes", "Rafi_Resume.docx");
assert.ok(fs.existsSync(master), "master resume must exist");

const r = tailorResumeForJob({
  master,
  jobId: "test-sa-azure",
  title: "Solutions Architect - .NET / Azure",
  company: "Example Corp",
  description:
    "We need a Solutions Architect with deep .NET Core, Azure, Microservices, Kafka, and Kubernetes experience to lead platform design.",
  skills: [".NET Core", "Azure", "Kafka", "Kubernetes"],
});

assert.strictEqual(r.ok, true, `tailor ok: ${r.error || ""}`);
assert.ok(fs.existsSync(r.out), "output docx exists");
assert.ok(r.bytes > 1000, "output size");
assert.ok(
  (r.matchedSkills || []).some((s) => /Azure|\.NET/i.test(s)),
  "matched Azure/.NET"
);
assert.ok(/Architect/i.test(r.headline || ""), "headline architect band");

const lead = tailorResumeForJob({
  master,
  jobId: "test-em",
  title: "Engineering Manager .NET",
  company: "Example",
  description: "Engineering Manager for .NET teams, mentoring, delivery, Azure",
  skills: ".NET, Azure",
});
assert.ok(lead.ok, `EM tailor ok: ${lead.error || ""}`);
assert.ok(/Manager|Lead|Architect/i.test(lead.headline || ""), "EM/lead headline");

console.log("resume_tailor.test.js OK");
console.log(
  JSON.stringify(
    {
      sa: { headline: r.headline, matched: r.matchedSkills, out: r.out },
      em: { headline: lead.headline, matched: lead.matchedSkills },
    },
    null,
    2
  )
);
