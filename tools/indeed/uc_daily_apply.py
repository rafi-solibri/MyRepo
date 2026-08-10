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


def _switch_smartapply_frame(sb) -> None:
    """SmartApply occasionally mounts the form inside an iframe."""
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    try:
        frames = sb.driver.find_elements("css selector", "iframe")
    except Exception:
        frames = []
    ranked = []
    for fr in frames:
        try:
            src = ((fr.get_attribute("src") or "") + " " + (fr.get_attribute("id") or "")).lower()
            ranked.append((0 if re.search(r"smartapply|indeedapply|apply", src) else 1, fr))
        except Exception:
            ranked.append((2, fr))
    ranked.sort(key=lambda x: x[0])
    for _, fr in ranked:
        try:
            sb.driver.switch_to.default_content()
            sb.driver.switch_to.frame(fr)
            body = ""
            try:
                body = (sb.get_text("body") or "").lower()
            except Exception:
                body = ""
            # Skip nested preview documents (about:srcdoc) — Submit lives on parent.
            try:
                fr_url = sb.driver.execute_script("return location.href") or ""
            except Exception:
                fr_url = ""
            if str(fr_url).startswith("about:"):
                continue
            if any(
                x in body
                for x in (
                    "continue",
                    "submit",
                    "question",
                    "resume",
                    "contact",
                    "review",
                )
            ):
                return
        except Exception:
            continue
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass


