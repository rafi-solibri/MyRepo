"""HTML calendar view (Google Hotels–style) for tracked hotel night prices."""

from __future__ import annotations

import calendar as cal
import html
from datetime import date
from typing import Any

from .calendar_prices import HotelCalendar


def _fmt_inr(amount: int | None) -> str:
    if amount is None:
        return "—"
    return f"₹{amount:,}".replace(",", ",")


def _month_grid(year: int, month: int, by_date: dict[str, dict[str, Any]], today: date) -> str:
    month_name = date(year, month, 1).strftime("%B")
    # Monday-first to match common travel UIs; screenshot is Sun-first — use Sun-first
    cal.setfirstweekday(cal.SUNDAY)
    weeks = cal.monthcalendar(year, month)
    priced = [v["lowest_price_inr"] for v in by_date.values() if v.get("lowest_price_inr")]
    min_price = min(priced) if priced else None

    head = "".join(
        f'<th style="padding:6px 4px;font-weight:600;color:#5f6368;font-size:12px">{d}</th>'
        for d in ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
    )
    rows = []
    for week in weeks:
        cells = []
        for day in week:
            if day == 0:
                cells.append('<td style="padding:4px;height:64px"></td>')
                continue
            d = date(year, month, day)
            key = d.isoformat()
            info = by_date.get(key) or {}
            price = info.get("lowest_price_inr")
            prov = info.get("lowest_provider") or ""
            is_past = d < today
            is_cheapest = price is not None and min_price is not None and price == min_price
            bg = "#ffffff"
            if is_cheapest and not is_past:
                bg = "#e8f0fe"
            if is_past:
                color = "#9aa0a6"
            elif is_cheapest:
                color = "#1a73e8"
            else:
                color = "#202124"
            price_html = (
                f'<div style="font-size:11px;margin-top:2px;color:{color};'
                f'font-weight:{"700" if is_cheapest else "500"}">{_fmt_inr(price)}</div>'
                if price is not None
                else '<div style="font-size:11px;margin-top:2px;color:#9aa0a6">—</div>'
            )
            title = html.escape(f"{key} · {_fmt_inr(price)} · {prov}" if price else key)
            cells.append(
                f'<td title="{title}" style="padding:6px 4px;height:64px;vertical-align:top;'
                f'border-radius:20px;background:{bg};text-align:center">'
                f'<div style="font-size:13px;font-weight:600;color:{color}">{day}</div>'
                f"{price_html}</td>"
            )
        rows.append("<tr>" + "".join(cells) + "</tr>")

    return f"""
    <div style="flex:1;min-width:280px;max-width:360px;margin:0 8px 16px">
      <div style="font-size:16px;font-weight:600;margin:0 0 8px;color:#202124">{month_name}</div>
      <table style="border-collapse:separate;border-spacing:2px;width:100%">
        <thead><tr>{head}</tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


def render_hotel_calendar_html(cal_data: HotelCalendar, *, today: date | None = None) -> str:
    today = today or date.today()
    by_date = {d.date: d.to_dict() for d in cal_data.days}
    priced = [d.lowest_price_inr for d in cal_data.days if d.lowest_price_inr is not None]
    cheapest = min(priced) if priced else None
    cheapest_days = [
        d.date
        for d in cal_data.days
        if d.lowest_price_inr is not None and d.lowest_price_inr == cheapest
    ]
    month_blocks = []
    for ym in cal_data.months:
        y, m = map(int, ym.split("-"))
        month_by = {k: v for k, v in by_date.items() if k.startswith(f"{y:04d}-{m:02d}")}
        last = cal.monthrange(y, m)[1]
        for day in range(1, last + 1):
            key = date(y, m, day).isoformat()
            month_by.setdefault(key, {"lowest_price_inr": None})
        month_blocks.append(_month_grid(y, m, month_by, today))

    cheapest_line = (
        f"Lowest night: <strong>{_fmt_inr(cheapest)}</strong> on {', '.join(cheapest_days[:6])}"
        + ("…" if len(cheapest_days) > 6 else "")
        if cheapest is not None
        else "No bookable nights found"
    )
    providers_seen: set[str] = set()
    for d in cal_data.days:
        providers_seen.update(d.providers.keys())

    return f"""
    <section style="margin:0 0 28px;padding:16px 16px 8px;border:1px solid #e8eaed;border-radius:12px;background:#fff">
      <h2 style="margin:0 0 4px;font-size:22px;color:#202124">{html.escape(cal_data.hotel)}</h2>
      <p style="margin:0 0 12px;color:#5f6368;font-size:13px">
        Best prices for a 1-night stay · 2 adults · lowest across hotel providers
        (Kayak comparison: {html.escape(', '.join(sorted(providers_seen)[:10]) or 'n/a')})
        <br>{cheapest_line}
      </p>
      <div style="display:flex;flex-wrap:wrap;justify-content:flex-start">
        {''.join(month_blocks)}
      </div>
    </section>
    """


def render_calendars_html(calendars: list[HotelCalendar], *, today: date | None = None) -> str:
    today = today or date.today()
    blocks = [render_hotel_calendar_html(c, today=today) for c in calendars]
    return f"""
    <div style="margin:0 0 32px">
      <h1 style="margin:0 0 8px;font-size:24px;color:#202124">Priority hotel calendars</h1>
      <p style="margin:0 0 16px;color:#5f6368;font-size:14px">
        Hotel Qualia Oak &amp; Oak Business Hotel — current month + next month.
        Each cell is the <strong>lowest nightly total</strong> across compared OTAs.
      </p>
      {''.join(blocks)}
    </div>
    """
