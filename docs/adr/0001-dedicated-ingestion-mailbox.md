# ADR-0001: Dedicated IONOS ingestion mailbox (interim)

- Status: Accepted (interim; superseded by ADR-0002 when TASK-07 lands)
- Date: 2026-11-04

## Context
Exchange Online retired Basic-auth IMAP; the bridge can't log into the M365
mailbox with a password. M365 shared mailboxes also reject interactive sign-in.

## Decision
Use a dedicated IONOS mailbox (`gophish-reports@lcstn-ionos.com`) that accepts
Basic-auth IMAP, fed by an auto-forward from `phishreport@lcstn.org`. The bridge
polls IONOS, never the M365 mailbox directly.

## Consequences
+ Unblocks reporting today with minimal code.
- Second provider + domain to maintain; a tenant forwarding exception (security
  review needed, TASK-09); re-injection-loop risk (TASK-05). Marked for removal.
