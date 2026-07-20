# Security policy

## Supported versions

Security fixes are provided for the latest tagged release and the `main` branch.

## Reporting a vulnerability

Do not open a public issue for a vulnerability, credential, personal-data exposure, or bypass of the catalog review boundary. Use GitHub's **Report a vulnerability** private reporting feature. The maintainers will acknowledge a report within seven days and coordinate disclosure after a fix is available.

The repository currently performs local routing only and makes no network requests. URL validation is catalog hygiene, not a general-purpose SSRF defense. Any future retrieval component must meet the controls in [the threat model](docs/threat-model.md) before it is enabled.

Never include secrets, authentication tokens, private datasets, or personal information in issues, source submissions, fixtures, or logs.
