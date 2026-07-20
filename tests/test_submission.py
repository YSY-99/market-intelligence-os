import csv
import tempfile
import unittest
from pathlib import Path

from market_intel.submission import validate_submission
from tests.test_ingest import ROW


class SubmissionTests(unittest.TestCase):
    def _write(self, path, rows):
        fieldnames = sorted({key for row in rows for key in row})
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _proposal(self):
        row = dict(ROW)
        row.update({
            "Company": "Community Source",
            "Website_URL": "https://example.org/",
            "Report_or_Research_URL": "https://example.org/data",
            "Blog_or_Insights_URL": "https://example.org/updates",
            "Data_Origin": "primary",
            "Access_Method": "api; web",
            "Decision_Types": "market_sizing",
            "Machine_Readable": "yes",
            "Business_Stage": "validation; launch",
            "Geography": "Global",
            "Geographic_Granularity": "country",
            "Methodology_Available": "yes",
            "Historical_Data_Available": "yes",
            "API_URL": "https://api.example.org/",
            "API_Docs_URL": "https://example.org/docs",
            "License": "Public domain",
            "Terms_or_Scraping_Restrictions": "Public API rate limits apply",
            "Contribution_Status": "pending",
            "Submitted_By": "community-member",
            "Provenance_URL": "https://example.org/about",
            "Publisher": "Example Agency",
            "Languages": "English",
            "Update_Frequency": "monthly",
            "Publication_Lag": "30 days",
        })
        return row

    def test_valid_submission(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            self._write(proposal, [self._proposal()])
            report = validate_submission(proposal, [])
            self.assertTrue(report["valid"])
            self.assertEqual(report["sources"], 1)

    def test_iso_country_code_is_valid_but_city_is_not_source_coverage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            row = self._proposal()
            row["Geography"] = "DE"
            self._write(proposal, [row])
            self.assertTrue(validate_submission(proposal, [])["valid"])
            row["Geography"] = "Warsaw"
            self._write(proposal, [row])
            report = validate_submission(proposal, [])
            self.assertFalse(report["valid"])
            self.assertIn("unsupported geography", " ".join(report["errors"]))

    def test_duplicate_against_baseline_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            baseline = Path(temp_dir) / "baseline.csv"
            row = self._proposal()
            self._write(proposal, [row])
            self._write(baseline, [row])
            report = validate_submission(proposal, [baseline])
            self.assertFalse(report["valid"])
            self.assertIn("duplicates existing source", " ".join(report["errors"]))

    def test_missing_provenance_and_restrictions_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            row = self._proposal()
            row["Provenance_URL"] = ""
            row["Terms_or_Scraping_Restrictions"] = ""
            self._write(proposal, [row])
            report = validate_submission(proposal, [])
            self.assertFalse(report["valid"])
            self.assertIn("explicit provenance", " ".join(report["errors"]))
            self.assertIn("terms or restrictions", " ".join(report["errors"]))

    def test_invalid_url_and_reviewed_status_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            row = self._proposal()
            row["Website_URL"] = "not-a-url"
            row["Contribution_Status"] = "reviewed"
            row["Reviewed_By"] = "self"
            self._write(proposal, [row])
            report = validate_submission(proposal, [])
            self.assertFalse(report["valid"])
            self.assertIn("invalid URL", " ".join(report["errors"]))
            self.assertIn("must be pending", " ".join(report["errors"]))

    def test_contributor_authority_future_date_and_unknown_vocab_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            row = self._proposal()
            row.update({
                "Authority_Score": "10",
                "Last_Verified": "9999-12-31",
                "Access_Method": "magic_connector",
                "Decision_Types": "make_me_rich",
            })
            self._write(proposal, [row])
            report = validate_submission(proposal, [])
            self.assertFalse(report["valid"])
            combined = " ".join(report["errors"])
            self.assertTrue("Authority" in combined or "authority" in combined)

    def test_same_canonical_url_under_new_name_is_duplicate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            baseline = Path(temp_dir) / "baseline.csv"
            proposed = self._proposal()
            existing = dict(proposed)
            existing.update({"Company": "Existing Name", "Contribution_Status": "seeded"})
            self._write(proposal, [proposed])
            self._write(baseline, [existing])
            report = validate_submission(proposal, [baseline])
            self.assertFalse(report["valid"])
            self.assertIn("duplicates existing URL", " ".join(report["errors"]))

    def test_empty_submission_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            self._write(proposal, [self._proposal()])
            lines = proposal.read_text(encoding="utf-8").splitlines()
            proposal.write_text(lines[0] + "\n", encoding="utf-8")
            report = validate_submission(proposal, [])
            self.assertFalse(report["valid"])

    def test_unknown_geography_and_intra_submission_url_duplicate_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            first = self._proposal()
            first["Geography"] = "Narnia"
            second = self._proposal()
            second["Company"] = "Another Community Source"
            self._write(proposal, [first, second])
            report = validate_submission(proposal, [])
            self.assertFalse(report["valid"])
            combined = " ".join(report["errors"])
            self.assertIn("unsupported geography", combined)
            self.assertIn("duplicates URL within submission", combined)

    def test_spreadsheet_formula_and_control_character_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proposal = Path(temp_dir) / "proposal.csv"
            row = self._proposal()
            row["Notes"] = "=HYPERLINK(\"https://evil.example\")"
            row["Description"] = "unsafe\x01text"
            self._write(proposal, [row])
            report = validate_submission(proposal, [])
            self.assertFalse(report["valid"])
            combined = " ".join(report["errors"])
            self.assertIn("spreadsheet formula", combined)
            self.assertIn("control characters", combined)


if __name__ == "__main__":
    unittest.main()
