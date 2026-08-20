#!/usr/bin/env node
"use strict";
/**
 * Smoke test: shared resume_tailor (Python) + Instahyre wiring contract.
 */
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { tailorResumeForJob } = require("./resume_tailor");
const { findResume } = require("./instahyre/resume");

const base = findResume();
assert.ok(base && fs.existsSync(base), "canonical resume must exist");

const result = tailorResumeForJob({
  master: base,
  title: "Technical Lead - Full Stack",
  company: "Nemetschek Group",
  description:
    "Technical Lead Full Stack SaaS platform with React.js AWS C# .NET PostgreSQL CI/CD. Mentors engineers.",
  skills: [".NET", "C#", "React.js", "AWS", "PostgreSQL"],
  jobId: "instahyre-439523-test",
});

assert.strictEqual(result.ok, true, result.error || "tailor failed");
assert.ok(result.out && fs.existsSync(result.out), "tailored out missing");
assert.ok((result.bytes || fs.statSync(result.out).size) > 1000);
assert.ok(Array.isArray(result.matchedSkills));
assert.ok(
  result.matchedSkills.some((s) => /\.NET|C#|React|AWS/i.test(s)),
  "expected owned JD skills in matchedSkills"
);
// Must not invent Golang as an owned skill label
assert.ok(!result.matchedSkills.some((s) => /golang|^go$/i.test(s)));

console.log(
  JSON.stringify(
    {
      ok: true,
      out: result.out,
      headline: result.headline,
      matchedSkills: result.matchedSkills,
    },
    null,
    2
  )
);
console.log("instahyre resume_tailor OK");
