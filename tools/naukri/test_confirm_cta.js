#!/usr/bin/env node
"use strict";
const assert = require("assert");
const { disabledCtaMeansApplied } = require("./daily_apply");

assert.strictEqual(
  disabledCtaMeansApplied("Quick apply Applied", true),
  true,
  "disabled dual-layer CTA means applied (Recruise 2026-08-28)"
);
assert.strictEqual(
  disabledCtaMeansApplied("Quick apply Applied", false),
  false,
  "enabled dual-layer is not yet applied"
);
assert.strictEqual(
  disabledCtaMeansApplied("Go to company site", true),
  false,
  "company-site CTA is not a Naukri Applied signal"
);
assert.strictEqual(disabledCtaMeansApplied("Applied", true), true);
assert.strictEqual(disabledCtaMeansApplied("", true), false);
console.log("test_confirm_cta: ok");
