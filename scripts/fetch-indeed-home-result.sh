#!/usr/bin/env bash
# Backward-compatible wrapper → fetch-home-result.sh indeed
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$ROOT/scripts/fetch-home-result.sh" indeed "$@"
