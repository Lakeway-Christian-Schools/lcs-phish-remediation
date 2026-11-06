# BASELINE — known-good state captured 2026-11-06

TASK-01. The real running bridge, unit, and environment captured from
`lcs-phish-01` before any changes. **This is the rollback point.** The files:

- `src/bridge.prod.py` — the actual running script (`/opt/gophish-bridge/bridge.py`)
- `deploy/gophish-bridge.prod.service` — the live systemd unit
- `deploy/service.properties.txt` — `systemctl show` output (what it runs as)
- `deploy/opt-listing.txt` — `ls -la /opt/gophish-bridge/` (ownership/perms)
- `.env.captured-keys` — `.env` keys only, values redacted
- `docs/baseline-diff.txt` — full diff of prod vs the reference `src/bridge.py`

No secrets were committed. `src/bridge.prod.py` was checked: **all credentials
come from `os.getenv`** — nothing hard-coded. Good.

## What the running system actually is (corrects earlier assumptions)

| Item | Assumed earlier | **Actual** |
|---|---|---|
| Service user | `gophish-bridge` | **`User=gophish`** (primary group `gophish`) |
| venv path | `/opt/gophish-bridge/.venv` | **`/opt/gophish-bridge/venv`** |
| Unit hardening | none | **already has** `Restart=always`, `RestartSec=5`, `NoNewPrivileges=yes`, `PrivateTmp=yes`, `EnvironmentFile=` |
| Log rotation | missing | **already running externally** (logrotate: `bridge.log.1.gz` … `.7.gz`) |

So there is **no `gophish-bridge` user/group** — that name was a scaffold
guess. The service runs as `gophish`. Don't create a `gophish-bridge` group;
if TASK-15 introduces a dedicated hardened user, decide the name then.

## Findings that change the backlog

### 🔴 `.env` is world-readable — bump TASK-04
`opt-listing.txt` shows `-rw-r--r-- 1 root root 194 … .env` (mode 0644). Every
local account on `lcs-phish-01` can read the IMAP/SMTP credentials. This is the
most urgent concrete issue found. Fix: `chmod 640` (or `600`), `chown
root:gophish` (so the service user can still read it), and rotate the
credentials (they've been readable by any local user). Note this is also why
the capture didn't need sudo — the files were world-readable.

### 🟠 Re-injection loop is bounded *in practice* but fragile — keep TASK-05
The script re-injects with `sendmail(SMTP_USER, SMTP_USER, raw)` — i.e. back
into the **same mailbox it polls** — then moves the original to `Processed` and
deletes it from `INBOX`. The re-injected copy lands in `INBOX` as a new UNSEEN
message, so the bridge reads it again next cycle. It is *not* re-injected a
second time only because re-injection fires solely for **wrapped** reports
(parts that are `.eml` / `ms-tnef` / `message/rfc822`); the clean re-injected
copy has no such part, so it logs "No usable email found" and is just
moved/deleted. That's a lucky invariant, not a guard. A single change (e.g.
re-injecting a wrapped copy) would turn it into an amplifying loop. **Still add
the explicit marker header + skip (TASK-05).** Also confirm how the "Reported"
event is actually logged — presumably Anglerphish's own IMAP monitor watches
this same mailbox and parses the re-injected clean copy; that dependency should
be written down.

### 🟠 RID logged vs RID sent can disagree — folds into TASK-12
`extract_rid()` matches `rid=` (unanchored, no base64/QP recovery), but
`send_to_gophish()` gates on `"?rid=" in raw`. A report can log a
`REPORT_EVENT` yet be skipped at send (or vice-versa). The TASK-12 hardening
(anchor to landing hosts, decode QP/base64) should make detection and send use
the same logic.

### 🟢 Transient IMAP failures already self-heal somewhat — TASK-03 downgraded
`process_emails()` opens a fresh `IMAP4_SSL` every cycle, so an `Errno 111`
recovers on the next 30s pass without a manual restart. What's missing is
backoff and making a single bad message non-fatal. Lower urgency than the
review assumed, but still worth doing.

### Already-done items (don't redo)
- Log rotation (external logrotate) — TASK-11 reduces to adding an in-code
  **heartbeat** + alerting; file rotation is handled.
- Partial unit hardening — TASK-15 reduces to the deeper sandboxing
  (`ProtectSystem=strict`, `ProtectHome`, `ReadWritePaths`, `After=network-online.target`)
  and the dedicated-user decision.

## Reference vs production

`src/bridge.py` (reference, 339 lines) vs `src/bridge.prod.py` (actual, 202
lines): the reference adds self-healing/backoff, loop-marker, mark-seen-after-
send, anchored+base64 RID extraction, config validation, rotation/heartbeat.
The reference is a **target**, not a drop-in — adopt its changes incrementally
per task, re-validating the reporting path each step. Full diff in
`docs/baseline-diff.txt`.
