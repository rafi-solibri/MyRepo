#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  scoreChatbotOption,
  preferChatbotCheckboxValues,
} = require("./chatbot_answers");

assert.ok(scoreChatbotOption(".Net") > scoreChatbotOption("Java"));
assert.ok(scoreChatbotOption("C#") > scoreChatbotOption("Python"));
assert.deepStrictEqual(preferChatbotCheckboxValues([".Net", "Java"]), [".Net"]);
assert.deepStrictEqual(preferChatbotCheckboxValues(["Java", "Python"]), ["Java"]);
assert.deepStrictEqual(
  preferChatbotCheckboxValues(["Azure", ".NET Core"]),
  ["Azure", ".NET Core"]
);
assert.deepStrictEqual(preferChatbotCheckboxValues(["Yes", "No"]), ["Yes"]);
assert.ok(
  scoreChatbotOption("Never served") >
    scoreChatbotOption("Currently serving")
);
assert.deepStrictEqual(
  preferChatbotCheckboxValues([
    "Currently serving",
    "Previously served",
    "Never served",
  ]),
  ["Never served"]
);
assert.deepStrictEqual(preferChatbotCheckboxValues([]), []);
console.log("chatbot_answers self-test OK");
