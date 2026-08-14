#!/usr/bin/env python3
"""Prepare a SeleniumBase UC profile that keeps Indeed auth but drops burned CF cookies.

The synced `/home/ubuntu/chrome-indeed-profile` often accumulates Cloudflare
challenge cookies that turn Turnstile into a hard "Additional Verification
Required" page (no widget). Copying auth cookies into a fresh profile and
deleting `cf_*` / `__cf*` rows lets `uc_gui_click_captcha()` clear CF again
while preserving Welcome / CTK / Passport tokens.

Chrome encrypts cookie values as `v10` AES-128-CBC ("peanuts" / saltysalt).
Copying the SQLite blobs into a *different* `--user-data-dir` leaves them
undecryptable (new profile key / no keyring), so Indeed renders the anonymous
"Get Started" home even though CTK / Passport cookie *names* are present.
Unlock those blobs to plaintext `value` (empty `encrypted_value`) so UC Chrome
can send the session after Turnstile clears.
"""
from __future__ import annotations

import argparse
import hashlib
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

AUTH_COOKIE_NAMES = (
    "CTK",
    "PPID",
    "__Secure-PassportAuthProxy-BearerToken",
    "rememberMe",
)

# Chrome cookie expires_utc is microseconds since 1601-01-01.
_CHROME_EPOCH_DELTA = 11644473600


def _aes_cbc_decrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        return decryptor.update(data) + decryptor.finalize()
    except Exception:
        pass
    try:
        from Crypto.Cipher import AES  # type: ignore

        return AES.new(key, AES.MODE_CBC, iv).decrypt(data)
    except Exception as exc:
        raise RuntimeError(f"no AES backend: {exc}") from exc


def _pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        return data
    pad = data[-1]
    if 1 <= pad <= 16 and data.endswith(bytes([pad]) * pad):
        return data[:-pad]
    return data


def _is_mostly_text(blob: bytes) -> bool:
    if not blob:
        return False
    text = sum(1 for b in blob if 32 <= b < 127 or b in (9, 10, 13))
    return (text / len(blob)) >= 0.85


def _strip_digest_prefix(plain: bytes) -> bytes:
    """Chrome Linux OSCrypt often prefixes a 32-byte MAC/digest."""
    if len(plain) > 32 and _is_mostly_text(plain[32:]) and not _is_mostly_text(plain[:32]):
        return plain[32:]
    return plain


def chrome_linux_v10_key(password: bytes = b"peanuts") -> bytes:
    return hashlib.pbkdf2_hmac("sha1", password, b"saltysalt", 1, dklen=16)


def decrypt_chrome_v10(blob: bytes, key: bytes | None = None) -> bytes | None:
    """Decrypt a Chrome Linux `v10`/`v11` cookie blob. Returns None on failure."""
    if not blob or not isinstance(blob, (bytes, bytearray, memoryview)):
        return None
    raw = bytes(blob)
    if len(raw) < 19:
        return None
    if raw[:3] not in (b"v10", b"v11"):
        return None
    key = key or chrome_linux_v10_key()
    try:
        pt = _pkcs7_unpad(_aes_cbc_decrypt(key, b" " * 16, raw[3:]))
    except Exception:
        return None
    if not pt:
        return None
    return _strip_digest_prefix(pt)


def encrypt_chrome_v10(plain: bytes, key: bytes | None = None) -> bytes:
    """Test helper: encrypt a value the way Chrome Linux `v10` cookies are stored."""
    key = key or chrome_linux_v10_key()
    pad = 16 - (len(plain) % 16)
    padded = plain + bytes([pad]) * pad
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        encryptor = Cipher(algorithms.AES(key), modes.CBC(b" " * 16)).encryptor()
        ct = encryptor.update(padded) + encryptor.finalize()
    except Exception:
        from Crypto.Cipher import AES  # type: ignore

        ct = AES.new(key, AES.MODE_CBC, b" " * 16).encrypt(padded)
    return b"v10" + ct


def _chrome_expiry_unix(expires_utc: int | None) -> float | None:
    if not expires_utc:
        return None
    try:
        unix = (int(expires_utc) / 1_000_000) - _CHROME_EPOCH_DELTA
    except Exception:
        return None
    if unix <= 0:
        return None
    return unix


def _samesite_name(val: int | None) -> str | None:
    # Chromium: -1 unspecified, 0 none, 1 lax, 2 strict
    if val == 0:
        return "None"
    if val == 1:
        return "Lax"
    if val == 2:
        return "Strict"
    return None


