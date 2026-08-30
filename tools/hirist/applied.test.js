#!/usr/bin/env node
"use strict";

const assert = require("assert");
const {
  istDayStartMs,
  jobIdFromAppliedRow,
  collectAppliedJobIds,
  applyLanded,
  idsFromReport,
} = require("./applied");

assert.strictEqual(
  jobIdFromAppliedRow({ jobDetail: { id: 1666937 }, id: 75979800 }),
  1666937
);
assert.strictEqual(jobIdFromAppliedRow({ jobId: "1652340" }), 1652340);
assert.strictEqual(jobIdFromAppliedRow({}), null);

const ids = collectAppliedJobIds([
  { jobDetail: { id: 1666928 } },
  { jobDetail: { id: 1666928 } },
  { id: 1 },
]);
assert.deepStrictEqual([...ids].sort(), [1666928]);

const fromReport = idsFromReport({
  applied: [{ id: 1652340 }, { jobId: 1660067 }],
  external: [{ id: 999 }],
  skipped: [{ id: 1 }],
});
assert.ok(fromReport.has(1652340));
assert.ok(fromReport.has(1660067));
assert.ok(fromReport.has(999));
assert.ok(!fromReport.has(1));

const start = istDayStartMs(Date.parse("2026-08-29T05:15:00+00:00"));
assert.strictEqual(start, Date.parse("2026-08-29T00:00:00+05:30"));
assert.ok(Date.parse("2026-08-28T22:02:14.000Z") >= start);
assert.ok(Date.parse("2026-08-28T18:29:00.000Z") < start);

assert.ok(
  applyLanded({ count: 147, lastAppliedJobId: 1 }, { count: 148, lastAppliedJobId: 1666928 }, 1666928)
);
assert.ok(
  applyLanded({ count: 147, lastAppliedJobId: 1 }, { count: 147, lastAppliedJobId: 1666937 }, 1666937)
);
assert.ok(
  !applyLanded({ count: 147, lastAppliedJobId: 1666937 }, { count: 147, lastAppliedJobId: 1666937 }, 1663997)
);

console.log("hirist applied ok");
