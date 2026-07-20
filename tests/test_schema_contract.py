import json
import unittest
from pathlib import Path

from market_intel import load_default_knowledge_base, search
from market_intel.schema_contract import validate_json_schema


class SchemaContractTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.schema_dir = self.root / "schemas"

    def _schema(self, name):
        with (self.schema_dir / name).open(encoding="utf-8") as handle:
            return json.load(handle)

    def test_source_and_search_response_match_published_schemas(self):
        sources = load_default_knowledge_base()
        validate_json_schema(sources[0], self._schema("source.schema.json"), self.schema_dir)
        validate_json_schema(search("subscription", sources, limit=1), self._schema("search-response.schema.json"), self.schema_dir)

    def test_negative_schema_types_are_rejected(self):
        response = search("subscription", limit=1)
        response["results"][0]["score"] = "high"
        with self.assertRaisesRegex(ValueError, "score must be number"):
            validate_json_schema(response, self._schema("search-response.schema.json"), self.schema_dir)


if __name__ == "__main__":
    unittest.main()
