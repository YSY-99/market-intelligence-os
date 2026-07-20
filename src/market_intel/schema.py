import re
import unicodedata
import ipaddress
from datetime import date, datetime
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse


SCHEMA_VERSION = "1.0"
PRIORITY_AUTHORITY = {"high": 9.0, "medium": 7.0, "low": 5.0}
TRUE_VALUES = {"1", "true", "yes", "y"}
FALSE_VALUES = {"0", "false", "no", "n"}
WILDCARD_DNS_SUFFIXES = (
    ".nip.io", ".sslip.io", ".xip.io", ".localtest.me", ".lvh.me", ".vcap.me",
)


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = re.sub(r"[^\w+#.-]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").casefold()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    if not slug:
        raise ValueError("Cannot create an ASCII id from company name")
    return slug


def parse_list(value: str) -> List[str]:
    seen = set()
    result = []
    for item in re.split(r"[;,]", value or ""):
        item = normalize_text(item)
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def authority_from_priority(priority: str) -> float:
    normalized = normalize_text(priority)
    if normalized not in PRIORITY_AUTHORITY:
        raise ValueError("Unsupported priority: {}".format(priority))
    return PRIORITY_AUTHORITY[normalized]


def validate_authority_score(value: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Authority score must be numeric: {}".format(value)) from error
    if not 0.0 <= score <= 10.0:
        raise ValueError("Authority score must be between 0 and 10: {}".format(value))
    return score


def parse_optional_bool(value: str) -> Optional[bool]:
    normalized = normalize_text(value)
    if not normalized:
        return None
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError("Boolean value must be yes/no or true/false: {}".format(value))


def validate_enum(value: str, allowed: Set[str], field_name: str, default: str = "") -> str:
    normalized = normalize_text(value)
    if not normalized:
        return default
    if normalized not in allowed:
        raise ValueError("Unsupported {}: {}".format(field_name, value))
    return normalized


def access_flags(value: str) -> Dict[str, object]:
    normalized = normalize_text(value)
    free = any(term in normalized for term in ("free", "freemium", "open data", "archive"))
    paid = any(term in normalized for term in ("paid", "commercial", "freemium", "platform", "subscription"))
    gated = "gated" in normalized
    return {"raw": value.strip(), "free": free, "paid": paid, "gated": gated}


def validate_date(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError("Date must use YYYY-MM-DD: {}".format(value)) from error
    if parsed > date.today():
        raise ValueError("Date cannot be in the future: {}".format(value))
    return value


def validate_public_url(value: str, field_name: str, allow_empty: bool = False) -> str:
    value = (value or "").strip()
    if not value and allow_empty:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("invalid URL in {}: {}".format(field_name, value))
    if parsed.username or parsed.password:
        raise ValueError("invalid URL credentials in {}: {}".format(field_name, value))
    hostname = parsed.hostname.casefold().rstrip(".")
    if not hostname or any(character.isspace() for character in hostname):
        raise ValueError("invalid URL host in {}: {}".format(field_name, value))
    if (
        hostname == "localhost"
        or hostname.endswith((".localhost", ".local", ".internal"))
        or hostname in {suffix[1:] for suffix in WILDCARD_DNS_SUFFIXES}
        or hostname.endswith(WILDCARD_DNS_SUFFIXES)
    ):
        raise ValueError("invalid private URL host in {}: {}".format(field_name, value))
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        if "." not in hostname or any(not label for label in hostname.split(".")):
            raise ValueError("invalid URL host in {}: {}".format(field_name, value))
    else:
        if not ip.is_global:
            raise ValueError("invalid private IP URL in {}: {}".format(field_name, value))
    try:
        parsed.port
    except ValueError as error:
        raise ValueError("invalid URL port in {}: {}".format(field_name, value)) from error
    return value
