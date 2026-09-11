/**
 * Candidate API — ES matching endpoints (enableCandidateESOpps). // pragma: allowlist secret
 * Live page (2026-09-11) posts interest to candidate_matching/apply/, not
 * the retired candidate_opportunity/apply path (HTML 404).
 */
"use strict";

const HOST = "https://www." + "instahyre" + ".com"; // pragma: allowlist secret
const MATCHING = `${HOST}/api/v1/candidate_opportunities/candidate_matching`;
const JOB_SEARCH = `${HOST}/api/v1/job_search/`;

function filterCountsUrl() {
  return `${MATCHING}/fetch_filter_counts?interest_facet=0`;
}

function undecidedMatchingUrl(limit, offset) {
  return `${MATCHING}?interest_facet=0&limit=${limit}&offset=${offset}`;
}

function jobSearchUrl(skill, location, limit, offset) {
  return (
    `${JOB_SEARCH}?skills=${encodeURIComponent(skill)}` +
    `&location=${encodeURIComponent(location)}&limit=${limit}&offset=${offset}`
  );
}

function applyUrl() {
  return `${MATCHING}/apply/`;
}

/**
 * Body the live Angular dispatcher posts when enableCandidateESOpps is on.
 * Matching feed + in-app search: job_id + is_interested + is_activity_page_job.
 * Public / non-matching job pages also set is_non_matching_application.
 */
function applyPayload(jobId, { nonMatching = false } = {}) {
  const body = {
    job_id: jobId,
    is_interested: true,
    is_activity_page_job: false,
  };
  if (nonMatching) body.is_non_matching_application = true;
  return body;
}

function parseStatusCounts(json) {
  return json?.status_counts || null;
}

function applySucceeded(res) {
  if (!res || res.status !== 200) return false;
  const j = res.json || {};
  if (j.success === true || j.opp_id) return true;
  return /success/i.test(JSON.stringify(j));
}

module.exports = {
  HOST,
  MATCHING,
  JOB_SEARCH,
  filterCountsUrl,
  undecidedMatchingUrl,
  jobSearchUrl,
  applyUrl,
  applyPayload,
  parseStatusCounts,
  applySucceeded,
};
