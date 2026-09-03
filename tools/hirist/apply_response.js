/**
 * Parse Hirist apply-multiple + applied-jobs API shapes.
 * apply-multiple returns HTTP 200 with [{ success, message }] — not { error }.
 */
"use strict";

function firstRow(json) {
  if (Array.isArray(json)) return json[0] || {};
  if (Array.isArray(json?.data)) return json.data[0] || {};
  if (json && typeof json === "object") return json;
  return {};
}

function messageOf(row) {
  if (!row) return "";
  const m = row.message;
  if (typeof m === "string") return m;
  if (m && typeof m === "object") return m.message || m.msg || "";
  return row.status?.message || row.error?.message || "";
}

/**
 * @param {{ status: number, json: any }} res
 * @returns {{ ok: boolean, alreadyApplied?: boolean, assessmentRequired?: boolean, reason: string }}
 */
function parseApplyMultipleResponse(res) {
  const status = Number(res?.status || 0);
  const json = res?.json;
  if (status === 401 || /UNAUTHORISED/i.test(String(json?.error?.name || ""))) {
    return { ok: false, reason: "apply_401" };
  }
  if (json?.error) {
    const reason = String(json.error.message || json.error.name || `apply_http_${status}`);
    return {
      ok: false,
      alreadyApplied: /already applied|duplicate/i.test(reason),
      reason,
    };
  }
  const row = firstRow(json);
  const msg = messageOf(row);
  if (row.success === true) {
    return { ok: true, reason: msg || "applied" };
  }
  const reason = msg || (status >= 200 && status < 300 ? "apply_success_false" : `apply_http_${status}`);
  return {
    ok: false,
    alreadyApplied: /already applied|duplicate/i.test(reason),
    assessmentRequired: /assessment|screening is required/i.test(reason),
    reason: String(reason).slice(0, 160),
  };
}

function extractAppliedJobIds(payload) {
  const jobs = payload?.data?.jobs || payload?.jobs || payload?.data || [];
  const ids = new Set();
  if (!Array.isArray(jobs)) return ids;
  for (const j of jobs) {
    const id = j?.jobDetail?.id ?? j?.jobId ?? j?.job_id ?? j?.refJobId;
    if (id != null && id !== "") ids.add(Number(id));
  }
  return ids;
}

function searchHitAlreadyApplied(job) {
  if (!job) return false;
  if (job.applied === true || Number(job.applied) === 1) return true;
  if (Number(job.applyStatus) === 0 && !job.applyUrl) return true;
  return false;
}

module.exports = {
  parseApplyMultipleResponse,
  extractAppliedJobIds,
  searchHitAlreadyApplied,
  messageOf,
};
