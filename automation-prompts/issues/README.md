# Per-portal issue logs (anti-collision)

Parallel cloud portal crons + home evening replicas used to all append the **same**
`automation-prompts/ISSUES_AND_FIXES.md`. When those PRs squash-merged the same day,
Git left `<<<<<<<` conflict markers on `main` and broke the shared history.

**Rule:** each portal owns one file in this directory. Agents must only touch their
portal file. Use:

```bash
bash scripts/append-issue-fix.sh <portal> "<issue one-liner>" "<fix one-liner>"
```

Shared apply helpers under `tools/<portal>/` stay shared (cloud + home). Collision
was never about different apply code — it was about concurrent edits to one markdown
file. Home runs set `HOME_LOCAL=1` and skip already-applied jobs; they do not need
forked apply implementations.
