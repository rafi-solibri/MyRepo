#!/usr/bin/env node
/**
 * Cutshort questionnaire helper — CORRECT payload shape.
 *
 * NEVER set screeningSubmitted:true until answers are verified non-empty.
 * Wrong shape (nested question object + screeningSubmitted) returns 200 but
 * locks empty answers (400 on retry) — caused 9/11 empty Qs on 2026-08-05.
 *
 * Working body:
 * {
 *   messageId,
 *   questions: [{ _id: answerRowId, question: "<questionIdString>", responseStringArray: ["<optionId>"] }],
 * }
 * Then same + screeningSubmitted: true after loadthread verifies answers.
 */
"use strict";

const {
  findResume,
  resumeUploadPath,
  CANONICAL_NAME,
  RESUME_LABEL,
  LEGACY_ALIASES,
} = require("../resume_paths");

const RESUME_CANDIDATES = [
  `/workspace/resumes/${CANONICAL_NAME}`,
  `/home/ubuntu/resumes/${CANONICAL_NAME}`,
  `/home/ubuntu/Documents/${CANONICAL_NAME}`,
  ...LEGACY_ALIASES.map((n) => `/workspace/resumes/${n}`),
];

function buildAnswerPayload(messageId, answers) {
  // answers: [{ answerRowId, questionId, optionId }]
  return {
    messageId,
    questions: answers.map((a) => ({
      _id: a.answerRowId,
      question: String(a.questionId),
      responseStringArray: [String(a.optionId)],
    })),
  };
}

function answersNonEmpty(questions) {
  return (questions || []).every(
    (q) => Array.isArray(q.responseStringArray) && q.responseStringArray.length > 0
  );
}

module.exports = {
  findResume,
  resumeUploadPath,
  buildAnswerPayload,
  answersNonEmpty,
  RESUME_CANDIDATES,
  RESUME_LABEL,
  CANONICAL_NAME,
  EXPECTED_CTC_LPA: 65,
  CURRENT_CTC_LPA: 52,
};

if (require.main === module) {
  console.log(JSON.stringify({ resume: findResume(), expectedCtc: 65 }, null, 2));
}
