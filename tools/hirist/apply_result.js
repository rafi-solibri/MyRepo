/**
 * Parse Hirist POST /job/apply-multiple responses.
 *
 * HTTP 200 is not enough: the API returns a JSON array of
 * `{ success: false, message: { message } }` when assessment/screening
 * is required, and daily_apply previously counted that as applied.
 */
"use strict";

function flattenMessage(value) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "object") {
    return String(value.message || value.error || value.reason || JSON.stringify(value));
  }
  return String(value);
}

function itemsFromPayload(json) {
  if (Array.isArray(json)) return json;
  if (Array.isArray(json?.data)) return json.data;
  if (Array.isArray(json?.data?.jobs)) return json.data.jobs;
  return null;
}

/**
 * @param {{ status?: number, json?: any }} res
 * @returns {{ kind: "applied"|"already"|"rejected"|"login", reason: string, message: string }}
 */
function interpretApplyMultiple(res) {
  const status = Number(res && res.status);
  const json = res && res.json;
  const errName = json?.error?.name || "";
  if (status === 401 || /UNAUTHORISED/i.test(String(errName))) {
    return { kind: "login", reason: "hirist_login_required", message: "apply_401" };
  }

  const items = itemsFromPayload(json);
  if (items) {
    const fails = items.filter((x) => x && x.success === false);
    const oks = items.filter((x) => x && x.success === true);
    if (fails.length && !oks.length) {
      const message = fails.map((f) => flattenMessage(f.message || f.reason || f.error)).join("; ");
      if (/already applied|duplicate/i.test(message)) {
        return { kind: "already", reason: "already_applied", message };
      }
      if (/assessment|screening/i.test(message)) {
        return { kind: "rejected", reason: "assessment_required", message };
      }
      return { kind: "rejected", reason: message.slice(0, 160) || "apply_failed", message };
    }
    if (oks.length) {
      return { kind: "applied", reason: "hirist_apply", message: "success" };
    }
    if (items.length === 0 && status >= 200 && status < 300) {
      return { kind: "rejected", reason: "apply_unconfirmed_empty", message: "empty apply-multiple payload" };
    }
  }

  if (json?.error) {
    const message = flattenMessage(json.error.message || json.error);
    if (/already applied|duplicate/i.test(message)) {
      return { kind: "already", reason: "already_applied", message };
    }
    return { kind: "rejected", reason: String(message).slice(0, 160), message };
  }

  if (status >= 200 && status < 300) {
    if (json && json.success === false) {
      const message = flattenMessage(json.message);
      if (/assessment|screening/i.test(message)) {
        return { kind: "rejected", reason: "assessment_required", message };
      }
      return { kind: "rejected", reason: message.slice(0, 160) || "apply_failed", message };
    }
    if (json && (json.success === true || Number(json.status?.code) === 200)) {
      return { kind: "applied", reason: "hirist_apply", message: "success" };
    }
    return {
      kind: "rejected",
      reason: `apply_http_${status}_unconfirmed`,
      message: "HTTP 200 without explicit success",
    };
  }

  const fallback =
    flattenMessage(json?.status?.message) ||
    flattenMessage(json?.error?.message) ||
    `apply_http_${status}`;
  return { kind: "rejected", reason: String(fallback).slice(0, 160), message: fallback };
}

function appliedJobIdFromRow(row) {
  if (!row || typeof row !== "object") return null;
  const id = row.jobDetail?.id || row.jobId || row.job?.id;
  const n = Number(id);
  return Number.isFinite(n) && n > 0 ? n : null;
}

module.exports = {
  interpretApplyMultiple,
  appliedJobIdFromRow,
  flattenMessage,
};
