"use strict";

const assert = require("assert");
const {
  authFailureReason,
  isCreateAccountConsentRequired,
  workdayQuestionAnswer,
  needsIndiaCountryFix,
  pickPromptAlreadySatisfied,
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

assert.strictEqual(
  workdayQuestionAnswer("Are you over the age of 18?").options[0].toString(),
  "/^Yes$/i"
);
assert.strictEqual(
  workdayQuestionAnswer(
    "Will you require sponsorship now or in the future to be authorized to work"
  ).options[0].toString(),
  "/^No$/i"
);
assert.strictEqual(
  workdayQuestionAnswer(
    "Have you previously signed or are you subject to any non compete"
  ).options[0].toString(),
  "/^No$/i"
);
assert.strictEqual(
  workdayQuestionAnswer("When are you available to start?").text,
  "Immediate"
);
assert.strictEqual(
  workdayQuestionAnswer(
    "What is the desired salary and total compensation range that you are seeking"
  ).text,
  "65 LPA"
);
assert.strictEqual(workdayQuestionAnswer("How did you hear about us?"), null);

assert.strictEqual(needsIndiaCountryFix("India"), false);
assert.strictEqual(needsIndiaCountryFix("Holy See (Vatican City State)"), true);
assert.strictEqual(needsIndiaCountryFix("United States"), true);
assert.strictEqual(needsIndiaCountryFix("Select One"), true);

assert.strictEqual(
  pickPromptAlreadySatisfied("How Did You Hear About Us?* Other", [
    /Other/i,
  ]),
  true
);
assert.strictEqual(
  pickPromptAlreadySatisfied("Select One", [/Other/i]),
  false
);

console.log("test_workday_auth: ok");
