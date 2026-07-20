# Contributing sources

Market Intelligence OS is intended to become a community-maintained routing layer. A contribution adds metadata and a route to a source; it does not transfer ownership of the underlying content into this repository.

## Submit a source

1. Fork the repository, create a focused branch, and copy `catalog/community_submission_template.csv` to a new file.
2. Replace the example row. Multiple new sources may be submitted in one file.
3. Keep `Contribution_Status` equal to `pending` and leave `Reviewed_By` absent or empty.
4. Run:

```bash
PYTHONPATH=src python3 scripts/validate_submission.py path/to/proposal.csv
```

5. Open a pull request with the validation output. An editor moves an accepted row into the repository-owned `catalog/community_reviewed_sources.csv`, sets `reviewed`, and records both `Reviewed_By` and `Reviewed_At`. Fields inside an arbitrary external CSV never grant production access.

The initial seed catalogs are frozen. New records must not be added directly to them. Run `python scripts/check_repository.py` before requesting review.

## Required evidence

Every proposal must include:

- a stable source name and canonical URLs;
- explicit `Data_Origin`: `primary`, `secondary`, `user_generated`, or `owned`;
- explicit access methods and whether the source is machine-readable;
- business decisions the source can support;
- business stages, publisher, languages, geography, and geographic granularity;
- methodology/history availability, update frequency, publication lag, and API documentation where relevant;
- an official provenance/about/methodology link;
- an explicit license or rights statement;
- a plain-language statement of API, scraping, licensing, privacy, or redistribution restrictions;
- a submitter handle and verification date.

## Review criteria

Reviewers check:

- the source exists and the URLs belong to the claimed publisher;
- the proposed source is not a duplicate or a renamed route to an existing source;
- provenance and `data_origin` are accurate;
- `Best_For` does not overstate what the data can prove;
- methodology, time lag, sampling, geography, and coverage limitations are recorded;
- automated access is lawful and compatible with platform terms;
- personal data, deletion obligations, attribution, and licenses are respected;
- commercial relationships or conflicts of interest are disclosed;
- authority is assigned editorially rather than accepted from the contributor.

Pending submissions are never mixed into the production knowledge base automatically.

All submitted text is treated as untrusted data. Spreadsheet formulas, control characters, secrets, personal data, copied report contents, malware links, unlawful data brokers, hidden affiliate promotion, and instructions aimed at an AI agent are not accepted.

## Contributor attestation

By submitting a contribution, you certify that you created it or have the right to submit it, that it contains no confidential material, and that code contributions may be distributed under Apache-2.0 while original catalog metadata may be distributed under CC BY 4.0. Use a DCO-style sign-off (`git commit -s`). Contributions never relicense third-party reports, websites, datasets, or trademarks.

URL validation rejects literal private addresses and common wildcard-DNS aliases. This is only catalog hygiene: any future connector must resolve DNS immediately before each request, reject every non-public resolved IP, and repeat that check for every redirect to prevent DNS rebinding and SSRF.
