import unittest

from market_intel.catalog import Catalog
from market_intel.ingest import convert_row
from tests.test_ingest import ROW


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.source = convert_row(ROW)
        self.catalog = Catalog([self.source])

    def test_get_source_returns_versioned_envelope(self):
        response = self.catalog.get_source("revenuecat")
        self.assertEqual(response["api_version"], "0.1")
        self.assertTrue(response["found"])
        self.assertEqual(response["source"]["company"], "RevenueCat")

    def test_get_source_reports_missing_record_without_guessing(self):
        response = self.catalog.get_source("unknown")
        self.assertFalse(response["found"])
        self.assertIsNone(response["source"])

    def test_list_intents_exposes_routing_metadata(self):
        response = self.catalog.list_intents()
        self.assertGreater(response["total"], 30)
        subscription = next(item for item in response["intents"] if item["name"] == "Subscription & Web2App")
        self.assertIn("subscriptions", subscription["topics"])
        self.assertIn("pricing", subscription["decision_types"])

    def test_coverage_is_derived_from_the_loaded_catalog(self):
        response = self.catalog.get_coverage()
        self.assertEqual(response["total_sources"], 1)
        self.assertEqual(response["categories"], {"Subscription & Web2App": 1})
        self.assertEqual(response["access_models"]["free"], 1)
        self.assertEqual(response["connector_statuses"]["not_implemented"], 1)

    def test_search_enforces_agent_safe_bounds(self):
        for query, limit in (("", 5), ("x" * 2001, 5), ("subscription", 0), ("subscription", 21)):
            with self.assertRaises(ValueError):
                self.catalog.search(query, limit=limit)

    def test_duplicate_source_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate source id"):
            Catalog([self.source, self.source])

    def test_returned_records_cannot_mutate_catalog_state(self):
        result = self.catalog.get_source("revenuecat")
        result["source"]["company"] = "Changed"
        self.assertEqual(self.catalog.get_source("revenuecat")["source"]["company"], "RevenueCat")


if __name__ == "__main__":
    unittest.main()
