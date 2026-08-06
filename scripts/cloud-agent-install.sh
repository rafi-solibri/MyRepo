#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/bootstrap-job-assets.sh
if [[ -f tools/package.json ]]; then
  (cd tools && npm ci --no-fund --no-audit || npm install --no-fund --no-audit)
fi
mkdir -p \
  /home/ubuntu/resumes \
  /home/ubuntu/Documents \
  /home/ubuntu/.naukri-chrome-profile \
  /home/ubuntu/.config/chrome-foundit \
  /home/ubuntu/chrome-instahyre-profile \
  /home/ubuntu/chrome-indeed-profile \
  /home/ubuntu/chrome-cdp-profile \
  /home/ubuntu/chrome-linkedin-profile \
  /home/ubuntu/chrome-cutshort-profile \
  /opt/cursor/artifacts
echo "Job-apply assets ready."
ls -la resumes/Rafi_Resume.docx /home/ubuntu/resumes/Rafi_Resume.docx 2>/dev/null || true
