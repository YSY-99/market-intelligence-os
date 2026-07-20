import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Union

from .ingest import load_taxonomy, repository_file
from .schema import normalize_text


QUERY_STOPWORDS = {
    "a", "an", "and", "are", "for", "from", "how", "in", "is", "latest", "me", "of", "on", "the", "to", "what", "with",
    "где", "для", "и", "как", "мне", "на", "найди", "найти", "о", "по", "с", "что", "это",
}
PRIORITY_POINTS = {"high": 5.0, "medium": 3.0, "low": 1.0}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
GEOGRAPHY_PATH = repository_file("config", "geographies.json")
GEOGRAPHY_REGIONS_PATH = repository_file("config", "geography_regions.json")
PLACE_GEOGRAPHY_PATH = repository_file("config", "place_geographies.json")
DECISION_TYPES_PATH = repository_file("config", "decision_types.json")
JURISDICTION_SENSITIVE_CATEGORIES = {
    "Corporate & Financial Filings", "Government & Business Statistics",
    "Procurement & Public Spending", "Regulation & Compliance",
    "Jobs & Talent Intelligence", "Local & Geospatial Intelligence",
    "Tax Incentives & Grants", "Standards & Certification",
    "Sector Regulators & Industry Data",
}
REQUIRED_SOURCE_FIELDS = {
    "schema_version", "id", "company", "category", "description", "best_for",
    "topics", "keywords", "access", "urls", "authority_score", "data_origin",
    "decision_types", "geographies", "integration", "verification", "contribution",
}


