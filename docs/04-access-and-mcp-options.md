# 04 — Giving an agent access to the platform, and the "own MCP" question

Two separate decisions get tangled here:

1. **How does a coding agent (Claude Code) reach `lcs-phish-01` to do the work?**
2. **Should the platform expose its own remote tool surface (an MCP server)?**

They're independent. (1) is about *where the agent runs and how it touches the
host*. (2) is about *turning platform operations into callable tools*. Do (1)
now; (2) is a real but later, security-heavy idea. The actual prerequisite for
"work from anywhere" is neither — it's a **git remote** (see TASK-02).

---

## Part 1 — Getting Claude Code onto / connected to `lcs-phish-01`

Claude Code is a CLI that runs **where you install it**. `lcs-phish-01` is Linux
(Ubuntu-class), which is a supported platform (Ubuntu 20.04+, Debian 10+, 4 GB+
RAM, x64/ARM64). It needs an internet connection and a paid account
(Pro/Max/Team/Enterprise or a Console/API key). Three patterns:

### Option A — Run Claude Code *on* the server (best for host-level work)
Install it on `lcs-phish-01` and run it in a clone of this repo there. Then it
can read `/opt/anglerphish`, `/opt/gophish-bridge`, run `systemctl`, tail logs,
and do TASK-01's baseline capture directly.

```bash
# on lcs-phish-01, as a NON-root sudo user (not the anglerphish service user)
curl -fsSL https://claude.ai/install.sh | bash      # native installer
#   or Debian/Ubuntu apt repo, or: npm i -g @anthropic-ai/claude-code (Node 22+)
claude --version
claude            # first run walks through login
```

- **Headless login:** a server has no browser. Either set `ANTHROPIC_API_KEY`
  (Console account) in the environment, or do the browser login step on a
  machine that has one and reuse the credential. Confirm the current method in
  the auth docs — it changes.
- **Scope it down.** This is a production security box holding captured
  submissions. Run as a dedicated non-root user, use Claude Code's permission
  settings / allowed-tools to constrain it, and prefer a **staging clone** of
  the host for anything destructive. Don't run the agent as the `anglerphish`
  service account.

### Option B — Run Claude Code on your workstation, reach the server over SSH
Keep the agent on your machine; it drives the server by running `ssh`/`scp`
through its Bash tool. The agent never lives on prod; you own the SSH boundary
(key, jump host, allowed commands). Good default for TASK-01: `scp` the running
`bridge.py` + unit back, commit, done — you don't even need Claude Code on the
box for that.

### Option C — This cloud session + the desktop bridge (what we're in now)
This chat runs in an isolated cloud container linked to your **workstation**
through the Claude desktop app. It reaches your workstation's connected folders,
**not** `lcs-phish-01` — unless your workstation itself can reach the server
(e.g. it can `ssh lcs-phish-01`), in which case this session can drive that ssh
on the workstation. Fine for editing this repo; not a direct line to the server.

> Note: this container's own outbound network is allowlisted (package registries
> + GitHub), so it can push to a git remote but can't freely SSH to arbitrary
> hosts. That's another reason the git-remote path (TASK-02) is the clean bridge
> between "work here" and "work on the server."

### Recommended now
- **TASK-01 (baseline):** Option B or a plain `scp` — lowest risk, no agent on
  prod.
- **Ongoing host work (TASK-03/05/06/15):** Option A on a **staging clone** of
  `lcs-phish-01`, promoting changes to prod through your normal deploy.

---

## Part 2 — "Move it to its own MCP online"

MCP (Model Context Protocol) is **not** a hosting location — it's a protocol for
exposing *tools and resources* to an LLM client. "Move it to an MCP" really
means one of three different things:

### Interpretation 1 — A hosted MCP server that wraps *platform operations*
e.g. tools like `get_campaign_report_status(rid)`, `bridge_health()`,
`tail_bridge_log(n)`, `list_recent_reports()`. Any Claude session could then
operate/observe the platform through a defined API instead of SSH.

- **Upside:** clean, auditable, least-privilege *if* the tools are narrow;
  great for recurring ops and for letting non-admins check results safely.
- **Serious caveats:** this platform holds **captured credentials and reporter
  PII**. An internet-reachable MCP server over that data is a new, high-value
  attack surface. If you ever build it:
  - **read-only first** (telemetry: reported counts, health, last-poll time) —
    no "send campaign", no credential access;
  - require real auth (OAuth2/mTLS), bind tightly, log every call;
  - keep it on the internal network / VPN, not open to the internet;
  - treat it as in-scope for the same authorization and retention rules
    (TASK-14).
- **Verdict:** legitimate, but **premature**. Not needed for any current task.
  Revisit once the P1 reliability/security items are closed.

### Interpretation 2 — A persistent / remote *coding* agent
"Online" meaning the agent isn't tied to your laptop session. That's Option A/B
above plus a durable host (run Claude Code in `tmux`/as a service on a dev box,
or a cloud dev environment). This is about the agent's lifecycle, not MCP.

### Interpretation 3 — Hosting the *bridge itself* as a managed service
A real architecture change, and it's already on the roadmap in a better-scoped
form: TASK-07 (Graph/OAuth2 ingestion) removes IONOS and can run the bridge as a
small hosted worker. That's the migration to pursue — not an MCP.

### Bottom line
- The thing that makes this "work from anywhere" is a **private git remote**
  (TASK-02), not an MCP.
- An **ops MCP** is a nice-to-have for later, read-only, internal, authenticated
  — explicitly *after* the P1 items and under the same governance.
- The real service-ification is **TASK-07**, already planned.

---

## Decision summary

| Want | Do | Task |
|---|---|---|
| Capture the running bridge safely | SSH/scp from workstation (Option B) | TASK-01 |
| Work from anywhere, share state | Private git remote (GitHub/GitLab) | TASK-02 |
| Agent does host-level changes | Claude Code on a **staging clone** (Option A) | TASK-03+ |
| Operate/observe platform as tools | (Later) read-only internal MCP, authed | TASK-22 |
| Stop running your own mail hop | Graph/OAuth2 ingestion | TASK-07 |
