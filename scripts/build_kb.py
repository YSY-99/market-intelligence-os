#!/usr/bin/env python3
import argparse
import json

from market_intel.ingest import load_catalogs, write_knowledge_base


def main():
    parser = argparse.ArgumentParser(description="Build the market-intelligence knowledge base")
    parser.add_argument("csv_paths", nargs="+")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()
    records = load_catalogs(args.csv_paths)
    print(json.dumps(write_knowledge_base(records, args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
