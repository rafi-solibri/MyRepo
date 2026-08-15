#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  scoreChatbotOption,
  preferChatbotCheckboxValues,
} = require("./chatbot_answers");

assert.strictEqual(scoreChatbotOption("Yes"), 10_000);
assert.strictEqual(scoreChatbotOption("Never served"), 9_500);
assert.ok(scoreChatbotOption("Currently serving") < 0);
assert.ok(scoreChatbotOption(".Net") >= 7500);
assert.ok(scoreChatbotOption("Java") < 7500);

assert.deepStrictEqual(preferChatbotCheckboxValues([".Net", "Java"]), [".Net"]);
assert.deepStrictEqual(
  preferChatbotCheckboxValues(["Java", "Python"]).length,
  1,
  "no preferred stack → single highest option so Save enables"
);
assert.deepStrictEqual(
  preferChatbotCheckboxValues([".Net", "C#", "Java"]).sort(),
  [".Net", "C#"].sort()
);

console.log("test_chatbot_answers.js OK");
