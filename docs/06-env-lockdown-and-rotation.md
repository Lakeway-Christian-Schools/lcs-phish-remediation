# 06 — `.env` lockdown & credential rotation (TASK-04)

**Why:** the baseline capture found `/opt/gophish-bridge/.env` at mode **0644,
root-owned** — world-readable. Every local account on `lcs-phish-01` can read
the IMAP/SMTP credentials. Because they have been exposed to any local user
(and the file dates to May), we both **lock the file down** and **rotate the
credentials**.

Run these on `lcs-phish-01` as a sudo-capable account. The bridge runs as user
`gophish` and polls every 30 s, so a brief restart is harmless.

---

## Part A — Lock the file down (do this first, zero downtime)

Owner `root`, group `gophish`, mode `640`: the service (user `gophish`, member
of group `gophish`) can still **read** it; no other local user can; and because
root owns it, the service account can't rewrite its own secrets file.

```bash
sudo chown root:gophish /opt/gophish-bridge/.env
sudo chmod 640          /opt/gophish-bridge/.env
stat -c '%A %U:%G %n' /opt/gophish-bridge/.env   # expect: -rw-r----- root:gophish …
```

`scripts/lockdown-env.sh` does exactly this and verifies it (idempotent — safe
to re-run). While you're here, confirm nothing else in the dir is permissive:

```bash
ls -la /opt/gophish-bridge/
# bridge.py 0644 root:root is fine (no secrets — verified at baseline).
# If any *.env.bak / .env.* copies exist, lock or remove them too.
```

Part A alone closes the exposure. Part B removes the risk that the old
(previously readable) credentials are still valid.

---

## Part B — Rotate the exposed credentials

The bridge uses one IONOS mailbox for both IMAP (read) and SMTP (re-inject).
Confirm from the real file (values, not just keys) whether `IMAP_PASS` and
`SMTP_PASS` are the same account:

```bash
sudo grep -E '^(IMAP|SMTP)_(USER|PASS)=' /opt/gophish-bridge/.env
```

> Run that in a shell where history isn't shared/synced, and clear it after
> (`history -c` for the current shell) so the secret isn't left in scrollback.

### B.1 — Set a new password in IONOS
In the IONOS control panel, change the password for the ingestion mailbox
(`gophish-reports@lcstn-ionos.com`, or whatever `*_USER` shows). Prefer a long
random value from a password manager. **Keep the old password until B.4
verifies** — don't delete the mailbox or disable the old secret elsewhere yet.

### B.2 — Update `.env`
Edit in place (the file is root-owned now, so use sudo):

```bash
sudo nano /opt/gophish-bridge/.env      # update IMAP_PASS (and SMTP_PASS if same)
```

Keep the same `KEY=value` format, no quotes, no trailing spaces.

### B.3 — Restart the bridge
`EnvironmentFile` is read at service start, so the new values take effect on
restart:

```bash
sudo systemctl restart gophish-bridge
systemctl status gophish-bridge --no-pager
```

### B.4 — Verify reporting still works (don't skip)
Watch the log for a clean cycle, then prove the full path end-to-end:

```bash
sudo tail -f /opt/gophish-bridge/bridge.log
# healthy: "Connecting to IMAP mailbox" → no auth errors
```

Then run the smoke test from `docs/04-operations-runbook.md`: send yourself a
campaign email, click **Report Phish**, and confirm a
`REPORT_EVENT | user=… | rid=…` line appears and the target shows **Reported**
in Anglerphish. **Only after this passes** is rotation complete.

### B.5 — Rollback (if B.4 fails)
Put the old password back in `.env`, `sudo systemctl restart gophish-bridge`,
confirm recovery, then diagnose (usually a typo, a quoting issue, or IONOS not
having applied the new password yet). Re-attempt rotation once resolved.

---

## After rotation

- Record the rotation date and set the next cadence in
  [`secrets-inventory.md`](secrets-inventory.md).
- Rotate the **other** secrets that may have shared the box's exposure if
  warranted (SMTP2Go API key, MariaDB app password) — see the inventory.
- **`ANGLERPHISH_ENCRYPTION_KEY` is different** — don't "rotate" it casually.
  Re-keying it re-encrypts stored SMTP creds and captured data; losing the old
  value forfeits that data. Escrow it (TASK-08) rather than rotating it here.

## Done when
- `.env` is `640 root:gophish` (verified by `stat`),
- IONOS credential rotated and `.env` updated,
- smoke test shows a Reported event on the new credential,
- `secrets-inventory.md` updated with the rotation date.
