#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  titleCasePersonName,
  indiaMobileDigits,
  nameNeedsTitleCaseFix,
  phoneNeedsIndiaFix,
  workdayCompliantPassword,
} = require("./workday_apply");

assert.strictEqual(titleCasePersonName("MOHAMMED ABDUL RAFI"), "Mohammed Abdul Rafi");
assert.strictEqual(titleCasePersonName("AHMED"), "Ahmed");
assert.strictEqual(titleCasePersonName("  rafi   ahmed "), "Rafi Ahmed");
assert.strictEqual(titleCasePersonName("Mohammed Abdul Rafi"), "Mohammed Abdul Rafi");

assert.strictEqual(indiaMobileDigits("8790251698"), "8790251698");
assert.strictEqual(indiaMobileDigits("+91 8790251698"), "8790251698");
assert.strictEqual(indiaMobileDigits("918790251698"), "8790251698");
assert.strictEqual(indiaMobileDigits("08790251698"), "8790251698");
assert.strictEqual(indiaMobileDigits("(879) 025-1698"), "8790251698");
assert.strictEqual(indiaMobileDigits(""), "8790251698");
assert.strictEqual(indiaMobileDigits("123"), "8790251698");

assert.strictEqual(nameNeedsTitleCaseFix("MOHAMMED ABDUL RAFI"), true);
assert.strictEqual(nameNeedsTitleCaseFix("AHMED"), true);
assert.strictEqual(nameNeedsTitleCaseFix("Mohammed Abdul Rafi"), false);
assert.strictEqual(nameNeedsTitleCaseFix(""), true);

assert.strictEqual(phoneNeedsIndiaFix(""), true);
assert.strictEqual(phoneNeedsIndiaFix("8790251698"), false);
assert.strictEqual(phoneNeedsIndiaFix("+918790251698"), true);
assert.strictEqual(phoneNeedsIndiaFix("91 8790 251698"), true);

const pw = workdayCompliantPassword("short");
assert.ok(pw.length >= 12);
assert.ok(/[A-Z]/.test(pw) && /[a-z]/.test(pw) && /[0-9]/.test(pw) && /[^A-Za-z0-9]/.test(pw));

console.log("test_workday_apply.js ok");
