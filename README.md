# MyRepo

## Notification email

Job-status emails for **Notification Job 11 AM** use Resend (no built-in Cursor email action).

See [docs/notification-email-setup.md](docs/notification-email-setup.md) for the full checklist (Resend API key, verified domain, Cloud Agent MCP, automation tool enablement).

Prompt snippet: [docs/notification-email-prompt-snippet.md](docs/notification-email-prompt-snippet.md)

Fallback CLI (only if `RESEND_API_KEY` / `RESEND_FROM_EMAIL` are set and MCP is unavailable):

```bash
node scripts/send-job-status-email.mjs \
  --to rafi.success@gmail.com \
  --subject "Job status — $(date -u +%F)" \
  --body-file ./report.md
```
