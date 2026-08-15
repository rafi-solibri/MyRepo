#!/usr/bin/env python3
"""Prepare a SeleniumBase UC profile that keeps Indeed auth but drops burned CF cookies.

The synced `/home/ubuntu/chrome-indeed-profile` often accumulates Cloudflare
challenge cookies that turn Turnstile into a hard "Additional Verification
Required" page (no widget). Copying auth cookies into a fresh profile and
deleting `cf_*` / `__cf*` rows lets `uc_gui_click_captcha()` clear CF again
while preserving Welcome / CTK / Passport tokens.
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

DEFAULT_SRC = Path(
    "/home/ubuntu/chrome-indeed-profile"
)
DEFAULT_DST = Path("/tmp/cursor/indeed-uc-hybrid")

COPY_PATHS = [
    "Default/Cookies",
    "Default/Cookies-journal",
    "Default/Login Data",
    "Default/Login Data-journal",
    "Default/Preferences",
    "Default/Secure Preferences",
    "Default/Local Storage",
    "Default/Session Storage",
    "Default/IndexedDB",
]


def prepare(src: Path, dst: Path) -> dict:
    if dst.exists():
        shutil.rmtree(dst)
    (dst / "Default").mkdir(parents=True)

    copied = []
    src_state = src / "Local State"
    if src_state.exists():
        shutil.copy2(src_state, dst / "Local State")
        copied.append("Local State")
    (dst / "First Run").touch()
    copied.append("First Run")
    for rel in COPY_PATHS:
        s = src / rel
        d = dst / rel
        if not s.exists():
            continue
        if s.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)
            for suf in ("-wal", "-shm"):
                p = Path(str(s) + suf)
                if p.exists():
                    shutil.copy2(p, str(d) + suf)
        copied.append(rel)

    cdb = dst / "Default" / "Cookies"
    deleted = 0
    remaining = []
    if cdb.exists():
        con = sqlite3.connect(str(cdb))
        cur = con.cursor()
        before = cur.execute("select count(*) from cookies").fetchone()[0]
        cur.execute(
            "delete from cookies where lower(name) like 'cf_%' "
            "or lower(name) like '__cf%' or lower(name) like '_cf%' "
            "or name in ('cf_clearance','cf_chl_rc_ni')"
        )
        con.commit()
        after = cur.execute("select count(*) from cookies").fetchone()[0]
        deleted = before - after
        remaining = sorted(
            {
                r[0]
                for r in cur.execute(
                    "select name from cookies where host_key like '%indeed%'"
                )
            }
        )
        con.close()

    return {
        "src": str(src),
        "dst": str(dst),
        "copied": copied,
        "cfCookiesDeleted": deleted,
        "indeedCookieNames": remaining,
        "hasAuth": any(
            n in remaining
            for n in (
                "CTK",
                "PPID",
                "__Secure-PassportAuthProxy-BearerToken",
                "rememberMe",
            )
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--dst", default=str(DEFAULT_DST))
    args = ap.parse_args()
    info = prepare(Path(args.src), Path(args.dst))
    import json

    print(json.dumps(info, indent=2))
    return 0 if info.get("hasAuth") or info.get("copied") else 2


if __name__ == "__main__":
    sys.exit(main())
