#!/usr/bin/env node
"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { tailorResumeForJob } = require("../resume_tailor");
const { findResume } = require("./questionnaire");

const master = findResume();
assert.ok(master && fs.existsSync(master), "canonical Rafi_Resume.docx must exist");

const r = tailorResumeForJob({
  master,
  jobId: "cutshort-test-sa",
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

const em = tailorResumeForJob({
  master,
  jobId: "cutshort-test-em",
  title: "Engineering Manager .NET",
  company: "Example",
  description: "Engineering Manager for .NET teams, mentoring, delivery, Azure",
  skills: ".NET, Azure",
});
assert.ok(em.ok, `EM tailor ok: ${em.error || ""}`);

console.log(
  "cutshort tailor_resume tests ok",
  JSON.stringify({
    sa: path.basename(r.out),
    matched: r.matchedSkills?.slice(0, 6),
    em: path.basename(em.out),
  })
);
