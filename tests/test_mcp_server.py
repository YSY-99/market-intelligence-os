import unittest

from market_intel.catalog import Catalog
from market_intel.ingest import convert_row
from market_intel.mcp_server import create_mcp_server
from tests.test_ingest import ROW


class FakeMCP:
    def __init__(self, name, **settings):
        self.name = name
        self.settings = settings
        self.tools = {}
        self.run_transport = None

    def tool(self):
        def register(function):
            self.tools[function.__name__] = function
            return function
        return register

    def run(self, transport="stdio"):
        self.run_transport = transport


class MCPServerTests(unittest.TestCase):
    def setUp(self):
        catalog = Catalog([convert_row(ROW)])
        self.server = create_mcp_server(catalog=catalog, server_factory=FakeMCP)

    def test_registers_only_the_documented_read_only_tools(self):
        self.assertEqual(
            set(self.server.tools),
            {"search_sources", "get_source", "list_intents", "get_coverage"},
        )

    def test_search_tool_returns_structured_explained_results(self):
        response = self.server.tools["search_sources"]("subscription retention", 1, False)
        self.assertEqual(response["results"][0]["source"]["id"], "revenuecat")
        self.assertIn("score_breakdown", response["results"][0])

    def test_lookup_and_discovery_tools_share_catalog_contracts(self):
        self.assertTrue(self.server.tools["get_source"]("revenuecat")["found"])
        self.assertGreater(self.server.tools["list_intents"]()["total"], 30)
        self.assertEqual(self.server.tools["get_coverage"]()["total_sources"], 1)


if __name__ == "__main__":
    unittest.main()
