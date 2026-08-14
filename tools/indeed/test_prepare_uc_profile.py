#!/usr/bin/env python3
"""Tests for Indeed UC hybrid-profile cookie unlock (v10 decrypt)."""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.indeed.prepare_uc_profile import (  # noqa: E402
    decrypt_chrome_v10,
    encrypt_chrome_v10,
    load_decrypted_indeed_cookies,
    prepare,
    unlock_cookie_db,
)
from tools.indeed.uc_daily_apply import home_looks_signed_out  # noqa: E402

_COOKIE_DDL = """
CREATE TABLE cookies (
  creation_utc INTEGER NOT NULL,
  host_key TEXT NOT NULL,
  top_frame_site_key TEXT NOT NULL,
  name TEXT NOT NULL,
  value TEXT NOT NULL,
  encrypted_value BLOB NOT NULL,
  path TEXT NOT NULL,
  expires_utc INTEGER NOT NULL,
  is_secure INTEGER NOT NULL,
  is_httponly INTEGER NOT NULL,
  last_access_utc INTEGER NOT NULL,
  has_expires INTEGER NOT NULL,
  is_persistent INTEGER NOT NULL,
  priority INTEGER NOT NULL,
  samesite INTEGER NOT NULL,
  source_scheme INTEGER NOT NULL,
  source_port INTEGER NOT NULL,
  last_update_utc INTEGER NOT NULL,
  source_type INTEGER NOT NULL,
  has_cross_site_ancestor INTEGER NOT NULL
);
"""


def _insert(con: sqlite3.Connection, name: str, host: str, plain: str, *, digest_prefix: bool = True) -> None:
    payload = plain.encode("utf-8")
    if digest_prefix:
        payload = b"\x00" * 32 + payload
    blob = encrypt_chrome_v10(payload)
    con.execute(
        "insert into cookies values (1,?,?,?,'',?, '/', 13373308800000000, 1, 1, 1, 1, 1, 1, 0, 2, 443, 1, 0, 0)",
        (host, host, name, blob),
    )


def test_decrypt_roundtrip_with_digest_prefix():
    token = "1jvav8fimgndg800"
    blob = encrypt_chrome_v10(b"\xff" * 32 + token.encode())
    assert decrypt_chrome_v10(blob) == token.encode()


def test_decrypt_roundtrip_plain():
    token = "eyJraWQiOiJkMmY2MzQ0MS03MzkwLTQzZDMtYWZjNy0zMWUz"
    blob = encrypt_chrome_v10(token.encode())
    assert decrypt_chrome_v10(blob) == token.encode()


def test_unlock_cookie_db_writes_plaintext():
    with tempfile.TemporaryDirectory() as td:
        cdb = Path(td) / "Cookies"
        con = sqlite3.connect(str(cdb))
        con.execute(_COOKIE_DDL)
        _insert(con, "CTK", ".indeed.com", "cktok1234567890")
        _insert(con, "PPID", ".indeed.com", "eyJhbGciOiJIUzI1NiJ9.abc")
        con.commit()
        con.close()
        stats = unlock_cookie_db(cdb)
        assert stats["unlocked"] == 2
        assert "CTK" in stats["authUnlocked"]
        assert "PPID" in stats["authUnlocked"]
        con = sqlite3.connect(str(cdb))
        rows = {n: (v, ev) for n, v, ev in con.execute("select name, value, encrypted_value from cookies")}
        con.close()
        assert rows["CTK"][0] == "cktok1234567890"
        assert not rows["CTK"][1]


def test_prepare_unlocks_and_strips_cf():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "src"
        dst = Path(td) / "dst"
        (src / "Default").mkdir(parents=True)
        cdb = src / "Default" / "Cookies"
        con = sqlite3.connect(str(cdb))
        con.execute(_COOKIE_DDL)
        _insert(con, "CTK", ".indeed.com", "session-ctk")
        _insert(con, "__Secure-PassportAuthProxy-BearerToken", ".indeed.com", "bearer-xyz")
        _insert(con, "cf_clearance", ".indeed.com", "burned")
        con.commit()
        con.close()
        info = prepare(src, dst)
        assert info["hasAuth"] is True
        assert info["cookiesUnlocked"] >= 2
        assert "CTK" in info["authUnlocked"]
        assert "cf_clearance" not in info["indeedCookieNames"]
        cookies = load_decrypted_indeed_cookies(dst)
        names = {c["name"] for c in cookies}
        assert "CTK" in names
        assert "cf_clearance" not in names
        values = {c["name"]: c["value"] for c in cookies}
        assert values["CTK"] == "session-ctk"


def test_home_looks_signed_out():
    anon = (
        "Sign in\nYour next job starts here\n"
        "Create an account or sign in to see your personalised job recommendations.\nGet Started"
    )
    assert home_looks_signed_out(anon)
    logged_in = "Welcome, Rafi\nSign out\nMy jobs\nAccount settings"
    assert not home_looks_signed_out(logged_in)


if __name__ == "__main__":
    test_decrypt_roundtrip_with_digest_prefix()
    test_decrypt_roundtrip_plain()
    test_unlock_cookie_db_writes_plaintext()
    test_prepare_unlocks_and_strips_cf()
    test_home_looks_signed_out()
    print("ok")
