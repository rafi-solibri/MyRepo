#!/usr/bin/env python3
"""Indeed Easy Apply via SeleniumBase UC + WARP SOCKS (cloud Cloudflare path).

Plain Chrome CDP through WARP still gets Request Blocked. UC mode works.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(
    os.environ.get(
        "INDEED_DAILY_REPORT", "/opt/cursor/artifacts/indeed-daily-run.json"
    )
)
RESUME = Path(
    os.environ.get(
        "RAFI_RESUME",
        str(ROOT / "resumes" / "Rafi_Resume.docx"),
    )
)
PROXY = os.environ.get("INDEED_HTTP_PROXY", "socks5://127.0.0.1:40000")
# Hybrid UC profile (auth cookies, CF cookies stripped) — see prepare_uc_profile.py
PROFILE = os.environ.get("INDEED_UC_PROFILE", "/tmp/cursor/indeed-uc-hybrid")
SEED_PROFILE = os.environ.get(
    "INDEED_SEED_PROFILE", "/home/ubuntu/chrome-indeed-profile"
)
MAX_APPLIES = int(os.environ.get("INDEED_MAX_APPLIES", "8"))
MAX_SEEN = int(os.environ.get("INDEED_MAX_SEEN", "40"))

TITLE_OK = re.compile(
    r"(architect|tech(?:nical)?\s*lead|engineering\s*manager|\bEM\b|"
    r"principal|staff|senior).{0,40}(\.?\s*net|c#|azure|cloud)|"
    r"(\.?\s*net|c#|azure).{0,40}(architect|tech(?:nical)?\s*lead|"
    r"engineering\s*manager|principal|staff)|"
    r"(solutions?\s*architect|technical\s*architect|software\s*architect|"
    r"cloud\s*architect|application\s*architect)",
    re.I,
)
TITLE_SKIP = re.compile(
    r"\b(java|python|node\.?js|golang|ruby|php)\b.{0,20}\b(only|mandatory|must)\b|"
    r"\b(qa|sdet|quality\s*analyst|intern|junior|graduate|trainee)\b|"
    r"\b(salesforce|servicenow|\bsap\b)\b.{0,30}\b(developer|admin|consultant)\b|"
    r"\b(android|ios|flutter|react\s*native)\b.{0,20}\b(developer|engineer)\b",
    re.I,
)
LOC_OK = re.compile(
    r"hyderabad|telangana|\bhyd\b|remote|work\s*from\s*home|\bwfh\b|india\s*remote",
    re.I,
)
LOC_HARD_SKIP = re.compile(
    r"\b(bengaluru|bangalore|pune|chennai|mumbai|noida|gurgaon|gurugram|"
    r"delhi|kolkata|ahmedabad)\b(?!.{0,40}(remote|wfh|hybrid))",
    re.I,
)


def ensure_warp() -> str:
    script = ROOT / "scripts" / "ensure-indeed-warp.sh"
    res = subprocess.run(
        ["bash", str(script)], capture_output=True, text=True, timeout=120
    )
    m = re.search(r"export INDEED_HTTP_PROXY=(.+)", res.stdout or "")
    if res.returncode != 0 or not m:
        raise SystemExit(f"WARP not ready: {res.stderr or res.stdout}")
    proxy = m.group(1).strip().strip("'\"")
    os.environ["INDEED_HTTP_PROXY"] = proxy
    return proxy


def prepare_profile() -> dict:
    script = ROOT / "tools" / "indeed" / "prepare_uc_profile.py"
    res = subprocess.run(
        [
            "python3",
            str(script),
            "--src",
            SEED_PROFILE,
            "--dst",
            PROFILE,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        return json.loads(res.stdout or "{}")
    except Exception:
        return {"error": (res.stderr or res.stdout or "")[:400], "exit": res.returncode}


def clear_cf(sb, attempts: int = 3) -> bool:
    for _ in range(attempts):
        title = sb.get_title() or ""
        try:
            text = sb.get_text("body") or ""
        except Exception:
            text = ""
        if not blocked(title, text):
            return True
        try:
            sb.uc_gui_click_captcha()
        except Exception:
            try:
                sb.uc_gui_handle_captcha()
            except Exception:
                pass
        time.sleep(4)
    title = sb.get_title() or ""
    try:
        text = sb.get_text("body") or ""
    except Exception:
        text = ""
    return not blocked(title, text)


def blocked(title: str, text: str) -> bool:
    blob = f"{title}\n{text}".lower()
    return any(
        x in blob
        for x in (
            "request blocked",
            "additional verification required",
            "just a moment",
            "security check - indeed",
            "you have been blocked",
        )
    )


def skip_reason(title: str, company: str, location: str, snippet: str) -> str | None:
    t = title or ""
    if TITLE_SKIP.search(t):
        return "title_skip"
    if not TITLE_OK.search(t):
        # Bias: when uncertain on architect/lead/.NET titles → apply.
        # Only skip clear non-matches (no senior/architect/lead/.net signal).
        if not re.search(
            r"architect|tech(?:nical)?\s*lead|engineering\s*manager|principal|staff|senior|\.net|\bc#\b",
            t,
            re.I,
        ):
            return "title_not_target"
    loc = f"{location} {snippet}"
    if LOC_HARD_SKIP.search(location or "") and not LOC_OK.search(loc):
        return "location"
    if location and not LOC_OK.search(loc):
        # Remote/Hyd hard filter — skip clear other-city-only
        if re.search(
            r"bengaluru|bangalore|pune|chennai|mumbai|noida|gurgaon|delhi",
            location,
            re.I,
        ):
            return "location"
    return None


def search_queries() -> list[tuple[str, str]]:
    # Prefer homepage form submit (deep /jobs links re-trigger hard CF blocks).
    return [
        ("Solutions Architect .NET", "Hyderabad, Telangana"),
        ("Technical Architect C#", "Hyderabad, Telangana"),
        ("Engineering Manager .NET", "Hyderabad, Telangana"),
        ("Principal .NET", "Hyderabad, Telangana"),
        ("Technical Lead .NET", "Hyderabad, Telangana"),
        (".NET Architect", "Remote"),
    ]


def run_homepage_search(sb, query: str, location: str) -> bool:
    sb.uc_open_with_reconnect("https://in.indeed.com/", 5)
    time.sleep(2)
    if not clear_cf(sb):
        return False
    typed = False
    for qsel in ("#text-input-what", "input[name='q']"):
        try:
            if sb.is_element_visible(qsel):
                sb.type(qsel, query)
                typed = True
                break
        except Exception:
            continue
    for lsel in ("#text-input-where", "input[name='l']"):
        try:
            if sb.is_element_visible(lsel):
                sb.type(lsel, location)
                break
        except Exception:
            continue
    if not typed:
        # Fallback deep link (may need captcha again)
        params = urllib.parse.urlencode(
            {"q": query, "l": location, "fromage": "7", "sort": "date"}
        )
        sb.uc_open_with_reconnect("https://in.indeed.com/jobs?" + params, 5)
        time.sleep(2)
        return clear_cf(sb)
    for sel in (
        "button.yosegi-InlineWhatWhere-primaryButton",
        "button[type='submit']",
        "//button[contains(., 'Find jobs')]",
    ):
        try:
            sb.click(sel)
            break
        except Exception:
            continue
    time.sleep(3)
    return clear_cf(sb)


def fill_common_questions(sb) -> None:
    """Best-effort form fill for smartapply.indeed.com / Easy Apply steps."""
    # JS fill by label/aria/placeholder — more reliable on SmartApply modules.
    try:
        sb.execute_script(
            """
            const vals = {
              first: 'Mohammed Abdul Rafi',
              last: 'Ahmed',
              phone: '8790251698',
              email: 'rafi.success@gmail.com',
              city: 'Hyderabad',
              current: '52',
              expected: '65',
              notice: 'Immediate',
              experience: '14'
            };
            // Employer custom questions (radios / selects / text).
            const answerQuestion = (root) => {
              const text = (root.innerText || '').toLowerCase();
              let want = null;
              if (/current.*(ctc|salary|compensation|pay)|ctc.*current|present.*ctc/.test(text)) want = '52';
              else if (/expected.*(ctc|salary|compensation|pay)|ctc.*expected|desired.*salary/.test(text)) want = '65';
              else if (/notice|joining|how soon|availability|immediate/.test(text)) want = 'Immediate';
              else if (/total.*(experience|exp)|years of experience|overall experience/.test(text)) want = '14';
              else if (/relocat|willing to work|hybrid|work from office|bond|service agreement/.test(text)) want = 'yes';
              else if (/authorized|work authori|visa|citizen|india/.test(text)) want = 'yes';
              else if (/gender/.test(text)) want = 'male';
              else if (/city|current location|prefer.*location|job location/.test(text)) want = 'Hyderabad';
              else if (/\\?/.test(text) && /(yes|no)/.test(text)) want = 'yes';
              if (!want) return;
              // radios
              for (const r of root.querySelectorAll('input[type=radio], input[type=checkbox]')) {
                const lab = ((r.getAttribute('aria-label')||'') + ' ' + (r.parentElement?.innerText||'')).toLowerCase();
                if (want === 'yes' && /\\byes\\b|yep|true/.test(lab)) { r.click(); return; }
                if (want === 'male' && /male/.test(lab) && !/female/.test(lab)) { r.click(); return; }
                if (want === 'Immediate' && /immediate|0\\s*day|serving|less than/.test(lab)) { r.click(); return; }
              }
              for (const sel of root.querySelectorAll('select')) {
                for (const opt of sel.options) {
                  const t = (opt.text||'').toLowerCase();
                  if (want === 'yes' && /\\byes\\b/.test(t)) { sel.value=opt.value; sel.dispatchEvent(new Event('change',{bubbles:true})); return; }
                  if (want === 'Immediate' && /immediate|0/.test(t)) { sel.value=opt.value; sel.dispatchEvent(new Event('change',{bubbles:true})); return; }
                  if (want === 'Hyderabad' && /hyderabad/.test(t)) { sel.value=opt.value; sel.dispatchEvent(new Event('change',{bubbles:true})); return; }
                }
              }
              for (const el of root.querySelectorAll('input:not([type=radio]):not([type=checkbox]):not([type=file]):not([type=hidden]), textarea')) {
                if (el.disabled || el.readOnly) continue;
                if (['52','65','14','Immediate','Hyderabad'].includes(want)) {
                  const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
                  const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
                  if (setter) setter.call(el, want); else el.value = want;
                  el.dispatchEvent(new Event('input',{bubbles:true}));
                  el.dispatchEvent(new Event('change',{bubbles:true}));
                  return;
                }
              }
            };
            for (const root of document.querySelectorAll('[class*="question"], fieldset, [data-testid*="question"], form, main')) {
              answerQuestion(root);
            }
            // Also scan each label block.
            for (const lab of document.querySelectorAll('label, legend, h1, h2, h3, span')) {
              const t = (lab.innerText||'').trim();
              if (t.length > 8 && t.length < 180 && /\\?|ctc|salary|notice|experience|relocat|authori|location/.test(t.toLowerCase())) {
                answerQuestion(lab.closest('div, fieldset, li, section') || lab.parentElement || lab);
              }
            }
            const setNative = (el, value) => {
              const proto = el.tagName === 'TEXTAREA'
                ? window.HTMLTextAreaElement.prototype
                : window.HTMLInputElement.prototype;
              const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
              if (setter) setter.call(el, value); else el.value = value;
              el.dispatchEvent(new Event('input', {bubbles:true}));
              el.dispatchEvent(new Event('change', {bubbles:true}));
            };
            const labelFor = (el) => {
              const id = el.getAttribute('id');
              let t = '';
              if (id) {
                const lab = document.querySelector(`label[for="${CSS.escape(id)}"]`);
                if (lab) t += ' ' + lab.innerText;
              }
              const wrap = el.closest('label, .ia-FormField, .mosaic-provider-module, div');
              if (wrap) t += ' ' + (wrap.innerText || '').slice(0, 120);
              t += ' ' + (el.getAttribute('aria-label') || '');
              t += ' ' + (el.getAttribute('name') || '');
              t += ' ' + (el.getAttribute('placeholder') || '');
              t += ' ' + (el.getAttribute('autocomplete') || '');
              return t.toLowerCase();
            };
            for (const el of document.querySelectorAll('input, textarea')) {
              const type = (el.getAttribute('type') || '').toLowerCase();
              if (['hidden','submit','button','file','checkbox','radio'].includes(type)) continue;
              if (el.disabled || el.readOnly) continue;
              const lab = labelFor(el);
              let val = null;
              if (/first\\s*name|given\\s*name|fname/.test(lab)) val = vals.first;
              else if (/last\\s*name|surname|family\\s*name|lname/.test(lab)) val = vals.last;
              else if (/phone|mobile|tel/.test(lab) || type === 'tel') val = vals.phone;
              else if (/e-?mail/.test(lab) || type === 'email') val = vals.email;
              else if (/current.*(ctc|salary|compensation)|ctc.*current/.test(lab)) val = vals.current;
              else if (/expected.*(ctc|salary|compensation)|ctc.*expected/.test(lab)) val = vals.expected;
              else if (/notice|joining|availability/.test(lab)) val = vals.notice;
              else if (/city|location|current\\s*location/.test(lab)) val = vals.city;
              else if (/experience|years/.test(lab)) val = vals.experience;
              if (val != null && (!el.value || /phone|mobile|tel|first|last|ctc|salary|notice|city|experience/.test(lab))) {
                setNative(el, val);
              }
            }
            // Prefer India dial code if a country select exists.
            for (const sel of document.querySelectorAll('select')) {
              const lab = labelFor(sel);
              if (/country|dial|phone/.test(lab)) {
                for (const opt of sel.options) {
                  if (/india|\\+91|^in$/i.test(opt.text + ' ' + opt.value)) {
                    sel.value = opt.value;
                    sel.dispatchEvent(new Event('change', {bubbles:true}));
                    break;
                  }
                }
              }
            }
            return true;
            """
        )
    except Exception:
        pass

    # Resume upload
    if RESUME.exists():
        try:
            for f in sb.find_elements("input[type='file']"):
                f.send_keys(str(RESUME.resolve()))
                time.sleep(1)
        except Exception:
            pass


def click_next_or_submit(sb) -> str:
    # SmartApply primary CTA via JS (visible Continue/Submit).
    try:
        clicked = sb.execute_script(
            """
            const labels = [
              'submit your application','submit application','submit',
              'continue','next','review','save and continue'
            ];
            const btns = [...document.querySelectorAll('button, a[role=button], input[type=submit]')];
            const score = (el) => {
              const t = ((el.innerText || el.value || el.getAttribute('aria-label') || '')).trim().toLowerCase();
              const idx = labels.findIndex(l => t === l || t.startsWith(l));
              return idx === -1 ? 999 : idx;
            };
            const visible = btns.filter(el => {
              const r = el.getBoundingClientRect();
              const t = ((el.innerText || el.value || '')).trim().toLowerCase();
              return r.width > 0 && r.height > 0 && !el.disabled && t && !/close|cancel|report|skip to|view full/.test(t);
            }).sort((a,b) => score(a)-score(b));
            const el = visible.find(el => score(el) < 999);
            if (!el) return null;
            el.click();
            return (el.innerText || el.value || '').trim().slice(0,80);
            """
        )
        if clicked:
            return str(clicked)
    except Exception:
        pass
    for sel in (
        "button.ia-continueButton",
        "button.ia-ApplicationConfirmation-button",
        "button[type='submit']",
    ):
        try:
            if sb.is_element_visible(sel, timeout=1):
                sb.click(sel)
                return sel
        except Exception:
            pass
    return ""


def easy_apply_flow(sb, max_steps: int = 12, deadline: float | None = None) -> str:
    """Returns 'submitted' | 'external' | 'failed'."""
    for step in range(max_steps):
        if deadline and time.time() > deadline:
            return "failed"
        time.sleep(0.8)
        # SmartApply often navigates to smartapply.indeed.com modules.
        try:
            sb.driver.switch_to.default_content()
        except Exception:
            pass
        body = ""
        url = ""
        try:
            url = sb.get_current_url() or ""
            body = (sb.get_text("body") or "").lower()
        except Exception:
            pass
        if any(
            x in body
            for x in (
                "application submitted",
                "your application was sent",
                "applied on indeed",
                "successfully submitted",
                "you applied",
            )
        ) or "confirmation" in url.lower():
            return "submitted"
        if "apply on company site" in body and "indeed apply" not in body:
            return "external"
        fill_common_questions(sb)
        # Resume card: prefer an existing Rafi resume if shown.
        if "resume-selection" in url:
            try:
                sb.execute_script(
                    """
                    const cards=[...document.querySelectorAll('button, [role=button], label, div, li')];
                    const el=cards.find(e => /rafi_resume|rafi resume|\\.docx/i.test(e.innerText||''));
                    if (el) el.click();
                    """
                )
            except Exception:
                pass
        clicked = click_next_or_submit(sb)
        print(f"  ea_step={step} clicked={clicked!r} url={url[:90]}", flush=True)
        if not clicked:
            # Review page Submit can hydrate slowly.
            time.sleep(2)
            fill_common_questions(sb)
            if "review" in url.lower():
                try:
                    clicked = sb.execute_script(
                        """
                        const btns=[...document.querySelectorAll('button')];
                        const el=btns.find(b => /submit/i.test((b.innerText||b.getAttribute('aria-label')||'')));
                        if(!el) return null; el.click();
                        return (el.innerText||'').trim().slice(0,80);
                        """
                    )
                except Exception:
                    clicked = None
            if not clicked:
                clicked = click_next_or_submit(sb)
            if not clicked and "review" not in url.lower() and "questions" not in url.lower():
                break
            if not clicked:
                continue
        time.sleep(1.5)
        try:
            body = (sb.get_text("body") or "").lower()
            url = sb.get_current_url() or ""
        except Exception:
            pass
        if any(
            x in body
            for x in (
                "application submitted",
                "your application was sent",
                "successfully submitted",
                "you applied",
                "application has been submitted",
            )
        ) or "confirmation" in url.lower():
            return "submitted"
        # Some flows land on review then leave the module after submit.
        if "review" in (url or "").lower() and clicked and "submit" in str(clicked).lower():
            time.sleep(2)
            try:
                body = (sb.get_text("body") or "").lower()
                url = sb.get_current_url() or ""
            except Exception:
                pass
            if any(
                x in body
                for x in (
                    "application submitted",
                    "your application was sent",
                    "successfully submitted",
                    "you applied",
                )
            ) or "confirmation" in url.lower() or "viewjob" in url.lower():
                return "submitted"
    return "failed"


def main() -> int:
    os.environ.setdefault("DISPLAY", ":1")
    proxy = ensure_warp()
    if not RESUME.exists():
        print(json.dumps({"error": "resume_missing", "path": str(RESUME)}))
        return 2

    from seleniumbase import SB

    prep = prepare_profile()
    report = {
        "portal": "indeed",
        "source": "cloud-warp-uc",
        "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "proxy": proxy,
        "resume": str(RESUME),
        "profilePrep": prep,
        "counts": {
            "applied": 0,
            "external": 0,
            "rejected": 0,
            "blocked": 0,
            "skipped": 0,
            "seen": 0,
        },
        "applied": [],
        "external": [],
        "rejected": [],
        "blocked": [],
        "skipped": [],
        "seen": [],
        "ok": False,
    }

    with SB(
        uc=True,
        headed=True,
        proxy=proxy if proxy.startswith("socks5") else proxy,
        user_data_dir=PROFILE,
        chromium_arg="--no-sandbox,--disable-dev-shm-usage",
    ) as sb:
        try:
            sb.set_default_timeout(4)
        except Exception:
            pass
        sb.uc_open_with_reconnect("https://in.indeed.com/", 5)
        time.sleep(2)
        if not clear_cf(sb):
            report["blocked"].append({"reason": "still_blocked_after_uc"})
            report["counts"]["blocked"] = 1
            report["blockerSummary"] = "indeed_cloudflare_still_blocked"
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, indent=2))
            print(json.dumps(report, indent=2))
            return 5

        seen_keys: set[str] = set()
        for query, location in search_queries():
            if report["counts"]["applied"] + report["counts"]["external"] >= MAX_APPLIES:
                break
            if report["counts"]["seen"] >= MAX_SEEN:
                break
            if not run_homepage_search(sb, query, location):
                report["blocked"].append(
                    {"reason": "search_blocked", "query": query, "location": location}
                )
                report["counts"]["blocked"] += 1
                continue

            # Collect job cards
            cards = []
            for sel in (
                "a.jcs-JobTitle",
                "h2.jobTitle a",
                "a[data-jk]",
                "a[href*='jk=']",
            ):
                try:
                    cards = sb.find_elements(sel)
                    if cards:
                        break
                except Exception:
                    continue

            hrefs = []
            for c in cards:
                try:
                    href = c.get_attribute("href") or ""
                    jk = c.get_attribute("data-jk") or ""
                    t = (c.text or "").strip()
                    if href:
                        hrefs.append((t, href, jk))
                except Exception:
                    continue

            for title_t, href, jk in hrefs[:12]:
                if report["counts"]["applied"] + report["counts"]["external"] >= MAX_APPLIES:
                    break
                if report["counts"]["seen"] >= MAX_SEEN:
                    break
                key = jk or href.split("?")[0]
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                report["counts"]["seen"] += 1
                # Persist progress for the notification job even if interrupted.
                try:
                    OUT.parent.mkdir(parents=True, exist_ok=True)
                    OUT.write_text(json.dumps(report, indent=2))
                except Exception:
                    pass

                try:
                    sb.uc_open_with_reconnect(href, 4)
                    time.sleep(2)
                    clear_cf(sb, attempts=2)
                except Exception as e:
                    report["rejected"].append({"title": title_t, "error": str(e)[:160]})
                    report["counts"]["rejected"] += 1
                    continue

                page_title = sb.get_title() or title_t
                try:
                    body = sb.get_text("body") or ""
                except Exception:
                    body = ""
                if blocked(page_title, body):
                    report["blocked"].append({"reason": "job_page_blocked", "title": title_t})
                    report["counts"]["blocked"] += 1
                    continue
                # location heuristic
                loc_m = re.search(
                    r"([A-Za-z].{0,40}(Hyderabad|Telangana|Remote|Bengaluru|Bangalore|Pune|Chennai|Mumbai|Noida|Gurgaon|Delhi)[^\n]{0,40})",
                    body,
                )
                location = loc_m.group(1).strip() if loc_m else ""
                company = ""
                try:
                    company = sb.get_text(
                        "[data-company-name], .jobsearch-InlineCompanyRating a, [data-testid='inlineHeader-companyName']"
                    )
                except Exception:
                    pass

                item = {
                    "title": page_title[:160],
                    "company": (company or "")[:120],
                    "location": location[:120],
                    "url": sb.get_current_url(),
                }
                report["seen"].append(item)

                reason = skip_reason(page_title, company, location, body[:1500])
                if reason:
                    item["reason"] = reason
                    report["skipped"].append(item)
                    report["counts"]["skipped"] += 1
                    continue

                print(
                    f"JOB seen={report['counts']['seen']} title={page_title[:80]!r}",
                    flush=True,
                )
                job_deadline = time.time() + int(
                    os.environ.get("INDEED_JOB_TIMEOUT_SEC", "180")
                )

                # Prefer Easy Apply ("Apply with Indeed" is the current IN CTA).
                applied = False
                for sel in (
                    "button.indeed-apply-button",
                    "#indeedApplyButton",
                    "button:contains('Apply with Indeed')",
                    "button:contains('Easily apply')",
                    "button:contains('Apply now')",
                    "//button[contains(., 'Apply with Indeed') or contains(., 'Easily apply') or contains(., 'Apply now')]",
                    "//a[contains(., 'Apply with Indeed') or contains(., 'Easily apply') or contains(., 'Apply now')]",
                ):
                    try:
                        if sb.is_element_visible(sel, timeout=2):
                            sb.click(sel)
                            applied = True
                            break
                    except Exception:
                        continue
                if not applied:
                    # JS fallback — SeleniumBase text selectors miss some CTA variants.
                    try:
                        clicked = sb.execute_script(
                            """
                            const cands=[...document.querySelectorAll('button, a, [role=button]')];
                            const el=cands.find(e => /apply with indeed|easily apply|apply now/i.test(
                              ((e.innerText||'') + ' ' + (e.getAttribute('aria-label')||'')).trim()
                            ));
                            if(!el) return null;
                            el.click();
                            return (el.innerText||el.getAttribute('aria-label')||'').slice(0,80);
                            """
                        )
                        if clicked:
                            applied = True
                            print("JS_APPLY_CLICK", clicked, flush=True)
                    except Exception:
                        pass

                if not applied:
                    # Company site — open and mark external (full ATS fill is best-effort)
                    for sel in (
                        "button:contains('Apply on company site')",
                        "a:contains('Apply on company site')",
                        "//a[contains(., 'Apply on company site')]",
                        "//button[contains(., 'Apply on company site')]",
                    ):
                        try:
                            if sb.is_element_visible(sel, timeout=2):
                                sb.click(sel)
                                item["path"] = "external_opened"
                                report["external"].append(item)
                                report["counts"]["external"] += 1
                                time.sleep(2)
                                fill_common_questions(sb)
                                applied = True
                                print("EXTERNAL", page_title[:80], flush=True)
                                break
                        except Exception:
                            continue
                    if not applied:
                        item["reason"] = "no_apply_button"
                        report["skipped"].append(item)
                        report["counts"]["skipped"] += 1
                    continue

                # Wait for SmartApply module navigation / modal hydration.
                for _ in range(10):
                    try:
                        cur = sb.get_current_url() or ""
                        txt = (sb.get_text("body") or "").lower()
                    except Exception:
                        cur, txt = "", ""
                    if "smartapply.indeed.com" in cur or "indeedapply" in cur or "contact information" in txt or "continue" in txt:
                        break
                    time.sleep(0.5)
                result = easy_apply_flow(sb, deadline=job_deadline)
                item["path"] = "easy_apply"
                item["result"] = result
                if result == "submitted":
                    report["applied"].append(item)
                    report["counts"]["applied"] += 1
                    print("APPLIED", page_title[:80], flush=True)
                elif result == "external":
                    report["external"].append(item)
                    report["counts"]["external"] += 1
                    print("EXTERNAL", page_title[:80], flush=True)
                else:
                    item["reason"] = "easy_apply_incomplete"
                    report["rejected"].append(item)
                    report["counts"]["rejected"] += 1
                    print("INCOMPLETE", page_title[:80], flush=True)

                # Close Easy Apply modal / extra windows so the next job is clean.
                try:
                    sb.press_keys("body", "\ue00c")  # ESC
                except Exception:
                    pass
                try:
                    handles = sb.driver.window_handles
                    if len(handles) > 1:
                        current = sb.driver.current_window_handle
                        for h in handles:
                            if h != current:
                                sb.driver.switch_to.window(h)
                                sb.driver.close()
                        sb.driver.switch_to.window(sb.driver.window_handles[0])
                except Exception:
                    pass
                time.sleep(1)

    report["finishedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report["ok"] = report["counts"]["blocked"] == 0
    report["date"] = report["finishedAt"][:10]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    # Normalize for notification job
    subprocess.run(
        [
            "node",
            str(ROOT / "tools/indeed/daily_run_report.js"),
            "write",
            "--in",
            str(OUT),
            "--source",
            "cloud-warp-uc",
            "--out",
            str(OUT),
        ],
        check=False,
    )
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 5


if __name__ == "__main__":
    sys.exit(main())
