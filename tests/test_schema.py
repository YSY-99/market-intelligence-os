import unittest

from market_intel.schema import (
    access_flags,
    authority_from_priority,
    parse_list,
    slugify,
    parse_optional_bool,
    validate_authority_score,
    validate_enum,
    validate_public_url,
    validate_date,
)


class SchemaTests(unittest.TestCase):
    def test_slugify_is_stable(self):
        self.assertEqual(slugify("RevenueCat Research"), "revenuecat-research")

    def test_parse_list(self):
        self.assertEqual(parse_list("Paywalls; LTV, retention"), ["paywalls", "ltv", "retention"])

    def test_priority_authority_defaults(self):
        self.assertEqual(authority_from_priority("High"), 9.0)
        self.assertEqual(authority_from_priority("Medium"), 7.0)
        self.assertEqual(authority_from_priority("Low"), 5.0)

    def test_access_flags(self):
        self.assertEqual(
            access_flags("Freemium / gated report"),
            {"raw": "Freemium / gated report", "free": True, "paid": True, "gated": True},
        )

    def test_validate_date(self):
        self.assertEqual(validate_date("2026-07-20"), "2026-07-20")
        with self.assertRaises(ValueError):
            validate_date("20/07/2026")
        with self.assertRaises(ValueError):
            validate_date("9999-12-31")

    def test_optional_bool_and_authority_validation(self):
        self.assertTrue(parse_optional_bool("yes"))
        self.assertFalse(parse_optional_bool("false"))
        self.assertIsNone(parse_optional_bool(""))
        with self.assertRaises(ValueError):
            parse_optional_bool("sometimes")
        self.assertEqual(validate_authority_score("9.5"), 9.5)
        with self.assertRaises(ValueError):
            validate_authority_score("11")

    def test_enum_validation(self):
        self.assertEqual(validate_enum("Primary", {"primary", "secondary"}, "origin"), "primary")
        with self.assertRaises(ValueError):
            validate_enum("unknown", {"primary", "secondary"}, "origin")

    def test_public_url_validation_rejects_ssrf_targets(self):
        self.assertEqual(validate_public_url("https://example.org/path", "url"), "https://example.org/path")
        for value in (
            "http://localhost/test",
            "http://127.0.0.1/test",
            "http://[::1]/test",
            "http://127.0.0.1.nip.io/test",
            "http://169.254.169.254.nip.io/latest/meta-data",
            "http://localtest.me/test",
            "https://user:pass@example.org/test",
            "https://.",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_public_url(value, "url")


if __name__ == "__main__":
    unittest.main()
