import unittest
import json
import tempfile
from datetime import date
from pathlib import Path

from market_intel.ingest import convert_row
from market_intel.router import detect_intents, load_knowledge_base, route_query
from tests.test_ingest import ROW


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.revenuecat = convert_row(ROW)
        competitor = dict(ROW)
        competitor.update({
            "Company": "Similarweb",
            "Category": "Web & Competitive Intelligence",
            "Source_Type": "Digital market intelligence",
            "Description": "Website traffic, competitor and audience intelligence.",
            "Best_For": "Website traffic; competitor benchmarking; market share",
            "Priority": "High",
            "Access_Model": "Freemium / paid",
        })
        self.similarweb = convert_row(competitor)

    def test_subscription_query_prefers_revenuecat(self):
        results = route_query("benchmark conversion for mobile subscriptions", [self.similarweb, self.revenuecat])
        self.assertEqual(results[0]["source"]["id"], "revenuecat")
        self.assertIn("score_breakdown", results[0])
        self.assertTrue(results[0]["matched_terms"])

    def test_library_rejects_invalid_limit(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            route_query("subscription", [self.revenuecat], limit=0)

    def test_knowledge_base_rejects_malformed_or_incompatible_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(json.dumps([{"schema_version": "2.0"}]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing"):
                load_knowledge_base(path)
            malformed = dict(self.revenuecat)
            malformed["urls"] = "https://example.org"
            path.write_text(json.dumps([malformed]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "field urls must be an object"):
                load_knowledge_base(path)
            malformed = dict(self.revenuecat)
            malformed["authority_score"] = "high"
            path.write_text(json.dumps([malformed]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "authority_score"):
                load_knowledge_base(path)

    def test_russian_competitor_query_prefers_similarweb(self):
        results = route_query("трафик сайта конкурента", [self.revenuecat, self.similarweb])
        self.assertEqual(results[0]["source"]["id"], "similarweb")

    def test_russian_subscription_word_forms(self):
        results = route_query("бенчмарк удержания для мобильных подписок", [self.similarweb, self.revenuecat])
        self.assertEqual(results[0]["source"]["id"], "revenuecat")

    def test_free_only_filter(self):
        paid = dict(self.similarweb)
        paid["id"] = "paid-only"
        paid["access"] = {"raw": "Paid", "free": False, "paid": True, "gated": False}
        results = route_query("competitor website traffic", [paid, self.similarweb], free_only=True)
        self.assertNotIn("paid-only", [result["source"]["id"] for result in results])

    def test_specific_intent_beats_shared_topic(self):
        saas_row = dict(ROW)
        saas_row.update({
            "Company": "SaaS Metrics Lab",
            "Category": "SaaS & B2B Benchmarks",
            "Source_Type": "SaaS benchmark research",
            "Description": "ARR, MRR and SaaS churn benchmarks.",
            "Best_For": "SaaS metrics; ARR; churn; B2B benchmarks",
        })
        saas = convert_row(saas_row)
        results = route_query("SaaS ARR churn benchmark", [self.revenuecat, saas])
        self.assertEqual(results[0]["source"]["id"], "saas-metrics-lab")

    def test_short_intent_aliases_match_whole_tokens_only(self):
        categories = {intent["category"] for intent in detect_intents("email marketing benchmarks")}
        self.assertNotIn("AI & Technology Research", categories)
        categories = {intent["category"] for intent in detect_intents("венчурные инвестиции")}
        self.assertNotIn("AI & Technology Research", categories)

    def test_ai_investment_query_routes_to_ai_and_vc(self):
        categories = {intent["category"] for intent in detect_intents("AI industry trends and investment")}
        self.assertIn("AI & Technology Research", categories)
        self.assertIn("VC & Strategy Research", categories)
        kb = Path(__file__).resolve().parents[1] / "data" / "sources.json"
        results = route_query("AI industry trends and investment", load_knowledge_base(kb), limit=10)
        result_categories = {result["source"]["category"] for result in results}
        self.assertIn("AI & Technology Research", result_categories)
        self.assertIn("VC & Strategy Research", result_categories)

    def test_consumer_behavior_scenario(self):
        kb = Path(__file__).resolve().parents[1] / "data" / "sources.json"
        results = route_query("consumer search behavior", load_knowledge_base(kb), limit=3)
        self.assertEqual(results[0]["source"]["category"], "Media & Consumer Behavior")

    def test_primary_source_domains_route_correctly(self):
        kb = Path(__file__).resolve().parents[1] / "data" / "sources.json"
        sources = load_knowledge_base(kb)
        cases = {
            "competitor 10-k financial statements": "Corporate & Financial Filings",
            "government tender contract award": "Procurement & Public Spending",
            "patent landscape scientific papers": "Patents & Scientific Research",
            "import export trade flows": "Trade & Supply Chain",
            "customer complaints feature requests": "Customer Voice & Reviews",
            "salary data competitor hiring": "Jobs & Talent Intelligence",
            "геоданные и выбор локации": "Local & Geospatial Intelligence",
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(route_query(query, sources, limit=1)[0]["source"]["category"], expected)

    def test_geography_constraints_prevent_wrong_jurisdiction(self):
        kb = Path(__file__).resolve().parents[1] / "data" / "sources.json"
        sources = load_knowledge_base(kb)
        self.assertEqual(
            route_query("company registry and ownership Brazil", sources, limit=1)[0]["source"]["id"],
            "opencorporates",
        )
        self.assertEqual(route_query("public procurement tenders India", sources, limit=5), [])
        self.assertEqual(route_query("insurance regulation Singapore", sources, limit=5), [])
        self.assertEqual(route_query("реестр компаний Казахстан владельцы", sources, limit=5), [])
        self.assertEqual(route_query("налоги и льготы для бизнеса в Беларуси", sources, limit=5), [])

    def test_lowercase_multilingual_and_region_geography_routing(self):
        kb = Path(__file__).resolve().parents[1] / "data" / "sources.json"
        sources = load_knowledge_base(kb)
        self.assertEqual(
            route_query("company filings uk", sources, limit=1)[0]["source"]["id"],
            "companies-house",
        )
        self.assertEqual(
            route_query("company filings us", sources, limit=1)[0]["source"]["id"],
            "sec-edgar",
        )
        self.assertEqual(
            route_query("GDPR regulation Germany", sources, limit=1)[0]["source"]["id"],
            "eur-lex",
        )
        self.assertEqual(
            route_query("госзакупки во Франции", sources, limit=1)[0]["source"]["id"],
            "ted-eu-tenders",
        )
        self.assertEqual(route_query("реестр компаний Германии владельцы", sources, limit=5), [])
        self.assertEqual(route_query("страховое регулирование в Японии", sources, limit=5), [])
        self.assertEqual(route_query("find us insurance regulation Singapore", sources, limit=5), [])
        self.assertEqual(route_query("give us public procurement tenders India", sources, limit=5), [])
        self.assertEqual(
            route_query("commercial real estate rents Warsaw", sources, limit=5),
            [],
        )

    def test_manual_synonym_enrichment_affects_ranking(self):
        enriched = dict(self.similarweb)
        enriched["id"] = "enriched"
        enriched["synonyms"] = ["growth-loop"]
        results = route_query("growth-loop", [self.revenuecat, enriched])
        self.assertEqual(results[0]["source"]["id"], "enriched")

    def test_recency_and_deterministic_tie_breaking(self):
        old = dict(self.revenuecat)
        old.update({"id": "z-old", "company": "Zulu", "last_verified": "2023-01-01", "verification": {"status": "verified"}})
        new = dict(self.revenuecat)
        new.update({"id": "a-new", "company": "Alpha", "last_verified": "2026-01-01", "verification": {"status": "verified"}})
        results = route_query("subscription", [old, new], today=date(2026, 7, 20))
        self.assertEqual(results[0]["source"]["id"], "a-new")
        old["last_verified"] = new["last_verified"]
        results = route_query("subscription", [old, new], today=date(2026, 7, 20))
        self.assertEqual([result["source"]["company"] for result in results], ["Alpha", "Zulu"])
        self.assertEqual(results[0]["score"], sum(results[0]["score_breakdown"].values()))


if __name__ == "__main__":
    unittest.main()
