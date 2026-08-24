# Hirist issues log

Portal-scoped log. Append via `bash scripts/append-issue-fix.sh hirist "issue" "fix"`.

| Date | Issue | Fix |
| --- | --- | --- |
| 2026-08-24 | No dedicated Hirist daily automation — Naukri only soft-skipped Hirist CTAs (`hirist_login_required_skip`) | Added `tools/hirist/*` runner + `09-hirist.md`, wired into Daily Apply Portals / home tasks / notification |
