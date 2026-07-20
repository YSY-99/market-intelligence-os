import csv
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Union
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .ingest import PROJECT_ROOT, load_catalogs, load_csv
from .schema import normalize_text


TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
MAX_SUBMISSION_BYTES = 2 * 1024 * 1024
MAX_SUBMISSION_ROWS = 1000
MAX_CELL_CHARACTERS = 10000
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _canonical_url(value: str) -> str:
    parsed = urlparse(value)
    query = urlencode(sorted(
        (key, item) for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_") and key.casefold() not in TRACKING_PARAMETERS
    ))
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme.casefold(), parsed.netloc.casefold(), path, "", query, ""))


def validate_submission(
    proposal_path: Union[Path, str],
    baseline_paths: Iterable[Union[Path, str]],
) -> Dict[str, object]:
    errors: List[str] = []
    proposal_file = Path(proposal_path)
    try:
        if proposal_file.stat().st_size > MAX_SUBMISSION_BYTES:
            return {"valid": False, "sources": 0, "errors": ["Submission exceeds 2 MiB"]}
    except OSError as error:
        return {"valid": False, "sources": 0, "errors": [str(error)]}
    try:
        with proposal_file.open(encoding="utf-8-sig", newline="") as handle:
            raw_rows = list(csv.DictReader(handle))
    except OSError as error:
        return {"valid": False, "sources": 0, "errors": [str(error)]}
    if not raw_rows:
        return {"valid": False, "sources": 0, "errors": ["Submission must contain at least one source"]}
    if len(raw_rows) > MAX_SUBMISSION_ROWS:
        return {"valid": False, "sources": len(raw_rows), "errors": ["Submission exceeds 1000 rows"]}
    for index, row in enumerate(raw_rows, 2):
        for field, value in row.items():
            value = value or ""
            if len(value) > MAX_CELL_CHARACTERS:
                errors.append("Row {} field {} exceeds 10000 characters".format(index, field))
            if CONTROL_CHARACTERS.search(value):
                errors.append("Row {} field {} contains control characters".format(index, field))
            if value.lstrip().startswith(("=", "+", "-", "@")):
                errors.append("Row {} field {} contains a spreadsheet formula".format(index, field))
        if (row.get("Authority_Score") or "").strip():
            errors.append("Row {} cannot submit Authority_Score; authority is editorial".format(index))
        if (row.get("Contribution_Status") or "").strip().casefold() != "pending":
            errors.append("Row {} contribution status must be pending".format(index))
        if (row.get("Reviewed_By") or "").strip():
            errors.append("Row {} cannot self-declare reviewed_by".format(index))
    try:
        proposed = load_csv(proposal_path)
    except (OSError, ValueError) as error:
        errors.append(str(error))
        return {"valid": False, "sources": len(raw_rows), "errors": errors}
    try:
        baseline = load_catalogs(baseline_paths, require_approved=False) if baseline_paths else []
    except (OSError, ValueError) as error:
        return {"valid": False, "sources": len(proposed), "errors": ["Baseline error: {}".format(error)]}

    baseline_ids = {record["id"] for record in baseline}
    baseline_urls = {
        _canonical_url(url)
        for record in baseline
        for url in record["urls"].values()
        if url
    }
    with (PROJECT_ROOT / "config" / "geographies.json").open(encoding="utf-8") as handle:
        geography_rules = json.load(handle)
    allowed_geographies = {
        normalize_text(alias) for aliases in geography_rules.values() for alias in aliases
    }.union(normalize_text(code) for code in geography_rules)
    proposal_urls = set()
    for record in proposed:
        label = record["id"]
        inferred = set(record["metadata"]["inferred_fields"])
        if label in baseline_ids:
            errors.append("{} duplicates existing source".format(label))
        proposed_urls = {_canonical_url(url) for url in record["urls"].values() if url}
        if proposed_urls.intersection(baseline_urls):
            errors.append("{} duplicates existing URL".format(label))
        duplicate_proposal_urls = proposed_urls.intersection(proposal_urls)
        if duplicate_proposal_urls:
            errors.append("{} duplicates URL within submission".format(label))
        proposal_urls.update(proposed_urls)
        if record["contribution"]["status"] != "pending":
            errors.append("{} contribution status must be pending".format(label))
        if record["contribution"]["reviewed_by"]:
            errors.append("{} cannot self-declare reviewed_by".format(label))
        if record["verification"]["status"] != "catalogued":
            errors.append("{} cannot self-declare verification status".format(label))
        if record["verification"]["verified_by"]:
            errors.append("{} cannot self-declare verified_by".format(label))
        if not record["contribution"]["submitted_by"]:
            errors.append("{} requires submitted_by".format(label))
        if record["data_origin"] == "unspecified" or "data_origin" in inferred:
            errors.append("{} requires explicit data origin".format(label))
        if "access_methods" in inferred:
            errors.append("{} requires explicit access method".format(label))
        if not record["decision_types"] or "decision_types" in inferred:
            errors.append("{} requires explicit decision types".format(label))
        if not record["business_stages"]:
            errors.append("{} requires explicit business stages".format(label))
        if not record["geographies"]:
            errors.append("{} requires explicit geography".format(label))
        else:
            invalid_geographies = sorted(
                value for value in record["geographies"]
                if normalize_text(value) not in allowed_geographies
            )
            if invalid_geographies:
                errors.append("{} has unsupported geography: {}".format(
                    label, ", ".join(invalid_geographies)
                ))
        if not record["languages"]:
            errors.append("{} requires explicit languages".format(label))
        if not record["geographic_granularity"]:
            errors.append("{} requires geographic granularity".format(label))
        if record["methodology_available"] is None:
            errors.append("{} requires methodology_available yes/no".format(label))
        if record["historical_data_available"] is None:
            errors.append("{} requires historical_data_available yes/no".format(label))
        if record["machine_readable"] is None:
            errors.append("{} requires machine_readable yes/no".format(label))
        if not record["license"]:
            errors.append("{} requires explicit license or rights statement".format(label))
        if not record["publisher"] or "publisher" in inferred:
            errors.append("{} requires explicit publisher".format(label))
        if not record["update_frequency"]:
            errors.append("{} requires update frequency or unknown".format(label))
        if not record["publication_lag"]:
            errors.append("{} requires publication lag or unknown".format(label))
        if "api" in record["access_methods"] and not record["integration"]["api_docs_url"]:
            errors.append("{} declares API access but has no API_Docs_URL".format(label))
        if not record["terms_or_scraping_restrictions"] or "terms_or_scraping_restrictions" in inferred:
            errors.append("{} requires terms or restrictions statement".format(label))
        if "contribution.provenance_url" in inferred:
            errors.append("{} requires explicit provenance URL".format(label))

    return {"valid": not errors, "sources": len(proposed), "errors": errors}
