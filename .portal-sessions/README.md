# Portal session seed (private)

Authenticated Chrome cookie DBs for the 6 daily job portals, captured from a
working Cloud Agent Desktop VM.

**Private repo only.** These files let `scripts/cloud-agent-install.sh` and
`scripts/cloud-agent-start.sh` restore sessions during environment builds so
cron agents do not boot into empty login walls.

Refresh when sessions expire:
```bash
bash scripts/open-portal-login-tabs.sh   # sign in on Desktop
# quit Chrome, then:
bash scripts/verify-portal-logins.sh --strict
# re-copy Cookies into this folder (or ask the agent to refresh the seed)
```
