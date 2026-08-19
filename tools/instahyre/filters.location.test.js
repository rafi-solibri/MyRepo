#!/usr/bin/env node
"use strict";
const assert = require("assert");
const { locationOk, skipReason } = require("./filters");

assert.strictEqual(locationOk("Hyderabad"), true);
assert.strictEqual(locationOk("Bengaluru"), false);
assert.strictEqual(
  locationOk("Pan India", "Solution Architect .NET", ".NET Azure"),
  true,
  "pan-India + senior .NET may pass"
);
assert.strictEqual(
  locationOk("Multiple locations across India", "Engineering Manager", "Azure"),
  true
);
assert.strictEqual(
  locationOk("Pan India", "Junior Support Associate", ""),
  false,
  "pan-India without senior/dotnet/cloud must fail"
);
assert.strictEqual(
  skipReason("Solution Architect .NET", { location: "Work from anywhere India" }),
  null
);
assert.strictEqual(
  skipReason("Backend Developer", { location: "Bengaluru" }),
  "location_not_hyd_remote"
);
assert.strictEqual(
  skipReason("Sr. Software Engineer", { location: "Hyderabad" }),
  null,
  "Hyd senior SWE is apply-bias (uncertain → APPLY)"
);
assert.strictEqual(
  skipReason("Senior Software Engineer", { location: "Work From Home" }),
  null
);
assert.strictEqual(
  skipReason("Software Engineer", { location: "Hyderabad" }),
  "generic_engineering_without_dotnet_cloud",
  "mid-level SWE without .NET/cloud still skips"
);
assert.strictEqual(
  skipReason("Senior Java Full Stack Developer - Angular", { location: "Hyderabad" }),
  "java_primary"
);

console.log("instahyre filters location soften OK");
