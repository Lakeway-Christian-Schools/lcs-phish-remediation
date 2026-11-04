# Recommendations

The prioritized technical review this project executes. Each item maps to a
`TASK-NN` in [`TASKS.md`](TASKS.md). Priorities: **P0** before anything else ·
**P1** correctness / security / data-loss · **P2** hardening · **P3** nice to have.

## P0 — baseline the known-good state (TASK-01)

The handoff says the working pipeline "should be preserved in source control
before additional development." Do it literally: commit the real running
`/opt/gophish-bridge/bridge.py`, its `.env` *schema* (not secrets), and the
live systemd unit before adopting anything here. `src/bridge.py` is a
reconstruction, not production. Diff before you trust it.

## P1 — correctness, security, data loss

- **Retire the IMAP/IONOS hop; move to OAuth2 against M365 (TASK-07).**
  Exchange Online retired Basic auth for IMAP — that is the real root cause, and
  excluding the account from MFA won't restore it. Target state: an Entra app
  (app-only `Mail.Read`, scoped to `phishreport@lcstn.org` via
  `New-ApplicationAccessPolicy`) reading the mailbox over Graph, or IMAP
  XOAUTH2. Removes the second provider, the external-forwarding exception, and
  the same-account reinjection loop. Biggest single architectural win.
- **Restore loop prevention + separate folders (TASK-05).** The revised bridge
  dropped the `X-Gophish-Processed` marker and reinjects into the same account
  it polls — a re-ingestion loop. Restore a marker header, skip messages that
  carry it, and separate the ingest folder from the one Anglerphish monitors.
- **Don't lose reports — mark-seen ordering + idempotency (TASK-06).** Mark a
  message `\Seen` / move it only after a confirmed SMTP re-injection; track
  processed `Message-ID`s so a crash can't double-inject or drop a report.
- **Self-healing bridge (TASK-03).** `[Errno 111] Connection refused` needed a
  manual restart. Reconnect with exponential backoff; `Restart=always` as a
  backstop; one bad message must not kill the loop.
- **Escrow `ANGLERPHISH_ENCRYPTION_KEY` (TASK-08).** It protects SMTP creds and
  captured submissions at rest. Lose it and that data is unrecoverable. Store a
  copy off-host in a vault; document recovery.
- **Rotate exposed credentials + secrets inventory (TASK-04).** Rotate anything
  ever present in the original bridge script. Build an inventory (IONOS,
  SMTP2Go, MariaDB, encryption key, TLS keys) with owners and rotation cadence.
- **Scope the external-forwarding exception (TASK-09).** The M365 outbound rule
  that unblocked forwarding should apply to the one mailbox, not tenant-wide
  (it's a known exfiltration path). Document it; remove it once TASK-07 lands.

## P2 — hardening and maintainability

- **Observability: rotation, heartbeat, alerting (TASK-11).** RotatingFileHandler,
  a periodic heartbeat line so a dead loop is detectable, alerts on repeated
  parse/SMTP failures, log to stdout for journald. Keep the machine-readable
  `REPORT_EVENT | user=… | rid=…` format.
- **Robust RID extraction (TASK-12).** Decode quoted-printable/base64 first;
  anchor the match to the real landing hosts so Defender's own wrapper text
  can't yield a false RID; handle multiple/ambiguous matches; log "no RID found".
- **Mail auth on the re-injection path (TASK-13).** Confirm SPF/DKIM/DMARC so
  re-injected mail isn't dropped/junked; carry `X-Original-Reporter` since the
  `From` rewrite (fix for `554 Unauthorized sender`) erases attribution.
- **Config validation + tests (TASK-10).** Fail fast on missing env vars; keep a
  corpus of real wrapped reports (`.eml`, `message/rfc822`, TNEF) as regression
  fixtures. The unwrapping is the brittle part.
- **Harden the systemd unit (TASK-15).** Dedicated user, `NoNewPrivileges`,
  `ProtectSystem=strict`, `ProtectHome`, `PrivateTmp`, `Restart=always`. Confirm
  the DB dependency is `mariadb.service`, not `mysql.service`.
- **Document the dropped DB foreign key (TASK-16).** The `reports` table was
  created by hand (FK omitted) outside goose. Document the divergence, add
  cleanup for orphaned rows, pin the Anglerphish version, capture DDL + goose
  state so a rebuild/upgrade is reproducible.
- **Backups + monitoring (TASK-17).** Scheduled MariaDB dumps + config/keys/
  certs; service-liveness and cert-expiry monitoring; test a restore.
- **Fix training asset URLs at the source (TASK-18).** Broken images come from
  HTML requesting assets on `phish.lcstn.org` while they're served on
  `training.lcstn.org`. Use relative/correct-host URLs, not cross-host proxying.

## P3 — later

- **Admin exposure (TASK-19).** Keep `:3333` bound to localhost / behind VPN;
  automate `phish.lcstn.org` TLS renewal.
- **Poll latency (TASK-20).** 30s is fine; Graph subscriptions (TASK-07) give
  push if near-real-time is ever wanted.
- **Cert scope / CT exposure (TASK-21).** Prefer a SAN cert over wildcard; the
  lookalike hostnames appear in public Certificate Transparency logs — tear down
  DNS/certs after each training window.

## Governance (TASK-14)

Keep on file: written authorization + scope with leadership sign-off per
campaign; a data-retention/purge policy for captured submissions; a procedure
for real credentials/PII that land in the reporting mailbox incidentally.
