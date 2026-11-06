# 05 — Git remote & sync (TASK-02)

## Remote

- **URL:** https://github.com/Lakeway-Christian-Schools/lcs-phish-remediation
- **Visibility:** private (keep it so — documents internal security infra)
- **Default branch:** `main`

## Clone into your working copies

**Workstation (Windows):**
```powershell
gh repo clone Lakeway-Christian-Schools/lcs-phish-remediation
cd lcs-phish-remediation
```

**`lcs-phish-01`** (private repo needs credentials — pick one):
- **Deploy key (recommended):** generate a read-only SSH key on the server, add
  its public half as a *deploy key* on the GitHub repo, then
  `git clone git@github.com:Lakeway-Christian-Schools/lcs-phish-remediation.git`.
  Finalize this in TASK-15 when we settle the server's identity.
- **Fine-grained PAT:** a token scoped to just this repo, `Contents: read`.

## One-time: add the baseline tags

The two tags (`baseline`, `v0-scaffold`) couldn't be pushed from the build
environment (its git proxy rejects tag-ref pushes). Add them once from your
workstation after cloning — your normal GitHub auth has no such limitation:
```powershell
git tag baseline 1a28c5d      # TASK-01 known-good baseline
git tag v0-scaffold fccb090   # initial scaffold
git push origin baseline v0-scaffold
```
(Confirm the SHAs with `git log --oneline`; they are the "baseline" and
"Scaffold …" commits.)

## Daily workflow

```bash
git pull --rebase origin main     # before starting
# ...work, in small commits...
git add -A && git commit -m "TASK-NN: <what changed>"
git push origin main
```

- Keep `TASKS.md` updated in the same commit as the work it describes.
- Never commit secrets — `.gitignore` blocks `.env`, `*.prod.env`, logs, and the
  `src/bridge.prod.py` / `*.prod.service` guard (those were force-added once at
  baseline after a secret review; keep new secret-bearing files out).
- Prefer a branch per task for anything non-trivial:
  `git switch -c task-04-env-lockdown`, push, open a PR, merge to `main`.

## How Claude works with this repo now

With the remote live, changes land as commits pushed to `main` (or a task
branch), not as tarballs. When this session pushes, it's the same `git push`;
only tag-refs are blocked here, so tag changes are yours to make.
