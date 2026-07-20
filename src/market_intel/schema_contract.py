import json
import re
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse


def validate_json_schema(
    value: object,
    schema: Dict[str, object],
    base_dir: Path,
    path: str = "$",
) -> None:
    """Validate the dependency-free JSON Schema subset used by public v0.1 contracts."""
    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or reference.startswith(("http:", "https:")):
            raise ValueError("{} uses an unsupported schema reference".format(path))
        with (base_dir / reference).open(encoding="utf-8") as handle:
            validate_json_schema(value, json.load(handle), base_dir, path)
        return
    if "const" in schema and value != schema["const"]:
        raise ValueError("{} must equal {!r}".format(path, schema["const"]))
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError("{} is outside the allowed enum".format(path))
    expected_type = schema.get("type")
    type_matches = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }
    if expected_type and not type_matches.get(expected_type, False):
        raise ValueError("{} must be {}".format(path, expected_type))
    if isinstance(value, dict):
        required = set(schema.get("required", []))
        missing = required.difference(value)
        if missing:
            raise ValueError("{} is missing {}".format(path, ", ".join(sorted(missing))))
        properties = schema.get("properties", {})
        for key, child_schema in properties.items():
            if key in value:
                validate_json_schema(value[key], child_schema, base_dir, "{}.{}".format(path, key))
        if schema.get("additionalProperties") is False:
            unexpected = set(value).difference(properties)
            if unexpected:
                raise ValueError("{} has unexpected fields {}".format(path, ", ".join(sorted(unexpected))))
        additional_schema = schema.get("additionalProperties")
        if isinstance(additional_schema, dict):
            for key in set(value).difference(properties):
                validate_json_schema(value[key], additional_schema, base_dir, "{}.{}".format(path, key))
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            validate_json_schema(item, schema["items"], base_dir, "{}[{}]".format(path, index))
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ValueError("{} is shorter than minLength".format(path))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ValueError("{} does not match pattern".format(path))
        if schema.get("format") == "uri":
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("{} must be an absolute URI".format(path))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError("{} is below minimum".format(path))
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError("{} is above maximum".format(path))
