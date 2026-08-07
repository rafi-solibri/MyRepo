"""Send the Resend email payload via curl (urllib is often CF-blocked)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def send_payload_file(payload_path: Path, *, api_key: str | None = None) -> dict[str, Any]:
    """POST send-payload.json to Resend. Returns parsed JSON response."""
    api_key = api_key or os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError(
            "RESEND_API_KEY is not set. Create a sending key via Resend MCP "
            "create-api-key, export it, then re-run — or curl the payload manually."
        )

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    idem = payload.get("idempotencyKey") or ""

    cmd = [
        "curl",
        "-sS",
        "-w",
        "\nHTTP:%{http_code}",
        "-X",
        "POST",
        "https://api.resend.com/emails",
        "-H",
        f"Authorization: Bearer {api_key}",
        "-H",
        "Content-Type: application/json",
        "-H",
        "User-Agent: Mozilla/5.0 (compatible; hotel-price-watch/1.0)",
    ]
    if idem:
        cmd.extend(["-H", f"Idempotency-Key: {idem}"])
    cmd.extend(["--data-binary", f"@{payload_path}"])

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    out = (proc.stdout or "").strip()
    if "HTTP:" not in out:
        raise RuntimeError(f"Unexpected curl output: {out!r} stderr={proc.stderr!r}")
    body, _, status_line = out.rpartition("\nHTTP:")
    status = int(status_line.strip())
    if status >= 400:
        raise RuntimeError(f"Resend HTTP {status}: {body[:2000]}")
    data = json.loads(body or "{}")
    log.info("Resend send ok id=%s", data.get("id"))
    return data
