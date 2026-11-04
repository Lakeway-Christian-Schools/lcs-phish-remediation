# 01 — Architecture

## The problem

Microsoft 365 Defender's **Report Phish** button does not forward the original
email intact. It wraps it in a new message — nested `message/rfc822`, a `.eml`
attachment, or TNEF (`winmail.dat`). Anglerphish/GoPhish can't reliably find the
campaign **RID** inside that wrapper, so the **Reported** event is lost and the
metric is unreliable.

## Current pipeline (known-good)

```
User receives Anglerphish campaign email  (SMTP2Go → M365 → mailbox)
        │  clicks Report Phish
        ▼
phishreport@lcstn.org            M365 licensed mailbox (not shared — see ADR-0001)
        │  automatic forward (scoped exception — TASK-09)
        ▼
gophish-reports@lcstn-ionos.com  IONOS, Basic-auth IMAP-pollable
        │  IMAP poll (30s, UNSEEN)
        ▼
bridge.py                        unwrap → extract RID → SMTP re-inject
        │
        ▼
Anglerphish reporting mailbox    logs "Reported"
```

## Why IONOS exists

Exchange Online retired **Basic authentication for IMAP**. The deployed
reporting flow logs in with a username/password, which Exchange now rejects
(`AccountDisabledException` / `LOGIN failed`) regardless of MFA group
membership. IONOS provides a mailbox that still accepts Basic-auth IMAP, so the
bridge has something to poll. This is a **workaround**, tracked for removal by
TASK-07 (OAuth2/Graph against the M365 mailbox directly).

## Hosts & listeners

| Component | Value |
|---|---|
| App host | `lcs-phish-01` |
| Anglerphish admin | `127.0.0.1:3333` (TLS) |
| Anglerphish phish | `127.0.0.1:8080` (behind NGINX) |
| MariaDB | `127.0.0.1:3306`, db `anglerphish` |
| Landing hosts | `phish/login/payroll/docs.lcstn.org` → NGINX → `:8080` |
| Training | `training.lcstn.org` → `/var/www/lcs-training` |

## Trust boundaries

- **Inbound to bridge:** report contents are attacker-influenced (a real phish
  may be inside). Parse defensively; never render/execute content.
- **Bridge → Anglerphish:** re-injected mail must pass SPF/DKIM/DMARC
  (TASK-13) or it may be dropped before the RID is seen.
