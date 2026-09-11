#!/usr/bin/env node
"use strict";

const assert = require("assert");
const { passwordCandidates, isLoggedOut, isGoogle2faChallenge, HOME, DASH, PORTAL } = require("./google_login");

assert.ok(new RegExp(`${PORTAL}\\.io\\/?$`).test(HOME), `HOME must be homepage, got ${HOME}`);
assert.doesNotMatch(HOME, /\/login$/, "HOME must not use the 404 /login path");
assert.ok(/candidate-dashboard/.test(DASH), "DASH must be candidate dashboard");

{
  const prev = process.env.LINKEDIN_PASSWORD;
  const gprev = process.env.GOOGLE_PASSWORD;
  process.env.LINKEDIN_PASSWORD = "linkedin-only-secret";
  delete process.env.GOOGLE_PASSWORD;
  delete process.env.GMAIL_PASSWORD;
  const pws = passwordCandidates();
  assert.strictEqual(pws.length, 0, "must not cross-feed LINKEDIN_PASSWORD into Google SSO");
  process.env.GOOGLE_PASSWORD = "gmail-only-secret";
  const g = passwordCandidates();
  assert.deepStrictEqual(g, ["gmail-only-secret"]);
  if (prev == null) delete process.env.LINKEDIN_PASSWORD;
  else process.env.LINKEDIN_PASSWORD = prev;
  if (gprev == null) delete process.env.GOOGLE_PASSWORD;
  else process.env.GOOGLE_PASSWORD = gprev;
}

assert.ok(
  isLoggedOut(`https://${PORTAL}.io/?redirect_url=%2Fprofile%2Fcandidate-dashboard`, "Candidate login"),
  "redirect_url home is logged out"
);
assert.ok(
  isLoggedOut(`https://${PORTAL}.io/`, "Candidate login\nFor Employers\nGet started"),
  "marketing home is logged out"
);
assert.ok(
  !isLoggedOut(
    `https://${PORTAL}.io/profile/candidate-dashboard`,
    "Matches for you\nRecommended jobs\nYour profile"
  ),
  "dashboard is logged in"
);

assert.ok(
  isGoogle2faChallenge(
    "https://accounts.google.com/v3/signin/challenge/dp",
    "Check your phone. Tap Yes on the notification"
  ),
  "device-prompt challenge/dp is 2FA"
);
assert.ok(
  !isGoogle2faChallenge(
    "https://accounts.google.com/v3/signin/challenge/pwd",
    "Enter your password"
  ),
  "challenge/pwd is not 2FA"
);

console.log("portal test_google_login: ok");
