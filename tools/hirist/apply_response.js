/**
 * Interpret Hirist POST /job/apply-multiple payloads.
 *
 * Success is an array item with message "Successfully Applied to Job" (no success:true).
 * Failure is HTTP 200 + [{ success: false, message: { message: "..." } }].
 */
"use strict";

function itemMessage(item) {
  if (item == null) return "";
  if (typeof item === "string") return item;
  if (typeof item.message === "string") return item.message;
  if (item.message && typeof item.message.message === "string") return item.message.message;
  if (typeof item.error === "string") return item.error;
  if (item.error && typeof item.error.message === "string") return item.error.message;
  return "";
}

function flattenItems(json) {
  if (Array.isArray(json)) return json;
  if (json == null) return [];
  return [json];
}

/**
 * @param {{ status?: number, json?: any }} res
 * @returns {{ kind: "ok"|"already"|"assessment"|"login"|"rejected", message: string }}
 */
function interpretApplyResponse(res) {
  const json = res && res.json;
  const status = Number(res && res.status);
  const errName = json && json.error && json.error.name;
  if (status === 401 || /UNAUTHORISED/i.test(String(errName || ""))) {
    return { kind: "login", message: "apply_401" };
  }

  const items = flattenItems(json);
  const msg = items.map(itemMessage).filter(Boolean).join(" | ") || itemMessage(json);

  if (items.some((x) => x && x.success === false)) {
    if (/already applied|duplicate/i.test(msg)) return { kind: "already", message: msg };
    if (/assessment|screening/i.test(msg)) return { kind: "assessment", message: msg };
    return { kind: "rejected", message: msg || "apply_failed" };
  }

  if (/successfully applied/i.test(msg) || /successfully applied/i.test(JSON.stringify(json || ""))) {
    return { kind: "ok", message: msg || "applied" };
  }

  if (/already applied|duplicate/i.test(msg)) return { kind: "already", message: msg };
  if (/assessment|screening/i.test(msg)) return { kind: "assessment", message: msg };

  if (status >= 200 && status < 300 && json && !json.error && items.some((x) => x && x.data && (x.data.jobId || x.data.id))) {
    return { kind: "ok", message: msg || "applied" };
  }

  return { kind: "rejected", message: msg || `apply_http_${status || "unknown"}` };
}

module.exports = { interpretApplyResponse, itemMessage };
