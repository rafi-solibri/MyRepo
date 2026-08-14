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
  locationOk("Pan India"),
  false,
  "daily_apply enqueueJob must pass title/skills; 1-arg pan-India must not pass"
);
assert.strictEqual(
  skipReason("Backend Developer", { location: "Bengaluru" }),
  "location_not_hyd_remote"
);

console.log("instahyre filters location soften OK");
