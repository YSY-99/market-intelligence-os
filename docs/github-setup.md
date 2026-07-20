# GitHub launch settings

After creating the repository:

1. Confirm repository URLs in `README.md`, `pyproject.toml`, and `CITATION.cff`, plus maintainer/CODEOWNERS entries.
2. Enable Issues and private vulnerability reporting. Enable Discussions if there is moderation capacity.
3. Protect `main`: require the `CI / test` checks, pull requests, current branches, conversation resolution, CODEOWNERS review, and signed commits if the maintainer workflow supports them. Dismiss stale approvals; block force pushes and deletion.
4. Require two approvals for `catalog/`, `config/`, `.github/workflows/`, schemas, ingestion/validation, and high-risk source changes.
5. Do not expose Actions secrets to fork pull requests and do not introduce `pull_request_target` for untrusted code.
6. Add repository topics such as `market-intelligence`, `open-data`, `research`, `ai-agents`, and `python`.
7. Run the first release checklist only after code/data licenses are finalized.
