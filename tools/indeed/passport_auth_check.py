#!/usr/bin/env python3
"""Check Indeed Passport cookies for live (non-expired) auth.

SQLite name presence alone is not enough: BearerToken / OauthExpires rows can
linger for weeks after the JWT expires, so preflight reports hasAuth=true while
UC hits a Sign-in wall. Decrypt Linux v10 Chrome cookies (peanuts key) and read
OauthExpires or the Bearer JWT `exp`.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    def _aes_cbc_decrypt(key: bytes, iv: bytes, payload: bytes) -> bytes:
        decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        return decryptor.update(payload) + decryptor.finalize()

except ImportError:  # pragma: no cover
    try:
        from Crypto.Cipher import AES as _AES

        def _aes_cbc_decrypt(key: bytes, iv: bytes, payload: bytes) -> bytes:
            return _AES.new(key, _AES.MODE_CBC, iv).decrypt(payload)

    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "passport_auth_check requires cryptography or pycryptodome"
        ) from exc


def _decrypt_v10(enc: bytes) -> bytes:
    if not enc.startswith(b"v10"):
        return enc
    key = hashlib.pbkdf2_hmac("sha1", b"peanuts", b"saltysalt", 1, 16)
    dec = _aes_cbc_decrypt(key, b" " * 16, enc[3:])
    pad = dec[-1]
    if isinstance(pad, int) and 1 <= pad <= 16 and dec.endswith(bytes([pad]) * pad):
        dec = dec[:-pad]
    return dec


def _cookie_blob(db: Path, name: str) -> bytes | None:
    if not db.exists():
        return None
    con = sqlite3.connect(str(db))
    try:
        row = con.execute(
            "select encrypted_value from cookies "
            "where name=? and host_key like '%indeed%' limit 1",
            (name,),
        ).fetchone()
    finally:
        con.close()
    return row[0] if row and row[0] else None


def status_from_plaintext(
    oauth_plain: bytes | None,
    bearer_plain: bytes | None,
    now: float | None = None,
) -> dict:
    """Derive Passport status from already-decrypted cookie payloads."""
    now = time.time() if now is None else now
    out: dict = {
        "ok": False,
        "hasCookies": bool(oauth_plain or bearer_plain),
        "exp": None,
        "expIso": None,
        "expired": None,
        "source": None,
        "reason": "passport_cookies_missing",
    }
    if not out["hasCookies"]:
        return out
    if oauth_plain:
        m = re.search(rb"(?<!\d)(\d{10})(?!\d)", oauth_plain)
        if m:
            exp = int(m.group(1))
            out.update(
                exp=exp,
                expIso=datetime.fromtimestamp(exp, tz=timezone.utc).isoformat(),
                expired=exp < now,
                ok=exp >= now,
                source="OauthExpires",
                reason="ok" if exp >= now else "indeed_passport_expired",
            )
            return out
    if bearer_plain:
        idx = bearer_plain.find(b"eyJ")
        if idx >= 0:
            tok = bearer_plain[idx:].decode("utf-8", "ignore")
            m = re.match(r"(eyJ[\w-]+\.eyJ[\w-]+\.[\w-]+)", tok)
            if m:
                parts = m.group(1).split(".")
                pad = "=" * ((4 - len(parts[1]) % 4) % 4)
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
                exp = int(payload.get("exp") or 0)
                out.update(
                    exp=exp or None,
                    expIso=(
                        datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
                        if exp
                        else None
                    ),
                    expired=(exp < now) if exp else None,
                    ok=bool(exp) and exp >= now,
                    source="BearerToken.jwt",
                    reason=(
                        "ok"
                        if exp and exp >= now
                        else "indeed_passport_expired"
                        if exp
                        else "passport_jwt_missing_exp"
                    ),
                )
                return out
    out["reason"] = "passport_cookies_undecryptable_or_missing_exp"
    return out


def check_passport(profile_root: str | Path) -> dict:
    root = Path(profile_root)
    db = root / "Default" / "Cookies"
    if not db.exists():
        db = root / "Default" / "Network" / "Cookies"
    out: dict = {
        "ok": False,
        "profile": str(root),
        "cookiesDb": str(db) if db.exists() else None,
        "hasCookies": False,
        "exp": None,
        "expIso": None,
        "expired": None,
        "source": None,
        "reason": "passport_cookies_missing",
    }
    if not db.exists():
        return out

    oauth = _cookie_blob(db, "__Secure-PassportAuthProxy-OauthExpires")
    bearer = _cookie_blob(db, "__Secure-PassportAuthProxy-BearerToken")
    out["hasCookies"] = bool(oauth or bearer)
    if not out["hasCookies"]:
        return out

    try:
        oauth_plain = _decrypt_v10(oauth) if oauth else None
        bearer_plain = _decrypt_v10(bearer) if bearer else None
        parsed = status_from_plaintext(oauth_plain, bearer_plain)
        out.update(parsed)
    except Exception as exc:  # pragma: no cover
        out["reason"] = f"passport_check_error:{type(exc).__name__}"
        out["error"] = str(exc)[:200]
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--profile",
        default="/home/ubuntu/chrome-indeed-profile",
        help="Chrome user-data-dir with Default/Cookies",
    )
    args = ap.parse_args()
    info = check_passport(args.profile)
    print(json.dumps(info, indent=2))
    return 0 if info.get("ok") else 3


if __name__ == "__main__":
    sys.exit(main())
