import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from market_intel.ingest import convert_row, load_catalogs, load_csv, write_knowledge_base


ROW = {
    "Company": "RevenueCat",
    "Category": "Subscription & Web2App",
    "Source_Type": "Subscription infrastructure / benchmarks",
    "Description": "Subscription conversion and retention benchmarks.",
    "Best_For": "Subscription apps; paywalls; LTV; retention",
    "Flagship_Report_or_Resource": "State of Subscription Apps",
    "Content_Format": "Annual report",
    "Website_URL": "https://www.revenuecat.com/",
    "Report_or_Research_URL": "https://www.revenuecat.com/state-of-subscription-apps-2025/",
    "Blog_or_Insights_URL": "https://www.revenuecat.com/blog/",
    "Priority": "High",
    "Access_Model": "Freemium / gated report",
    "Notes": "Use latest edition.",
    "Last_Verified": "2026-07-20",
}


class IngestTests(unittest.TestCase):
    def test_convert_row_preserves_urls_and_normalizes_lists(self):
        record = convert_row(ROW)
        self.assertEqual(record["id"], "revenuecat")
        self.assertEqual(record["best_for"][0], "subscription apps")
        self.assertEqual(record["urls"]["research"], ROW["Report_or_Research_URL"])
        self.assertIn("subscriptions", record["topics"])
        self.assertTrue({"authority_score", "keywords", "topics"}.issubset(record["metadata"]["inferred_fields"]))

    def test_load_csv_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sources.csv"
            header = list(ROW)
            import csv
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=header)
                writer.writeheader()
                writer.writerow(ROW)
                writer.writerow(ROW)
            with self.assertRaises(ValueError):
                load_csv(path)

    def test_catalog_label_is_independent_of_absolute_or_relative_input(self):
        project_root = Path(__file__).resolve().parents[1]
        relative = Path("catalog/community_submission_template.csv")
        absolute = project_root / relative
        self.assertEqual(
            load_csv(relative)[0]["metadata"]["catalog"],
            load_csv(absolute)[0]["metadata"]["catalog"],
        )

    def test_write_knowledge_base(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = write_knowledge_base([convert_row(ROW)], Path(temp_dir))
            self.assertEqual(summary["sources"], 1)
            self.assertTrue((Path(temp_dir) / "sources.json").exists())
            self.assertTrue((Path(temp_dir) / "sources.jsonl").exists())

    def test_expanded_metadata_fields(self):
        row = dict(ROW)
        row.update({
            "Authority_Score": "10",
            "Data_Origin": "primary",
            "Access_Method": "api; bulk download",
            "Business_Stage": "validation; growth",
            "Decision_Types": "market_sizing; competitor_analysis",
            "Geography": "United States",
            "Geographic_Granularity": "county; state",
            "Industry_Codes": "NAICS",
            "Methodology_Available": "yes",
            "Citation_Required": "true",
            "Terms_or_Scraping_Restrictions": "Respect API rate limits",
            "Historical_Data_Available": "yes",
            "Machine_Readable": "true",
            "API_URL": "https://api.example.com/",
            "API_Auth": "api_key",
            "API_Docs_URL": "https://example.com/docs",
            "License": "public domain",
            "Contribution_Status": "reviewed",
            "Submitted_By": "seed-team",
            "Reviewed_By": "editor",
            "Provenance_URL": "https://example.com/about",
            "Connector_Status": "available",
            "Publisher": "Example Agency",
            "Languages": "English; Spanish",
            "Update_Frequency": "monthly",
            "Publication_Lag": "30 days",
            "Verification_Status": "verified",
            "Verified_By": "editor",
            "Content_Updated_At": "2026-07-01",
        })
        record = convert_row(row)
        self.assertEqual(record["authority_score"], 10.0)
        self.assertEqual(record["data_origin"], "primary")
        self.assertEqual(record["access_methods"], ["api", "bulk download"])
        self.assertEqual(record["decision_types"], ["market_sizing", "competitor_analysis"])
        self.assertTrue(record["machine_readable"])
        self.assertEqual(record["integration"]["api_auth"], "api_key")
        self.assertEqual(record["integration"]["connector_status"], "available")
        self.assertEqual(record["publisher"], "Example Agency")
        self.assertEqual(record["languages"], ["english", "spanish"])
        self.assertEqual(record["verification"]["status"], "verified")
        self.assertEqual(record["contribution"]["status"], "reviewed")

    def test_load_catalogs_detects_cross_file_duplicates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            import csv
            paths = [Path(temp_dir) / "one.csv", Path(temp_dir) / "two.csv"]
            for path in paths:
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(ROW))
                    writer.writeheader()
                    writer.writerow(ROW)
            with self.assertRaises(ValueError):
                load_catalogs(paths)

    def test_load_catalogs_rejects_pending_sources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            import csv
            path = Path(temp_dir) / "pending.csv"
            row = dict(ROW)
            row["Contribution_Status"] = "pending"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            with self.assertRaisesRegex(ValueError, "not approved for production"):
                load_catalogs([path])

    def test_external_reviewed_catalog_cannot_self_approve(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            import csv
            path = Path(temp_dir) / "reviewed.csv"
            row = dict(ROW)
            row["Contribution_Status"] = "reviewed"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            with self.assertRaisesRegex(ValueError, "not approved for production"):
                load_catalogs([path])

    def test_trusted_reviewed_catalog_still_requires_full_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            import csv
            path = Path(temp_dir) / "community_reviewed_sources.csv"
            row = dict(ROW)
            row.update({
                "Contribution_Status": "reviewed",
                "Submitted_By": "submitter",
                "Reviewed_By": "editor",
                "Reviewed_At": "2026-07-20",
            })
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            with patch("market_intel.ingest.TRUSTED_REVIEWED_PATHS", {path.resolve()}):
                with self.assertRaisesRegex(ValueError, "not approved for production"):
                    load_catalogs([path])
            row.update({"Reviewed_By": "editor", "Reviewed_At": "2026-07-20"})
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            with self.assertRaisesRegex(ValueError, "not approved for production"):
                load_catalogs([path])


if __name__ == "__main__":
    unittest.main()
