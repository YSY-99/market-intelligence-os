#!/usr/bin/env python3
import argparse
import json

from market_intel.submission import validate_submission


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a community source catalog")
    parser.add_argument("proposal")
    parser.add_argument(
        "--baseline",
        nargs="*",
        default=[
            "catalog/market_intelligence_sources.csv",
            "catalog/public_primary_sources.csv",
            "catalog/global_public_sources.csv",
            "catalog/community_reviewed_sources.csv",
        ],
    )
    args = parser.parse_args()
    report = validate_submission(args.proposal, args.baseline)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
