/**
 * Naukri TopTier recruiter-chatbot option scoring.
 * Used by daily_apply.js (passed into page.evaluate) and unit tests.
 */
"use strict";

/** Prefer these skill/location chips over Java/Python-only options. */
const CHATBOT_PREFER_RE =
  /\.net|dotnet|c#|csharp|azure|yes|hyderabad|secunderabad|remote|wfh|immediate/i;

function scoreChatbotOption(text) {
  const s = String(text || "").trim();
  if (/^yes$/i.test(s)) return 10_000;
  if (/never served/i.test(s)) return 9_500;
  if (/immediate|serving notice|available/i.test(s) && !/currently serving|previously served/i.test(s))
    return 9_000;
  if (/hyderabad|secunderabad|remote|work from home|wfh|any location/i.test(s))
    return 8_000;
  if (/\.net|dotnet|c#|csharp|azure/i.test(s)) return 7_500;
  if (/currently serving|previously served/i.test(s)) return -1;
  if (/^no$/i.test(s)) return -1;
  const nums = (s.match(/\d+/g) || []).map(Number);
  if (!nums.length) return 0;
  const top = Math.max(...nums);
  if (/>|plus|\+/i.test(s)) return top + 50;
  return top;
}

/**
 * Pick which multiselect checkbox labels to tick.
 * Prefer .NET/C#/Azure/Yes; if none, take the single highest-scoring option
 * so Save can enable (Jade: .Net + Java → .Net only).
 */
function preferChatbotCheckboxValues(values) {
  const list = (values || []).map((v) => String(v || "").trim()).filter(Boolean);
  if (!list.length) return [];
  const scored = list
    .map((v) => ({ v, s: scoreChatbotOption(v) }))
    .sort((a, b) => b.s - a.s);
  const top = scored[0].s;
  if (top >= 7500) return scored.filter((x) => x.s >= 7500).map((x) => x.v);
  return [scored[0].v];
}

module.exports = {
  CHATBOT_PREFER_RE,
  scoreChatbotOption,
  preferChatbotCheckboxValues,
};
