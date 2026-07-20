# Governance

Market Intelligence OS is maintained as a public-interest source-routing project.

## Roles

- Contributors propose code, metadata, documentation, or source corrections.
- Editors verify source provenance, scope, rights metadata, conflicts, and routing claims.
- Maintainers approve releases, security changes, workflows, schemas, and editor membership.

Editors may not approve their own source submission. A disclosed commercial relationship requires recusal. High-risk sources involving sanctions, personal data, financial decisions, health, safety, or legal compliance require two independent approvals.

## Source lifecycle

New sources enter as `pending`, are reviewed in a pull request, and are added only to `catalog/community_reviewed_sources.csv`. The three initial seed catalogs are frozen by hashes in `config/seed_catalog_hashes.json`. Sources may be marked stale, restricted, or removed when provenance, availability, safety, ownership, or terms change.

Anyone may request correction, removal, or appeal through an issue. Personal-data and security requests must use the private channel described in `SECURITY.md`. Maintainers document the decision and its evidence; a maintainer with a conflict recuses.

## Repository controls

Before launch, enable branch protection on `main`: required CI, required current branch, dismissal of stale approvals, no force pushes, no direct pushes, and CODEOWNERS review. Use two approvals for the high-risk areas above and for workflow/security changes.
