/**
 * Live-verify portal logins on an existing Chrome CDP (:9222).
 * Usage: node tools/verify_cdp_logins.js
 */
const { chromium } = require("playwright-core");

const CHECKS = [
  {
    portal: "linkedin",
    url: "https://www.linkedin.com/feed/",
    ok: (u, t) => /linkedin\.com\/(feed|in\/)/i.test(u) && !/\/login|authwall/i.test(u),
  },
  {
    portal: "naukri",
    url: "https://www.naukri.com/mnjuser/homepage",
    ok: (u, t) => /mnjuser|homepage|suggest/i.test(u) && !/nlogin|login/i.test(u),
  },
  {
    portal: "foundit",
    url: "https://www.foundit.in/profile",
    ok: (u, t) => /foundit\.in/i.test(u) && !/rio\/login|signin/i.test(u + t),
  },
  {
    portal: "cutshort",
    url: "https://cutshort.io/profile/candidate-dashboard",
    ok: (u, t) => /candidate-dashboard|profile/i.test(u) && !/\/login|sign in/i.test(u),
  },
  {
    portal: "instahyre",
    url: "https://www.instahyre.com/candidate/opportunities/",
    ok: (u, t) => /opportunities|candidate/i.test(u) && !/\/login/i.test(u),
  },
  {
    portal: "indeed",
    url: "https://www.indeed.com/",
    ok: (u, t) => /indeed\.com/i.test(u) && !/secure\.indeed\.com\/auth|login/i.test(u),
  },
];

(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const context = browser.contexts()[0] || (await browser.newContext());
  const results = [];
  for (const c of CHECKS) {
    const page = await context.newPage();
    try {
      await page.goto(c.url, { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(2500);
      const url = page.url();
      const text = await page.evaluate(() => (document.body && document.body.innerText) || "").catch(() => "");
      const cookies = await context.cookies();
      const names = cookies.map((x) => x.name);
      const authHints = {
        linkedin: names.includes("li_at"),
        naukri: names.includes("nauk_at") || names.includes("nauk_rt"),
        foundit: names.includes("MSSOAT"),
        cutshort: names.includes("cutshort_authentication"),
        instahyre: names.includes("sessionid"),
        indeed: names.some((n) => /Passport|Indeed|CTK/i.test(n)),
      };
      const looksOk = c.ok(url, text.slice(0, 400));
      results.push({
        portal: c.portal,
        ok: looksOk,
        url,
        cookieAuth: Boolean(authHints[c.portal]),
      });
    } catch (e) {
      results.push({ portal: c.portal, ok: false, error: String(e.message || e) });
    } finally {
      await page.close().catch(() => {});
    }
  }
  // Don't close browser — user still needs it for evening runs.
  console.log(JSON.stringify({ okCount: results.filter((r) => r.ok).length, results }, null, 2));
  process.exit(results.every((r) => r.ok) ? 0 : 2);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
