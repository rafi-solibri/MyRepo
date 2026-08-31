/**
 * Parse Hirist POST /job/apply-multiple bodies.
 * HTTP 200 + [{success:false,...}] is NOT an apply.
 */
"use strict";

function itemMessage(item) {
  if (item == null) return "";
  if (typeof item === "string") return item;
  const m = item.message;
  if (typeof m === "string") return m;
  if (m && typeof m.message === "string") return m.message;
  if (item.error && typeof item.error.message === "string") return item.error.message;
  return "";
}

function itemSuccess(item) {
  if (item == null || typeof item !== "object") return false;
  if (item.success === true) return true;
  if (item.success === false) return false;
  const st = String(item.status || item.statusCode || "").toLowerCase();
  if (st === "success" || st === "ok" || st === "applied") return true;
  return false;
}

/**
 * @returns {{
 *   applied: boolean,
 *   assessmentRequired: boolean,
 *   alreadyApplied: boolean,
 *   message: string,
 *   results: Array<{success: boolean, message: string}>
 * }}
 */
function parseApplyMultiple(json) {
  if (json == null) {
    return {
      applied: false,
      assessmentRequired: false,
      alreadyApplied: false,
      message: "empty_apply_response",
      results: [],
    };
  }
  if (json.error) {
    const message = itemMessage(json.error) || itemMessage(json) || String(json.error.name || "error");
    return {
      applied: false,
      assessmentRequired: /assessment|screening/i.test(message),
      alreadyApplied: /already applied|duplicate/i.test(message),
      message,
      results: [{ success: false, message }],
    };
  }

  let items = [];
  if (Array.isArray(json)) items = json;
  else if (Array.isArray(json.data)) items = json.data;
  else if (Array.isArray(json.results)) items = json.results;
  else items = [json];

  const results = items.filter((x) => x != null).map((item) => {
    const message = itemMessage(item);
    return { success: itemSuccess(item), message };
  });

  const applied = results.length > 0 && results.every((r) => r.success);
  const joined = results.map((r) => r.message).filter(Boolean).join("; ");
  const firstFail = results.find((r) => !r.success);
  return {
    applied,
    assessmentRequired: results.some((r) => /assessment|screening/i.test(r.message)),
    alreadyApplied: results.some((r) => /already applied|duplicate/i.test(r.message)),
    message: applied ? "ok" : firstFail?.message || joined || "apply_failed",
    results,
  };
}

function jobAlreadyAppliedFlag(job) {
  if (!job || typeof job !== "object") return false;
  if (job.applied === true || job.applied === 1 || job.applied === "1") return true;
  if (Number(job.applied) === 1) return true;
  return false;
}

module.exports = {
  parseApplyMultiple,
  itemMessage,
  itemSuccess,
  jobAlreadyAppliedFlag,
};
