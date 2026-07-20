# Source coverage

## Current baseline

The production knowledge base contains 213 sources across 36 routing categories. The original 141 sources remain the digital and secondary-research layer. The additional 72 records cover public filings, business statistics, procurement, patents and science, trade, customer voice, regulation, labor, geospatial analysis, taxes and grants, trademarks, standards, climate, energy, real estate, logistics, demographics, sector data, B2B sales, cyber risk, and pricing.

Explicit origins in the expanded catalog:

- 42 primary sources;
- 14 user-generated platforms;
- 16 secondary/aggregation sources;
- 141 legacy records awaiting origin backfill and therefore marked `unspecified`.

The `unspecified` label is deliberate. Community editors should backfill provenance rather than infer it silently.

## Decision coverage

The taxonomy now supports routing for:

- market selection and sizing;
- problem and customer discovery;
- competitor analysis;
- pricing and unit economics;
- product and technology validation;
- channel selection and growth;
- sales intelligence and procurement;
- regulatory risk;
- fundraising;
- geographic expansion.

## Known boundaries

The catalog cannot be permanently complete. Coverage will vary by country, language, industry, and data-access law. Important community expansion areas include national company registers, local statistical offices, sector regulators, municipal open-data portals, country-specific procurement systems, and specialist forums.

Owned sources such as CRM, product analytics, payments, customer support, interviews, and sales calls are intentionally not bundled. Deployments may add them as `data_origin=owned` without publishing private data.

User-generated sources are routes for lawful research rather than permission to scrape. Each connector must enforce platform terms, licensing, privacy, deletion, attribution, and rate limits.