def fill_common_questions(sb) -> None:
    """Best-effort form fill for smartapply.indeed.com / Easy Apply steps."""
    _switch_smartapply_frame(sb)
    # JS fill by label/aria/placeholder — more reliable on SmartApply modules.
    try:
        filled = sb.execute_script(
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
            const setNative = (el, value) => {
              if (!el) return false;
              el.focus();
              const proto = el.tagName === 'TEXTAREA'
                ? window.HTMLTextAreaElement.prototype
                : window.HTMLInputElement.prototype;
              const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
              if (setter) setter.call(el, value); else el.value = value;
              el.dispatchEvent(new InputEvent('input', {bubbles:true, cancelable:true, inputType:'insertText', data:String(value)}));
              el.dispatchEvent(new Event('change', {bubbles:true}));
              el.blur();
              return true;
            };
            const labelFor = (el) => {
              const id = el.getAttribute('id');
              let t = '';
              if (id) {
                try {
                  const lab = document.querySelector(`label[for="${CSS.escape(id)}"]`);
                  if (lab) t += ' ' + lab.innerText;
                } catch (e) {}
              }
              const wrap = el.closest('label, fieldset, [class*="question"], [data-testid*="question"], .ia-Questions-item, .ia-FormField, li, section, div');
              if (wrap) t += ' ' + (wrap.innerText || '').slice(0, 220);
              t += ' ' + (el.getAttribute('aria-label') || '');
              t += ' ' + (el.getAttribute('name') || '');
              t += ' ' + (el.getAttribute('placeholder') || '');
              t += ' ' + (el.getAttribute('autocomplete') || '');
              return t.toLowerCase();
            };
            const wantFromText = (text) => {
              const t = (text || '').toLowerCase();
              if (/current.*(ctc|salary|compensation|pay)|ctc.*current|present.*ctc|current.*package/.test(t)) return '52';
              if (/expected.*(ctc|salary|compensation|pay)|ctc.*expected|desired.*salary|expected.*package/.test(t)) return '65';
              if (/notice|joining|how soon|availability|immediate|serve notice/.test(t)) return 'Immediate';
              if (/total.*(experience|exp)|years of experience|overall experience|relevant experience/.test(t)) return '14';
              if (/relocat|willing to work|hybrid|work from office|bond|service agreement|background check|drug test/.test(t)) return 'yes';
              if (/authorized|work authori|visa|citizen|india|legally/.test(t)) return 'yes';
              if (/gender/.test(t)) return 'male';
              if (/city|current location|prefer.*location|job location|base location/.test(t)) return 'Hyderabad';
              if (/\\?/.test(t) && /(yes|no)/.test(t)) return 'yes';
              if (/cover letter|why (do )?you|tell us|about yourself|summary|additional information/.test(t)) {
                return 'Solutions Architect / Tech Lead with 14+ years in .NET, Azure, microservices. Immediate joiner. Hyd/Remote. Expected 65 LPA.';
              }
              return null;
            };
            const clickMatching = (root, want) => {
              const radios = [...root.querySelectorAll('input[type=radio], input[type=checkbox], [role=radio], [role=checkbox]')];
              for (const r of radios) {
                const lab = ((r.getAttribute('aria-label')||'') + ' ' + (r.parentElement?.innerText||'') + ' ' + (r.value||'')).toLowerCase().slice(0,160);
                const hit =
                  (want === 'yes' && /\\byes\\b|yep|true|agree|available/.test(lab) && !/\\bno\\b/.test(lab)) ||
                  (want === 'male' && /\\bmale\\b/.test(lab) && !/female/.test(lab)) ||
                  (want === 'Immediate' && /immediate|0\\s*day|serving|less than|currently serving/.test(lab));
                if (hit) {
                  try { r.click(); } catch (e) {}
                  try { (r.closest('label') || r).click(); } catch (e) {}
                  return true;
                }
              }
              for (const sel of root.querySelectorAll('select')) {
                for (const opt of sel.options) {
                  const t = (opt.text||'').toLowerCase();
                  if (
                    (want === 'yes' && /\\byes\\b/.test(t)) ||
                    (want === 'Immediate' && /immediate|0\\s*day|0-15|less than/.test(t)) ||
                    (want === 'Hyderabad' && /hyderabad/.test(t)) ||
                    (want === '52' && /\\b52\\b|50-55|45-55/.test(t)) ||
                    (want === '65' && /\\b65\\b|60-70|60-65/.test(t)) ||
                    (want === '14' && /\\b14\\b|12-15|10\\+/.test(t))
                  ) {
                    sel.value = opt.value;
                    sel.dispatchEvent(new Event('change',{bubbles:true}));
                    return true;
                  }
                }
              }
              for (const el of root.querySelectorAll('input:not([type=radio]):not([type=checkbox]):not([type=file]):not([type=hidden]), textarea')) {
                if (el.disabled || el.readOnly) continue;
                if (want) { setNative(el, want); return true; }
              }
              // Custom listbox / button options
              for (const el of root.querySelectorAll('button, [role=option], li, label, span')) {
                const t = ((el.innerText||'') + ' ' + (el.getAttribute('aria-label')||'')).trim().toLowerCase();
                if (!t || t.length > 40) continue;
                if (want === 'yes' && /\\byes\\b/.test(t) && !/\\bno\\b/.test(t)) { el.click(); return true; }
                if (want === 'Immediate' && /immediate|0\\s*day/.test(t)) { el.click(); return true; }
              }
              return false;
            };
            let answered = 0;
            const roots = [
              ...document.querySelectorAll('[class*="question"], fieldset, [data-testid*="question"], .ia-Questions-item, .ia-Questions, form, main, [role=main]')
            ];
            for (const root of roots) {
              const want = wantFromText(root.innerText || '');
              if (want && clickMatching(root, want)) answered += 1;
            }
            for (const lab of document.querySelectorAll('label, legend, h1, h2, h3, p, span')) {
              const t = (lab.innerText||'').trim();
              if (t.length > 6 && t.length < 220 && /\\?|ctc|salary|notice|experience|relocat|authori|location|package|lpa|gender|hybrid|bond/.test(t.toLowerCase())) {
                const want = wantFromText(t);
                if (want && clickMatching(lab.closest('div, fieldset, li, section, [class*="question"]') || lab.parentElement || lab, want)) {
                  answered += 1;
                }
              }
            }
            // Profile / contact fields
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
              else if (/current.*(ctc|salary|compensation|package)|ctc.*current/.test(lab)) val = vals.current;
              else if (/expected.*(ctc|salary|compensation|package)|ctc.*expected/.test(lab)) val = vals.expected;
              else if (/notice|joining|availability/.test(lab)) val = vals.notice;
              else if (/city|location|current\\s*location/.test(lab)) val = vals.city;
              else if (/experience|years/.test(lab)) val = vals.experience;
              else if (!(el.value || '').trim()) {
                const w = wantFromText(lab);
                if (w) val = w;
              }
              if (val != null && (!(el.value || '').trim() || /phone|mobile|tel|first|last|ctc|salary|notice|city|experience|package/.test(lab))) {
                if (setNative(el, val)) answered += 1;
              }
            }
            // Unchecked radio groups → prefer Yes / Immediate / first option.
            const names = new Set(
              [...document.querySelectorAll('input[type=radio]')].map(r => r.name).filter(Boolean)
            );
            for (const name of names) {
              const group = [...document.querySelectorAll(`input[type=radio][name="${CSS.escape(name)}"]`)];
              if (!group.length || group.some(r => r.checked)) continue;
              const scored = group.map(r => {
                const lab = ((r.getAttribute('aria-label')||'') + ' ' + (r.parentElement?.innerText||'') + ' ' + (r.value||'')).toLowerCase();
                let s = 0;
                if (/\\byes\\b|immediate|agree|available|hyderabad|male\\b/.test(lab)) s += 3;
                if (/\\bno\\b|female|not available|never/.test(lab)) s -= 2;
                return {r, s, lab};
              }).sort((a,b) => b.s - a.s);
              try { scored[0].r.click(); answered += 1; } catch (e) {}
              try { (scored[0].r.closest('label') || scored[0].r).click(); } catch (e) {}
            }
            // Required empty selects → first non-placeholder option.
            for (const sel of document.querySelectorAll('select')) {
              if (sel.disabled || (sel.value && sel.selectedIndex > 0)) continue;
              const lab = labelFor(sel);
              if (/country|dial|phone/.test(lab)) {
                for (const opt of sel.options) {
                  if (/india|\\+91|^in$/i.test(opt.text + ' ' + opt.value)) {
                    sel.value = opt.value;
                    sel.dispatchEvent(new Event('change', {bubbles:true}));
                    answered += 1;
                    break;
                  }
                }
                continue;
              }
              for (const opt of [...sel.options].slice(1)) {
                if ((opt.text || '').trim()) {
                  sel.value = opt.value;
                  sel.dispatchEvent(new Event('change', {bubbles:true}));
                  answered += 1;
                  break;
                }
              }
            }
            // Remaining empty required-looking text inputs.
            for (const el of document.querySelectorAll('input:not([type=hidden]):not([type=file]):not([type=radio]):not([type=checkbox]), textarea')) {
              if (el.disabled || el.readOnly || (el.value || '').trim()) continue;
              const lab = labelFor(el);
              const req = el.required || el.getAttribute('aria-required') === 'true' || /required|\\*/.test(lab);
              if (!req && !/question|ctc|salary|notice|experience/.test(lab)) continue;
              const w = wantFromText(lab) || (/how many|years|experience/.test(lab) ? '14' : (/salary|ctc|lpa|package/.test(lab) ? '65' : 'Yes'));
              if (setNative(el, w)) answered += 1;
            }
            return {answered, url: location.href};
            """
        )
        if isinstance(filled, dict):
            print(f"  fill={filled}", flush=True)
    except Exception as e:
        print(f"  fill_error={e!s}"[:200], flush=True)

    # Resume upload
    if RESUME.exists():
        try:
            for f in sb.find_elements("input[type='file']"):
                f.send_keys(str(RESUME.resolve()))
                time.sleep(1)
        except Exception:
            pass


def click_next_or_submit(sb, allow_disabled: bool = False) -> str:
    # SmartApply primary CTA via JS (visible Continue/Submit).
    _switch_smartapply_frame(sb)
    try:
        clicked = sb.execute_script(
            """
            const allowDisabled = Boolean(arguments[0]);
            const labels = [
              'submit your application','submit application','submit',
              'continue applying','continue','next','save and continue','apply'
            ];
            const btns = [...document.querySelectorAll(
              'button, a[role=button], input[type=submit], [data-testid*="continue"], [data-testid*="submit"], .ia-continueButton'
            )];
            const textOf = (el) => ((el.innerText || el.value || el.getAttribute('aria-label') || '')).trim().toLowerCase();
            const reject = (t) => /close|cancel|report|skip to|view full|back|previous|remove|delete|preview|employer sees|download|edit/.test(t);
            const score = (el) => {
              const t = textOf(el);
              // Exact / prefix match only — avoid matching "Preview..." via includes('review').
              const idx = labels.findIndex(l => t === l || t.startsWith(l + ' ') || t.startsWith(l));
              return idx === -1 ? 999 : idx;
            };
            const visible = btns.filter(el => {
              const r = el.getBoundingClientRect();
              const t = textOf(el);
              const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true';
              return r.width > 0 && r.height > 0 && t && !reject(t)
                && (allowDisabled || !disabled);
            }).sort((a,b) => score(a)-score(b));
            let el = visible.find(el => score(el) < 999);
            // On review, prefer an explicit Submit even if Continue also exists.
            const submitEl = visible.find(el => /^submit/.test(textOf(el)));
            if (submitEl) el = submitEl;
            if (!el && allowDisabled) {
              el = btns.find(el => {
                const r = el.getBoundingClientRect();
                const t = textOf(el);
                return r.width > 0 && r.height > 0 && /submit|continue|next|apply/.test(t)
                  && !reject(t);
              });
            }
            if (!el) return null;
            if (el.disabled || el.getAttribute('aria-disabled') === 'true') {
              el.disabled = false;
              el.removeAttribute('disabled');
              el.setAttribute('aria-disabled', 'false');
            }
            el.scrollIntoView({block:'center'});
            el.click();
            return (el.innerText || el.value || '').trim().slice(0,80);
            """,
            allow_disabled,
        )
        if clicked:
            return str(clicked)
    except Exception:
        pass
    for sel in (
        "button.ia-continueButton",
        "button.ia-ApplicationConfirmation-button",
        "button[type='submit']",
        "[data-testid='continue-button']",
        "[data-testid='submit-button']",
    ):
        try:
            if sb.is_element_visible(sel, timeout=1):
                sb.click(sel)
                return sel
        except Exception:
            pass
    return ""


def _is_submitted(body: str, url: str) -> bool:
    b = (body or "").lower()
    u = (url or "").lower()
    return any(
        x in b
        for x in (
            "application submitted",
            "your application was sent",
            "applied on indeed",
            "successfully submitted",
            "you applied",
            "application has been submitted",
            "thanks for applying",
            "thank you for applying",
            "we have received your application",
        )
    ) or ("confirmation" in u and "review" not in u)


def _page_has_recaptcha(sb) -> bool:
    try:
        body = (sb.get_text("body") or "").lower()
    except Exception:
        body = ""
    if "i'm not a robot" in body or "im not a robot" in body or "recaptcha" in body:
        return True
    try:
        return bool(
            sb.execute_script(
                """
                return Boolean(
                  document.querySelector('iframe[src*="recaptcha"], .g-recaptcha, #g-recaptcha, [data-sitekey]')
                );
                """
            )
        )
    except Exception:
        return False


def _recaptcha_token_present(sb) -> bool:
    try:
        return bool(
            sb.execute_script(
                """
                const ta = document.querySelector(
                  '#g-recaptcha-response, textarea[name="g-recaptcha-response"]'
                );
                return Boolean(ta && (ta.value || '').trim().length > 20);
                """
            )
        )
    except Exception:
        return False


def clear_recaptcha(sb, attempts: int = 3) -> bool:
    """Clear Google reCAPTCHA on SmartApply review via UC GUI click."""
    frames = (
        'iframe[title="reCAPTCHA"]',
        'iframe[src*="recaptcha/api2/anchor"]',
        'iframe[src*="recaptcha"]',
        "iframe",
    )
    for n in range(attempts):
        try:
            sb.driver.switch_to.default_content()
        except Exception:
            pass
        if _recaptcha_token_present(sb):
            return True
        if not _page_has_recaptcha(sb):
            return True
        print(f"  recaptcha_attempt={n+1}", flush=True)
        # Bring widget into view so PyAutoGUI lands on the checkbox.
        for fr in frames[:3]:
            try:
                if sb.is_element_present(fr):
                    sb.scroll_to(fr)
                    break
            except Exception:
                continue
        clicked = False
        for fr in frames:
            try:
                if hasattr(sb, "uc_gui_click_rc"):
                    sb.uc_gui_click_rc(frame=fr, retry=True)
                    clicked = True
                    break
            except Exception:
                pass
            try:
                sb.uc_gui_click_captcha(frame=fr, retry=True)
                clicked = True
                break
            except TypeError:
                # Older SB binding may not accept frame kwargs on the SB wrapper.
                try:
                    sb.driver.uc_gui_click_captcha(frame=fr, retry=True)
                    clicked = True
                    break
                except Exception:
                    continue
            except Exception:
                continue
        if not clicked:
            try:
                sb.uc_gui_click_captcha()
            except Exception as e1:
                try:
                    sb.uc_gui_handle_captcha()
                except Exception as e2:
                    print(f"  recaptcha_click_error={e1!s}|{e2!s}"[:220], flush=True)
        time.sleep(2.5)
        if _recaptcha_token_present(sb):
            print("  recaptcha_token=ok", flush=True)
            return True
        # Image challenge may have opened — second GUI pass.
        try:
            if hasattr(sb, "uc_gui_click_rc"):
                sb.uc_gui_click_rc(retry=True, blind=True)
            else:
                sb.uc_gui_click_captcha()
        except Exception:
            pass
        time.sleep(2)
        if _recaptcha_token_present(sb):
            print("  recaptcha_token=ok", flush=True)
            return True
    return _recaptcha_token_present(sb)


def submit_review_application(sb) -> bool:
    """On review-module: solve reCAPTCHA, tick cert boxes, force Submit."""
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    if _page_has_recaptcha(sb):
        clear_recaptcha(sb, attempts=3)
    try:
        sb.execute_script(
            """
            for (const c of document.querySelectorAll('input[type=checkbox]')) {
              if (!c.checked) {
                try { c.click(); } catch (e) {}
                try { (c.closest('label') || c).click(); } catch (e) {}
              }
            }
            """
        )
    except Exception:
        pass
    # Prefer SeleniumBase click (fires trusted events) over bare JS click.
    clicked_sel = ""
    for sel in (
        "//button[normalize-space()='Submit your application']",
        "//button[contains(normalize-space(.), 'Submit your application')]",
        "//button[contains(normalize-space(.), 'Submit application')]",
        "//button[normalize-space()='Submit']",
        "button.ia-continueButton",
    ):
        try:
            if sb.is_element_visible(sel, timeout=1):
                try:
                    sb.scroll_to(sel)
                except Exception:
                    pass
                # UC click when available — better against bot detection.
                try:
                    sb.uc_click(sel)
                except Exception:
                    sb.click(sel)
                clicked_sel = sel
                print(f"  review_click={sel!r}", flush=True)
                break
        except Exception:
            continue
    if not clicked_sel:
        clicked = click_next_or_submit(sb, allow_disabled=True)
        print(f"  review_js_click={clicked!r}", flush=True)
        if not clicked:
            return False

    # Poll for confirmation / navigation away from review.
    for i in range(20):
        time.sleep(0.5)
        try:
            sb.driver.switch_to.default_content()
        except Exception:
            pass
        try:
            url = sb.get_current_url() or ""
            body = (sb.get_text("body") or "")
        except Exception:
            url, body = "", ""
        if _is_submitted(body, url):
            return True
        if "review-module" not in url.lower() and "smartapply" not in url.lower():
            if not re.search(r"something went wrong|unable to submit|try again", body, re.I):
                return True
        # reCAPTCHA may reappear / remain unsolved after a dead Submit click.
        if i in (3, 8, 14) and _page_has_recaptcha(sb):
            clear_recaptcha(sb, attempts=1)
            click_next_or_submit(sb, allow_disabled=True)
        try:
            sb.press_keys("body", "\ue00c")  # ESC preview overlays
        except Exception:
            pass
    return False


def easy_apply_flow(sb, max_steps: int = 18, deadline: float | None = None) -> str:
    """Returns 'submitted' | 'external' | 'failed'."""
    stuck_questions = 0
    review_submit_attempts = 0
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
        if _is_submitted(body, url):
            return "submitted"
        if "apply on company site" in body and "indeed apply" not in body:
            return "external"
        # Review page: dedicated submit path (JS click alone often no-ops).
        if "review-module" in url.lower() or (
            "review" in url.lower() and "question" not in url.lower()
        ):
            review_submit_attempts += 1
            print(f"  ea_step={step} review_submit attempt={review_submit_attempts} url={url[:90]}", flush=True)
            if submit_review_application(sb):
                return "submitted"
            # CAPTCHA wall: don't burn the whole job budget (AUTO_FIX ~3–4 min).
            if review_submit_attempts >= 2 and _page_has_recaptcha(sb) and not _recaptcha_token_present(sb):
                try:
                    sample = (sb.get_text("body") or "")[:500].replace("\n", " | ")
                    print(f"  review_recaptcha_blocked sample={sample!r}", flush=True)
                    sb.save_screenshot("/opt/cursor/artifacts/indeed-review-stuck.png")
                except Exception:
                    pass
                return "recaptcha"
            if review_submit_attempts >= 3:
                try:
                    sample = (sb.get_text("body") or "")[:500].replace("\n", " | ")
                    print(f"  review_stuck sample={sample!r}", flush=True)
                    sb.save_screenshot("/opt/cursor/artifacts/indeed-review-stuck.png")
                except Exception:
                    pass
                return "failed"
            continue
        fill_common_questions(sb)
        # Resume card: prefer an existing Rafi resume if shown.
        if "resume-selection" in url or "resume" in url.lower():
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
        clicked = click_next_or_submit(sb, allow_disabled=False)
        print(f"  ea_step={step} clicked={clicked!r} url={url[:90]}", flush=True)
        if not clicked:
            # Review / questions: fill again, wait for CTA enable, then force-click.
            time.sleep(1.5)
            fill_common_questions(sb)
            time.sleep(0.8)
            if "review" in url.lower() or "question" in url.lower():
                try:
                    sb.driver.switch_to.default_content()
                except Exception:
                    pass
                try:
                    clicked = sb.execute_script(
                        """
                        const btns=[...document.querySelectorAll('button, [role=button], input[type=submit]')];
                        const textOf = (b) => ((b.innerText||b.value||b.getAttribute('aria-label')||'')).trim().toLowerCase();
                        const reject = (t) => /close|cancel|back|previous|preview|employer sees|download|edit/.test(t);
                        const scored = btns.map(b => {
                          const t=textOf(b);
                          const r=b.getBoundingClientRect();
                          let s = 999;
                          if (/^submit your application|^submit application|^submit$/.test(t)) s = 0;
                          else if (/^continue/.test(t)) s = 1;
                          else if (/^next|^apply$/.test(t)) s = 2;
                          return {b,t,r,s};
                        }).filter(x => x.r.width>0 && x.r.height>0 && x.s<999 && !reject(x.t))
                          .sort((a,b) => a.s-b.s);
                        const el = scored[0]?.b;
                        if(!el) return null;
                        el.disabled=false; el.removeAttribute('disabled');
                        el.setAttribute('aria-disabled','false');
                        el.click();
                        return (el.innerText||el.value||'').trim().slice(0,80);
                        """
                    )
                except Exception:
                    clicked = None
            if not clicked:
                try:
                    sb.driver.switch_to.default_content()
                except Exception:
                    pass
                clicked = click_next_or_submit(sb, allow_disabled=True)
            if not clicked and "review" not in url.lower() and "questions" not in url.lower():
                break
            if not clicked:
                stuck_questions += 1
                if stuck_questions >= 4:
                    try:
                        sample = (sb.get_text("body") or "")[:400].replace("\n", " | ")
                        print(f"  questions_stuck sample={sample!r}", flush=True)
                    except Exception:
                        pass
                    break
                continue
            stuck_questions = 0
        else:
            stuck_questions = 0
        time.sleep(1.5)
        try:
            body = sb.get_text("body") or ""
            url = sb.get_current_url() or ""
        except Exception:
            body, url = "", ""
        if _is_submitted(body, url):
            return "submitted"
        # Landed on review after Continue — dedicated submit next loop.
        if "review-module" in (url or "").lower():
            continue
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
                elif result == "recaptcha":
                    item["reason"] = "easy_apply_recaptcha"
                    report["blocked"].append(item)
                    report["counts"]["blocked"] += 1
                    print("RECAPTCHA", page_title[:80], flush=True)
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
