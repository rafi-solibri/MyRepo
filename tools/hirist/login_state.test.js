#!/usr/bin/env node
"use strict";

const assert = require("assert");
const { isPublicAppliedJobs, isLoggedOutUi, sessionFromSignals } = require("./login_state");

assert.strictEqual(
  isPublicAppliedJobs(
    "https://www.hirist.tech/applied-jobs",
    "Applied Jobs\nYou Don't Have Applied Jobs"
  ),
  true
);
assert.strictEqual(
  isPublicAppliedJobs("https://www.hirist.tech/", "Login Register"),
  false
);
assert.ok(
  isLoggedOutUi(
    "https://www.hirist.tech/login",
    "Login here\nEmail Address\nContinue with Google\nFind Your Dream Tech Job"
  )
);
assert.ok(
  isLoggedOutUi(
    "https://www.hirist.tech/",
    "Download App\nLogin\nRegister\nLogin as Recruiter\nFind Your Dream Tech Job"
  )
);

const urlOnly = sessionFromSignals({
  url: "https://www.hirist.tech/applied-jobs",
  body: "",
  hasAuthCookie: false,
  jobfeedStatus: 0,
});
assert.strictEqual(urlOnly.ok, false, "applied-jobs URL alone is not login");

const publicEmpty = sessionFromSignals({
  url: "https://www.hirist.tech/applied-jobs",
  body: "You Don't Have Applied Jobs",
  hasAuthCookie: false,
  jobfeedStatus: 401,
  jobfeedError: "UNAUTHORISED_ACCESS",
});
assert.strictEqual(publicEmpty.ok, false);
assert.strictEqual(publicEmpty.reason, "public_applied_jobs");

const apiOk = sessionFromSignals({
  url: "https://www.hirist.tech/applied-jobs",
  body: "You Don't Have Applied Jobs",
  hasAuthCookie: true,
  jobfeedStatus: 200,
});
assert.strictEqual(apiOk.ok, true);
assert.strictEqual(apiOk.reason, "jobfeed_ok");

const stale = sessionFromSignals({
  url: "https://www.hirist.tech/applied-jobs",
  hasAuthCookie: true,
  jobfeedStatus: 401,
  jobfeedError: "UNAUTHORISED_ACCESS",
});
assert.strictEqual(stale.ok, false);
assert.strictEqual(stale.reason, "stale_cookie");

console.log("hirist login_state ok");
