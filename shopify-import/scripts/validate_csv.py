#!/usr/bin/env python3
"""Validate a platform CSV before importing into Shopify.

Usage:
  python3 validate_csv.py <path-to-csv> --platform <platform-name>

Checks:
  Blocking (errors): file missing, unsupported platform, missing headers, parse failure,
                     >100 variants, >3 options, zero parseable products
  Warning: $0 price, missing SKU, duplicate SKUs, empty description, title >255 chars,
           sale price >= regular price, skipped items

Platform names: square, woocommerce, etsy, wix, amazon, ebay, clover,
                lightspeed-r, lightspeed-x, google-merchant-center
"""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from parsers import PARSERS, REQUIRED_HEADERS


def validate(csv_path, platform):
    """Validate a CSV for import. Returns (errors, warnings, stats).

    errors: list of str — blocking issues, import should not proceed
    warnings: list of str — non-blocking, merchant should review
    stats: dict or None — includes product/variant counts, skipped items,
           and 'products'/'skipped' keys with the parsed data so callers
           can reuse without parsing again
    """
    errors = []
    warnings = []

    # --- Blocking checks ---

    if not os.path.exists(csv_path):
        errors.append(f"File not found: {csv_path}")
        return errors, warnings, None

    parser = PARSERS.get(platform)
    if parser is None:
        errors.append(f"Unsupported platform: {platform}")
        errors.append(f"Supported: {', '.join(sorted(PARSERS.keys()))}")
        return errors, warnings, None

    # Check headers
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
    except Exception as e:
        errors.append(f"Could not read CSV: {e}")
        return errors, warnings, None

    required = REQUIRED_HEADERS.get(platform, [])
    missing = [h for h in required if h not in headers]
    if missing:
        errors.append(f"Missing required headers for {platform}: {', '.join(missing)}")
        errors.append(f"Found headers: {', '.join(headers[:20])}{'...' if len(headers) > 20 else ''}")

    # Try parsing
    try:
        products, skipped = parser(csv_path)
    except Exception as e:
        errors.append(f"Parse error: {e}")
        return errors, warnings, None

    if not products and not skipped:
        errors.append("No products found in CSV. Check that the file is not empty and the platform is correct.")
        return errors, warnings, None

    # --- Per-product blocking checks ---

    all_skus = []
    for p in products:
        title = p["input"]["title"]
        if len(p["input"]["variants"]) > 100:
            errors.append(f"'{title}' has {len(p['input']['variants'])} variants (max 100)")
        if len(p["input"]["productOptions"]) > 3:
            errors.append(f"'{title}' has {len(p['input']['productOptions'])} options (max 3)")

    # --- Warning checks ---

    for p in products:
        title = p["input"]["title"]

        # Title length
        if len(title) > 255:
            warnings.append(f"Title exceeds 255 chars for '{title[:50]}...' — will be accepted but may display poorly")

        # Empty description
        if not p["input"].get("descriptionHtml", "").strip():
            warnings.append(f"Empty description for '{title}'")

        for v in p["input"]["variants"]:
            sku = v.get("sku", "")

            # Zero price
            if v["price"] == 0:
                warnings.append(f"Price is $0 for variant '{sku or 'no SKU'}' in '{title}' — review after import")

            # Missing SKU
            if not sku:
                warnings.append(f"Missing SKU for a variant in '{title}'")
            else:
                all_skus.append(sku)

            # compareAtPrice sanity (should never happen if parsers are correct, but defense in depth)
            if "compareAtPrice" in v and v["compareAtPrice"] <= v["price"]:
                warnings.append(f"Compare-at price (${v['compareAtPrice']}) ≤ price (${v['price']}) for '{sku}' in '{title}' — compare-at will be ignored by Shopify")

    # Duplicate SKUs
    seen_skus = set()
    duplicate_skus = set()
    for sku in all_skus:
        if sku in seen_skus:
            duplicate_skus.add(sku)
        seen_skus.add(sku)
    if duplicate_skus:
        warnings.append(f"Duplicate SKUs found: {', '.join(sorted(duplicate_skus))} — Shopify allows this but it may indicate a data error")

    # --- Stats ---

    total_variants = sum(len(p["input"]["variants"]) for p in products)
    total_inventory = sum(sum(p["inventory"]) for p in products)

    stats = {
        "products": len(products),
        "variants": total_variants,
        "skipped": skipped,
        "inventory_total": total_inventory,
        # Include parsed data so callers (e.g. import.py) can reuse without parsing twice.
        # skipped is already in stats["skipped"] — no separate _parsed_skipped needed.
        "_parsed_products": products,
    }

    return errors, warnings, stats


def main():
    ap = argparse.ArgumentParser(description="Validate a platform CSV for Shopify import")
    ap.add_argument("csv_path", help="Path to the CSV file")
    ap.add_argument("--platform", required=True, help="Source platform name")
    args = ap.parse_args()

    print(f"🔍 Validating: {args.csv_path}")
    print(f"📦 Platform: {args.platform}")
    print()

    errors, warnings, stats = validate(args.csv_path, args.platform)

    if errors:
        print("❌ ERRORS (must fix before importing):")
        for e in errors:
            print(f"  • {e}")
        print()

    if warnings:
        print("⚠️  WARNINGS (review after import):")
        for w in warnings:
            print(f"  • {w}")
        print()

    if stats:
        print("📊 VALIDATION SUMMARY:")
        print(f"  Products to import: {stats['products']}")
        print(f"  Variants total:     {stats['variants']}")
        print(f"  Inventory units:    {stats['inventory_total']}")
        if stats["skipped"]:
            print(f"  Will be skipped:    {len(stats['skipped'])}")
            for s in stats["skipped"]:
                print(f"    • {s['title']} ({s['reason']})")
        print()
        if not errors:
            print("✅ Ready to import!")
        else:
            print("🚫 Fix errors above before importing.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
