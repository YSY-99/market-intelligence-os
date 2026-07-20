# Threat model

## Current boundary

Version 0.1 loads local repository data and recommends links. It does not fetch pages, execute source content, or connect to third-party APIs. Catalog text, issue text, and future fetched documents are untrusted data and must never be interpreted as agent instructions.

## Threats and controls

- **Catalog poisoning:** arbitrary CSVs cannot enter production; community rows require repository-controlled review, frozen seeds, CI, and protected branches.
- **Self-approval and conflicts:** contributors cannot set authority or verification; editors recuse and high-risk sources require two approvals.
- **CSV/formula abuse:** submissions have file, row, and cell limits and reject control characters and spreadsheet-formula prefixes.
- **Path disclosure and artifact tampering:** catalog labels are repository-relative and CI reproduces JSON/JSONL byte-for-byte.
- **License/privacy abuse:** source metadata must state provenance and restrictions. The project does not redistribute linked source content. Secrets and personal data are forbidden.
- **Compromised automation:** CI has read-only permissions, no `pull_request_target`, and no fork secrets. Release signing and provenance are required before publishing packages.
- **Denial of service:** local submissions are size-limited. Hosted APIs will require request limits, quotas, timeouts, and log redaction.

## Requirements before network retrieval

A central safe fetcher must use an approved-host policy, resolve and validate every A/AAAA address immediately before connection, reject private/link-local/reserved/cloud-metadata ranges, pin the validated connection, and repeat checks for every redirect. It must cap redirects, time, bytes, decompression, and MIME types; apply rate limits, caching, robots/terms/licensing rules, and a clear user agent. Retrieved content is isolated from tool control, stored with URL/time/hash/provenance, and processed under deletion and privacy policies.