def unlock_cookie_db(cdb: Path) -> dict:
    """Decrypt v10 blobs in-place to plaintext `value`; clear `encrypted_value`."""
    stats = {"unlocked": 0, "failed": 0, "alreadyPlain": 0, "authUnlocked": []}
    if not cdb.exists():
        return stats
    con = sqlite3.connect(str(cdb))
    cur = con.cursor()
    try:
        rows = cur.execute(
            "select rowid, host_key, name, value, encrypted_value from cookies"
        ).fetchall()
    except sqlite3.Error:
        con.close()
        return stats
    for rowid, host, name, value, ev in rows:
        if isinstance(value, str) and value.strip():
            stats["alreadyPlain"] += 1
            continue
        plain = decrypt_chrome_v10(ev or b"")
        if plain is None:
            if ev:
                stats["failed"] += 1
            continue
        try:
            text = plain.decode("utf-8")
        except UnicodeDecodeError:
            stats["failed"] += 1
            continue
        cur.execute(
            "update cookies set value=?, encrypted_value=x'' where rowid=?",
            (text, rowid),
        )
        stats["unlocked"] += 1
        if name in AUTH_COOKIE_NAMES:
            stats["authUnlocked"].append(name)
    con.commit()
    con.close()
    stats["authUnlocked"] = sorted(set(stats["authUnlocked"]))
    return stats


def load_decrypted_indeed_cookies(src: Path) -> list[dict]:
    """Return CDP Network.setCookie payloads for Indeed cookies in `src`."""
    cdb = src / "Default" / "Cookies"
    alt = src / "Default" / "Network" / "Cookies"
    path = cdb if cdb.exists() else alt
    if not path.exists():
        return []
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "select host_key, name, value, encrypted_value, path, expires_utc, "
            "is_secure, is_httponly, samesite from cookies "
            "where host_key like '%indeed%'"
        ).fetchall()
    except sqlite3.Error:
        con.close()
        return []
    con.close()
    out = []
    for host, name, value, ev, cpath, exp, secure, httponly, samesite in rows:
        text = value.decode("utf-8") if isinstance(value, bytes) else (value or "")
        if not str(text).strip():
            plain = decrypt_chrome_v10(ev or b"")
            if plain is None:
                continue
            try:
                text = plain.decode("utf-8")
            except UnicodeDecodeError:
                continue
        cookie = {
            "name": name,
            "value": text,
            "domain": host,
            "path": cpath or "/",
            "secure": bool(secure),
            "httpOnly": bool(httponly),
        }
        unix = _chrome_expiry_unix(exp)
        if unix:
            cookie["expires"] = unix
        same = _samesite_name(samesite)
        if same:
            cookie["sameSite"] = same
        out.append(cookie)
    return out


def prepare(src: Path, dst: Path) -> dict:
    if dst.exists():
        shutil.rmtree(dst)
    (dst / "Default").mkdir(parents=True)

    copied = []
    local_state = src / "Local State"
    if local_state.exists():
        shutil.copy2(local_state, dst / "Local State")
        copied.append("Local State")

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

    # Chrome 115+ may read Default/Network/Cookies; mirror the unlocked DB there.
    src_net = src / "Default" / "Network" / "Cookies"
    if src_net.exists():
        dnet = dst / "Default" / "Network" / "Cookies"
        dnet.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_net, dnet)
        copied.append("Default/Network/Cookies")

    cdb = dst / "Default" / "Cookies"
    deleted = 0
    remaining = []
    unlock = {"unlocked": 0, "failed": 0, "alreadyPlain": 0, "authUnlocked": []}
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
        unlock = unlock_cookie_db(cdb)
        net = dst / "Default" / "Network" / "Cookies"
        if net.exists() and net.resolve() != cdb.resolve():
            unlock_cookie_db(net)
        elif not net.exists() and unlock.get("unlocked"):
            net.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cdb, net)

    return {
        "src": str(src),
        "dst": str(dst),
        "copied": copied,
        "cfCookiesDeleted": deleted,
        "indeedCookieNames": remaining,
        "cookiesUnlocked": unlock.get("unlocked", 0),
        "cookiesUnlockFailed": unlock.get("failed", 0),
        "authUnlocked": unlock.get("authUnlocked") or [],
        "hasAuth": any(
            n in remaining
            for n in AUTH_COOKIE_NAMES
        )
        or bool(unlock.get("authUnlocked")),
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
