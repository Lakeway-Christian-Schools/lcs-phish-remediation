# ADR-0002: Move ingestion to Graph/OAuth2 (target)

- Status: Proposed (TASK-07)
- Date: 2026-11-04

## Context
ADR-0001's IONOS hop is a workaround for the Basic-auth retirement. It adds a
provider, a forwarding exception, and loop risk.

## Decision
Authenticate to the M365 mailbox with modern auth: an Entra app (app-only
`Mail.Read`) scoped to `phishreport@lcstn.org` via application access policy,
reading over Graph (or IMAP XOAUTH2). Retire IONOS and the forwarding exception.

## Consequences
+ One provider, in-tenant, no forwarding exception, no loop; push via Graph
  subscriptions possible.
- Azure app registration + consent to manage; token lifecycle in the bridge.

## Rollout
Parallel-run vs the IONOS path on a seed campaign; flip behind a config flag;
keep IONOS warm one cycle as rollback. See docs/02-reporting-path-options.md.
