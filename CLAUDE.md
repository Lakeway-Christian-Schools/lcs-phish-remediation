# CLAUDE.md — project context

Read this first. It orients any session (human or Claude) working on this repo.

## What this project is

Remediation and hardening work for **Lakeway Christian Schools' (lcstn.org)**
authorized phishing-awareness platform. The platform runs **Anglerphish** (a
maintained GoPhish fork) on host `lcs-phish-01`, and a custom Python **bridge**
repairs the "Reported" telemetry that Microsoft 365 Defender's *Report Phish*
button otherwise breaks.

This repo is **not** the Anglerphish source. It holds:
- the **reporting bridge** (`src/bridge.py`) and its deploy assets,
- the **prioritized recommendations** from a technical review (`RECOMMENDATIONS.md`),
- a **work backlog** that turns those into trackable tasks (`TASKS.md`),
- **docs** capturing architecture, the reporting path, and troubleshooting.

## The core problem (why the bridge exists)

When a user clicks **Report Phish**, Defender wraps the original email inside a
new message (nested `message/rfc822`, a `.eml` attachment, or TNEF
`winmail.dat`). Anglerphish/GoPhish can't reliably find the campaign **RID**
inside that wrapper, so the **Reported** event is lost and the metric becomes
untrustworthy. The bridge ingests the wrapped report, recovers the RID, and
re-injects a clean copy so the event is logged against the right target.

## Current known-good pipeline (do not regress)

```
Report Phish (M365 Defender)
  → phishreport@lcstn.org            (M365 licensed mailbox)
  → forward → gophish-reports@lcstn-ionos.com   (IONOS, IMAP-pollable)
  → bridge.py  (poll → unwrap → extract RID → re-inject via SMTP)
  → Anglerphish logs "Reported"
```

Why IONOS at all: **Exchange Online has retired Basic auth for IMAP**, so the
bridge cannot log into the M365 mailbox with a password. IONOS is the
short-term pollable mailbox. The strategic fix (TASK-07) is OAuth2 against the
M365 mailbox directly, retiring IONOS and the external-forwarding exception.

## Hosts, domains, paths (from the handoff + project record)

| Thing | Value |
|---|---|
| App host | `lcs-phish-01` (Linux) |
| App service | `anglerphish.service`, user `anglerphish`, dir `/opt/anglerphish` |
| Admin listener | `127.0.0.1:3333` (TLS) — keep off the public internet |
| Phish listener | `127.0.0.1:8080` (no TLS, behind NGINX) |
| DB | MariaDB `127.0.0.1:3306`, database `anglerphish` |
| Bridge service | `gophish-bridge.service`, logs `/opt/gophish-bridge/bridge.log` |
| Landing hosts | `phish / login / payroll / docs.lcstn.org` → NGINX → `:8080` |
| Training site | `training.lcstn.org` → `/var/www/lcs-training` |
| Outbound campaign relay | SMTP2Go |
| Encryption key | `ANGLERPHISH_ENCRYPTION_KEY` via systemd (value NOT in repo) |

## Golden rules

1. **Baseline before change (TASK-01).** The running `/opt/gophish-bridge/bridge.py`
   and the live systemd unit must be committed (secrets scrubbed) *before*
   adopting the reference versions here. `src/bridge.py` is a **reconstruction**,
   not the production script.
2. **No secrets in git.** Credentials live only in `.env` (chmod 600, service
   account). `.gitignore` already blocks `.env` and `*.prod.*`. If a secret was
   ever in the old script, treat it as exposed and rotate it (TASK-04).
3. **Don't lose reports.** Mark a message seen / move it only *after* a
   confirmed re-injection (TASK-05).
4. **Authorized testing only.** This targets staff of a real school. Keep
   written authorization and a retention policy on file (TASK-14).
5. **This session has a linked computer.** The `mcp__remote-devices__*` tools
   reach the user's workstation — not necessarily `lcs-phish-01`. Confirm which
   host you're on before assuming you can read `/opt/...`.

## Where to look

- `RECOMMENDATIONS.md` — the full prioritized review (the "why").
- `TASKS.md` — the backlog (the "what/next"), IDs `TASK-01`…; mirrors the task widget.
- `docs/` — architecture, reporting-path options (incl. Graph), troubleshooting.
- `docs/adr/` — decisions worth not re-litigating.
- `src/bridge.py` — reference bridge with the reliability fixes applied.
- `tests/` — fixture-based RID-extraction tests.

## Working agreement

Pick the next unblocked item from `TASKS.md`, do it on a branch, keep the
pipeline above working, and update `TASKS.md` + the commit message so the next
session sees state. Prefer small, reviewable commits.
