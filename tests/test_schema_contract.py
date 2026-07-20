import json
import unittest
from pathlib import Path

from market_intel import Catalog, load_default_knowledge_base, search
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

    def test_mcp_catalog_responses_match_published_schemas(self):
        catalog = Catalog()
        validate_json_schema(catalog.get_source("revenuecat"), self._schema("source-lookup.schema.json"), self.schema_dir)
        validate_json_schema(catalog.get_source("missing"), self._schema("source-lookup.schema.json"), self.schema_dir)
        validate_json_schema(catalog.list_intents(), self._schema("intent-list.schema.json"), self.schema_dir)
        validate_json_schema(catalog.get_coverage(), self._schema("coverage.schema.json"), self.schema_dir)

    def test_negative_schema_types_are_rejected(self):
        response = search("subscription", limit=1)
        response["results"][0]["score"] = "high"
        with self.assertRaisesRegex(ValueError, "score must be number"):
            validate_json_schema(response, self._schema("search-response.schema.json"), self.schema_dir)

    def test_lookup_schema_validates_the_nested_source(self):
        response = Catalog().get_source("revenuecat")
        response["source"]["authority_score"] = "trusted"
        with self.assertRaisesRegex(ValueError, "authority_score must be number"):
            validate_json_schema(response, self._schema("source-lookup.schema.json"), self.schema_dir)


if __name__ == "__main__":
    unittest.main()
