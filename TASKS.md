# Backlog

Work items derived from [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md). This file is
the source of truth for state; keep it current in the same commit as the work.

Status: ☐ todo · ◐ in progress · ☑ done · ⊘ blocked
Effort: S (<½ day) · M (~1 day) · L (multi-day)

## Do first

| ID | Pri | Status | Effort | Item | Acceptance criteria |
|----|-----|--------|--------|------|---------------------|
| TASK-01 | P0 | ☐ | S | Baseline the running bridge + unit in git | Real `/opt/gophish-bridge/bridge.py`, live `gophish-bridge.service`, and the `.env` *keys* (no values) committed on a `baseline` tag; secrets scrubbed; diff vs `src/bridge.py` recorded in a short note. |

## P1

| ID | Pri | Status | Effort | Item | Acceptance criteria |
|----|-----|--------|--------|------|---------------------|
| TASK-03 | P1 | ☐ | M | Self-healing bridge | Transient IMAP failure (`Errno 111`) recovers automatically with backoff; a single malformed message is logged and skipped, not fatal; no manual restart needed in a 24h soak. |
| TASK-04 | P1 | ☐ | S | Rotate exposed creds + secrets inventory | Every credential ever in the old script rotated; `docs/secrets-inventory.md` lists each secret, owner, store, rotation cadence. No secret in git history (verified). |
| TASK-05 | P1 | ☐ | M | Loop prevention + folder separation | Re-injected mail carries `X-LCS-Bridge-Processed`; bridge skips any message with it; ingest folder ≠ Anglerphish-monitored folder; documented test shows no re-ingestion loop. |
| TASK-06 | P1 | ☐ | M | Mark-seen ordering + idempotency | Message marked seen/moved only after confirmed re-injection; processed `Message-ID`s tracked across restart; injected-SMTP-fail test leaves message re-processable, no duplicate Reported event. |
| TASK-07 | P1 | ☐ | L | Retire IONOS → OAuth2/Graph ingestion | Entra app (app-only `Mail.Read`, access-policy-scoped to `phishreport@lcstn.org`) reads the mailbox; bridge authenticates without Basic auth; parallel-validated against current path; IONOS + forwarding exception decommissioned. See `docs/02-reporting-path-options.md` and `docs/adr/0002-*`. |
| TASK-08 | P1 | ☐ | S | Escrow encryption key | `ANGLERPHISH_ENCRYPTION_KEY` copy stored off-host in a vault; recovery procedure documented and dry-run tested; owner assigned. |
| TASK-09 | P1 | ☐ | S | Scope external-forwarding exception | M365 rule limited to the single mailbox (not tenant-wide); documented with owner + review date; ticket to remove it after TASK-07. |

## P2

| ID | Pri | Status | Effort | Item | Acceptance criteria |
|----|-----|--------|--------|------|---------------------|
| TASK-10 | P2 | ☐ | M | Config validation + fixture tests | Missing env var exits with a clear message at startup; ≥3 real wrapped-report fixtures committed; `pytest` covers each MIME branch; CI-runnable. |
| TASK-11 | P2 | ☐ | S | Observability | RotatingFileHandler active; heartbeat line each cycle; stdout→journald; alert hook on repeated SMTP/parse errors; `REPORT_EVENT` line unchanged for SIEM. |
| TASK-12 | P2 | ☐ | M | Robust RID extraction | QP/base64 decoded before match; match anchored to `LANDING_DOMAINS`; multiple/ambiguous RIDs logged not silently picked; explicit "no RID found" log. Covered by TASK-10 tests. |
| TASK-13 | P2 | ☐ | S | Re-injection mail auth | SPF/DKIM/DMARC verified for the sending path; `X-Original-Reporter` preserved; end-to-end test shows re-injected mail accepted, not junked. |
| TASK-15 | P2 | ☐ | S | Harden systemd unit | Dedicated user, sandboxing directives, `Restart=always`/`RestartSec`; DB dependency confirmed (`mariadb.service`); `systemd-analyze security` improved. |
| TASK-16 | P2 | ☐ | M | Document DB FK divergence | `docs/db-divergence.md` records the omitted FK + root cause (signed INT types); orphan-row cleanup added; Anglerphish version pinned; `reports` DDL + goose state (`20260720000002`) captured. |
| TASK-17 | P2 | ☐ | M | Backups + monitoring | Scheduled MariaDB dump + config/keys/certs backup; restore tested once; monitoring for service liveness + cert expiry. |
| TASK-18 | P2 | ☐ | S | Fix training asset URLs | Training HTML uses relative/correct-host paths; all images/CSS/JS load from `training.lcstn.org`; no cross-host/mixed-content warnings. |

## P3

| ID | Pri | Status | Effort | Item | Acceptance criteria |
|----|-----|--------|--------|------|---------------------|
| TASK-19 | P3 | ☐ | S | Admin-surface exposure | `:3333` bound to localhost/VPN only (verified from off-host); `phish.lcstn.org` TLS auto-renews. |
| TASK-20 | P3 | ☐ | S | Poll latency option | Decision recorded: keep 30s poll or adopt Graph subscription (depends on TASK-07). |
| TASK-21 | P3 | ☐ | S | Cert scope / CT teardown | SAN cert (not wildcard) for lures; documented DNS+cert teardown step after each campaign window. |

## Governance

| ID | Pri | Status | Effort | Item | Acceptance criteria |
|----|-----|--------|--------|------|---------------------|
| TASK-14 | Gov | ☐ | S | Authorization + retention policy | Signed authorization/scope on file per campaign; retention/purge policy for captured data; incidental-PII handling procedure. |

## Notes / decisions log

- 2026-11-04 — Repo scaffolded from the technical review. `src/bridge.py` is a
  reconstruction; TASK-01 must capture the real running script before changes.
- 2026-11-04 — Seeded fixture tests (TASK-10, partial). They immediately caught
  a real unwrapping bug: a base64-encoded nested `message/rfc822` hid the RID
  (would have shown as "No RID found" on genuine Defender reports). Added a
  base64-recovery pass in `extract_rid` (TASK-12). Still need REAL wrapped
  samples in `tests/fixtures/` across Outlook desktop/OWA/new Outlook.
- (add dated entries here as tasks complete)
