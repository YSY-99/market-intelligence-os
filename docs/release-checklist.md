# Release checklist

1. Confirm `LICENSE`, `LICENSE-DATA`, `NOTICE`, maintainer handles, repository URL, and CODEOWNERS.
2. Run `python scripts/check_repository.py` from a clean checkout.
3. Build wheel and sdist, install the wheel in a clean environment, and run CLI/Python API smoke tests outside the checkout.
4. Confirm generated data are unchanged and record their SHA-256 hashes.
5. Update `CHANGELOG.md`, package version, schema compatibility notes, and `CITATION.cff` together.
6. Obtain required editorial/security reviews and verify branch protection.
7. Tag the signed release and publish GitHub artifacts with provenance. PyPI publication is a separate explicit decision.
