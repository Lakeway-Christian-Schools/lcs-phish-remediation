# 03 — Troubleshooting

Failures seen during development, cause, and fix. Each hardening item has a
backlog ID.

## 1. `554 Unauthorized sender address` (SMTP re-inject)
Relay account (`SMTP_USER`) differed from the `From` header. **Fix:** rewrite
`From` to `SMTP_USER`; keep the reporter in `X-Original-Reporter` (TASK-13).

## 2. `550 5.7.520` external forwarding blocked
M365 default outbound policy blocks auto external forwarding. **Fix:** allow it
**for the one mailbox only** (TASK-09) — not tenant-wide (exfiltration path).

## 3. `Recipient domain does not exist` (lcstn-ionos.com)
Domain created in IONOS but **not verified**, so DNS wasn't published. **Fix:**
verify the domain, re-enable DNS. Confirm: `dig +short MX lcstn-ionos.com`.

## 4. `AccountDisabledException` on `phishreport` / shared mailbox
M365 **shared mailboxes don't support interactive sign-in**; and Exchange has
retired Basic-auth IMAP generally. A licensed mailbox was chosen, but the bridge
still can't Basic-auth into it — hence IONOS, and TASK-07 (OAuth2) as the fix.

## 5. `[Errno 111] Connection refused` (IMAP), bridge stops
Stale connection / DNS / env reload. **Immediate:** `sudo systemctl restart
gophish-bridge`. **Proper fix:** self-healing reconnect with backoff (TASK-03)
so no human restart is needed.

## 6. `i/o timeout` to `…:993` while manual TCP/TLS tests pass
Network path is fine; the app-level login/handshake is the problem. Compare
service user, DNS result, and auth method — points back to the Basic-auth
retirement (TASK-07), not the firewall.

## Quick diagnosis

| Symptom | Likely item |
|---|---|
| Report never reaches ingestion mailbox | #2 forwarding or #3 DNS |
| Bridge running, no `REPORT_EVENT` | RID not found — check MIME unwrap / anchoring (TASK-12) |
| Re-inject `554` | #1 From rewrite |
| Bridge silent/stopped | #5 reconnect (TASK-03) |
| Reported event still missing | RID recovered but mail dropped — SPF/DKIM/DMARC (TASK-13) |
| Same report counted twice / loop | marker + idempotency (TASK-05/06) |
