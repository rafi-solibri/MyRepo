/**
 * Hirist already-applied helpers — skip jobs present on /job/applied-jobs.
 */
"use strict";

const IST = "Asia/Kolkata";

function istDayStartMs(now = Date.now()) {
  const fmt = new Intl.DateTimeFormat("en-CA", {
    timeZone: IST,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const day = fmt.format(new Date(now));
  return Date.parse(`${day}T00:00:00+05:30`);
}

function jobIdFromAppliedRow(row) {
  const id = row?.jobDetail?.id ?? row?.jobId ?? row?.job_id;
  const n = Number(id);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function collectAppliedJobIds(rows) {
  const ids = new Set();
  for (const row of rows || []) {
    const id = jobIdFromAppliedRow(row);
    if (id) ids.add(id);
  }
  return ids;
}

function applyLanded(before, after, jobId) {
  const id = Number(jobId);
  const prevCount = Number(before?.count || 0);
  const nextCount = Number(after?.count || 0);
  const last = Number(after?.lastAppliedJobId || 0);
  if (Number.isFinite(id) && id > 0 && last === id) return true;
  if (nextCount > prevCount) return true;
  return false;
}

function idsFromReport(json) {
  const ids = new Set();
  if (!json || typeof json !== "object") return ids;
  for (const row of [...(json.applied || []), ...(json.external || [])]) {
    const n = Number(row?.id ?? row?.jobId);
    if (Number.isFinite(n) && n > 0) ids.add(n);
  }
  for (const raw of json.ids || json.jobIds || []) {
    const n = Number(raw);
    if (Number.isFinite(n) && n > 0) ids.add(n);
  }
  return ids;
}

module.exports = {
  IST,
  istDayStartMs,
  jobIdFromAppliedRow,
  collectAppliedJobIds,
  applyLanded,
  idsFromReport,
};
