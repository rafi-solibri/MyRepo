#!/usr/bin/env node
/** Unit checks for Hirist Google SSO helpers. */
"use strict";

const assert = require("assert");
const {
  isGooglePasswordChallenge,
  isGoogle2faChallenge,
  isHiristAuthCookieName,
} = require("./google_login");

const pwdUrl =
  "https://accounts.google.com/v3/signin/challenge/pwd?app_domain=https://www.hirist.tech";
assert.strictEqual(isGooglePasswordChallenge(pwdUrl, "Enter your password"), true);
assert.strictEqual(
  isGoogle2faChallenge(pwdUrl, "Enter your password"),
  false,
  "password URL must not be treated as 2FA"
);

const totpUrl = "https://accounts.google.com/v3/signin/challenge/totp";
assert.strictEqual(isGoogle2faChallenge(totpUrl, "Enter a code"), true);
assert.strictEqual(
  isGoogle2faChallenge("https://accounts.google.com/signin", "2-Step Verification"),
  true
);

assert.ok(isHiristAuthCookieName("hirist_seeker_enc"));
assert.ok(isHiristAuthCookieName("token"));
assert.ok(!isHiristAuthCookieName("PHPSESSID"));

console.log("hirist google_login helpers ok");
