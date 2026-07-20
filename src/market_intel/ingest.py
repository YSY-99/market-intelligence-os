import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Union

from .schema import (
    SCHEMA_VERSION,
    access_flags,
    authority_from_priority,
    normalize_text,
    parse_optional_bool,
    parse_list,
    slugify,
    validate_authority_score,
    validate_date,
    validate_enum,
    validate_public_url,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def repository_file(section: str, name: str) -> Path:
    project_path = PROJECT_ROOT / section / name
    if project_path.exists():
        return project_path
    installed_path = Path(sys.prefix) / "share" / "market-intelligence-os" / section / name
    if installed_path.exists():
        return installed_path
    return project_path


TAXONOMY_PATH = repository_file("config", "taxonomy.json")
REQUIRED_COLUMNS = {
    "Company", "Category", "Source_Type", "Description", "Best_For",
    "Flagship_Report_or_Resource", "Content_Format", "Website_URL",
    "Report_or_Research_URL", "Blog_or_Insights_URL", "Priority",
    "Access_Model", "Notes", "Last_Verified",
}
STOPWORDS = {
    "and", "the", "for", "with", "from", "into", "covering", "on", "of", "to", "a", "an",
    "и", "в", "на", "для", "из", "по", "с", "о",
}
DATA_ORIGINS = {"primary", "secondary", "user_generated", "owned", "unspecified"}
CONTRIBUTION_STATUSES = {"seeded", "reviewed", "pending", "rejected"}
ACCESS_METHODS = {"api", "bulk download", "web", "manual", "export"}
BUSINESS_STAGES = {"idea", "validation", "launch", "growth", "scale"}
CONNECTOR_STATUSES = {"not_implemented", "manual", "available", "degraded", "disabled"}
VERIFICATION_STATUSES = {"catalogued", "verified", "stale", "failed"}
MAX_CATALOG_BYTES = 2 * 1024 * 1024
MAX_CATALOG_ROWS = 1000
MAX_CELL_CHARACTERS = 10000
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
TRUSTED_SEED_PATHS = {
    (PROJECT_ROOT / "catalog" / "market_intelligence_sources.csv").resolve(),
    (PROJECT_ROOT / "catalog" / "public_primary_sources.csv").resolve(),
    (PROJECT_ROOT / "catalog" / "global_public_sources.csv").resolve(),
}
TRUSTED_REVIEWED_PATHS = {
    (PROJECT_ROOT / "catalog" / "community_reviewed_sources.csv").resolve(),
}


def load_taxonomy(path: Union[Path, str] = TAXONOMY_PATH) -> Dict[str, object]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _tokens(value: str) -> List[str]:
    return [token for token in normalize_text(value).split() if len(token) > 2 and token not in STOPWORDS]


def _content_formats(value: str) -> List[str]:
    return parse_list(re.sub(r"\s*(?:/|\+)\s*", ";", value or ""))


def convert_row(row: Dict[str, str], taxonomy: Dict[str, object] = None) -> Dict[str, object]:
    taxonomy = taxonomy or load_taxonomy()
    missing = [name for name in REQUIRED_COLUMNS if not (row.get(name) or "").strip()]
    if missing:
        raise ValueError("Missing required values: {}".format(", ".join(sorted(missing))))
    category = row["Category"].strip()
    if category not in taxonomy:
        raise ValueError("Unknown category: {}".format(category))
    best_for = parse_list(row["Best_For"])
    explicit_topics = parse_list(row.get("Topics") or "")
    category_topics = taxonomy[category]["topics"]
    topics = list(dict.fromkeys(
        explicit_topics + best_for if explicit_topics
        else [normalize_text(item) for item in category_topics] + best_for
    ))
    keyword_text = " ".join([
        row["Description"], row["Best_For"], row["Source_Type"],
        row["Flagship_Report_or_Resource"], category,
    ])
    explicit_keywords = parse_list(row.get("Keywords") or "")
    keywords = explicit_keywords or sorted(set(_tokens(keyword_text)))
    priority = normalize_text(row["Priority"])
    inferred_fields = []
    if not explicit_keywords:
        inferred_fields.append("keywords")
    if not explicit_topics:
        inferred_fields.append("topics")
    explicit_authority = (row.get("Authority_Score") or "").strip()
    if explicit_authority:
        authority_score = validate_authority_score(explicit_authority)
    else:
        authority_score = authority_from_priority(priority)
        inferred_fields.append("authority_score")
    explicit_origin = (row.get("Data_Origin") or "").strip()
    data_origin = validate_enum(explicit_origin, DATA_ORIGINS, "data origin", "unspecified")
    if not explicit_origin:
        inferred_fields.append("data_origin")
    access_methods = parse_list(row.get("Access_Method") or "")
    if not access_methods:
        access_methods = ["web"]
        inferred_fields.append("access_methods")
    invalid_access = sorted(set(access_methods).difference(ACCESS_METHODS))
    if invalid_access:
        raise ValueError("Unsupported access methods: {}".format(", ".join(invalid_access)))
    decision_types = parse_list(row.get("Decision_Types") or "")
    if not decision_types:
        decision_types = list(taxonomy[category].get("decision_types", []))
        inferred_fields.append("decision_types")
    allowed_decisions = {
        decision for rule in taxonomy.values() for decision in rule.get("decision_types", [])
    }
    invalid_decisions = sorted(set(decision_types).difference(allowed_decisions))
    if invalid_decisions:
        raise ValueError("Unsupported decision types: {}".format(", ".join(invalid_decisions)))
    business_stages = parse_list(row.get("Business_Stage") or "")
    invalid_stages = sorted(set(business_stages).difference(BUSINESS_STAGES))
    if invalid_stages:
        raise ValueError("Unsupported business stages: {}".format(", ".join(invalid_stages)))
    contribution_value = (row.get("Contribution_Status") or "").strip()
    contribution_status = validate_enum(
        contribution_value, CONTRIBUTION_STATUSES, "contribution status", "seeded"
    )
    if not contribution_value:
        inferred_fields.append("contribution.status")
    citation_value = (row.get("Citation_Required") or "").strip()
    citation_required = parse_optional_bool(citation_value)
    if citation_required is None:
        citation_required = True
        inferred_fields.append("citation_required")
    restrictions = (row.get("Terms_or_Scraping_Restrictions") or "").strip()
    if not restrictions and explicit_origin:
        restrictions = row["Notes"].strip()
        inferred_fields.append("terms_or_scraping_restrictions")
    provenance_url = (row.get("Provenance_URL") or "").strip()
    if not provenance_url:
        provenance_url = row["Website_URL"].strip()
        inferred_fields.append("contribution.provenance_url")
    website_url = validate_public_url(row["Website_URL"], "Website_URL")
    research_url = validate_public_url(row["Report_or_Research_URL"], "Report_or_Research_URL")
    blog_url = validate_public_url(row["Blog_or_Insights_URL"], "Blog_or_Insights_URL")
    provenance_url = validate_public_url(provenance_url, "Provenance_URL")
    api_url = validate_public_url(row.get("API_URL") or "", "API_URL", allow_empty=True)
    api_docs_url = validate_public_url(row.get("API_Docs_URL") or "", "API_Docs_URL", allow_empty=True)
    connector_status = validate_enum(
        row.get("Connector_Status") or "", CONNECTOR_STATUSES, "connector status", "not_implemented"
    )
    verification_status = validate_enum(
        row.get("Verification_Status") or "", VERIFICATION_STATUSES, "verification status", "catalogued"
    )
    reviewed_at_raw = (row.get("Reviewed_At") or "").strip()
    reviewed_at = validate_date(reviewed_at_raw) if reviewed_at_raw else ""
    content_updated_raw = (row.get("Content_Updated_At") or "").strip()
    content_updated_at = validate_date(content_updated_raw) if content_updated_raw else ""
    publisher = (row.get("Publisher") or "").strip()
    if not publisher:
        publisher = row["Company"].strip()
        inferred_fields.append("publisher")
    return {
        "schema_version": SCHEMA_VERSION,
        "id": slugify(row["Company"]),
        "company": row["Company"].strip(),
        "category": category,
        "subcategory": row["Source_Type"].strip(),
        "description": row["Description"].strip(),
        "best_for": best_for,
        "topics": topics,
        "keywords": keywords,
        "synonyms": parse_list(row.get("Synonyms") or ""),
        "source_type": row["Source_Type"].strip(),
        "content_formats": _content_formats(row["Content_Format"]),
        "access": access_flags(row["Access_Model"]),
        "urls": {
            "website": website_url,
            "research": research_url,
            "blog": blog_url,
        },
        "flagship_resources": [{
            "title": row["Flagship_Report_or_Resource"].strip(),
            "url": row["Report_or_Research_URL"].strip(),
        }],
        "priority": priority,
        "authority_score": authority_score,
        "publisher": publisher,
        "data_origin": data_origin,
        "access_methods": access_methods,
        "business_stages": business_stages,
        "decision_types": decision_types,
        "geographies": parse_list(row.get("Geography") or ""),
        "languages": parse_list(row.get("Languages") or ""),
        "geographic_granularity": parse_list(row.get("Geographic_Granularity") or ""),
        "industry_codes": parse_list(row.get("Industry_Codes") or ""),
        "methodology_available": parse_optional_bool(row.get("Methodology_Available") or ""),
        "citation_required": citation_required,
        "terms_or_scraping_restrictions": restrictions,
        "historical_data_available": parse_optional_bool(row.get("Historical_Data_Available") or ""),
        "machine_readable": parse_optional_bool(row.get("Machine_Readable") or ""),
        "license": (row.get("License") or "").strip(),
        "update_frequency": normalize_text(row.get("Update_Frequency") or ""),
        "publication_lag": normalize_text(row.get("Publication_Lag") or ""),
        "coverage_start": (row.get("Coverage_Start") or "").strip(),
        "coverage_end": (row.get("Coverage_End") or "").strip(),
        "integration": {
            "api_url": api_url,
            "api_auth": normalize_text(row.get("API_Auth") or ""),
            "api_docs_url": api_docs_url,
            "connector_status": connector_status,
        },
        "verification": {
            "status": verification_status,
            "verified_by": (row.get("Verified_By") or "").strip(),
            "metadata_checked_at": validate_date(row["Last_Verified"].strip()),
            "content_updated_at": content_updated_at,
        },
        "contribution": {
            "status": contribution_status,
            "submitted_by": (row.get("Submitted_By") or "").strip(),
            "reviewed_by": (row.get("Reviewed_By") or "").strip(),
            "reviewed_at": reviewed_at,
            "provenance_url": provenance_url,
        },
        "last_verified": validate_date(row["Last_Verified"].strip()),
        "notes": row["Notes"].strip(),
        "search_examples": [],
        "example_prompts": [],
        "when_not_to_use": [],
        "related_sources": [],
        "metadata": {
            "source": "csv",
            "inferred_fields": sorted(inferred_fields),
        },
    }


def load_csv(path: Union[Path, str], taxonomy: Dict[str, object] = None) -> List[Dict[str, object]]:
    taxonomy = taxonomy or load_taxonomy()
    input_path = Path(path)
    if input_path.stat().st_size > MAX_CATALOG_BYTES:
        raise ValueError("Catalog exceeds 2 MiB: {}".format(input_path))
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_columns = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing_columns:
            raise ValueError("Missing CSV columns: {}".format(", ".join(sorted(missing_columns))))
        raw_rows = list(reader)
    if len(raw_rows) > MAX_CATALOG_ROWS:
        raise ValueError("Catalog exceeds 1000 rows: {}".format(input_path))
    for row_number, row in enumerate(raw_rows, 2):
        for field, value in row.items():
            value = value or ""
            if len(value) > MAX_CELL_CHARACTERS:
                raise ValueError("Row {} field {} exceeds 10000 characters".format(row_number, field))
            if CONTROL_CHARACTERS.search(value):
                raise ValueError("Row {} field {} contains control characters".format(row_number, field))
            if value.lstrip().startswith(("=", "+", "-", "@")):
                raise ValueError("Row {} field {} contains a spreadsheet formula".format(row_number, field))
    records = [convert_row(row, taxonomy) for row in raw_rows]
    catalog_path = Path(path).resolve()
    try:
        catalog_label = catalog_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        catalog_label = catalog_path.name
    for record in records:
        record["metadata"]["catalog"] = catalog_label
    ids = [record["id"] for record in records]
    duplicates = sorted({source_id for source_id in ids if ids.count(source_id) > 1})
    if duplicates:
        raise ValueError("Duplicate source ids: {}".format(", ".join(duplicates)))
    return sorted(records, key=lambda record: record["id"])


def load_catalogs(
    paths: Iterable[Union[Path, str]],
    taxonomy: Dict[str, object] = None,
    require_approved: bool = True,
) -> List[Dict[str, object]]:
    taxonomy = taxonomy or load_taxonomy()
    records = []
    for path in paths:
        records.extend(load_csv(path, taxonomy))
    if require_approved:
        unapproved = []
        for record in records:
            catalog_path = Path(record["metadata"]["catalog"]).resolve()
            contribution = record["contribution"]
            if catalog_path in TRUSTED_SEED_PATHS:
                approved = contribution["status"] in {"seeded", "reviewed"}
            elif catalog_path in TRUSTED_REVIEWED_PATHS:
                approved = (
                    contribution["status"] == "reviewed"
                    and bool(contribution["reviewed_by"])
                    and bool(contribution["reviewed_at"])
                    and contribution["reviewed_by"] != contribution["submitted_by"]
                    and not reviewed_record_errors(record)
                )
            else:
                # Approval is conferred by an editor-controlled catalog path,
                # never by fields supplied inside an arbitrary external CSV.
                approved = False
            if not approved:
                unapproved.append(record["id"])
        unapproved.sort()
        if unapproved:
            raise ValueError(
                "Sources not approved for production: {}".format(", ".join(unapproved))
            )
    seen = set()
    duplicates = set()
    for record in records:
        if record["id"] in seen:
            duplicates.add(record["id"])
        seen.add(record["id"])
    if duplicates:
        raise ValueError("Duplicate source ids across catalogs: {}".format(", ".join(sorted(duplicates))))
    return sorted(records, key=lambda record: record["id"])


def reviewed_record_errors(record: Dict[str, object]) -> List[str]:
    """Return evidence gaps that prevent a community row from entering production."""
    inferred = set(record.get("metadata", {}).get("inferred_fields", []))
    errors = []
    required_values = {
        "data_origin": record.get("data_origin") not in {"", "unspecified"},
        "access_methods": bool(record.get("access_methods")) and "access_methods" not in inferred,
        "decision_types": bool(record.get("decision_types")) and "decision_types" not in inferred,
        "business_stages": bool(record.get("business_stages")),
        "geographies": bool(record.get("geographies")),
        "languages": bool(record.get("languages")),
        "geographic_granularity": bool(record.get("geographic_granularity")),
        "license": bool(record.get("license")),
        "terms_or_scraping_restrictions": bool(record.get("terms_or_scraping_restrictions"))
            and "terms_or_scraping_restrictions" not in inferred,
        "publisher": bool(record.get("publisher")) and "publisher" not in inferred,
        "update_frequency": bool(record.get("update_frequency")),
        "publication_lag": bool(record.get("publication_lag")),
        "provenance_url": "contribution.provenance_url" not in inferred,
    }
    for field, valid in required_values.items():
        if not valid:
            errors.append(field)
    for field in ("methodology_available", "historical_data_available", "machine_readable"):
        if record.get(field) is None:
            errors.append(field)
    if "api" in record.get("access_methods", []) and not record.get("integration", {}).get("api_docs_url"):
        errors.append("api_docs_url")
    return errors


def write_knowledge_base(records: Iterable[Dict[str, object]], output_dir: Union[Path, str]) -> Dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    records = sorted(list(records), key=lambda record: record["id"])
    json_path = output_path / "sources.json"
    jsonl_path = output_path / "sources.jsonl"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {
        "sources": len(records),
        "json": str(json_path),
        "jsonl": str(jsonl_path),
        "categories": len({record["category"] for record in records}),
    }
