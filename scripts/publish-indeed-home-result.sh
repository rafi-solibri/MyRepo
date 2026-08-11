#!/usr/bin/env bash
# Backward-compatible wrapper → publish-home-result.sh indeed
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$ROOT/scripts/publish-home-result.sh" indeed "$@"
