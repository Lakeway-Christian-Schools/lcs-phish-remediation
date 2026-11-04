# 02 — Reporting path: current vs target (TASK-07)

## Root cause recap

Exchange Online retired Basic auth for IMAP. The bridge can't log into the M365
mailbox with a password, so today it polls an IONOS mailbox fed by external
forwarding. That adds a second provider, a tenant forwarding exception, and a
same-account re-injection loop risk.

## Option A — Microsoft Graph, app-only  (preferred target)

```
Report Phish → phishreport@lcstn.org
        │  (no forward, no IONOS)
        ▼
bridge  ──Graph (HTTPS, app-only token)──►  read mailbox / subscribe to new mail
```

- Entra ID app registration; **application** permission `Mail.Read`.
- Scope it to the one mailbox with `New-ApplicationAccessPolicy` so the app
  cannot read the whole tenant.
- Bridge swaps `imaplib` for Graph REST (`/messages`, `$value` for MIME) or a
  change subscription/webhook for push.
- Removes IONOS, the forwarding exception (TASK-09), and the loop risk.

## Option B — IMAP XOAUTH2

Keep IMAP semantics but authenticate with an OAuth2 token instead of a password.
Same Entra app with `IMAP.AccessAsApp` + application access policy. Smaller code
change than Graph; keeps the current mailbox-polling shape.

## Why a bridge still exists either way

Anglerphish's built-in IMAP monitor most likely speaks only Basic auth — the
same wall. The bridge stays as the OAuth2 speaker and the unwrapper; it then
writes the Reported event via the Anglerphish API/DB or re-injects into a
mailbox Anglerphish can read.

## Cutover plan

1. Register + scope the Entra app; verify it reads `phishreport@lcstn.org`.
2. Add a Graph (or XOAUTH2) ingestion mode to the bridge behind a config flag.
3. Run both paths in parallel; compare Reported counts on a seed campaign.
4. Flip the flag; keep IONOS warm one campaign cycle as rollback.
5. Decommission IONOS + remove the forwarding exception (TASK-09).

See `docs/adr/0002-graph-oauth2-ingestion.md`.
