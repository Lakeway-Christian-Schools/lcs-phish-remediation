#!/usr/bin/env bash
#
# TASK-04 — lock down /opt/gophish-bridge/.env permissions.
# Idempotent: owner root, group gophish, mode 640 so the service user `gophish`
# can read it but no other local user can. Run on lcs-phish-01 with sudo.
# Does NOT read, print, or modify the file's contents — permissions only.
#
#   sudo ./lockdown-env.sh
#
set -euo pipefail

ENV_FILE="${1:-/opt/gophish-bridge/.env}"
SVC_GROUP="${SVC_GROUP:-gophish}"   # group the bridge service runs under

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: run with sudo (need to chown/chmod a root-owned file)." >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found." >&2
  exit 1
fi

if ! getent group "$SVC_GROUP" >/dev/null; then
  echo "ERROR: group '$SVC_GROUP' does not exist. Set SVC_GROUP=<service group>." >&2
  echo "       (Confirm with: systemctl show gophish-bridge -p User,Group)" >&2
  exit 1
fi

echo "Before: $(stat -c '%A %U:%G %n' "$ENV_FILE")"

chown "root:${SVC_GROUP}" "$ENV_FILE"
chmod 640 "$ENV_FILE"

echo "After:  $(stat -c '%A %U:%G %n' "$ENV_FILE")"

# Verify the end state explicitly.
mode=$(stat -c '%a' "$ENV_FILE")
owner=$(stat -c '%U' "$ENV_FILE")
group=$(stat -c '%G' "$ENV_FILE")
if [[ "$mode" == "640" && "$owner" == "root" && "$group" == "$SVC_GROUP" ]]; then
  echo "OK: $ENV_FILE is 640 root:${SVC_GROUP} — not readable by other local users."
else
  echo "WARN: unexpected end state ($mode $owner:$group). Review manually." >&2
  exit 1
fi

# Flag any sibling env copies that might still be exposed.
shopt -s nullglob
dir=$(dirname "$ENV_FILE")
extra=( "$dir"/.env.* "$dir"/*.env "$dir"/.env~ )
if (( ${#extra[@]} )); then
  echo "NOTE: other env-like files present — check/lock these too:"
  for f in "${extra[@]}"; do
    [[ "$f" == "$ENV_FILE" ]] && continue
    echo "  $(stat -c '%A %U:%G %n' "$f")"
  done
fi
