from __future__ import annotations

import contextlib
from typing import Iterator

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@contextlib.contextmanager
def browser_session(
    *,
    headless: bool = True,
    locale: str = "en-IN",
) -> Iterator[tuple[Playwright, Browser, BrowserContext]]:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-http2",  # some Indian OTAs fail HTTP/2 from cloud IPs
            ],
        )
        context = browser.new_context(
            locale=locale,
            timezone_id="Asia/Kolkata",
            user_agent=DEFAULT_UA,
            viewport={"width": 1440, "height": 960},
            extra_http_headers={"Accept-Language": "en-IN,en;q=0.9"},
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        try:
            yield p, browser, context
        finally:
            context.close()
            browser.close()


def dismiss_overlays(page: Page) -> None:
    selectors = [
        'button:has-text("Accept")',
        'button:has-text("I agree")',
        'button:has-text("I understand")',
        'button:has-text("Got it")',
        'button:has-text("OK")',
        'button:has-text("No thanks")',
        'button:has-text("Not now")',
        '[aria-label="Close"]',
        'button[aria-label="Close"]',
    ]
    for sel in selectors:
        with contextlib.suppress(Exception):
            loc = page.locator(sel).first
            if loc.is_visible(timeout=600):
                loc.click(timeout=1200)


def scroll_results(page: Page, rounds: int = 8, pause_s: float = 0.9) -> None:
    import time

    for _ in range(rounds):
        page.mouse.wheel(0, 2800)
        time.sleep(pause_s)
        for sel in (
            'button:has-text("Show more")',
            'button:has-text("Load more")',
            'button:has-text("See more")',
            'a:has-text("Show more results")',
        ):
            with contextlib.suppress(Exception):
                loc = page.locator(sel).first
                if loc.is_visible(timeout=400):
                    loc.click(timeout=1200)
                    time.sleep(1.0)
