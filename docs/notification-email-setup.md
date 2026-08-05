# Notification email setup (Resend)

Cursor Automations have no built-in **Send Email** tool. Job-status emails go through the **Resend MCP**.

## 1. Resend account

1. Create an account at [resend.com](https://resend.com).
2. Create an API key: [API keys](https://resend.com/api-keys).
3. Verify a sending domain: [Domains](https://resend.com/domains) (SPF/DKIM).
4. Pick a From address on that domain, e.g. `notifications@yourdomain.com`.

`rafi.success@gmail.com` is the **recipient**. It cannot be the From address unless you own and verify that domain in Resend. Resend’s `onboarding@resend.dev` test sender only delivers to your Resend account email.

## 2. Cloud Agent secrets

In the Cloud Agent environment secrets UI, add:

| Secret | Required | Example |
|--------|----------|---------|
| `RESEND_API_KEY` | Yes | `re_...` |
| `RESEND_FROM_EMAIL` | Yes | `notifications@yourdomain.com` |

## 3. Add Resend MCP for Cloud Agents

Preferred: [Resend Marketplace MCP](https://cursor.com/marketplace/mcp/resend) or custom HTTP MCP under [cursor.com/agents](https://cursor.com/agents) / Team [Integrations & MCP](https://cursor.com/dashboard/integrations):

```json
{
  "mcpServers": {
    "resend": {
      "url": "https://mcp.resend.com/mcp",
      "headers": {
        "Authorization": "Bearer re_YOUR_API_KEY"
      }
    }
  }
}
```

Paste the real API key into the header. Cloud Agent MCP config does not interpolate `${env:...}` secrets.

This repo also includes `.cursor/mcp.json` (URL only) for local/IDE OAuth against the same Resend MCP endpoint.

## 4. Enable on Notification Job 11 AM

1. Open [Notification Job 11 AM](https://cursor.com/automations/8e34696c-90b1-11f1-ba66-0e7d0216e441).
2. Tools → enable **MCP server** → select Resend.
3. Append the prompt block from `docs/notification-email-prompt-snippet.md`.
4. Save / activate.

If the automation is **Team Owned**, configure Resend MCP for the team automations service account.

## 5. Smoke test

Run the automation once (or wait for the next cron). Confirm:

- Resend MCP tools appear in the run.
- An email arrives at `rafi.success@gmail.com`.
- Resend dashboard shows a delivered event.
