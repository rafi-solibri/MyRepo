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

const RESUME_CANDIDATES = [
  "/workspace/resumes/Rafi_Resume.docx",
  "/home/ubuntu/resumes/Rafi_Resume.docx",
  "/home/ubuntu/Documents/Rafi_Resume.docx",
  "/workspace/resumes/Rafi_Resume_Architect.docx",
];

function findResume() {
  const fs = require("fs");
  for (const p of RESUME_CANDIDATES) {
    if (fs.existsSync(p) && fs.statSync(p).size > 1000) return p;
  }
  return null;
}

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
  buildAnswerPayload,
  answersNonEmpty,
  RESUME_CANDIDATES,
  EXPECTED_CTC_LPA: 65,
  CURRENT_CTC_LPA: 52,
};

if (require.main === module) {
  console.log(JSON.stringify({ resume: findResume(), expectedCtc: 65 }, null, 2));
}
