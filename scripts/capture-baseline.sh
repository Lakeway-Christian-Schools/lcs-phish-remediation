#!/usr/bin/env bash
# TASK-01 — capture the KNOWN-GOOD running bridge into this repo before changes.
# Run ON lcs-phish-01 (or wherever the bridge runs). Scrubs no secrets itself —
# review src/bridge.prod.py and the .env keys before committing.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="/opt/gophish-bridge"

echo "[*] Capturing running bridge from ${SRC}"
[ -f "${SRC}/bridge.py" ] && cp "${SRC}/bridge.py" "${REPO}/src/bridge.prod.py" \
  && echo "    -> src/bridge.prod.py (gitignored; review before committing)"

echo "[*] Capturing live systemd unit"
systemctl cat gophish-bridge > "${REPO}/deploy/gophish-bridge.prod.service" 2>/dev/null \
  && echo "    -> deploy/gophish-bridge.prod.service" || echo "    (unit not found)"

echo "[*] Capturing .env KEYS only (values redacted)"
if [ -f "${SRC}/.env" ]; then
  sed -E 's/=.*/=<REDACTED>/' "${SRC}/.env" > "${REPO}/.env.captured-keys"
  echo "    -> .env.captured-keys (keys only; safe to review)"
fi

echo "[*] Diff reference vs production:"
diff -u "${REPO}/src/bridge.prod.py" "${REPO}/src/bridge.py" || true

cat <<'NEXT'

Next:
  1. Review src/bridge.prod.py for embedded secrets; scrub, then force-add:
       git add -f src/bridge.prod.py deploy/gophish-bridge.prod.service
  2. git commit -m "TASK-01: baseline known-good running bridge"
     git tag baseline
  3. Rotate anything that was embedded (TASK-04).
NEXT
