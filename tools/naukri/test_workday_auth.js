"use strict";

const assert = require("assert");
const {
  authFailureReason,
  isCreateAccountConsentRequired,
} = require("./workday_apply");

// Static checklist alone must NOT be treated as a policy error.
assert.strictEqual(
  authFailureReason(
    "Create Account\nPassword Requirements:\n- minimum of 8 characters\n- one number\n- one special character"
  ),
  null
);

// Real validation error line should classify as policy.
assert.strictEqual(
  authFailureReason(
    "Error\nPassword does not meet the requirements\nPassword Requirements:\n- minimum of 8 characters"
  ),
  "ats_password_policy"
);

assert.strictEqual(
  authFailureReason("Error: wrong email address or password. Try again."),
  "ats_login_wall"
);

assert.strictEqual(authFailureReason(""), null);

// Blackbaud-style Create Account: no consent control → allow submit.
assert.strictEqual(
  isCreateAccountConsentRequired({
    checkboxPresent: false,
    consentCopyPresent: false,
  }),
  false
);
// Wells Fargo-style: checkbox or consent copy is required.
assert.strictEqual(
  isCreateAccountConsentRequired({
    checkboxPresent: true,
    consentCopyPresent: false,
  }),
  true
);
assert.strictEqual(
  isCreateAccountConsentRequired({
    checkboxPresent: false,
    consentCopyPresent: true,
  }),
  true
);

console.log("test_workday_auth: ok");
