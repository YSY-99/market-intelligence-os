import unittest

import market_intel


class PublicApiTests(unittest.TestCase):
    def test_version_and_default_catalog(self):
        self.assertEqual(market_intel.__version__, "0.1.0")
        self.assertGreater(len(market_intel.load_default_knowledge_base()), 200)

    def test_search_sources(self):
        results = market_intel.search_sources("mobile subscription conversion benchmark", limit=1)
        self.assertEqual(len(results), 1)
        self.assertIn("source", results[0])
        self.assertIn("score_breakdown", results[0])
        response = market_intel.search("mobile subscription conversion benchmark", limit=1)
        self.assertEqual(response["api_version"], "0.1")
        self.assertEqual(response["kb_schema_version"], "1.0")
        self.assertEqual(response["ranking_version"], "lexical-v1")


if __name__ == "__main__":
    unittest.main()
