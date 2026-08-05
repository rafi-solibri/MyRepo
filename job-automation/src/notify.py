"""Digest + optional webhook/email notifications."""

from __future__ import annotations

import json
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import requests

from utils.models import Job, utc_now_iso


def write_digest(
    path: Path,
    matched: list[Job],
    new_jobs: list[Job],
    portal_links: dict[str, list[dict[str, str]]],
    pack_paths: list[Path],
    profile: dict[str, Any],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Daily job digest — {utc_now_iso()}",
        "",
        f"Candidate: **{profile.get('name')}** | Target CTC: **{profile.get('expected_ctc_lpa')} LPA**",
        f"Focus: Hyderabad + Remote WFH",
        "",
        f"- Matched today: **{len(matched)}**",
        f"- Newly seen (not in tracker before): **{len(new_jobs)}**",
        f"- Application packs written: **{len(pack_paths)}**",
        "",
        "## Important",
        "",
        "This automation **discovers, ranks, and packages** applications.",
        "It does **not** log into Naukri/LinkedIn/Indeed/etc. or auto-submit forms",
        "(that violates portal Terms of Service and can ban your account).",
        "Use the portal links below while logged in, then tick the checklist in each pack.",
        "",
        "## Portal quick links (manual Easy Apply)",
        "",
    ]
    for portal, links in portal_links.items():
        lines.append(f"### {portal.title()}")
        for link in links:
            lines.append(f"- [{link['label']}]({link['url']})")
        lines.append("")

    lines.append("## Top matched jobs")
    lines.append("")
    if not matched:
        lines.append("_No jobs met the match threshold today. Try broadening titles/skills in profile.yaml._")
    for i, job in enumerate(matched, 1):
        badge = "NEW" if any(j.id == job.id for j in new_jobs) else "seen"
        lines.extend(
            [
                f"### {i}. {job.title} @ {job.company} ({badge})",
                f"- Score: `{job.match_score}` | Source: `{job.source}` | Location: {job.location}",
                f"- Reasons: {', '.join(job.match_reasons) or 'n/a'}",
                f"- Salary: {job.salary_text or 'Not disclosed'}",
                f"- Apply: {job.url}",
                "",
            ]
        )

    if pack_paths:
        lines.append("## Application packs")
        lines.append("")
        for p in pack_paths:
            lines.append(f"- `{p.as_posix()}`")
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def send_webhook(digest_path: Path, matched_count: int, new_count: int) -> None:
    url = os.getenv("NOTIFY_WEBHOOK_URL", "").strip()
    if not url:
        return
    text = (
        f"Daily job hunt: {matched_count} matched, {new_count} new. "
        f"Digest: {digest_path.name}"
    )
    payload: dict[str, Any]
    # Slack-style and Discord-style both accept {"text": ...} or Discord {"content": ...}
    if "discord.com" in url or "discordapp.com" in url:
        payload = {"content": text}
    else:
        payload = {"text": text}
    try:
        requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=20)
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] webhook failed: {exc}")


def send_email(digest_path: Path) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    to_addr = os.getenv("NOTIFY_EMAIL_TO", "").strip() or user
    if not (host and user and password and to_addr):
        return
    port = int(os.getenv("SMTP_PORT", "587"))
    msg = MIMEText(digest_path.read_text(encoding="utf-8"), "plain", "utf-8")
    msg["Subject"] = f"Daily job digest — {digest_path.stem}"
    msg["From"] = user
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
    except Exception as exc:  # noqa: BLE001
        print(f"[notify] email failed: {exc}")