def validate_source_record(record: Dict[str, object], index: int = 0) -> None:
    """Validate the runtime fields used by routing and return field-specific errors."""
    if not isinstance(record, dict):
        raise ValueError("Knowledge-base record {} must be an object".format(index))
    missing = REQUIRED_SOURCE_FIELDS.difference(record)
    if missing:
        raise ValueError(
            "Knowledge-base record {} is missing: {}".format(index, ", ".join(sorted(missing)))
        )
    if record["schema_version"] != "1.0":
        raise ValueError(
            "Unsupported source schema version in record {}: {}".format(index, record["schema_version"])
        )
    for field in ("id", "company", "category", "description"):
        if not isinstance(record[field], str) or not record[field]:
            raise ValueError("Knowledge-base record {} field {} must be a non-empty string".format(index, field))
    for field in ("best_for", "topics", "keywords", "decision_types", "geographies"):
        if not isinstance(record[field], list) or not all(isinstance(item, str) for item in record[field]):
            raise ValueError("Knowledge-base record {} field {} must be a string array".format(index, field))
    authority = record["authority_score"]
    if isinstance(authority, bool) or not isinstance(authority, (int, float)) or not 0 <= authority <= 10:
        raise ValueError("Knowledge-base record {} field authority_score must be between 0 and 10".format(index))
    for field in ("access", "urls", "integration", "verification", "contribution"):
        if not isinstance(record[field], dict):
            raise ValueError("Knowledge-base record {} field {} must be an object".format(index, field))
    for field in ("free", "paid", "gated"):
        if not isinstance(record["access"].get(field), bool):
            raise ValueError("Knowledge-base record {} field access.{} must be boolean".format(index, field))
    for field in ("website", "research", "blog"):
        if not isinstance(record["urls"].get(field), str):
            raise ValueError("Knowledge-base record {} field urls.{} must be a string".format(index, field))
    if not isinstance(record["verification"].get("status"), str):
        raise ValueError("Knowledge-base record {} field verification.status must be a string".format(index))
    if not isinstance(record["integration"].get("connector_status"), str):
        raise ValueError("Knowledge-base record {} field integration.connector_status must be a string".format(index))
    if not isinstance(record["contribution"].get("status"), str):
        raise ValueError("Knowledge-base record {} field contribution.status must be a string".format(index))
    last_verified = record.get("last_verified")
    if not isinstance(last_verified, str):
        raise ValueError("Knowledge-base record {} field last_verified must be a date string".format(index))
    try:
        datetime.strptime(last_verified, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError("Knowledge-base record {} field last_verified must use YYYY-MM-DD".format(index)) from error


def _stem(token: str) -> str:
    if token.isascii() and len(token) > 4:
        if token.endswith("ies"):
            return token[:-3] + "y"
        if token.endswith("s") and not token.endswith("ss"):
            return token[:-1]
    return token


def _tokens(text: str) -> Set[str]:
    return {_stem(token) for token in normalize_text(text).split() if token not in QUERY_STOPWORDS and len(token) > 1}


def _term_matches(term: str, query_normalized: str, query_tokens: Set[str]) -> bool:
    term_normalized = normalize_text(term)
    term_tokens = _tokens(term_normalized)
    if not term_tokens:
        return False
    return term_tokens.issubset(query_tokens)


def _load_json(path: Path) -> Dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def detect_decision_types(query: str, rules: Dict[str, object] = None) -> Set[str]:
    rules = rules or _load_json(DECISION_TYPES_PATH)
    normalized = normalize_text(query)
    tokens = _tokens(query)
    return {
        decision for decision, aliases in rules.items()
        if any(_term_matches(alias, normalized, tokens) for alias in aliases)
    }


def detect_geographies(
    query: str,
    rules: Dict[str, object] = None,
    allow_lowercase_codes: bool = False,
) -> Set[str]:
    rules = rules or _load_json(GEOGRAPHY_PATH)
    normalized = normalize_text(query)
    tokens = _tokens(query)
    result = set()
    for code, aliases in rules.items():
        for alias in aliases:
            normalized_alias = normalize_text(alias)
            if normalized_alias in {"us", "uk", "eu"}:
                uppercase_match = re.search(r"\b{}\b".format(re.escape(normalized_alias.upper())), query)
                safe_lowercase = normalized_alias in {"uk", "eu"}
                if normalized_alias == "us" and allow_lowercase_codes:
                    safe_lowercase = bool(re.search(
                        r"\b(?:in|for|from|market|filings?|regulation|procurement|tenders?|tax|grants?|registry|statistics|data|prices?|jobs?)\s+(?:the\s+)?us\b",
                        normalized,
                    ))
                if uppercase_match or (safe_lowercase and _term_matches(alias, normalized, tokens)):
                    result.add(code)
                    break
            elif _term_matches(alias, normalized, tokens):
                result.add(code)
                break
    place_rules = _load_json(PLACE_GEOGRAPHY_PATH)
    for code, aliases in place_rules.items():
        if any(_term_matches(alias, normalized, tokens) for alias in aliases):
            result.add(code)
    result.discard("GLOBAL")
    return result


def _geography_alias_index(rules: Dict[str, object]) -> Dict[str, str]:
    index = {
        normalize_text(alias): code
        for code, aliases in rules.items()
        for alias in aliases
    }
    index.update({normalize_text(code): code for code in rules})
    return index


def _source_geography_codes(source: Dict[str, object], alias_index: Dict[str, str]) -> Set[str]:
    values = {normalize_text(value) for value in source.get("geographies", [])}
    return {alias_index[value] for value in values if value in alias_index}


def _geographies_intersect(
    source_codes: Set[str], query_codes: Set[str], regions: Dict[str, object]
) -> bool:
    if "GLOBAL" in source_codes or source_codes.intersection(query_codes):
        return True
    for region, members in regions.items():
        member_codes = set(members)
        if region in source_codes and query_codes.intersection(member_codes):
            return True
        if region in query_codes and source_codes.intersection(member_codes):
            return True
    return False


def detect_intents(query: str, taxonomy: Dict[str, object] = None) -> List[Dict[str, object]]:
    taxonomy = taxonomy or load_taxonomy()
    query_normalized = normalize_text(query)
    query_tokens = _tokens(query)
    intents = []
    for category, rule in taxonomy.items():
        matched = [term for term in rule["query_terms"] if _term_matches(term, query_normalized, query_tokens)]
        if matched:
            matched_concepts = [
                concept for concept, aliases in rule.get("concept_aliases", {}).items()
                if any(_term_matches(alias, query_normalized, query_tokens) for alias in aliases)
            ]
            intents.append({
                "category": category,
                "matched_terms": matched,
                "strength": len(matched),
                "routing_topics": matched_concepts or rule.get("topics", []),
            })
    return intents


def _freshness_points(last_verified: str, today: Optional[date] = None) -> float:
    today = today or date.today()
    verified = datetime.strptime(last_verified, "%Y-%m-%d").date()
    age_days = max(0, (today - verified).days)
    if age_days <= 365:
        return 5.0
    if age_days <= 730:
        return 3.0
    if age_days <= 1095:
        return 1.0
    return 0.0


def _record_text(record: Dict[str, object], fields: Iterable[str]) -> str:
    values = []
    for field in fields:
        value = record.get(field, "")
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        else:
            values.append(str(value))
    return " ".join(values)


def score_source(
    query: str,
    source: Dict[str, object],
    intents: List[Dict[str, object]],
    today: Optional[date] = None,
    detected_decisions: Set[str] = None,
    query_geographies: Set[str] = None,
    geography_rules: Dict[str, object] = None,
    geography_alias_index: Dict[str, str] = None,
    geography_tokens: Set[str] = None,
    geography_regions: Dict[str, object] = None,
) -> Optional[Dict[str, object]]:
    detected_decisions = detected_decisions or set()
    query_geographies = query_geographies or set()
    geography_rules = geography_rules or _load_json(GEOGRAPHY_PATH)
    geography_alias_index = geography_alias_index or _geography_alias_index(geography_rules)
    geography_regions = geography_regions or _load_json(GEOGRAPHY_REGIONS_PATH)
    geography_tokens = geography_tokens or _tokens(" ".join(
        alias for aliases in geography_rules.values() for alias in aliases
    ))
    query_tokens = _tokens(query)
    intended_categories = {intent["category"] for intent in intents}
    category_match = source["category"] in intended_categories
    source_intents = [intent for intent in intents if intent["category"] == source["category"]]
    routing_tokens = set()
    for intent in intents:
        if intent["category"] == source["category"]:
            routing_tokens.update(_tokens(" ".join(intent.get("routing_topics", []))))

    primary_topic_tokens = _tokens(_record_text(source, ("best_for", "source_type", "flagship_resources")))
    canonical_fields = ["keywords", "synonyms"]
    if "topics" not in source.get("metadata", {}).get("inferred_fields", []):
        canonical_fields.append("topics")
    canonical_metadata_tokens = _tokens(_record_text(source, canonical_fields))
    topic_tokens = primary_topic_tokens.union(canonical_metadata_tokens)
    topic_overlap = sorted(query_tokens.intersection(topic_tokens))
    routed_topic_overlap = sorted(routing_tokens.intersection(primary_topic_tokens).difference(query_tokens))
    description_tokens = _tokens(_record_text(source, ("company", "description", "subcategory", "source_type")))
    description_overlap = sorted(query_tokens.intersection(description_tokens))
    routed_description_overlap = sorted(routing_tokens.intersection(description_tokens).difference(query_tokens))

    source_geographies = _source_geography_codes(source, geography_alias_index)
    if query_geographies and source["category"] in JURISDICTION_SENSITIVE_CATEGORIES and not source_geographies:
        return None
    if query_geographies and source_geographies:
        if not _geographies_intersect(source_geographies, query_geographies, geography_regions):
            return None
    direct_specific_overlap = query_tokens.intersection(primary_topic_tokens.union(description_tokens)).difference(geography_tokens)
    if query_geographies and source["category"] in JURISDICTION_SENSITIVE_CATEGORIES and "GLOBAL" in source_geographies:
        return None
    if query_geographies and intents and not category_match:
        return None
    if query_geographies and not intents and len(direct_specific_overlap) < 2:
        return None
    if (
        query_geographies
        and source["category"] in JURISDICTION_SENSITIVE_CATEGORIES
        and not category_match
        and not direct_specific_overlap
    ):
        return None

    intent_strength = max((intent.get("strength", 1) for intent in source_intents), default=0)
    category_score = min(30.0, 20.0 + max(0, intent_strength - 1) * 5.0) if category_match else 0.0
    topic_score = min(25.0, len(topic_overlap) * 6.0 + len(routed_topic_overlap) * 2.5)
    description_score = min(15.0, len(description_overlap) * 5.0 + len(routed_description_overlap) * 1.5)
    matched_decisions = sorted(detected_decisions.intersection(source.get("decision_types", [])))
    decision_score = min(10.0, len(matched_decisions) * 5.0)
    relevance_score = category_score + topic_score + description_score + decision_score
    if relevance_score <= 0:
        return None

    authority_score = min(10.0, max(0.0, float(source.get("authority_score", 0.0))))
    priority_score = PRIORITY_POINTS.get(source.get("priority", ""), 0.0)
    verification_status = source.get("verification", {}).get("status")
    freshness_score = (
        _freshness_points(source["last_verified"], today)
        if verification_status in {None, "verified"}
        else 0.0
    )
    breakdown = {
        "intent_category": category_score,
        "topic_best_for": topic_score,
        "description_title": description_score,
        "decision_fit": decision_score,
        "authority": authority_score,
        "priority": priority_score,
        "freshness": freshness_score,
    }
    matched_intents = source_intents
    recommended_url = source["urls"].get("research") or source["urls"].get("website")
    caveats = []
    if source["access"].get("gated"):
        caveats.append("registration may be required")
    if not source["access"].get("free"):
        caveats.append("paid access may be required")
    if query_geographies and not source_geographies:
        caveats.append("geographic coverage is unverified")
        breakdown["geography_uncertainty"] = -5.0
    return {
        "source": source,
        "score": round(sum(breakdown.values()), 2),
        "score_breakdown": breakdown,
        "matched_terms": sorted(set(topic_overlap + description_overlap)),
        "matched_routing_concepts": sorted(set(routed_topic_overlap + routed_description_overlap)),
        "matched_intents": matched_intents,
        "matched_decisions": matched_decisions,
        "query_geographies": sorted(query_geographies),
        "source_geographies": sorted(source_geographies),
        "recommended_url": recommended_url,
        "caveats": caveats,
    }


def route_query(
    query: str,
    sources: Iterable[Dict[str, object]],
    limit: int = 10,
    free_only: bool = False,
    taxonomy: Dict[str, object] = None,
    today: Optional[date] = None,
) -> List[Dict[str, object]]:
    if not normalize_text(query):
        raise ValueError("Query cannot be empty")
    if limit <= 0:
        raise ValueError("Limit must be a positive integer")
    taxonomy = taxonomy or load_taxonomy()
    intents = detect_intents(query, taxonomy)
    decisions = detect_decision_types(query)
    geography_rules = _load_json(GEOGRAPHY_PATH)
    geography_alias_index = _geography_alias_index(geography_rules)
    geography_regions = _load_json(GEOGRAPHY_REGIONS_PATH)
    geography_tokens = _tokens(" ".join(
        alias for aliases in geography_rules.values() for alias in aliases
    ) + " " + " ".join(
        alias for aliases in _load_json(PLACE_GEOGRAPHY_PATH).values() for alias in aliases
    ))
    query_geographies = detect_geographies(
        query, geography_rules, allow_lowercase_codes=bool(intents or decisions)
    )
    results = []
    for source in sources:
        if free_only and not source["access"].get("free"):
            continue
        result = score_source(
            query, source, intents, today,
            detected_decisions=decisions,
            query_geographies=query_geographies,
            geography_rules=geography_rules,
            geography_alias_index=geography_alias_index,
            geography_tokens=geography_tokens,
            geography_regions=geography_regions,
        )
        if result is not None:
            results.append(result)
    results.sort(key=lambda result: (-result["score"], result["source"]["company"].casefold()))
    return results[:max(0, limit)]


def load_knowledge_base(path: Union[Path, str]) -> List[Dict[str, object]]:
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("Knowledge base must contain a JSON array")
    for index, record in enumerate(payload):
        validate_source_record(record, index)
    return payload
