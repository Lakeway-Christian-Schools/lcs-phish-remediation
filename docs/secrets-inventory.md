# Secrets inventory (TASK-04)

Every secret the platform depends on, where it lives, who owns it, and how often
to rotate it. **No secret values go in this file or anywhere in git** — this is
a register, not a store. Fill in the owner/date columns as you confirm them.

Legend — Store: `env` = `/opt/gophish-bridge/.env` (640 root:gophish after
TASK-04) · `systemd` = unit `Environment=`/credential · `app-config` =
Anglerphish `config.json` · `external` = provider console · `fs` = file on host.

| Secret | Purpose | Store | Owner | Last rotated | Cadence | Notes |
|---|---|---|---|---|---|---|
| IONOS mailbox password | IMAP read + SMTP re-inject by the bridge (`IMAP_PASS`, `SMTP_PASS`) | `env` | _TBD_ | _set at TASK-04_ | 90 d | Likely one account for both; rotate together. Exposed while `.env` was 0644 → rotate now. |
| SMTP2Go API key / SMTP creds | Outbound campaign email from Anglerphish | `app-config` / `external` | _TBD_ | _TBD_ | 90 d | Check whether it was ever in a world-readable file; rotate if so. |
| MariaDB app password | Anglerphish → `anglerphish` DB (`127.0.0.1:3306`) | `app-config` | _TBD_ | _TBD_ | 180 d | Local-only bind; still rotate periodically. |
| `ANGLERPHISH_ENCRYPTION_KEY` | Encrypts stored SMTP creds + captured submissions at rest | `systemd` | _TBD_ | n/a | **do not rotate casually** | **Escrow off-host (TASK-08).** Re-keying re-encrypts data; losing the old value forfeits it. |
| TLS private key(s) — landing hosts | HTTPS for `phish/login/payroll/docs.lcstn.org` | `fs` | _TBD_ | _TBD_ | per cert (auto) | Let's Encrypt renews; key rotates on renewal. Restrict to `600 root`. |
| TLS private key — admin `:3333` | HTTPS for the admin listener | `fs` | _TBD_ | _TBD_ | per cert | Keep admin off the public internet regardless (TASK-19). |
| GitHub deploy key (server) | Read-only clone/pull of this repo on `lcs-phish-01` | `fs` (`~/.ssh`) | _TBD_ | _at TASK-15_ | on staff change | Created in TASK-15; read-only; one key per host. |
| `agent` SSH key (workstation→server) | Claude Code / admin access to `lcs-phish-01` | `fs` (workstation) | celder | 2026-11 | on staff change | Scoped sudo; revoke by removing from `authorized_keys`. |

## Handling rules

- Values live only in their store (above). This register names them; it never
  holds them.
- When reading a secret for maintenance, use a shell whose history isn't
  synced, and clear scrollback afterward.
- On any suspected exposure, rotate immediately and record the date here.
- New secret? Add a row **before** it goes into service.

## Open follow-ups
- TASK-04: rotate the IONOS credential and set its "Last rotated" date.
- TASK-08: escrow `ANGLERPHISH_ENCRYPTION_KEY` and record the vault location
  (not the value) here.
- TASK-15: create the server deploy key and record it here.
