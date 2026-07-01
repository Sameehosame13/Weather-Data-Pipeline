"""
Test script: بيقرأ ملف raw JSON (سواء من extraction.py أو ملف sample جاهز)،
يعمل flatten + clean عليه، وبعدين يصدّر النتيجة CSV نضيف عشان تراجعه.

الاستخدام:
    python test_pipeline.py raw_sample_20260701_145805.json
    python test_pipeline.py raw_sample_20260701_145805.json --out cleaned_weather.csv
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from transformation import clean_data, flatten_all

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run(input_path: str, output_path: str) -> None:
    raw_file = Path(input_path)
    if not raw_file.exists():
        logger.error(f"File not found: {raw_file}")
        sys.exit(1)

    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    logger.info(f"Loaded raw data for {len(raw_data)} cities from {raw_file.name}")

    rows = flatten_all(raw_data)
    logger.info(f"Flattened into {len(rows)} rows")

    df = clean_data(rows)
    logger.info(f"Cleaned data shape: {df.shape}")

    # ملخص سريع عشان تتأكد إن كل حاجة تمام
    print("\n--- Summary ---")
    print("Rows:", len(df))
    print("Cities:", df["city"].nunique() if not df.empty else 0)
    print("Date range:", df["time"].min(), "->", df["time"].max() if not df.empty else "N/A")
    print("Missing values per column:\n", df.isna().sum())

    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Saved cleaned data → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the extraction+transformation pipeline and export a CSV")
    parser.add_argument("input", help="Path to raw JSON file (e.g. raw_sample_*.json)")
    parser.add_argument("--out", default="cleaned_weather.csv", help="Output CSV path")
    args = parser.parse_args()

    run(args.input, args.out)