"use strict";

const assert = require("assert");
const { normalizeWorkdayPhone } = require("./workday_apply");

assert.strictEqual(normalizeWorkdayPhone("8790251698"), "8790251698");
assert.strictEqual(normalizeWorkdayPhone("+91 8790251698"), "8790251698");
assert.strictEqual(normalizeWorkdayPhone("+91-8790251698"), "8790251698");
assert.strictEqual(normalizeWorkdayPhone("91 8790251698"), "8790251698");
assert.strictEqual(normalizeWorkdayPhone("918790251698"), "8790251698");
assert.strictEqual(normalizeWorkdayPhone(""), "8790251698");

console.log("test_workday_phone: ok");
