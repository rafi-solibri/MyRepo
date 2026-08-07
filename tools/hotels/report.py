"""Build sorted tabular HTML / plain text / CSV for hotel price emails."""

from __future__ import annotations

import base64
import csv
import html
import io
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .requirements_spec import (
    EMAIL_FROM,
    EMAIL_SUBJECT_PREFIX,
    EMAIL_TO,
    REQUIRED_AREAS,
)


def sort_offers(offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        offers,
        key=lambda o: (o["date"], o["lowest_price_inr"], o["hotel"].lower()),
    )


def offers_to_csv(offers: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "Date",
            "Day",
            "Hotel",
            "Area",
            "Stars",
            "Lowest Price (INR)",
            "Lowest Provider",
            "All Providers",
            "Source",
        ]
    )
    for o in offers:
        all_p = "; ".join(
            f"{p['provider']}=₹{p['price_inr']}" for p in o.get("providers") or []
        )
        w.writerow(
            [
                o["date"],
                o.get("day", ""),
                o["hotel"],
                o.get("area", ""),
                o.get("stars", ""),
                o["lowest_price_inr"],
                o.get("lowest_provider", ""),
                all_p,
                o.get("source", ""),
            ]
        )
    return buf.getvalue()


def build_email_bodies(
    payload: dict[str, Any],
) -> tuple[str, str]:
    """Return (html, text) for the full inventory email."""
    offers = sort_offers(list(payload.get("offers") or []))
    areas = ", ".join(payload.get("areas") or list(REQUIRED_AREAS))
    providers = payload.get("providers_seen") or {}
    provider_line = ", ".join(f"{k} ({v})" for k, v in list(providers.items())[:16])

    by_date: dict[str, list] = defaultdict(list)
    for o in offers:
        by_date[o["date"]].append(o)

    rows_html: list[str] = []
    for date, group in by_date.items():
        day = group[0].get("day") or ""
        rows_html.append(
            f'<tr><td colspan="6" style="background:#0f3d2e;color:#fff;padding:8px 10px;'
            f'font-weight:600">{html.escape(date)} ({html.escape(str(day))}) — '
            f"{len(group)} hotels</td></tr>"
        )
        for o in group:
            all_p = "; ".join(
                f"{p['provider']}=₹{p['price_inr']:,}" for p in o.get("providers") or []
            )
            stars = o.get("stars")
            stars_s = f"{stars:g}★" if stars is not None else ""
            rows_html.append(
                "<tr>"
                f"<td style='padding:6px 8px;border-bottom:1px solid #e5e7eb'>{html.escape(o['hotel'])}</td>"
                f"<td style='padding:6px 8px;border-bottom:1px solid #e5e7eb'>{html.escape(o.get('area') or '')}</td>"
                f"<td style='padding:6px 8px;border-bottom:1px solid #e5e7eb;text-align:center'>{html.escape(stars_s)}</td>"
                f"<td style='padding:6px 8px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:600'>₹{o['lowest_price_inr']:,}</td>"
                f"<td style='padding:6px 8px;border-bottom:1px solid #e5e7eb'>{html.escape(o.get('lowest_provider') or '')}</td>"
                f"<td style='padding:6px 8px;border-bottom:1px solid #e5e7eb;font-size:12px;color:#374151'>{html.escape(all_p)}</td>"
                "</tr>"
            )

    html_body = f"""<!DOCTYPE html>
<html><body style="font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#111;line-height:1.4">
  <h2 style="margin:0 0 8px">{html.escape(EMAIL_SUBJECT_PREFIX)}</h2>
  <p style="margin:0 0 12px;color:#374151">
    Areas: {html.escape(areas)}<br>
    Filter: 4★ and above · Adults: 2 · Scope: remaining Sat/Sun this month<br>
    Hotels found: <strong>{len(offers)}</strong> (full inventory, deduped across areas)<br>
    Providers seen: {html.escape(provider_line)}
  </p>
  <p style="margin:0 0 16px;color:#6b7280;font-size:13px">
    Sorted by date, then ascending lowest price. Full CSV attached.
    Prices from Kayak’s live OTA comparison (Booking.com, Agoda, Expedia, brand sites, etc.).
  </p>
  <table style="border-collapse:collapse;width:100%;font-size:13px">
    <thead>
      <tr style="background:#f3f4f6;text-align:left">
        <th style="padding:8px">Hotel</th>
        <th style="padding:8px">Area</th>
        <th style="padding:8px">Stars</th>
        <th style="padding:8px">Lowest</th>
        <th style="padding:8px">Provider</th>
        <th style="padding:8px">All providers</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
</body></html>"""

    text_lines = [
        EMAIL_SUBJECT_PREFIX,
        f"Areas: {areas}",
        f"Hotels found: {len(offers)}",
        f"Providers: {provider_line}",
        "",
        "Date | Day | Hotel | Area | Stars | Lowest INR | Provider",
        "-" * 72,
    ]
    for o in offers:
        text_lines.append(
            f"{o['date']} | {o.get('day', '')} | {o['hotel']} | {o.get('area', '')} | "
            f"{o.get('stars')} | ₹{o['lowest_price_inr']:,} | {o.get('lowest_provider')}"
        )
    return html_body, "\n".join(text_lines)


def build_resend_payload(
    payload: dict[str, Any],
    *,
    idempotency_key: str,
    month_label: str,
) -> dict[str, Any]:
    offers = sort_offers(list(payload.get("offers") or []))
    html_body, text_body = build_email_bodies(payload)
    csv_text = offers_to_csv(offers)
    csv_b64 = base64.b64encode(csv_text.encode("utf-8")).decode("ascii")
    return {
        "from": EMAIL_FROM,
        "to": [EMAIL_TO],
        "subject": f"{EMAIL_SUBJECT_PREFIX} — {month_label} ({len(offers)} hotels)",
        "html": html_body,
        "text": text_body,
        "attachments": [
            {
                "filename": f"hyderabad-4star-weekend-hotels-{month_label}.csv",
                "content": csv_b64,
                "contentType": "text/csv",
            }
        ],
        "idempotencyKey": idempotency_key,
    }


def write_report_artifacts(
    payload: dict[str, Any],
    out_dir: Path,
    *,
    idempotency_key: str,
    month_label: str,
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    offers = sort_offers(list(payload.get("offers") or []))
    html_body, text_body = build_email_bodies(payload)
    csv_text = offers_to_csv(offers)
    send_payload = build_resend_payload(
        payload, idempotency_key=idempotency_key, month_label=month_label
    )

    paths = {
        "html": out_dir / "email.html",
        "text": out_dir / "email.txt",
        "csv": out_dir / "hotels.csv",
        "json": out_dir / "hotels.json",
        "send_payload": out_dir / "send-payload.json",
    }
    paths["html"].write_text(html_body, encoding="utf-8")
    paths["text"].write_text(text_body, encoding="utf-8")
    paths["csv"].write_text(csv_text, encoding="utf-8")
    paths["json"].write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["send_payload"].write_text(json.dumps(send_payload), encoding="utf-8")
    return paths
