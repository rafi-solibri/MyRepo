#!/usr/bin/env python3
"""Finish any open Easy Apply modal, then exit."""
import re, time
from playwright.sync_api import sync_playwright

PROFILE_PHONE = "8790251698"

def main():
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = b.contexts[0]
        page = next((pg for pg in ctx.pages if "linkedin.com/jobs" in pg.url), ctx.pages[0])
        page.bring_to_front()
        print("url", page.url, flush=True)

        # Resolve Save dialog
        if page.get_by_text("Save this application?").count():
            print("discarding save dialog", flush=True)
            page.get_by_role("button", name="Discard").click(timeout=3000)
            time.sleep(1)

        # Reopen Easy Apply if needed
        dlg = page.locator("[role='dialog']:has-text('Apply to'), .jobs-easy-apply-modal")
        if not (dlg.count() and dlg.first.is_visible()):
            ea = page.locator("button:has-text('Easy Apply'), button.jobs-apply-button").first
            if ea.count() and ea.is_visible():
                ea.click(timeout=5000)
                time.sleep(1.5)

        for step in range(15):
            if page.get_by_text("Save this application?").count():
                page.get_by_role("button", name="Discard").click(timeout=2000)
                time.sleep(0.8)
                page.locator("button:has-text('Easy Apply')").first.click(timeout=4000)
                time.sleep(1)

            # fill phone if empty
            try:
                phone = page.locator("input[type='text'][id*='phone'], input[inputmode='text']").filter(
                    has=page.locator("xpath=ancestor::div[.//label[contains(.,'phone') or contains(.,'Phone')]]")
                )
            except Exception:
                phone = page.locator("label:has-text('Mobile phone number') + input, label:has-text('Mobile phone number') >> xpath=../input")
            try:
                for inp in page.locator("[role='dialog'] input[type='text']").all()[:6]:
                    lab = ""
                    try:
                        lab = inp.evaluate("e => (e.getAttribute('aria-label')||'') + (e.labels && e.labels[0] ? e.labels[0].innerText : '')")
                    except Exception:
                        pass
                    if re.search(r"phone|mobile", lab or "", re.I):
                        val = inp.input_value()
                        if not val:
                            inp.fill(PROFILE_PHONE)
            except Exception:
                pass

            # resume
            try:
                r = page.get_by_text(re.compile(r"Rafi_Resume_Architect|Architect", re.I))
                if r.count():
                    r.first.click(timeout=1500)
            except Exception:
                pass

            # success?
            body = page.locator("body").inner_text()[:4000]
            if re.search(r"application (was )?submitted", body, re.I):
                print("SUBMITTED", flush=True)
                page.screenshot(path="/opt/cursor/artifacts/submitted-manual.png")
                try:
                    page.get_by_role("button", name=re.compile(r"done|dismiss", re.I)).first.click(timeout=2000)
                except Exception:
                    pass
                return

            # footer primary
            primary = page.locator(
                "[role='dialog'] button.artdeco-button--primary, "
                ".jobs-easy-apply-modal button.artdeco-button--primary"
            ).first
            if primary.count() and primary.is_visible():
                txt = (primary.inner_text() or "").strip()
                print(f"step {step} click primary: {txt!r}", flush=True)
                try:
                    primary.click(timeout=3000, force=True)
                except Exception:
                    primary.evaluate("el => el.click()")
                time.sleep(1.6)
                continue

            print(f"step {step} no primary", flush=True)
            page.screenshot(path=f"/opt/cursor/artifacts/finish-step-{step}.png")
            time.sleep(1)

        print("FAILED to finish", flush=True)
        page.screenshot(path="/opt/cursor/artifacts/finish-failed.png")

if __name__ == "__main__":
    main()
