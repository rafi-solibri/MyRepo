#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  MATCHING,
  filterCountsUrl,
  undecidedMatchingUrl,
  jobSearchUrl,
  applyUrl,
  applyPayload,
  parseStatusCounts,
  applySucceeded,
} = require("./api");

assert.ok(MATCHING.includes("/candidate_matching"));
assert.ok(!MATCHING.includes("candidate_opportunity/"));
assert.strictEqual(
  filterCountsUrl(),
  `${MATCHING}/fetch_filter_counts?interest_facet=0`
);
assert.strictEqual(
  undecidedMatchingUrl(50, 0),
  `${MATCHING}?interest_facet=0&limit=50&offset=0`
);
assert.ok(jobSearchUrl(".NET", "Hyderabad", 50, 0).includes("job_search/"));
assert.strictEqual(applyUrl(), `${MATCHING}/apply/`);
assert.deepStrictEqual(applyPayload(435674), {
  job_id: 435674,
  is_interested: true,
  is_activity_page_job: false,
});
assert.strictEqual(applyPayload(1, { nonMatching: true }).is_non_matching_application, true);
assert.deepStrictEqual(parseStatusCounts({ success: true, status_counts: { "0": 7, "1": 367 } }), {
  "0": 7,
  "1": 367,
});
assert.strictEqual(parseStatusCounts({ raw: "<html>" }), null);
assert.strictEqual(applySucceeded({ status: 404, json: { raw: "<html>" } }), false);
assert.strictEqual(applySucceeded({ status: 200, json: { success: true, opp_id: 1 } }), true);
assert.strictEqual(applySucceeded({ status: 200, json: { opp_id: 99, applied_on: "x" } }), true);

console.log("portal api matching endpoints OK");
