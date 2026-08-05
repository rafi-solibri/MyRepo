#!/usr/bin/env node
/**
 * Fallback sender when Resend MCP tools are unavailable but RESEND_API_KEY
 * is present in the environment. Prefer the Resend MCP in automations.
 *
 * Usage:
 *   node scripts/send-job-status-email.mjs \
 *     --to rafi.success@gmail.com \
 *     --subject "Job status — 2026-08-05" \
 *     --body-file ./report.md
 *
 * Env:
 *   RESEND_API_KEY (required)
 *   RESEND_FROM_EMAIL (required)
 */
import { readFileSync } from "node:fs";

function usage() {
  console.error(
    "Usage: node scripts/send-job-status-email.mjs --to <email> --subject <text> (--body <text> | --body-file <path>)",
  );
  process.exit(2);
}

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i === -1 || i + 1 >= process.argv.length) return null;
  return process.argv[i + 1];
}

const to = argValue("--to");
const subject = argValue("--subject");
const bodyInline = argValue("--body");
const bodyFile = argValue("--body-file");
const apiKey = process.env.RESEND_API_KEY;
const from = process.env.RESEND_FROM_EMAIL;

if (!to || !subject || (!bodyInline && !bodyFile)) usage();
if (!apiKey) {
  console.error("Missing RESEND_API_KEY");
  process.exit(1);
}
if (!from) {
  console.error("Missing RESEND_FROM_EMAIL");
  process.exit(1);
}

const text = bodyInline ?? readFileSync(bodyFile, "utf8");

const res = await fetch("https://api.resend.com/emails", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    from,
    to: [to],
    subject,
    text,
  }),
});

const payload = await res.json().catch(() => ({}));
if (!res.ok) {
  console.error("Resend API error:", res.status, payload);
  process.exit(1);
}

console.log("Email sent:", payload.id ?? payload);
