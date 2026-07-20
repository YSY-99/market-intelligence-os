import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from market_intel.cli import main
from market_intel.ingest import convert_row, write_knowledge_base
from tests.test_ingest import ROW


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.kb = Path(self.temp_dir.name) / "sources.json"
        write_knowledge_base([convert_row(ROW)], Path(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_search_json(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--kb", str(self.kb), "search", "subscription retention", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["results"][0]["source"]["id"], "revenuecat")

    def test_inspect(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--kb", str(self.kb), "inspect", "revenuecat"])
        self.assertEqual(code, 0)
        self.assertIn("RevenueCat", output.getvalue())

    def test_search_text_limit_and_russian_query(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--kb", str(self.kb), "search", "мобильных подписок", "--limit", "1"])
        self.assertEqual(code, 0)
        self.assertIn("1. RevenueCat", output.getvalue())
        self.assertNotIn("2.", output.getvalue())

    def test_missing_kb_is_user_facing_error(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            code = main(["--kb", str(Path(self.temp_dir.name) / "missing.json"), "search", "test"])
        self.assertEqual(code, 2)
        self.assertIn("Cannot load knowledge base", error.getvalue())

    def test_free_only_cli_filter(self):
        paid_row = dict(ROW)
        paid_row.update({"Company": "Paid Source", "Access_Model": "Paid"})
        write_knowledge_base([convert_row(ROW), convert_row(paid_row)], Path(self.temp_dir.name))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--kb", str(self.kb), "search", "subscription", "--free-only", "--json"])
        self.assertEqual(code, 0)
        ids = [result["source"]["id"] for result in json.loads(output.getvalue())["results"]]
        self.assertNotIn("paid-source", ids)

    def test_empty_query_and_negative_limit_are_user_facing_errors(self):
        for arguments in (["search", ""], ["search", "subscription", "--limit", "-1"]):
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                code = main(["--kb", str(self.kb)] + arguments)
            self.assertEqual(code, 2)
            self.assertTrue(error.getvalue())


if __name__ == "__main__":
    unittest.main()
