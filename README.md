# lcs-phish-remediation

Hardening and remediation for Lakeway Christian Schools' authorized
phishing-awareness platform (Anglerphish on `lcs-phish-01`) and its reporting
bridge.

New here? Read [`CLAUDE.md`](CLAUDE.md) for full context, then
[`TASKS.md`](TASKS.md) for what to do next.

## Layout

```
lcs-phish-remediation/
├── CLAUDE.md             # project context — read first
├── README.md             # this file
├── RECOMMENDATIONS.md    # the prioritized technical review (the "why")
├── TASKS.md              # work backlog, TASK-01… (the "what/next")
├── .env.example          # bridge config template (no secrets)
├── requirements.txt
├── src/
│   └── bridge.py         # REFERENCE bridge with reliability fixes
├── tests/
│   ├── test_rid_extraction.py
│   └── fixtures/         # wrapped-report samples (add real ones — TASK-10)
├── deploy/
│   └── gophish-bridge.service   # hardened systemd unit
├── docs/
│   ├── 01-architecture.md
│   ├── 02-reporting-path-options.md   # IONOS now vs Graph/OAuth2 target
│   ├── 03-troubleshooting.md
│   └── adr/              # architecture decision records
└── scripts/
    └── capture-baseline.sh   # TASK-01 helper: pull running bridge into git
```

## Quick start (dev)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # fill in, then: chmod 600 .env
pytest                       # RID-extraction tests
```

## Status

Pipeline is operational (see `CLAUDE.md`). This repo tracks the work to make it
reliable, secure, and maintainable. Highest-priority open item is **TASK-01**
(commit the real running bridge as a baseline) — do it before adopting the
reference code here.
