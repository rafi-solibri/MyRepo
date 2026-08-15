#!/usr/bin/env node
"use strict";

const assert = require("assert");
const { classify, maxCtcLpa, isHydOrRemote, titleOf } = require("./daily_apply.js");

function job(partial) {
  return {
    headline: partial.title || "",
    aiGeneratedData: { jobHeadline: partial.title || "" },
    company: partial.company || "TestCo",
    locations: partial.locations || ["Hyderabad"],
    remoteType: partial.remoteType || "remote_not_okay",
    salaryRange: partial.salaryRange || {
      max: 4500000,
      maxVanity: 4500000,
    },
    expRange: partial.expRange || { min: 8, max: 15 },
    allSkillsObj: partial.skills
      ? Object.fromEntries(partial.skills.map((s, i) => [String(i), s]))
      : {},
    ...partial.extra,
  };
}

// C# / .NET word-boundary trap: `\bc#\b` never matches "C#".
{
  const j = job({
    title: "Firmware Lead",
    skills: ["C++", "C#"],
    salaryRange: { max: 4000000, maxVanity: 4000000 },
  });
  const c = classify(j);
  assert.ok(c && c.tier === 2, `Firmware Lead + C# should be tier2, got ${JSON.stringify(c)}`);
}

{
  const j = job({
    title: "Senior .NET Developer",
    skills: ["ASP.NET", "Azure"],
  });
  const c = classify(j);
  assert.ok(c && c.tier === 2, `Senior .NET should pass, got ${JSON.stringify(c)}`);
}

{
  const j = job({
    title: "Engineering Leader",
    skills: ["Java", "TypeScript", "NodeJS (Node.js)"],
    salaryRange: { max: 4500000, maxVanity: 4500000, hideSalary: true },
  });
  const c = classify(j);
  assert.ok(c && c.tier === 1, `Engineering Leader should be tier1, got ${JSON.stringify(c)}`);
}

{
  const j = job({
    title: "Head of Engineering",
    skills: ["React", "AWS"],
  });
  const c = classify(j);
  assert.ok(c && c.tier === 1, `Head of Engineering should be tier1, got ${JSON.stringify(c)}`);
}

{
  const j = job({
    title: "SAP MM Consultant",
    skills: ["SAP MM", "HANA"],
  });
  assert.strictEqual(classify(j), null, "SAP title must hard-skip");
}

{
  const j = job({
    title: "Tech Lead",
    skills: ["Java", "React.js"],
    salaryRange: { max: 1800000, maxVanity: 1800000 },
  });
  assert.strictEqual(classify(j), null, "listed max under 35L must skip");
  assert.strictEqual(maxCtcLpa(j), 18);
}

{
  const j = job({
    title: "Senior Backend Engineer",
    locations: ["Bengaluru (Bangalore)"],
    remoteType: "remote_not_okay",
    skills: ["Node.js"],
  });
  assert.strictEqual(isHydOrRemote(j), false);
  assert.strictEqual(classify(j), null);
}

{
  const j = job({
    title: "Solutions Architect",
    skills: ["AWS"],
    expRange: { min: 5, max: 7 },
  });
  assert.ok(
    classify(j)?.tier === 1,
    "tier1 with maxExp 7 should pass (was hard-skip <8)"
  );
}

{
  const j = job({
    title: "Senior Backend Engineer",
    skills: ["Node.js"],
    expRange: { min: 5, max: 7 },
  });
  assert.strictEqual(
    classify(j),
    null,
    "non-tier1 non-.NET with maxExp 7 should still skip"
  );
}

{
  const j = job({
    title: "Senior .NET Developer",
    skills: ["ASP.NET", "Azure"],
    locations: ["India"],
    remoteType: "remote_not_okay",
    expRange: { min: 5, max: 7 },
  });
  assert.ok(isHydOrRemote(j), "India-only + .NET senior should count as Hyd/remote bias");
  assert.ok(
    classify(j)?.tier === 2,
    `India-only Senior .NET maxExp7 should qualify, got ${JSON.stringify(classify(j))}`
  );
}

{
  const j = job({
    title: "Tech Lead - Remote",
    locations: [],
    remoteType: "remote_not_okay",
    skills: ["Java", "React"],
  });
  assert.ok(isHydOrRemote(j), "remote in title should count as Hyd/remote");
  assert.ok(classify(j)?.tier === 1);
}

{
  const j = job({
    title: "Associate Technical Architect",
    skills: ["Azure", ".NET"],
  });
  assert.ok(
    classify(j)?.tier === 1,
    `Associate Technical Architect must not hard-skip, got ${JSON.stringify(classify(j))}`
  );
}

{
  const j = job({ title: "Solutions Architect", skills: ["AWS"] });
  assert.strictEqual(titleOf(j), "Solutions Architect");
  assert.ok(classify(j)?.tier === 1);
}

console.log("cutshort test_filters: ok");
