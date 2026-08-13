# Portal session seed (private)

Authenticated Chrome cookie DBs for the 6 daily job portals, captured from a
working Cloud Agent Desktop VM.

**Private repo only.** These files let `scripts/cloud-agent-install.sh` and
`scripts/cloud-agent-start.sh` restore sessions during environment builds so
cron agents do not boot into empty login walls.

Refresh when sessions expire:
```bash
# Preferred (unattended after live login succeeds):
bash scripts/launch-chrome-cdp.sh linkedin   # auto-login + refresh-portal-session-seed.sh
# Or manually:
bash scripts/refresh-portal-session-seed.sh linkedin --commit
git push   # so next cloud boot restores the new Cookies

# Manual headed path:
bash scripts/home-headed-login.sh linkedin
bash scripts/refresh-portal-session-seed.sh linkedin --commit
```

Cloud LinkedIn Chrome uses WARP SOCKS by default (same as Indeed) to reduce
datacenter CAPTCHA. Set `LINKEDIN_SKIP_WARP=1` on residential home.
