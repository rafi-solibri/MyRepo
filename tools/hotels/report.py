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


def calendars_to_csv(calendars: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "Hotel",
            "Date",
            "Lowest Price (INR)",
            "Lowest Provider",
            "All Providers",
        ]
    )
    for cal in calendars:
        for d in cal.get("days") or []:
            all_p = "; ".join(
                f"{k}=₹{v}" for k, v in sorted((d.get("providers") or {}).items(), key=lambda kv: kv[1])
            )
            w.writerow(
                [
                    cal.get("hotel"),
                    d.get("date"),
                    d.get("lowest_price_inr") or "",
                    d.get("lowest_provider") or "",
                    all_p,
                ]
            )
    return buf.getvalue()


def build_email_bodies(
    payload: dict[str, Any],
) -> tuple[str, str]:
    """Return (html, text). Calendars (priority) lead; weekend inventory follows."""
    from .calendar_prices import HotelCalendar, DayPrice
    from .calendar_view import render_calendars_html

    offers = sort_offers(list(payload.get("offers") or []))
    areas = ", ".join(payload.get("areas") or list(REQUIRED_AREAS))
    providers = payload.get("providers_seen") or {}
    provider_line = ", ".join(f"{k} ({v})" for k, v in list(providers.items())[:16])

    calendar_objs: list[HotelCalendar] = []
    for raw in payload.get("calendars") or []:
        days = [
            DayPrice(
                date=d["date"],
                lowest_price_inr=d.get("lowest_price_inr"),
                lowest_provider=d.get("lowest_provider"),
                providers=d.get("providers") or {},
            )
            for d in raw.get("days") or []
        ]
        calendar_objs.append(
            HotelCalendar(
                hotel=raw["hotel"],
                hid=raw.get("hid") or "",
                months=list(raw.get("months") or []),
                days=days,
                details_base_url=raw.get("details_base_url") or "",
            )
        )
    calendars_html = render_calendars_html(calendar_objs) if calendar_objs else ""

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

    inventory_table = ""
    if offers:
        inventory_table = f"""
  <h2 style="margin:24px 0 8px;font-size:20px">All 4★+ weekend hotels</h2>
  <p style="margin:0 0 12px;color:#374151">
    Areas: {html.escape(areas)} · Filter: 4★+ · remaining Sat/Sun ·
    <strong>{len(offers)}</strong> hotel-nights · {html.escape(provider_line)}
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
"""

    html_body = f"""<!DOCTYPE html>
<html><body style="font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#111;line-height:1.4;background:#f8f9fa;padding:12px">
  <div style="max-width:920px;margin:0 auto">
  <h1 style="margin:0 0 8px;font-size:24px">{html.escape(EMAIL_SUBJECT_PREFIX)}</h1>
  <p style="margin:0 0 16px;color:#5f6368;font-size:13px">
    Priority: Qualia Oak &amp; Oak Business Hotel calendars (current + next month),
    then full 4★+ weekend inventory. CSVs attached.
  </p>
  {calendars_html}
  {inventory_table}
  </div>
</body></html>"""

    text_lines = [
        EMAIL_SUBJECT_PREFIX,
        "",
        "=== PRIORITY CALENDARS (lowest across providers) ===",
    ]
    for cal in payload.get("calendars") or []:
        text_lines.append(f"\n{cal.get('hotel')}")
        for d in cal.get("days") or []:
            if d.get("lowest_price_inr") is None:
                continue
            text_lines.append(
                f"  {d['date']}: ₹{d['lowest_price_inr']:,} ({d.get('lowest_provider')})"
            )
    text_lines.extend(
        [
            "",
            "=== WEEKEND 4★+ INVENTORY ===",
            f"Areas: {areas}",
            f"Hotels found: {len(offers)}",
            f"Providers: {provider_line}",
            "",
            "Date | Day | Hotel | Area | Stars | Lowest INR | Provider",
            "-" * 72,
        ]
    )
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
    cal_csv = calendars_to_csv(list(payload.get("calendars") or []))
    attachments = [
        {
            "filename": f"hyderabad-4star-weekend-hotels-{month_label}.csv",
            "content": base64.b64encode(csv_text.encode("utf-8")).decode("ascii"),
            "contentType": "text/csv",
        },
        {
            "filename": f"qualia-oak-calendars-{month_label}.csv",
            "content": base64.b64encode(cal_csv.encode("utf-8")).decode("ascii"),
            "contentType": "text/csv",
        },
    ]
    n_cal = len(payload.get("calendars") or [])
    return {
        "from": EMAIL_FROM,
        "to": [EMAIL_TO],
        "subject": (
            f"{EMAIL_SUBJECT_PREFIX} — {month_label} "
            f"({n_cal} calendars, {len(offers)} weekend hotels)"
        ),
        "html": html_body,
        "text": text_body,
        "attachments": attachments,
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
    cal_csv = calendars_to_csv(list(payload.get("calendars") or []))
    send_payload = build_resend_payload(
        payload, idempotency_key=idempotency_key, month_label=month_label
    )

    paths = {
        "html": out_dir / "email.html",
        "text": out_dir / "email.txt",
        "csv": out_dir / "hotels.csv",
        "calendars_csv": out_dir / "calendars.csv",
        "calendars_html": out_dir / "calendars.html",
        "json": out_dir / "hotels.json",
        "send_payload": out_dir / "send-payload.json",
    }
    paths["html"].write_text(html_body, encoding="utf-8")
    paths["text"].write_text(text_body, encoding="utf-8")
    paths["csv"].write_text(csv_text, encoding="utf-8")
    paths["calendars_csv"].write_text(cal_csv, encoding="utf-8")
    # Standalone calendars fragment for quick preview
    from .calendar_view import render_calendars_html
    from .calendar_prices import HotelCalendar, DayPrice

    cal_objs = []
    for raw in payload.get("calendars") or []:
        cal_objs.append(
            HotelCalendar(
                hotel=raw["hotel"],
                hid=raw.get("hid") or "",
                months=list(raw.get("months") or []),
                days=[
                    DayPrice(
                        date=d["date"],
                        lowest_price_inr=d.get("lowest_price_inr"),
                        lowest_provider=d.get("lowest_provider"),
                        providers=d.get("providers") or {},
                    )
                    for d in raw.get("days") or []
                ],
                details_base_url=raw.get("details_base_url") or "",
            )
        )
    paths["calendars_html"].write_text(
        "<!DOCTYPE html><html><body style='font-family:Segoe UI,Helvetica,Arial,sans-serif'>"
        + render_calendars_html(cal_objs)
        + "</body></html>",
        encoding="utf-8",
    )
    paths["json"].write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["send_payload"].write_text(json.dumps(send_payload), encoding="utf-8")
    return paths
